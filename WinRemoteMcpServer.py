#!/usr/bin/env python3
"""
MCP Server for Windows Remote Control Integration

This server provides tools to interact with a remote Windows machine using the Remote Control
tray application. It exposes browser control, shell operations, and file transfer capabilities
as MCP tools that can be used by MCP clients like Claude Desktop.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Any, Dict, List, Optional, Sequence

# MCP imports
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# Local imports
from remote_control_client import RemoteControlClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-winremote-server")

class WinRemoteMCPServer:
    def __init__(self):
        self.server = Server("winremote-mcp-server")
        self.client: Optional[RemoteControlClient] = None
        self.host = "localhost"
        self.port = 8417
        
        # Register tools
        self._register_tools()
        
    def _register_tools(self):
        """Register all available Windows Remote Control tools with the MCP server."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available Windows Remote Control tools."""
            return [
                # Browser control
                Tool(
                    name="launch_browser",
                    description="Launch the default browser on Windows with a specified URL",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to open in the browser"
                            }
                        },
                        "required": ["url"]
                    }
                ),
                
                # Shell operations
                Tool(
                    name="shell_start",
                    description="Start a Windows Command Prompt shell session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "working_directory": {
                                "type": "string",
                                "description": "Initial working directory for the shell (optional)"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="shell_stop",
                    description="Stop the current Windows shell session",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="shell_status",
                    description="Check if a Windows shell session is currently running",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="shell_command",
                    description="Execute a command in the Windows shell and get output",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The command to execute in the Windows shell"
                            },
                            "auto_start": {
                                "type": "boolean",
                                "description": "Automatically start shell if not running (default: true)",
                                "default": True
                            },
                            "working_directory": {
                                "type": "string",
                                "description": "Working directory to use when starting shell (only used if auto_start is true)"
                            }
                        },
                        "required": ["command"]
                    }
                ),
                Tool(
                    name="shell_get_output",
                    description="Get pending output from the Windows shell",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="shell_cd",
                    description="Change the working directory of the running Windows shell",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "The directory path to change to"
                            }
                        },
                        "required": ["directory"]
                    }
                ),
                
                # File operations
                Tool(
                    name="upload_file",
                    description="Upload a local file to the Windows machine",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "local_path": {
                                "type": "string",
                                "description": "Path to the local file to upload"
                            },
                            "remote_path": {
                                "type": "string",
                                "description": "Path where the file should be saved on Windows (e.g., 'C:/temp/file.txt')"
                            }
                        },
                        "required": ["local_path", "remote_path"]
                    }
                ),
                Tool(
                    name="download_file",
                    description="Download a file from the Windows machine to local system",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "remote_path": {
                                "type": "string",
                                "description": "Path to the file on Windows (e.g., 'C:/temp/file.txt')"
                            },
                            "local_path": {
                                "type": "string",
                                "description": "Path where the file should be saved locally"
                            }
                        },
                        "required": ["remote_path", "local_path"]
                    }
                ),
                Tool(
                    name="file_exists",
                    description="Check if a file exists on the Windows machine",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to check on Windows (e.g., 'C:/temp/file.txt')"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="get_file_info",
                    description="Get detailed information about a file on Windows",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file on Windows (e.g., 'C:/temp/file.txt')"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="delete_file",
                    description="Delete a file on the Windows machine",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file to delete on Windows (e.g., 'C:/temp/file.txt')"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="list_files",
                    description="List files in a directory on the Windows machine",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path on Windows (e.g., 'C:/temp/')"
                            },
                            "pattern": {
                                "type": "string",
                                "description": "File pattern to match (e.g., '*.txt', default: '*')",
                                "default": "*"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                
                # Connection management
                Tool(
                    name="test_connection",
                    description="Test connection to the Windows Remote Control service",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_status",
                    description="Get status information about the connection",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="configure_connection",
                    description="Configure the connection host and port",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "host": {
                                "type": "string",
                                "description": "Host to connect to (default: localhost)",
                                "default": "localhost"
                            },
                            "port": {
                                "type": "integer",
                                "description": "Port to connect to (default: 8417)",
                                "default": 8417
                            }
                        },
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
            """Handle tool calls."""
            try:
                # Ensure client is initialized
                await self._ensure_client_initialized()
                
                if name == "launch_browser":
                    return await self._launch_browser(arguments)
                elif name == "shell_start":
                    return await self._shell_start(arguments)
                elif name == "shell_stop":
                    return await self._shell_stop(arguments)
                elif name == "shell_status":
                    return await self._shell_status(arguments)
                elif name == "shell_command":
                    return await self._shell_command(arguments)
                elif name == "shell_get_output":
                    return await self._shell_get_output(arguments)
                elif name == "shell_cd":
                    return await self._shell_cd(arguments)
                elif name == "upload_file":
                    return await self._upload_file(arguments)
                elif name == "download_file":
                    return await self._download_file(arguments)
                elif name == "file_exists":
                    return await self._file_exists(arguments)
                elif name == "get_file_info":
                    return await self._get_file_info(arguments)
                elif name == "delete_file":
                    return await self._delete_file(arguments)
                elif name == "list_files":
                    return await self._list_files(arguments)
                elif name == "test_connection":
                    return await self._test_connection(arguments)
                elif name == "get_status":
                    return await self._get_status(arguments)
                elif name == "configure_connection":
                    return await self._configure_connection(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                    
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _ensure_client_initialized(self):
        """Ensure Remote Control client is initialized."""
        if self.client is None:
            self.client = RemoteControlClient(host=self.host, port=self.port)
            logger.info(f"Initialized Remote Control client for {self.host}:{self.port}")

    # Browser control methods
    async def _launch_browser(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Launch browser with specified URL."""
        url = arguments["url"]
        
        try:
            success = self.client.launch_browser(url)
            result = {
                "success": success,
                "url": url,
                "message": f"Successfully launched browser with URL: {url}" if success else "Failed to launch browser"
            }
        except Exception as e:
            result = {
                "success": False,
                "url": url,
                "error": str(e)
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    # Shell operation methods
    async def _shell_start(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Start a Windows shell session."""
        working_directory = arguments.get("working_directory")
        
        try:
            success = self.client.start_shell(working_directory)
            result = {
                "success": success,
                "working_directory": working_directory,
                "message": f"Shell started successfully" + (f" in {working_directory}" if working_directory else "") if success else "Failed to start shell"
            }
        except Exception as e:
            result = {
                "success": False,
                "working_directory": working_directory,
                "error": str(e)
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _shell_stop(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Stop the current shell session."""
        try:
            success = self.client.stop_shell()
            result = {
                "success": success,
                "message": "Shell stopped successfully" if success else "Failed to stop shell"
            }
        except Exception as e:
            result = {
                "success": False,
                "error": str(e)
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _shell_status(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Get shell status."""
        try:
            is_running = self.client.get_shell_status()
            result = {
                "running": is_running,
                "status": "running" if is_running else "stopped"
            }
        except Exception as e:
            result = {
                "running": False,
                "error": str(e)
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _shell_command(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute a shell command and get output."""
        command = arguments["command"]
        auto_start = arguments.get("auto_start", True)
        working_directory = arguments.get("working_directory")
        
        try:
            # Start shell if requested and not running
            if auto_start and not self.client.get_shell_status():
                self.client.start_shell(working_directory)
                await asyncio.sleep(0.1)  # Brief delay for shell to start
            
            # Send command
            self.client.send_shell_input(command)
            
            # Wait a moment for command to execute
            await asyncio.sleep(0.5)
            
            # Get output
            output_result = self.client.get_shell_output()
            
            result = {
                "command": command,
                "working_directory": working_directory,
                "success": True,
                "output": output_result["output"],
                "error": output_result["error"]
            }
        except Exception as e:
            result = {
                "command": command,
                "working_directory": working_directory,
                "success": False,
                "error": str(e)
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _shell_get_output(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Get pending shell output."""
        try:
            output_result = self.client.get_shell_output()
            result = {
                "success": True,
                "output": output_result["output"],
                "error": output_result["error"]
            }
        except Exception as e:
            result = {
                "success": False,
                "error": str(e)
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _shell_cd(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Change working directory of the running shell."""
        directory = arguments["directory"]
        
        try:
            success = self.client.change_directory(directory)
            result = {
                "success": success,
                "directory": directory,
                "message": f"Changed directory to {directory}" if success else "Failed to change directory"
            }
        except Exception as e:
            result = {
                "success": False,
                "directory": directory,
                "error": str(e)
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    # File operation methods
    async def _upload_file(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Upload a file to Windows."""
        local_path = arguments["local_path"]
        remote_path = arguments["remote_path"]
        
        try:
            success = self.client.upload_file(local_path, remote_path)
            
            # Get file size for info
            file_size = 0
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
            
            result = {
                "success": success,
                "local_path": local_path,
                "remote_path": remote_path,
                "file_size": file_size,
                "message": f"Successfully uploaded {local_path} to {remote_path}" if success else "Upload failed"
            }
        except Exception as e:
            result = {
                "success": False,
                "local_path": local_path,
                "remote_path": remote_path,
                "error": str(e)
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _download_file(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Download a file from Windows."""
        remote_path = arguments["remote_path"]
        local_path = arguments["local_path"]
        
        try:
            success = self.client.download_file(remote_path, local_path)
            
            # Get file size for info
            file_size = 0
            if success and os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
            
            result = {
                "success": success,
                "remote_path": remote_path,
                "local_path": local_path,
                "file_size": file_size,
                "message": f"Successfully downloaded {remote_path} to {local_path}" if success else "Download failed"
            }
        except Exception as e:
            result = {
                "success": False,
                "remote_path": remote_path,
                "local_path": local_path,
                "error": str(e)
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _file_exists(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Check if file exists on Windows."""
        path = arguments["path"]
        
        try:
            exists = self.client.file_exists(path)
            result = {
                "path": path,
                "exists": exists
            }
        except Exception as e:
            result = {
                "path": path,
                "exists": False,
                "error": str(e)
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _get_file_info(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Get file information from Windows."""
        path = arguments["path"]
        
        try:
            file_info = self.client.get_file_info(path)
            result = {
                "path": path,
                "exists": True,
                "info": file_info
            }
        except Exception as e:
            result = {
                "path": path,
                "exists": False,
                "error": str(e)
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _delete_file(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Delete a file on Windows."""
        path = arguments["path"]
        
        try:
            success = self.client.delete_file(path)
            result = {
                "path": path,
                "success": success,
                "message": f"Successfully deleted {path}" if success else "Delete failed"
            }
        except Exception as e:
            result = {
                "path": path,
                "success": False,
                "error": str(e)
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _list_files(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """List files in a Windows directory."""
        path = arguments["path"]
        pattern = arguments.get("pattern", "*")
        
        try:
            files = self.client.list_files(path, pattern)
            result = {
                "path": path,
                "pattern": pattern,
                "success": True,
                "file_count": len(files),
                "files": [os.path.basename(f) for f in files],
                "full_paths": files
            }
        except Exception as e:
            result = {
                "path": path,
                "pattern": pattern,
                "success": False,
                "error": str(e)
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    # Connection management methods
    async def _test_connection(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Test connection to Windows Remote Control service."""
        try:
            connected = self.client.test_connection()
            result = {
                "host": self.host,
                "port": self.port,
                "connected": connected,
                "message": "Connection successful" if connected else "Connection failed"
            }
        except Exception as e:
            result = {
                "host": self.host,
                "port": self.port,
                "connected": False,
                "error": str(e)
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _get_status(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Get connection status information."""
        try:
            status = self.client.get_status()
            result = {
                "connection": status,
                "shell_running": self.client.get_shell_status() if status["connected"] else False
            }
        except Exception as e:
            result = {
                "connection": {
                    "host": self.host,
                    "port": self.port,
                    "connected": False,
                    "url": f"http://{self.host}:{self.port}/"
                },
                "shell_running": False,
                "error": str(e)
            }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _configure_connection(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Configure connection settings."""
        host = arguments.get("host", self.host)
        port = arguments.get("port", self.port)
        
        # Update connection settings
        self.host = host
        self.port = port
        
        # Reinitialize client with new settings
        self.client = RemoteControlClient(host=self.host, port=self.port)
        
        result = {
            "host": self.host,
            "port": self.port,
            "message": f"Connection configured for {self.host}:{self.port}"
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Windows Remote Control MCP Server...")
    winremote_server = WinRemoteMCPServer()
    logger.info("Windows Remote Control MCP Server initialized with tools")
    
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await winremote_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="winremote-mcp-server",
                server_version="1.0.0",
                capabilities=winremote_server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())