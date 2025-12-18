import json
from typing import List, Any


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
