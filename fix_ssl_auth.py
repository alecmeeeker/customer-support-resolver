#!/usr/bin/env python3
"""
SSL Certificate Fix for Gmail OAuth
Run this script to fix the SSL certificate verification error.
"""
import subprocess
import sys
import re
from pathlib import Path

def main():
    print("=== Gmail OAuth SSL Fix ===\n")

    # Step 1: Install certifi
    print("Step 1: Installing certifi package...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "certifi"],
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to install certifi: {result.stderr}")
        sys.exit(1)
    print("certifi installed successfully.\n")

    # Step 2: Patch local_oauth_service.py
    print("Step 2: Patching local_oauth_service.py...")
    script_dir = Path(__file__).parent
    oauth_file = script_dir / "local_oauth_service.py"

    if not oauth_file.exists():
        print(f"Error: {oauth_file} not found")
        sys.exit(1)

    content = oauth_file.read_text()

    # Check if already patched
    if "import certifi" in content:
        print("Already patched! No changes needed.\n")
    else:
        # Add imports
        content = content.replace(
            "import asyncio\n",
            "import asyncio\nimport ssl\n"
        )
        content = content.replace(
            "import aiohttp\n",
            "import aiohttp\nimport certifi\n"
        )

        # Add SSL context
        content = content.replace(
            "        async with aiohttp.ClientSession() as session:\n            async with session.post(token_url, data=data) as response:",
            "        ssl_context = ssl.create_default_context(cafile=certifi.where())\n        async with aiohttp.ClientSession() as session:\n            async with session.post(token_url, data=data, ssl=ssl_context) as response:"
        )

        oauth_file.write_text(content)
        print("Patched successfully.\n")

    print("=== Fix Complete ===")
    print("You can now run your email pipeline again.")
    print("Your existing OAuth configuration is preserved.")

if __name__ == "__main__":
    main()
