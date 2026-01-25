import asyncio
import json
from typing import Any, Dict, List
from fastmcp.client import Client
from rich.prompt import Prompt
from rich.panel import Panel
from rich.syntax import Syntax

from .display import console


async def list_tools(client: Client) -> List[Any]:
    """
    List all available tools from the MCP server.

    Args:
        client: Connected MCP client

    Returns:
        List of tool objects
    """
    with console.status("  [dim]Retrieving tool manifest...[/dim]", spinner="dots"):
        tools = await asyncio.wait_for(client.list_tools(), timeout=15.0)

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

    console.print()
    console.rule("[bold cyan]ENTER PARAMETERS[/bold cyan]")
    console.print("Enter parameter values (press [bold]Enter[/bold] to skip optional parameters)\n")

    for param_name, param_info in properties.items():
        param_type = param_info.get("type", "string")
        param_desc = param_info.get("description", "")
        is_required = param_name in required

        # Show parameter info
        req_str = "[red](required)[/red]" if is_required else "[green](optional)[/green]"
        console.print(f"[bold cyan]{param_name}[/bold cyan] ({param_type}) {req_str}")
        if param_desc:
            console.print(f"  [dim]{param_desc}[/dim]")

        # Show enum values if present
        if "enum" in param_info:
            console.print(f"  Allowed values: {', '.join(str(v) for v in param_info['enum'])}")

        # Get value
        while True:
            try:
                # We use generic Prompt and handle manual validation to support complex types and skipping
                value_str = Prompt.ask("  ->", default="", show_default=False)

                if not value_str:
                    if is_required:
                        console.print(
                            "  [red]This parameter is required. Please enter a value.[/red]"
                        )
                        continue
                    else:
                        break

                # Parse the value
                value = parse_parameter_value(value_str, param_type)
                params[param_name] = value
                break

            except (ValueError, json.JSONDecodeError) as e:
                console.print(f"  [red]Invalid value for type {param_type}:[/red] {e}")
                console.print("  Please try again.")

        console.print()

    return params


async def call_tool(client: Client, tool: Any, params: Dict[str, Any]):
    """Call a tool with the given parameters."""
    console.print()
    console.rule("[bold magenta]CALLING TOOL[/bold magenta]")
    console.print(f"Tool: [bold]{tool.name}[/bold]")
    console.print()

    # Show parameters nicely
    if params:
        json_str = json.dumps(params, indent=2)
        console.print(
            Panel(
                Syntax(json_str, "json", theme="monokai", line_numbers=False),
                title="[bold]Parameters[/bold]",
                title_align="left",
                border_style="cyan",
            )
        )
    else:
        console.print("[dim]No parameters[/dim]")

    console.print("\n[bold]Executing...[/bold]")

    try:
        with console.status("Waiting for response...", spinner="dots"):
            result = await client.call_tool(tool.name, params)

        console.print("\n[bold green]Tool execution completed![/bold green]\n")
        console.rule("[bold green]RESULT[/bold green]")
        console.print()

        # Extract and display result
        if result.content:
            for item in result.content:
                text = getattr(item, "text", None)
                if text:
                    # Try to detect if it looks like JSON for syntax highlighting
                    text_stripped = text.strip()
                    if text_stripped.startswith(("{", "[")) and text_stripped.endswith(("}", "]")):
                        try:
                            # Validate and pretty-print JSON
                            parsed = json.loads(text_stripped)
                            formatted = json.dumps(parsed, indent=2)
                            console.print(
                                Panel(
                                    Syntax(formatted, "json", theme="monokai", line_numbers=False),
                                    border_style="green",
                                    title="[bold]Response[/bold]",
                                    title_align="left",
                                )
                            )
                            continue
                        except json.JSONDecodeError:
                            pass

                    # For non-JSON text responses
                    console.print(
                        Panel(
                            text.strip(),
                            border_style="green",
                            title="[bold]Response[/bold]",
                            title_align="left",
                        )
                    )
                else:
                    console.print(str(item))
        else:
            console.print("[dim]No content returned[/dim]")

        console.print()
        console.rule()
        console.print()

    except Exception as e:
        console.print(f"[bold red]Tool execution failed:[/bold red] {type(e).__name__}")
        console.print(f"   Error: {e}\n")
