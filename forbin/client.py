import asyncio
from typing import Optional
import httpx
from fastmcp.client import Client
from fastmcp.client.auth import BearerAuth

from . import config
from .display import console


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


async def connect_to_mcp_server(max_attempts: int = 3, wait_seconds: float = 5) -> Optional[Client]:
    """
    Connect to the MCP server with retry logic.

    Args:
        max_attempts: Maximum connection attempts
        wait_seconds: Seconds to wait between attempts

    Returns:
        Connected Client instance or None if failed
    """
    server_url = config.MCP_SERVER_URL or ""
    token = config.MCP_TOKEN or ""

    with console.status("  [dim]Establishing connection...[/dim]", spinner="dots") as status:
        for attempt in range(1, max_attempts + 1):
            try:
                status.update(f"  [dim]Attempt {attempt}/{max_attempts}...[/dim]")

                client = Client(
                    server_url,
                    auth=BearerAuth(token=token),
                    init_timeout=30.0,  # Extended timeout for cold starts
                )

                # Test the connection by entering the context
                await client.__aenter__()
                return client

            except asyncio.TimeoutError:
                if config.VERBOSE or attempt == max_attempts:
                    console.print("  [red]Timeout (server not responding)[/red]")
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

                if attempt < max_attempts:
                    await asyncio.sleep(wait_seconds)

    return None
