import sys


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
