import json
from typing import List, Any, Optional
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax
from rich.control import Control, ControlType

# Global console instance with constrained width for better readability
console = Console(width=100)


def display_logo():
    """Display the Forbin ASCII logo."""
    logo = """
[bold cyan]
  ███████╗ ██████╗ ██████╗ ██████╗ ██╗███╗   ██╗
  ██╔════╝██╔═══██╗██╔══██╗██╔══██╗██║████╗  ██║
  █████╗  ██║   ██║██████╔╝██████╔╝██║██╔██╗ ██║
  ██╔══╝  ██║   ██║██╔══██╗██╔══██╗██║██║╚██╗██║
  ██║     ╚██████╔╝██║  ██║██████╔╝██║██║ ╚████║
  ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═══╝[/bold cyan]
[dim]         MCP Remote Tool Tester v1.0.0[/dim]
[italic dim]    "This is the voice of world control..."[/italic dim]
"""
    console.print(logo)


def display_config_panel(server_url: Optional[str], health_url: Optional[str] = None):
    """Display configuration information in a panel."""
    from rich.table import Table

    config_table = Table.grid(padding=(0, 2))
    config_table.add_column(style="bold cyan", justify="right")
    config_table.add_column(style="white")

    server_url_display = server_url or "[dim]Not configured[/dim]"
    config_table.add_row("Server URL:", server_url_display)
    if health_url:
        config_table.add_row("Health URL:", health_url)
    else:
        config_table.add_row("Health URL:", "[dim]Not configured[/dim]")

    console.print()
    console.print(
        Panel(
            config_table,
            title="[bold]Configuration[/bold]",
            title_align="left",
            border_style="cyan",
            padding=(1, 2),
        )
    )
    console.print()


def display_step(
    step_num: int, total_steps: int, title: str, status: str = "in_progress", update: bool = False
):
    """Display a step indicator with status.

    Args:
        step_num: Current step number
        total_steps: Total number of steps
        title: Step title
        status: One of 'in_progress', 'success', 'skip'
        update: If True, updates the previous line instead of creating a new one
    """
    icons = {"in_progress": "⏳", "success": "✓", "skip": "⊝"}

    colors = {"in_progress": "yellow", "success": "green", "skip": "dim"}

    icon = icons.get(status, "•")
    color = colors.get(status, "white")

    step_text = f"[{color}]{icon} Step {step_num}/{total_steps}:[/{color}] [bold {color}]{title}[/bold {color}]"

    if update:
        # Move cursor up one line and clear it, then print the updated status
        console.control(Control((ControlType.CURSOR_UP, 1), (ControlType.ERASE_IN_LINE, 2)))
        console.print(step_text)
    else:
        console.print(step_text)


def display_tools(tools: List[Any]):
    """Display all available tools in a formatted table."""
    if not tools:
        console.print(
            Panel(
                "No tools available on this server.", title="Available Tools", border_style="yellow"
            )
        )
        return

    table = Table(title="AVAILABLE TOOLS", show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description")

    for i, tool in enumerate(tools, 1):
        description = tool.description.strip() if tool.description else "No description"

        # Check if description contains JSON and highlight it
        description_display = _highlight_json_in_text(description)

        table.add_row(str(i), tool.name, description_display)

    console.print()
    console.print(table)
    console.print()


def _highlight_json_in_text(text: str):
    """Highlight JSON content in text with syntax colors.

    Detects JSON objects/arrays and applies basic syntax highlighting.
    Returns a Text object with styled content.
    """
    import re

    # Simple check if text looks like it contains JSON
    if not any(char in text for char in ["{", "[", '":']):
        return text

    # Try to detect and highlight JSON-like patterns
    result = Text()

    # Pattern to match JSON-like content (simple approach)
    # This will highlight common JSON patterns with colors
    current_pos = 0

    # Find JSON strings (simple pattern for "key": "value")
    string_pattern = r'"([^"\\]*(\\.[^"\\]*)*)"'

    for match in re.finditer(string_pattern, text):
        # Add text before match
        if match.start() > current_pos:
            result.append(text[current_pos : match.start()])

        # Add the matched string with color
        matched_text = match.group(0)

        # Check if this looks like a key (followed by :)
        next_char_pos = match.end()
        if next_char_pos < len(text) and text[next_char_pos : next_char_pos + 1].strip().startswith(
            ":"
        ):
            result.append(matched_text, style="bold cyan")  # JSON key
        else:
            result.append(matched_text, style="green")  # JSON value

        current_pos = match.end()

    # Add remaining text
    if current_pos < len(text):
        remaining = text[current_pos:]
        # Highlight other JSON syntax
        remaining = remaining.replace("{", "{\u200b")  # Add zero-width space for splitting
        remaining = remaining.replace("}", "}\u200b")
        remaining = remaining.replace("[", "[\u200b")
        remaining = remaining.replace("]", "]\u200b")
        remaining = remaining.replace(":", ":\u200b")

        for part in remaining.split("\u200b"):
            if part in ["{", "}", "[", "]"]:
                result.append(part, style="bold yellow")
            elif part == ":":
                result.append(part, style="dim")
            else:
                result.append(part)

    return result if len(result) > 0 else text


def display_tool_schema(tool: Any):
    """Display detailed schema for a specific tool."""

    content: List[Any] = []

    if tool.description:
        content.append(Text(f"{tool.description}\n", style="italic"))

    if tool.inputSchema:
        schema = tool.inputSchema
        if isinstance(schema, dict) and "properties" in schema:
            content.append(Text("\nParameters:", style="bold underline"))
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            for param_name, param_info in properties.items():
                param_type = param_info.get("type", "unknown")
                param_desc = param_info.get("description", "No description")
                is_required = param_name in required

                req_str = "[red](required)[/red]" if is_required else "[green](optional)[/green]"

                param_text = Text()
                param_text.append(f"\n• {param_name}", style="bold cyan")
                param_text.append(f" ({param_type}) ", style="yellow")
                param_text.append(req_str)
                param_text.append(f"\n  {param_desc}")

                content.append(param_text)

                if "enum" in param_info:
                    enum_vals = ", ".join(str(v) for v in param_info["enum"])
                    content.append(Text(f"    Allowed values: {enum_vals}", style="dim"))
        else:
            content.append(Text("\nSchema:", style="bold underline"))
            json_str = json.dumps(schema, indent=2)
            content.append(Syntax(json_str, "json", theme="monokai", line_numbers=False))
    else:
        content.append(Text("\nNo input parameters required.", style="dim"))

    # Combine all content
    panel_content = Group(*content)

    console.print()
    console.print(
        Panel(
            panel_content,
            title=f"Tool: [bold]{tool.name}[/bold]",
            subtitle="[dim]Press Enter to continue[/dim]",
            border_style="blue",
            expand=False,
        )
    )
    console.print()
