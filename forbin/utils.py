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


def setup_logging():
    """Replace stderr with filtered version."""
    sys.stderr = FilteredStderr(sys.stderr)
