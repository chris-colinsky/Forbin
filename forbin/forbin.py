#!/usr/bin/env python3
"""
Forbin - MCP Remote Tool Tester

Inspired by Colossus: The Forbin Project, where two computers learn to communicate.

An interactive CLI tool for testing remote MCP servers and tools.
Supports suspended services (like Fly.io) with automatic wake-up.

Named after Dr. Charles Forbin, who built systems to enable communication
between powerful computing systems - just as this tool helps test MCP
communication between AI agents and their tools.
"""

from fastmcp.client import Client
from fastmcp.client.auth import BearerAuth
import asyncio
import json
import os
import sys
from typing import Optional, Dict, Any, List
import httpx
from dotenv import load_dotenv


# Suppress stderr warnings from MCP library (like "Session termination failed: 400")
class FilteredStderr:
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.suppress_patterns = [
            "Error in post_writer",
            "Session termination failed",
            "httpx.HTTPStatusError",
            "streamable_http.py",
            "Traceback (most recent call last)",
        ]
        self.buffer = ""
        self.suppressing = False

    def write(self, text):
        # Check if this line starts a suppressible error block
        if any(pattern in text for pattern in self.suppress_patterns):
            self.suppressing = True
            return

        # If we're suppressing and hit a blank line, stop suppressing
        if self.suppressing and text.strip() == "":
            self.suppressing = False
            return

        # If not suppressing, write to original stderr
        if not self.suppressing:
            self.original_stderr.write(text)

    def flush(self):
        self.original_stderr.flush()


# Replace stderr with filtered version
sys.stderr = FilteredStderr(sys.stderr)

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
MCP_HEALTH_URL = os.getenv("MCP_HEALTH_URL")
MCP_TOKEN = os.getenv("MCP_TOKEN")

# Validate required environment variables
if not MCP_SERVER_URL:
    print("❌ Error: MCP_SERVER_URL environment variable is required")
    print("Please create a .env file (see .env.example for template)")
    sys.exit(1)
if not MCP_TOKEN:
    print("❌ Error: MCP_TOKEN environment variable is required")
    print("Please create a .env file (see .env.example for template)")
    sys.exit(1)


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
    server_url = MCP_SERVER_URL or ""
    token = MCP_TOKEN or ""

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


async def list_tools(client: Client) -> List[Any]:
    """
    List all available tools from the MCP server.

    Args:
        client: Connected MCP client

    Returns:
        List of tool objects
    """
    print("\n  Retrieving tool manifest...")
    tools = await asyncio.wait_for(client.list_tools(), timeout=15.0)
    print(f"  ✓ Found {len(tools)} tools\n")
    return tools


def display_tools(tools: List[Any]):
    """Display all available tools in a formatted list."""
    print(f"\n{'=' * 70}")
    print("AVAILABLE TOOLS")
    print(f"{'=' * 70}\n")

    if not tools:
        print("No tools available on this server.")
        return

    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool.name}")
        if tool.description:
            # Wrap description
            desc_lines = tool.description.split("\n")
            for line in desc_lines:
                print(f"   {line}")
        print()


def display_tool_schema(tool: Any):
    """Display detailed schema for a specific tool."""
    print(f"\n{'=' * 70}")
    print(f"TOOL: {tool.name}")
    print(f"{'=' * 70}\n")

    if tool.description:
        print(f"Description: {tool.description}\n")

    if tool.inputSchema:
        schema = tool.inputSchema
        if isinstance(schema, dict) and "properties" in schema:
            print("Parameters:")
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            for param_name, param_info in properties.items():
                param_type = param_info.get("type", "unknown")
                param_desc = param_info.get("description", "No description")
                req_marker = " (required)" if param_name in required else " (optional)"

                print(f"\n  • {param_name} ({param_type}){req_marker}")
                print(f"    {param_desc}")

                # Show enum values if present
                if "enum" in param_info:
                    print(f"    Allowed values: {', '.join(str(v) for v in param_info['enum'])}")
        else:
            print("Schema:")
            print(json.dumps(schema, indent=2))
    else:
        print("No input parameters required.")

    print()


def parse_parameter_value(value_str: str, param_type: str) -> Any:
    """Parse a string input into the appropriate type."""
    if not value_str.strip():
        return None

    if param_type == "boolean":
        return value_str.lower() in ("true", "t", "yes", "y", "1")
    elif param_type == "integer":
        return int(value_str)
    elif param_type == "number":
        return float(value_str)
    elif param_type in ("object", "array"):
        return json.loads(value_str)
    else:  # string
        return value_str


def get_tool_parameters(tool: Any) -> Dict[str, Any]:
    """Interactively collect parameters for a tool."""
    params: dict[str, Any] = {}

    if not tool.inputSchema or not isinstance(tool.inputSchema, dict):
        return params

    properties = tool.inputSchema.get("properties", {})
    required = tool.inputSchema.get("required", [])

    if not properties:
        return params

    print(f"\n{'=' * 70}")
    print("ENTER PARAMETERS")
    print(f"{'=' * 70}\n")
    print("Enter parameter values (press Enter to skip optional parameters)")
    print()

    for param_name, param_info in properties.items():
        param_type = param_info.get("type", "string")
        param_desc = param_info.get("description", "")
        is_required = param_name in required

        # Show parameter info
        req_str = "(required)" if is_required else "(optional)"
        print(f"{param_name} ({param_type}) {req_str}")
        if param_desc:
            print(f"  {param_desc}")

        # Show enum values if present
        if "enum" in param_info:
            print(f"  Allowed values: {', '.join(str(v) for v in param_info['enum'])}")

        # Get value
        while True:
            try:
                value_str = input("  → ").strip()

                if not value_str:
                    if is_required:
                        print("  ❌ This parameter is required. Please enter a value.")
                        continue
                    else:
                        break

                # Parse the value
                value = parse_parameter_value(value_str, param_type)
                params[param_name] = value
                break

            except (ValueError, json.JSONDecodeError) as e:
                print(f"  ❌ Invalid value for type {param_type}: {e}")
                print("  Please try again.")

        print()

    return params


async def call_tool(client: Client, tool: Any, params: Dict[str, Any]):
    """Call a tool with the given parameters."""
    print(f"\n{'=' * 70}")
    print("CALLING TOOL")
    print(f"{'=' * 70}\n")
    print(f"Tool: {tool.name}")
    print(f"Parameters: {json.dumps(params, indent=2)}")
    print("\nExecuting...\n")

    try:
        result = await client.call_tool(tool.name, params)

        print("✓ Tool execution completed!\n")
        print(f"{'=' * 70}")
        print("RESULT")
        print(f"{'=' * 70}\n")

        # Extract and display result
        if result.content:
            for item in result.content:
                text = getattr(item, "text", None)
                if text:
                    print(text)
                else:
                    print(item)
        else:
            print("No content returned")

        print(f"\n{'=' * 70}\n")

    except Exception as e:
        print(f"❌ Tool execution failed: {type(e).__name__}")
        print(f"   Error: {e}\n")


async def test_connectivity():
    """Test connectivity to the MCP server."""
    print(f"\n{'=' * 70}")
    print("CONNECTIVITY TEST")
    print(f"{'=' * 70}\n")
    print(f"Server URL: {MCP_SERVER_URL}")
    print(f"Health URL: {MCP_HEALTH_URL or 'Not configured'}")
    print()

    # Step 1: Wake up server if health URL is configured
    if MCP_HEALTH_URL:
        is_awake = await wake_up_server(MCP_HEALTH_URL, max_attempts=6, wait_seconds=5)

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
    print(f"\n{'=' * 70}")
    print("FORBIN - MCP REMOTE TOOL TESTER")
    print(f"{'=' * 70}\n")
    print(f"Server: {MCP_SERVER_URL}\n")

    # Step 1: Wake up server if health URL is configured
    if MCP_HEALTH_URL:
        is_awake = await wake_up_server(MCP_HEALTH_URL, max_attempts=6, wait_seconds=5)

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
    import sys

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


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
