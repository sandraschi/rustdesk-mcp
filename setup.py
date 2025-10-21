"""
DXT Packaging for RustDesk MCP Server

This setup file follows DXT Packaging Standards for creating distributable packages.
"""
from setuptools import setup, find_packages
import os

# Read the README for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="rustdesk-mcp",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="FastMCP 2.10 server for RustDesk remote desktop management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rustdesk-mcp",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    entry_points={
        "console_scripts": [
            "rustdesk-mcp=rustdesk_mcp.server:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/rustdesk-mcp/issues",
        "Source": "https://github.com/yourusername/rustdesk-mcp",
    },
)
