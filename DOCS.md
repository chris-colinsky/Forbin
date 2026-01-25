# Forbin Technical Documentation

This document provides a detailed look at how Forbin works under the hood, its connection logic, and its user interface components.

## How It Works

### Wake-Up Process

For suspended services (like Fly.io apps), Forbin uses a orchestrated three-step approach to ensure the server is ready before attempting an MCP connection:

1. **Health Check Wake-Up**
   - Polls the configured `MCP_HEALTH_URL` until it returns a successful (200 OK) response.
   - **Limit:** 6 attempts with 5-second intervals (30 seconds total).
   - This triggers the cloud provider to wake up the suspended instance.

2. **Initialization Wait**
   - Once the health endpoint responds, Forbin waits for an additional **20 seconds**.
   - This gives the MCP server time to fully initialize its inner services after the container has started.

3. **Connection with Retry**
   - Connects to the MCP server with an extended `init_timeout` of **30 seconds**.
   - **Retry logic:** 3 attempts with 5-second waits between them if the connection fails or times out.

This process ensures reliable connections even to cold-started servers that might take significant time to become "fully" ready for MCP traffic.

---

## User Interface

### Step Indicators

Throughout the connection and execution process, Forbin displays step indicators to show progress.

| Color | Icon | Meaning |
|-------|------|---------|
| **Yellow** | > | **In Progress** - The current action is being performed. |
| **Green** | + | **Success** - The step completed successfully. |
| **Dim/Grey** | - | **Skip** - This step was skipped (e.g., wake-up skipped if no health URL). |

### Anytime Logging Toggle

Forbin includes a background listener that monitors for the **`v`** keypress.

- **Non-blocking:** You can toggle logging even while Forbin is waiting for a health check or establishing a connection.
- **Real-time unsuppression:** When logging is toggled **ON**, Forbin's `FilteredStderr` immediately stops suppressing typical MCP library warnings and errors, showing you full tracebacks and connection details.
- **Visual Feedback:** A notification will appear in the CLI whenever the logging state changes.

### Interactive Tool Browser

1. **Discovery:** Forbin lists all tools provided by the MCP server.
2. **Inspection:** Selecting a tool shows its description and parameter requirements.
3. **Execution:** Forbin prompts for each parameter, performing basic type validation:
   - **Strings:** Direct input.
   - **Booleans:** Accepts `true`, `false`, `y`, `n`, `1`, `0`.
   - **Numbers:** Parses integers and floats.
   - **Objects/Arrays:** Parses local JSON strings.

---

## Error Handling Details

- **Session termination errors:** FastMCP sometimes returns a 400 error when a session is closed. Forbin automatically suppresses these harmless warnings.
- **Connection retries:** Uses exponential backoff and fresh client instantiation for each retry to recover from transient network issues.
- **Timeout management:** Specifically tuned timeouts for discovery (15s) and tool execution (30s+).
