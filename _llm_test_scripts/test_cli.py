#!/usr/bin/env python3
"""Test RustDesk CLI commands."""

import asyncio
import subprocess
import sys
from pathlib import Path

RUSTDESK_PATH = r"C:\Program Files\RustDesk\rustdesk.exe"

async def test_cli_command(args):
    """Test a RustDesk CLI command."""
    try:
        cmd = [RUSTDESK_PATH] + args
        print(f"Running: {' '.join(cmd)}")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=10
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            print("Command timed out")
            return -1, "", "Timeout"

        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        print(f"Return code: {proc.returncode}")
        print(f"Stdout: '{stdout_str}'")
        print(f"Stderr: '{stderr_str}'")
        print()

        return proc.returncode, stdout_str, stderr_str

    except Exception as e:
        print(f"Error: {e}")
        return -1, "", str(e)

async def main():
    """Test various RustDesk CLI commands."""
    print("=== Testing RustDesk CLI Commands ===\n")

    commands = [
        ["--version"],
        ["--get-id"],
        ["--help"],
    ]

    for cmd_args in commands:
        print(f"Testing: rustdesk {' '.join(cmd_args)}")
        await test_cli_command(cmd_args)

if __name__ == "__main__":
    asyncio.run(main())