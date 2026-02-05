# Configuration Guide

Forbin uses environment variables for configuration, typically stored in a `.env` file.

## Quick Setup

```bash
# Create configuration file
cp .env.example .env

# Edit with your settings
nano .env  # or your preferred editor
```

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `MCP_SERVER_URL` | Full URL to your MCP server endpoint | `https://my-app.fly.dev/mcp` |
| `MCP_TOKEN` | Bearer token for authentication | `your-secret-token` |

### Optional

| Variable | Description | Example |
|----------|-------------|---------|
| `MCP_HEALTH_URL` | Health check endpoint for wake-up | `https://my-app.fly.dev/health` |

## Configuration Examples

### Local Development

For testing against a local MCP server:

```env
MCP_SERVER_URL=http://localhost:8000/mcp
MCP_TOKEN=dev-token-123
```

No health URL needed for local servers that don't suspend.

### Fly.io Production

For Fly.io apps that may suspend when idle:

```env
MCP_SERVER_URL=https://my-app.fly.dev/mcp
MCP_HEALTH_URL=https://my-app.fly.dev/health
MCP_TOKEN=prod-token-xyz
```

The health URL enables automatic wake-up for suspended services.

### Railway / Render

Similar to Fly.io, for platforms with cold starts:

```env
MCP_SERVER_URL=https://my-app.railway.app/mcp
MCP_HEALTH_URL=https://my-app.railway.app/health
MCP_TOKEN=your-token
```

### Always-On Server

For servers that don't suspend (dedicated VPS, always-on containers):

```env
MCP_SERVER_URL=https://api.example.com/mcp
MCP_TOKEN=your-token
# No MCP_HEALTH_URL needed
```

## Health URL Behavior

When `MCP_HEALTH_URL` is configured:

1. Forbin polls the health endpoint before connecting
2. Waits for HTTP 200 response (up to 6 attempts, 5 seconds apart)
3. Pauses 5 seconds for MCP server initialization
4. Then connects to the MCP endpoint

When `MCP_HEALTH_URL` is NOT configured:

1. Forbin connects directly to the MCP endpoint
2. Uses retry logic if connection fails
3. Suitable for always-on servers

## Server Requirements

Your MCP server should:

### Implement MCP Endpoint

Expose an MCP-compatible endpoint (typically `/mcp`):

```python
from fastapi import FastAPI
from fastmcp import FastMCP

app = FastAPI()
mcp = FastMCP("My Tools")

@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description"""
    return f"Result: {param}"

app.include_router(mcp.get_router(), prefix="/mcp")
```

### Implement Bearer Authentication

The MCP endpoint should validate the bearer token:

```python
from fastmcp.server.auth import BearerAuthProvider

auth = BearerAuthProvider(token="your-secret-token")
mcp = FastMCP("My Tools", auth=auth)
```

### Implement Health Endpoint (Optional)

For suspended services, add a simple health check:

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

This endpoint should:
- Return HTTP 200 when the server is ready
- Be lightweight (no database queries)
- Not require authentication

## Timeouts and Retries

Forbin uses these defaults for resilience:

| Setting | Value | Description |
|---------|-------|-------------|
| Health check attempts | 6 | Number of wake-up attempts |
| Health check interval | 5s | Wait between health checks |
| Post-wake initialization | 5s | Wait after health check succeeds |
| Connection timeout | 30s | MCP init timeout for cold starts |
| Tool operation timeout | 600s | Max time for tool execution |
| Tool listing timeout | 15s | Timeout for retrieving tool list |

These are tuned for Fly.io cold starts but work well with most platforms.

## Troubleshooting

### "Failed to wake up server"

- Verify `MCP_HEALTH_URL` is correct and accessible
- Check if the endpoint returns HTTP 200
- Try accessing the health URL in a browser
- Remove `MCP_HEALTH_URL` if your server doesn't suspend

### "Failed to connect to MCP server"

- Verify `MCP_SERVER_URL` is correct
- Check that `MCP_TOKEN` matches your server's token
- Ensure the server is running and accessible
- Try `curl -H "Authorization: Bearer YOUR_TOKEN" YOUR_URL` to test

### "Connection error (server not ready)"

- The server may need more initialization time
- This often resolves on retry
- Enable verbose mode (`v`) to see retry attempts

### Token Issues

- Tokens are case-sensitive
- No quotes needed in `.env` file
- Avoid trailing whitespace

### URL Format

URLs should:
- Include the protocol (`http://` or `https://`)
- Include the full path to the endpoint (`/mcp`, `/health`)
- Not have a trailing slash

```env
# Correct
MCP_SERVER_URL=https://my-app.fly.dev/mcp

# Incorrect
MCP_SERVER_URL=my-app.fly.dev/mcp        # Missing protocol
MCP_SERVER_URL=https://my-app.fly.dev/   # Wrong path
MCP_SERVER_URL=https://my-app.fly.dev/mcp/  # Trailing slash
```

## Security Notes

- Never commit `.env` files to version control
- Use different tokens for development and production
- Rotate tokens periodically
- Consider using environment-specific `.env` files (`.env.local`, `.env.production`)

## Next Steps

- See [Usage Guide](USAGE.md) for how to use Forbin
- See [Installation Guide](INSTALLATION.md) for installation options
