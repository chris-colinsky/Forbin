# Usage Guide

This guide covers how to use Forbin to test MCP servers and their tools.

## Quick Start

```bash
# Test connectivity to your MCP server
forbin --test

# Start interactive tool browser
forbin

# Show help
forbin --help
```

## Modes

### Interactive Mode (Default)

Run without arguments to start the interactive tool browser:

```bash
forbin
```

The tool will:
1. Wake up your server (if health URL is configured)
2. Connect to the MCP server
3. List all available tools
4. Enter the interactive browser

### Connectivity Test Mode

Test server connectivity without entering interactive mode:

```bash
forbin --test
```

Useful for:
- Verifying server is reachable
- Checking health endpoint configuration
- Validating authentication tokens
- CI/CD health checks

## Interactive Navigation

Forbin uses a two-level navigation system for a cleaner experience.

### Tool List View

After connecting, you'll see a compact list of available tools:

```
Available Tools

   1. generate_report - Generate a monthly summary report...
   2. get_user_stats - Retrieves user statistics for a given...

Commands:
  number - Select a tool
  v      - Toggle verbose logging (current: OFF)
  q      - Quit

Select tool:
```

Enter a number to select a tool, `v` to toggle verbose logging, or `q` to quit.

### Tool View

After selecting a tool, you enter the tool view with these options:

```
─────────────────────────── generate_report ───────────────────────────

Options:
  d - View details
  r - Run tool
  b - Back to tool list
  q - Quit

Choose option:
```

**Options:**
- **d** - View the full tool schema with syntax-highlighted JSON
- **r** - Run the tool (prompts for parameters)
- **b** - Go back to the tool list
- **q** - Quit the application

### Viewing Tool Details

Press `d` to see the complete tool schema, including:
- Description
- Response examples (syntax-highlighted JSON)
- Output schemas
- Input parameters

Example output:
```
╭──────────────────────── generate_report - Details ────────────────────────╮
│ Generate Report                                                           │
│                                                                           │
│ ### Responses:                                                            │
│                                                                           │
│ **200**: Successful Response                                              │
│                                                                           │
│ {                                                                         │
│   "success": true,                                                        │
│   "message": "Report generated successfully",                             │
│   "report_month": "2025-06"                                               │
│ }                                                                         │
│                                                                           │
│ Input Schema:                                                             │
│                                                                           │
│ {                                                                         │
│   "type": "object",                                                       │
│   "properties": {                                                         │
│     "report_month": {                                                     │
│       "type": "string",                                                   │
│       "description": "Report month in YYYY-MM format"                     │
│     }                                                                     │
│   },                                                                      │
│   "required": ["report_month"]                                            │
│ }                                                                         │
╰───────────────────────────────────────────────────────────────────────────╯
```

### Running a Tool

Press `r` to run the tool. You'll be prompted for each parameter:

```
──────────────────────────── ENTER PARAMETERS ─────────────────────────────
Enter parameter values (press Enter to skip optional parameters)

report_month (string) (required)
  Report month in YYYY-MM format (e.g., '2025-06')
  -> 2025-06

use_preview_db (boolean) (optional)
  Whether to use preview database instead of production
  -> false
```

After entering parameters, the tool executes and displays the result:

```
───────────────────────────── CALLING TOOL ────────────────────────────────
Tool: generate_report

╭─ Parameters ─────────────────────────────────────────────────────────────╮
│ {                                                                        │
│   "report_month": "2025-06",                                             │
│   "use_preview_db": false                                                │
│ }                                                                        │
╰──────────────────────────────────────────────────────────────────────────╯

Executing...

Tool execution completed!

────────────────────────────── RESULT ─────────────────────────────────────

╭─ Response ───────────────────────────────────────────────────────────────╮
│ {                                                                        │
│   "success": true,                                                       │
│   "message": "Monthly report generated successfully",                    │
│   "report_month": "2025-06",                                             │
│   "generated_at": "2025-02-04T15:30:00Z"                                 │
│ }                                                                        │
╰──────────────────────────────────────────────────────────────────────────╯
```

After the result is displayed, you return to the tool view where you can:
- Run the tool again with different parameters
- View details
- Go back to the tool list
- Quit

## Verbose Logging

Toggle verbose logging at any time by pressing `v`:
- Shows detailed connection information
- Displays retry attempts and errors
- Useful for debugging connection issues

```
Verbose logging toggled ON
```

## Parameter Types

Forbin automatically parses parameter values based on their schema type:

| Type | Example Input | Parsed Value |
|------|--------------|--------------|
| string | `hello world` | `"hello world"` |
| boolean | `true`, `yes`, `1` | `true` |
| boolean | `false`, `no`, `0` | `false` |
| integer | `42` | `42` |
| number | `3.14` | `3.14` |
| object | `{"key": "value"}` | `{"key": "value"}` |
| array | `[1, 2, 3]` | `[1, 2, 3]` |

For objects and arrays, enter valid JSON.

## Step Indicators

During startup, Forbin shows progress with colored indicators:

- **> Yellow** - In progress
- **+ Green** - Completed successfully
- **- Dim** - Skipped

Example:
```
> Step 1/2: WAKING UP SERVER
+ Step 1/2: WAKING UP SERVER

> Step 2/2: CONNECTING AND LISTING TOOLS
+ Step 2/2: CONNECTING AND LISTING TOOLS

Test complete! Server has 3 tools available
```

## Keyboard Shortcuts Summary

| Key | Context | Action |
|-----|---------|--------|
| `1-9` | Tool List | Select tool by number |
| `v` | Any | Toggle verbose logging |
| `q` | Any | Quit application |
| `d` | Tool View | View tool details |
| `r` | Tool View | Run tool |
| `b` | Tool View | Back to tool list |

## Command Line Options

```
forbin              Run interactive session
forbin --test       Test connectivity only
forbin --help       Show help message
```

## Next Steps

- See [Configuration Guide](CONFIGURATION.md) for setting up your MCP server connection
- See [Installation Guide](INSTALLATION.md) for installation options
- See [Development Guide](DEVELOPMENT.md) for contributing
