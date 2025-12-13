import asyncio
import sys
import os

# Add the current directory to sys.path to ensure we can import the module correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from forbin.forbin import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Exit gracefully on Ctrl+C
        sys.exit(0)
