import asyncio
from typing import Optional
import httpx
from fastmcp.client import Client
from fastmcp.client.auth import BearerAuth

from . import config
from .display import console


class MCPSession:
    """Wrapper to hold both the client and session for proper lifecycle management."""

    def __init__(self, client: Client, session):
        self.client = client
        self.session = session

    async def list_tools(self):
        """List available tools from the MCP server."""
        return await self.session.list_tools()

    async def call_tool(self, name: str, arguments: dict):
        """Call a tool with the given arguments."""
        return await self.session.call_tool(name, arguments)

    async def cleanup(self):
        """Close the MCP session."""
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception:
                # Suppress session termination errors (these are harmless cleanup warnings)
                pass


async def wake_up_server(health_url: str, max_attempts: int = 6, wait_seconds: float = 5) -> bool:
    """
    Wake up a suspended server by calling the health endpoint.
    Useful for Fly.io and other platforms that suspend inactive services.

    Args:
        health_url: The health endpoint URL
        max_attempts: Maximum number of health check attempts
        wait_seconds: Seconds to wait between attempts

    Returns:
        True if server is awake, False otherwise
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        with console.status("  [dim]Polling health endpoint...[/dim]", spinner="dots") as status:
            for attempt in range(1, max_attempts + 1):
                try:
                    status.update(f"  [dim]Attempt {attempt}/{max_attempts}...[/dim]")
                    response = await client.get(health_url)

                    if response.status_code == 200:
                        return True
                    else:
                        if attempt == max_attempts:
                            console.print(
                                f"  [yellow]Server responded with status {response.status_code}[/yellow]"
                            )

                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    if config.VERBOSE or attempt == max_attempts:
                        error_msg = f"  [yellow]Connection failed: {type(e).__name__}[/yellow]"
                        if config.VERBOSE:
                            error_msg += f" [dim]({str(e)})[/dim]"
                        console.print(error_msg)
                except Exception as e:
                    if config.VERBOSE or attempt == max_attempts:
                        console.print(f"  [red]Unexpected error: {e}[/red]")

                if attempt < max_attempts:
                    await asyncio.sleep(wait_seconds)

    return False


async def connect_to_mcp_server(
    max_attempts: int = 3, wait_seconds: float = 5
) -> Optional[MCPSession]:
    """
    Connect to the MCP server with retry logic.

    Args:
        max_attempts: Maximum connection attempts
        wait_seconds: Seconds to wait between attempts

    Returns:
        MCPSession instance or None if failed
    """
    server_url = config.MCP_SERVER_URL or ""
    token = config.MCP_TOKEN or ""

    with console.status("  [dim]Establishing connection...[/dim]", spinner="dots") as status:
        for attempt in range(1, max_attempts + 1):
            client = None
            try:
                status.update(f"  [dim]Attempt {attempt}/{max_attempts}...[/dim]")

                client = Client(
                    server_url,
                    auth=BearerAuth(token=token),
                    init_timeout=30.0,  # Extended timeout for cold starts
                    timeout=600.0,  # Wait up to 10 minutes for tool operations
                )

                # Enter the client context and capture the session
                session = await client.__aenter__()
                return MCPSession(client, session)

            except asyncio.TimeoutError:
                if config.VERBOSE or attempt == max_attempts:
                    console.print("  [red]Timeout (server not responding)[/red]")
                # Clean up partial connection
                if client:
                    try:
                        await client.__aexit__(None, None, None)
                    except Exception:
                        pass
                if attempt < max_attempts:
                    await asyncio.sleep(wait_seconds)
            except Exception as e:
                error_name = type(e).__name__
                if config.VERBOSE or attempt == max_attempts:
                    if "BrokenResourceError" in error_name or "ClosedResourceError" in error_name:
                        console.print("  [yellow]Connection error (server not ready)[/yellow]")
                    else:
                        console.print(f"  [red]{error_name}: {e}[/red]")

                    if config.VERBOSE and not (
                        "BrokenResourceError" in error_name or "ClosedResourceError" in error_name
                    ):
                        import traceback

                        console.print(f"[dim]{traceback.format_exc()}[/dim]")

                # Clean up partial connection
                if client:
                    try:
                        await client.__aexit__(None, None, None)
                    except Exception:
                        pass

                if attempt < max_attempts:
                    await asyncio.sleep(wait_seconds)

    return None


async def connect_and_list_tools(
    max_attempts: int = 3, wait_seconds: float = 5
) -> tuple[Optional[MCPSession], list]:
    """
    Connect to MCP server AND list tools in a single retry loop.

    This combines connection and tool listing to avoid session expiry
    between the two operations.

    Args:
        max_attempts: Maximum connection attempts
        wait_seconds: Seconds to wait between attempts

    Returns:
        Tuple of (MCPSession instance or None, list of tools)
    """
    server_url = config.MCP_SERVER_URL or ""
    token = config.MCP_TOKEN or ""

    with console.status("  [dim]Establishing connection...[/dim]", spinner="dots") as status:
        for attempt in range(1, max_attempts + 1):
            client = None
            try:
                status.update(f"  [dim]Attempt {attempt}/{max_attempts}...[/dim]")

                client = Client(
                    server_url,
                    auth=BearerAuth(token=token),
                    init_timeout=30.0,  # Extended timeout for cold starts
                    timeout=600.0,  # Wait up to 10 minutes for tool operations
                )

                # Enter the client context and capture the session
                session = await client.__aenter__()
                mcp_session = MCPSession(client, session)

                # Immediately list tools while session is fresh
                status.update(
                    f"  [dim]Retrieving tools (attempt {attempt}/{max_attempts})...[/dim]"
                )
                tools = await asyncio.wait_for(mcp_session.list_tools(), timeout=15.0)

                return mcp_session, tools

            except asyncio.TimeoutError:
                if config.VERBOSE or attempt == max_attempts:
                    console.print("  [red]Timeout (server not responding)[/red]")
                # Clean up partial connection
                if client:
                    try:
                        await client.__aexit__(None, None, None)
                    except Exception:
                        pass
                if attempt < max_attempts:
                    await asyncio.sleep(wait_seconds)
            except Exception as e:
                error_name = type(e).__name__
                if config.VERBOSE or attempt == max_attempts:
                    if "BrokenResourceError" in error_name or "ClosedResourceError" in error_name:
                        console.print("  [yellow]Connection error (server not ready)[/yellow]")
                    else:
                        console.print(f"  [red]{error_name}: {e}[/red]")

                    if config.VERBOSE and not (
                        "BrokenResourceError" in error_name or "ClosedResourceError" in error_name
                    ):
                        import traceback

                        console.print(f"[dim]{traceback.format_exc()}[/dim]")

                # Clean up partial connection
                if client:
                    try:
                        await client.__aexit__(None, None, None)
                    except Exception:
                        pass

                if attempt < max_attempts:
                    await asyncio.sleep(wait_seconds)

    return None, []
