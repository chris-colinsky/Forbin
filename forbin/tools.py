import asyncio
import json
from typing import Any, Dict, List
from fastmcp.client import Client


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


def parse_parameter_value(value_str: str, param_type: str) -> Any:
    """Parse a string input into the appropriate type."""
    if not value_str.strip():
        return None

    if param_type == "boolean":
        return value_str.lower() in ("true", "t", "yes", "y", "1")
    elif param_type == "integer":
        try:
            return int(value_str)
        except ValueError:
            # Re-raise to be caught by caller
            raise
    elif param_type == "number":
        try:
            return float(value_str)
        except ValueError:
            raise
    elif param_type in ("object", "array"):
        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            raise
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
