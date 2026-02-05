from .cli import main as main, interactive_session as interactive_session
from .client import (
    connect_to_mcp_server as connect_to_mcp_server,
    connect_and_list_tools as connect_and_list_tools,
    wake_up_server as wake_up_server,
    MCPSession as MCPSession,
)
from .tools import (
    list_tools as list_tools,
    call_tool as call_tool,
    get_tool_parameters as get_tool_parameters,
)
from .display import (
    display_tools as display_tools,
    display_tool_header as display_tool_header,
    display_tool_menu as display_tool_menu,
    display_tool_schema as display_tool_schema,
)

__version__ = "0.1.0"

__all__ = [
    "main",
    "interactive_session",
    "connect_to_mcp_server",
    "connect_and_list_tools",
    "wake_up_server",
    "MCPSession",
    "list_tools",
    "call_tool",
    "get_tool_parameters",
    "display_tools",
    "display_tool_header",
    "display_tool_menu",
    "display_tool_schema",
]
