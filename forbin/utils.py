import sys
import asyncio
import select
from . import config


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
            "File ",  # Suppress file paths in tracebacks
            "raise ",
            "await ",
            "BrokenResourceError",
            "ClosedResourceError",
            "raise_for_status",
            "handle_request_async",
            "_handle_post_request",
        ]
        self.buffer = ""
        self.suppressing = False
        self.suppress_depth = 0

    def write(self, text):
        # If verbose mode is ON, don't suppress anything
        if config.VERBOSE:
            self.original_stderr.write(text)
            return

        # Check if this line starts a suppressible error block
        if any(pattern in text for pattern in self.suppress_patterns):
            self.suppressing = True
            self.suppress_depth = 10  # Suppress next 10 lines
            return

        # If we're suppressing, decrement counter
        if self.suppressing:
            if text.strip() == "":
                # Blank line ends suppression
                self.suppressing = False
                self.suppress_depth = 0
            else:
                # Any line during suppression decrements counter
                self.suppress_depth -= 1
                if self.suppress_depth <= 0:
                    self.suppressing = False
                    return

            return

        # If not suppressing, write to original stderr
        if not self.suppressing:
            self.original_stderr.write(text)

    def flush(self):
        self.original_stderr.flush()


def setup_logging():
    """Replace stderr with filtered version."""
    sys.stderr = FilteredStderr(sys.stderr)


async def listen_for_toggle():
    """
    Background task to listen for 'v' key to toggle verbose logging.
    Uses non-blocking stdin read.
    """
    # Only try to import termios/tty on Unix-like systems
    try:
        import termios
        import tty
    except ImportError:
        return

    fd = sys.stdin.fileno()
    # Check if we are in a terminal
    if not sys.stdin.isatty():
        return

    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            # Non-blocking check for input
            if select.select([sys.stdin], [], [], 0.1)[0]:
                char = sys.stdin.read(1).lower()
                if char == "v":
                    config.VERBOSE = not config.VERBOSE
                    from .display import console

                    status = (
                        "[bold green]ON[/bold green]"
                        if config.VERBOSE
                        else "[bold red]OFF[/bold red]"
                    )
                    # Clear current line and print toggle status
                    console.print(f"\n[bold cyan]Verbose logging toggled {status}[/bold cyan]")

            await asyncio.sleep(0.1)
    except Exception:
        # Silently fail if something goes wrong with the terminal settings
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
