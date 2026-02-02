import asyncio
import sys

from rich.prompt import Prompt, Confirm

from . import config
from .config import validate_config
from .utils import setup_logging, listen_for_toggle
from .client import connect_to_mcp_server, wake_up_server
from .tools import list_tools, get_tool_parameters, call_tool
from .display import (
    display_tools,
    display_tool_schema,
    display_logo,
    display_config_panel,
    display_step,
    console,
)


async def test_connectivity():
    """Test connectivity to the MCP server."""
    # Start background listener for 'v' key toggle
    listener_task = asyncio.create_task(listen_for_toggle())
    try:
        display_logo()
        display_config_panel(config.MCP_SERVER_URL, config.MCP_HEALTH_URL)

        # Determine total steps
        total_steps = 3 if config.MCP_HEALTH_URL else 2
        current_step = 1

        # Step 1: Wake up server if health URL is configured
        if config.MCP_HEALTH_URL:
            display_step(current_step, total_steps, "WAKING UP SERVER", "in_progress")
            is_awake = await wake_up_server(config.MCP_HEALTH_URL, max_attempts=6, wait_seconds=5)

            if not is_awake:
                console.print("[bold red]  Failed to wake up server[/bold red]\n")
                return

            display_step(current_step, total_steps, "WAKING UP SERVER", "success", update=True)

            # Wait for MCP server to fully initialize
            with console.status(
                "  [dim]Waiting for server initialization (20s)...[/dim]", spinner="dots"
            ):
                await asyncio.sleep(20)

            console.print()
            current_step += 1

        # Step 2: Connect to MCP server
        display_step(current_step, total_steps, "CONNECTING TO MCP SERVER", "in_progress")
        client = await connect_to_mcp_server(max_attempts=3, wait_seconds=5)

        if not client:
            console.print("[bold red]  Failed to connect to MCP server[/bold red]\n")
            return

        display_step(current_step, total_steps, "CONNECTING TO MCP SERVER", "success", update=True)
        console.print()
        current_step += 1

        # Step 3: List tools
        display_step(current_step, total_steps, "LISTING TOOLS", "in_progress")

        try:
            tools = await list_tools(client)
        except Exception as e:
            console.print(f"[bold red]  Failed to list tools: {type(e).__name__}[/bold red]")
            console.print(f"  [dim]{str(e)}[/dim]\n")
            console.print("[yellow]This may indicate:[/yellow]")
            console.print("  - The MCP server is not properly configured")
            console.print("  - The server endpoint URL is incorrect")
            console.print("  - The server is returning errors for MCP requests")
            return

        display_step(current_step, total_steps, "LISTING TOOLS", "success", update=True)
        console.print()
        console.print(
            f"[bold green]Test complete![/bold green] Server has [bold cyan]{len(tools)}[/bold cyan] tools available"
        )
        console.print()

    finally:
        # Cancel the listener task when exiting
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
        try:
            await client.__aexit__(None, None, None)
        except Exception:
            # Suppress session termination errors (these are harmless cleanup warnings)
            pass


async def interactive_session():
    """Run an interactive session to explore and test MCP tools."""
    validate_config()
    setup_logging()

    # Start background listener for 'v' key toggle during setup
    listener_task = asyncio.create_task(listen_for_toggle())

    try:
        # Display logo and configuration
        display_logo()
        display_config_panel(config.MCP_SERVER_URL, config.MCP_HEALTH_URL)

        # Determine total steps
        total_steps = 3 if config.MCP_HEALTH_URL else 2
        current_step = 1

        # Step 1: Wake up server if health URL is configured
        if config.MCP_HEALTH_URL:
            display_step(current_step, total_steps, "WAKING UP SERVER", "in_progress")
            is_awake = await wake_up_server(config.MCP_HEALTH_URL, max_attempts=6, wait_seconds=5)

            if not is_awake:
                console.print(
                    "[bold red]  Failed to wake up server after all attempts[/bold red]\n"
                )
                return

            display_step(current_step, total_steps, "WAKING UP SERVER", "success", update=True)

            # Wait for MCP server to fully initialize
            with console.status(
                "  [dim]Waiting for server initialization (20s)...[/dim]", spinner="dots"
            ):
                await asyncio.sleep(20)

            console.print()
            current_step += 1

        # Step 2: Connect to MCP server
        display_step(current_step, total_steps, "CONNECTING TO MCP SERVER", "in_progress")
        client = await connect_to_mcp_server(max_attempts=3, wait_seconds=5)

        if not client:
            console.print("[bold red]  Failed to connect to MCP server[/bold red]\n")
            return

        display_step(current_step, total_steps, "CONNECTING TO MCP SERVER", "success", update=True)
        console.print()
        current_step += 1

        # Step 3: Get tools
        display_step(current_step, total_steps, "LISTING TOOLS", "in_progress")

        try:
            tools = await list_tools(client)
        except Exception as e:
            console.print(f"[bold red]  Failed to list tools: {type(e).__name__}[/bold red]")
            console.print(f"  [dim]{str(e)}[/dim]\n")
            console.print("[yellow]This may indicate:[/yellow]")
            console.print("  - The MCP server is not properly configured")
            console.print("  - The server endpoint URL is incorrect")
            console.print("  - The server is returning errors for MCP requests")
            return

        display_step(current_step, total_steps, "LISTING TOOLS", "success", update=True)
        console.print()

        if not tools:
            console.print("[yellow]No tools available on this server.[/yellow]")
            return

        # Stop background listener before entering interactive loop
        # The interactive loop handles 'v' key itself
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass

        # Main interaction loop
        while True:
            display_tools(tools)

            console.print("[bold underline]Commands:[/bold underline]")
            console.print("  [bold cyan]number[/bold cyan] - View tool details and call tool")
            console.print("  [bold cyan]'list'[/bold cyan]   - Show tools list again")
            console.print(
                "  [bold cyan]'v'[/bold cyan]      - Toggle verbose logging (current: {})".format(
                    "[green]ON[/green]" if config.VERBOSE else "[red]OFF[/red]"
                )
            )
            console.print("  [bold cyan]'quit'[/bold cyan]   - Exit")
            console.print()

            choice = Prompt.ask("Enter choice").strip().lower()

            if choice in ("quit", "q", "exit"):
                console.print("\n[bold yellow]Exiting...[/bold yellow]")
                break

            if choice in ("list", "l", ""):
                continue

            if choice == "v":
                config.VERBOSE = not config.VERBOSE
                status = (
                    "[bold green]ON[/bold green]" if config.VERBOSE else "[bold red]OFF[/bold red]"
                )
                console.print(f"\n[bold cyan]Verbose logging toggled {status}[/bold cyan]\n")
                continue

            # Try to parse as tool number
            try:
                tool_num = int(choice)
                if 1 <= tool_num <= len(tools):
                    selected_tool = tools[tool_num - 1]

                    # Show tool details
                    display_tool_schema(selected_tool)

                    # Ask if user wants to call it
                    if Confirm.ask("Call this tool?"):
                        params = get_tool_parameters(selected_tool)
                        await call_tool(client, selected_tool, params)

                    console.print("\n[dim]Press Enter to continue...[/dim]")
                    input()
                else:
                    console.print(
                        f"[red]Invalid tool number. Choose between 1 and {len(tools)}[/red]\n"
                    )
            except ValueError:
                console.print("[red]Invalid choice. Enter a number, 'list', or 'quit'[/red]\n")

    finally:
        # Ensure listener is cancelled if we exit early
        if not listener_task.done():
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass

        try:
            await client.__aexit__(None, None, None)
        except Exception:
            # Suppress session termination errors (these are harmless cleanup warnings)
            pass


async def main():
    """Main entry point."""
    setup_logging()

    try:
        # Check for command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] in ("--test", "-t"):
                await test_connectivity()
                return
            elif sys.argv[1] in ("--help", "-h"):
                display_logo()
                console.print("\n[bold]Usage:[/bold]")
                console.print("  forbin           Run interactive session")
                console.print("  forbin --test    Test connectivity only")
                console.print("  forbin --help    Show this help message")
                console.print("\n[bold]Configuration:[/bold]")
                console.print("  Set MCP_SERVER_URL, MCP_TOKEN, and optionally MCP_HEALTH_URL")
                console.print("  in a .env file (see .env.example)")
                console.print("\n[bold]Interactive Shortcuts:[/bold]")
                console.print("  [bold cyan]'v'[/bold cyan] - Toggle verbose logging at any time")
                return

        # Run interactive session by default
        await interactive_session()
    except asyncio.CancelledError:
        pass
