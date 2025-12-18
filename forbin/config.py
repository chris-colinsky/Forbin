import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
MCP_HEALTH_URL = os.getenv("MCP_HEALTH_URL")
MCP_TOKEN = os.getenv("MCP_TOKEN")


def validate_config():
    """Validate required environment variables."""
    if not MCP_SERVER_URL:
        print("❌ Error: MCP_SERVER_URL environment variable is required")
        print("Please create a .env file (see .env.example for template)")
        sys.exit(1)
    if not MCP_TOKEN:
        print("❌ Error: MCP_TOKEN environment variable is required")
        print("Please create a .env file (see .env.example for template)")
        sys.exit(1)
