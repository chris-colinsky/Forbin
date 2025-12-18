import asyncio
import sys

from . import config
from .config import validate_config
from .utils import setup_logging
from .client import connect_to_mcp_server, wake_up_server
from .tools import list_tools, get_tool_parameters, call_tool
from .display import display_tools, display_tool_schema


async def test_connectivity():
    """Test connectivity to the MCP server."""
    print(f"\n{'=' * 70}")
    print("CONNECTIVITY TEST")
    print(f"{'=' * 70}\n")
    print(f"Server URL: {config.MCP_SERVER_URL}")
    print(f"Health URL: {config.MCP_HEALTH_URL or 'Not configured'}")
    print()

    # Step 1: Wake up server if health URL is configured
    if config.MCP_HEALTH_URL:
        is_awake = await wake_up_server(config.MCP_HEALTH_URL, max_attempts=6, wait_seconds=5)

        if not is_awake:
            print("\n❌ Failed to wake up server")
            return

        # Wait for MCP server to fully initialize
        print("\nWaiting 20 seconds for MCP server to fully initialize...")
        await asyncio.sleep(20)
    else:
        print("No health URL configured - skipping wake-up")

    # Step 2: Connect to MCP server
    print(f"\n{'=' * 70}")
    print("CONNECTING TO MCP SERVER")
    print(f"{'=' * 70}")

    client = await connect_to_mcp_server(max_attempts=3, wait_seconds=5)

    if not client:
        print("\n❌ Failed to connect to MCP server")
        return

    try:
        # Step 3: List tools
        tools = await list_tools(client)

        print("\n✓ Successfully connected!")
        print(f"✓ Server has {len(tools)} tools available")
        print(f"\n{'=' * 70}\n")

    finally:
        await client.__aexit__(None, None, None)


async def interactive_session():
    """Run an interactive session to explore and test MCP tools."""
    validate_config()
    setup_logging()

    print(f"\n{'=' * 70}")
    print("FORBIN - MCP REMOTE TOOL TESTER")
    print(f"{'=' * 70}\n")
    print(f"Server: {config.MCP_SERVER_URL}\n")

    # Step 1: Wake up server if health URL is configured
    if config.MCP_HEALTH_URL:
        # Note: In the original file, it checks the env var directly or passed arg?
        # The refactored version uses config.MCP_HEALTH_URL
        is_awake = await wake_up_server(config.MCP_HEALTH_URL, max_attempts=6, wait_seconds=5)

        if not is_awake:
            print("\n❌ Failed to wake up server after all attempts.")
            return

        # Wait for MCP server to fully initialize
        print("\nWaiting 20 seconds for MCP server to fully initialize...")
        await asyncio.sleep(20)
    else:
        print("Note: No health URL configured - skipping wake-up")

    # Step 2: Connect to MCP server
    print(f"\n{'=' * 70}")
    print("CONNECTING TO MCP SERVER")
    print(f"{'=' * 70}")

    client = await connect_to_mcp_server(max_attempts=3, wait_seconds=5)

    if not client:
        print("\n❌ Failed to connect to MCP server")
        return

    try:
        # Step 3: Get tools
        tools = await list_tools(client)

        if not tools:
            print("No tools available on this server.")
            return

        # Main interaction loop
        while True:
            display_tools(tools)

            print("Commands:")
            print("  [number] - View tool details and call tool")
            print("  'list'   - Show tools list again")
            print("  'quit'   - Exit")
            print()

            choice = input("Enter choice: ").strip().lower()

            if choice in ("quit", "q", "exit"):
                print("\nExiting...")
                break

            if choice in ("list", "l", ""):
                continue

            # Try to parse as tool number
            try:
                tool_num = int(choice)
                if 1 <= tool_num <= len(tools):
                    selected_tool = tools[tool_num - 1]

                    # Show tool details
                    display_tool_schema(selected_tool)

                    # Ask if user wants to call it
                    call_choice = input("Call this tool? (y/n): ").strip().lower()

                    if call_choice in ("y", "yes"):
                        params = get_tool_parameters(selected_tool)
                        await call_tool(client, selected_tool, params)

                    input("\nPress Enter to continue...")
                else:
                    print(f"Invalid tool number. Choose between 1 and {len(tools)}\n")
            except ValueError:
                print("Invalid choice. Enter a number, 'list', or 'quit'\n")

    finally:
        await client.__aexit__(None, None, None)


async def main():
    """Main entry point."""
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ("--test", "-t"):
            await test_connectivity()
            return
        elif sys.argv[1] in ("--help", "-h"):
            print("Forbin - MCP Remote Tool Tester")
            print("Inspired by Colossus: The Forbin Project")
            print("\nUsage:")
            print("  forbin           Run interactive session")
            print("  forbin --test    Test connectivity only")
            print("  forbin --help    Show this help message")
            print("\nConfiguration:")
            print("  Set MCP_SERVER_URL, MCP_TOKEN, and optionally MCP_HEALTH_URL")
            print("  in a .env file (see .env.example)")
            return

    # Run interactive session by default
    await interactive_session()
