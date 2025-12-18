import asyncio
from typing import Optional
import httpx
from fastmcp.client import Client
from fastmcp.client.auth import BearerAuth

from . import config


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
    print(f"\n{'=' * 70}")
    print("WAKING UP SERVER")
    print(f"{'=' * 70}")
    print(f"Health endpoint: {health_url}\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(1, max_attempts + 1):
            try:
                print(f"Attempt {attempt}/{max_attempts}...", end=" ")
                response = await client.get(health_url)

                if response.status_code == 200:
                    print(f"✓ Server is awake! (status: {response.status_code})")
                    return True
                else:
                    print(f"Server responded with status {response.status_code}")

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                print(f"Connection failed: {type(e).__name__}")
            except Exception as e:
                print(f"Unexpected error: {e}")

            if attempt < max_attempts:
                print(f"Waiting {wait_seconds} seconds before next attempt...\n")
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

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"\nConnection attempt {attempt}/{max_attempts}...")

            client = Client(
                server_url,
                auth=BearerAuth(token=token),
                init_timeout=30.0,  # Extended timeout for cold starts
            )

            # Test the connection by entering the context
            await client.__aenter__()
            print("  ✓ Connected to MCP server")
            print(f"    Initialized: {client.initialize_result is not None}")

            return client

        except asyncio.TimeoutError:
            print(f"  ✗ Timeout on attempt {attempt} (server not responding)")
            if attempt < max_attempts:
                print(f"  Waiting {wait_seconds} seconds before retry...\n")
                await asyncio.sleep(wait_seconds)
        except Exception as e:
            error_name = type(e).__name__
            if "BrokenResourceError" in error_name or "ClosedResourceError" in error_name:
                print(f"  ✗ Connection error on attempt {attempt} (server not ready)")
            else:
                print(f"  ✗ {error_name} on attempt {attempt}: {e}")

            if attempt < max_attempts:
                print(f"  Waiting {wait_seconds} seconds before retry...\n")
                await asyncio.sleep(wait_seconds)

    return None
