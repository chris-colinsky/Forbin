import asyncio
import sys

from rich.prompt import Prompt

from . import config
from .config import validate_config
from .utils import setup_logging, listen_for_toggle
from .client import connect_and_list_tools, wake_up_server
from .tools import get_tool_parameters, call_tool
from .display import (
    display_tools,
    display_tool_header,
    display_tool_menu,
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
    mcp_session = None
    try:
        display_logo()
        display_config_panel(config.MCP_SERVER_URL, config.MCP_HEALTH_URL)

        # Determine total steps
        total_steps = 2 if config.MCP_HEALTH_URL else 1
        current_step = 1

        # Step 1: Wake up server if health URL is configured
        if config.MCP_HEALTH_URL:
            display_step(current_step, total_steps, "WAKING UP SERVER", "in_progress")
            is_awake = await wake_up_server(config.MCP_HEALTH_URL, max_attempts=6, wait_seconds=5)

            if not is_awake:
                console.print("[bold red]  Failed to wake up server[/bold red]\n")
                return

            display_step(current_step, total_steps, "WAKING UP SERVER", "success", update=True)

            # Wait for MCP server to initialize (shorter wait like working example)
            with console.status(
                "  [dim]Waiting for server initialization (5s)...[/dim]", spinner="dots"
            ):
                await asyncio.sleep(5)

            console.print()
            current_step += 1

        # Step 2: Connect to MCP server AND list tools in one operation
        # (This avoids session expiry between connect and list_tools)
        display_step(current_step, total_steps, "CONNECTING AND LISTING TOOLS", "in_progress")
        mcp_session, tools = await connect_and_list_tools(max_attempts=3, wait_seconds=5)

        if not mcp_session:
            console.print("[bold red]  Failed to connect to MCP server[/bold red]\n")
            console.print("[yellow]This may indicate:[/yellow]")
            console.print("  - The MCP server is not properly configured")
            console.print("  - The server endpoint URL is incorrect")
            console.print("  - The server is returning errors for MCP requests")
            return

        display_step(
            current_step, total_steps, "CONNECTING AND LISTING TOOLS", "success", update=True
        )
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
        # Clean up MCP session
        if mcp_session:
            await mcp_session.cleanup()


async def interactive_session():
    """Run an interactive session to explore and test MCP tools."""
    validate_config()
    setup_logging()

    # Start background listener for 'v' key toggle during setup
    listener_task = asyncio.create_task(listen_for_toggle())
    mcp_session = None

    try:
        # Display logo and configuration
        display_logo()
        display_config_panel(config.MCP_SERVER_URL, config.MCP_HEALTH_URL)

        # Determine total steps
        total_steps = 2 if config.MCP_HEALTH_URL else 1
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

            # Wait for MCP server to initialize (shorter wait like working example)
            with console.status(
                "  [dim]Waiting for server initialization (5s)...[/dim]", spinner="dots"
            ):
                await asyncio.sleep(5)

            console.print()
            current_step += 1

        # Step 2: Connect to MCP server AND list tools in one operation
        # (This avoids session expiry between connect and list_tools)
        display_step(current_step, total_steps, "CONNECTING AND LISTING TOOLS", "in_progress")
        mcp_session, tools = await connect_and_list_tools(max_attempts=3, wait_seconds=5)

        if not mcp_session:
            console.print("[bold red]  Failed to connect to MCP server[/bold red]\n")
            console.print("[yellow]This may indicate:[/yellow]")
            console.print("  - The MCP server is not properly configured")
            console.print("  - The server endpoint URL is incorrect")
            console.print("  - The server is returning errors for MCP requests")
            return

        display_step(
            current_step, total_steps, "CONNECTING AND LISTING TOOLS", "success", update=True
        )
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

        # Main interaction loop - Tool List View
        running = True
        while running:
            display_tools(tools)

            console.print("[bold underline]Commands:[/bold underline]")
            console.print("  [bold cyan]number[/bold cyan] - Select a tool")
            console.print(
                "  [bold cyan]v[/bold cyan]      - Toggle verbose logging (current: {})".format(
                    "[green]ON[/green]" if config.VERBOSE else "[red]OFF[/red]"
                )
            )
            console.print("  [bold cyan]q[/bold cyan]      - Quit")
            console.print()

            choice = Prompt.ask("Select tool").strip().lower()

            if choice in ("quit", "q", "exit"):
                console.print("\n[bold yellow]Exiting...[/bold yellow]")
                break

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

                    # Enter Tool View loop
                    while True:
                        display_tool_header(selected_tool)
                        display_tool_menu()

                        tool_choice = Prompt.ask("Choose option").strip().lower()

                        if tool_choice in ("d", "details", "1"):
                            # View details
                            display_tool_schema(selected_tool)

                        elif tool_choice in ("r", "run", "2"):
                            # Run tool
                            params = get_tool_parameters(selected_tool)
                            await call_tool(mcp_session, selected_tool, params)

                        elif tool_choice in ("b", "back", "3"):
                            # Back to tool list
                            break

                        elif tool_choice in ("q", "quit", "exit"):
                            # Quit entirely
                            console.print("\n[bold yellow]Exiting...[/bold yellow]")
                            running = False
                            break

                        elif tool_choice == "v":
                            config.VERBOSE = not config.VERBOSE
                            status = (
                                "[bold green]ON[/bold green]"
                                if config.VERBOSE
                                else "[bold red]OFF[/bold red]"
                            )
                            console.print(
                                f"\n[bold cyan]Verbose logging toggled {status}[/bold cyan]\n"
                            )

                        else:
                            console.print(
                                "[red]Invalid option. Use 'd' for details, 'r' to run, 'b' to go back, or 'q' to quit.[/red]\n"
                            )
                else:
                    console.print(
                        f"[red]Invalid tool number. Choose between 1 and {len(tools)}[/red]\n"
                    )
            except ValueError:
                console.print("[red]Invalid choice. Enter a tool number or 'q' to quit.[/red]\n")

    finally:
        # Ensure listener is cancelled if we exit early
        if not listener_task.done():
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass

        # Clean up MCP session
        if mcp_session:
            await mcp_session.cleanup()


async def async_main():
    """Async main entry point."""
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


def main():
    """Synchronous entry point for CLI."""
    asyncio.run(async_main())
