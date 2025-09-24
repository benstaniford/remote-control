# Remote Control MCP Server

A comprehensive remote control solution that provides Claude Desktop on Linux with full access to a Windows machine through SSH tunneling. This system consists of a lightweight Windows tray application and an MCP (Model Context Protocol) server that enables natural language control of browser, shell, and file operations.

## Overview

This project bridges the gap between Claude Desktop and Windows systems by providing:

- 🖥️ **Windows Tray Application**: Lightweight service running on Windows
- 🌐 **SSH Tunnel Integration**: Secure remote access through SSH
- 🤖 **MCP Server**: Native Claude Desktop integration via Model Context Protocol
- 🔧 **Comprehensive Control**: Browser, shell, and file system access

## Quick Start

### 1. Windows Machine Setup

**Install and Run the Tray Application:**
```bash
# Build the Windows application
dotnet build RemoteControl.sln

# Run the tray application (stays in system tray)
RemoteControlApp\bin\Debug\RemoteControlApp.exe
```

### 2. SSH Tunnel Setup

**From your Linux/Mac machine:**
```bash
# Create reverse SSH tunnel to forward port 8417
ssh -R 8417:localhost:8417 user@linux-machine

# The Windows app is now accessible on the Linux machine at localhost:8417
```

### 3. Claude Desktop Integration

**Install MCP dependencies:**
```bash
pip install mcp
```

**Configure Claude Desktop** by adding to your MCP settings file:
```json
{
  "mcpServers": {
    "windows-remote": {
      "command": "python",
      "args": ["/path/to/remote-control/WinRemoteMcpServer.py"],
      "env": {}
    }
  }
}
```

### 4. Start Using with Claude

Once configured, you can control your Windows machine naturally:

```
"Launch https://github.com in my Windows browser"
"List files in C:/temp/ on Windows"
"Run 'dir' command on Windows and show me the output"
"Upload document.txt to C:/Users/username/Documents/"
"Download C:/temp/report.pdf to my local machine"
```

## Features

### 🌐 Browser Control
- Launch URLs in Windows default browser
- Cross-platform URL handling via SSH tunnel

### 💻 Shell Operations
- Start/stop Windows Command Prompt sessions
- Execute commands remotely with real-time output
- Interactive shell management with I/O pipes

### 📁 File Operations
- **Upload**: Transfer files from local machine to Windows
- **Download**: Transfer files from Windows to local machine
- **File Management**: Check existence, get info, delete files
- **Directory Listing**: Browse Windows file system with pattern matching
- **Integrity Checking**: SHA256 hashing for file verification

### 🔌 Connection Management
- Automatic connection testing and status reporting
- Configurable host/port settings
- Robust error handling and retry logic

## Architecture

```
[Claude Desktop] ←→ [MCP Server] ←→ [SSH Tunnel] ←→ [Windows Tray App]
     (Linux/Mac)        (Linux)      (Network)         (Windows)
```

**Components:**
- **RemoteControlApp**: C# Windows tray application with HTTP API server
- **WinRemoteMcpServer.py**: MCP server exposing Windows functionality to Claude
- **remote_control_client.py**: Python client library for direct API access
- **SSH Tunnel**: Secure connection bridge between systems

## Available MCP Tools

Claude Desktop automatically discovers these tools:

**Browser Control:**
- `launch_browser` - Open URLs in Windows browser

**Shell Operations:**
- `shell_start` - Start Command Prompt session
- `shell_stop` - Stop shell session
- `shell_status` - Check shell status
- `shell_command` - Execute commands with output
- `shell_get_output` - Retrieve pending shell output

**File Operations:**
- `upload_file` - Upload local files to Windows
- `download_file` - Download files from Windows
- `file_exists` - Check if files exist
- `get_file_info` - Get file metadata and hash
- `delete_file` - Delete Windows files
- `list_files` - List directory contents

**Connection:**
- `test_connection` - Verify Windows app connectivity
- `get_status` - Get connection and shell status
- `configure_connection` - Set host/port settings

## Command Line Tools

For direct usage without Claude Desktop:

```bash
# Browser control
python launch_browser.py https://github.com --port 8417

# Interactive shell
python remote_shell.py --port 8417

# File operations
python file_copy.py document.txt remote:C:/temp/document.txt    # Upload
python file_copy.py remote:C:/temp/doc.txt ./downloaded.txt     # Download
python file_copy.py --list remote:C:/temp/ --pattern "*.txt"    # List
python file_copy.py --info remote:C:/temp/document.txt          # Info
python file_copy.py --delete remote:C:/temp/document.txt        # Delete

# Testing
python tests/run_tests.py               # Run all tests with summary
python tests/test_shell_client.py       # Test shell functionality only
python tests/test_file_copy.py          # Test file operations only  
python tests/test_mcp_server.py         # Test MCP server only
```

## Building

### Prerequisites
- Visual Studio 2019+ or .NET SDK
- .NET Framework 4.8
- Python 3.8+ (for MCP server)
- SSH access between machines

### Build Steps
```bash
# Windows application
dotnet build RemoteControl.sln

# Or with Visual Studio
# 1. Open RemoteControl.sln
# 2. Build -> Build Solution
# 3. Installer generated in RemoteControlInstaller\bin\Release\
```

## Security

- **Local Network Only**: Windows app binds to localhost:8417
- **SSH Encryption**: All traffic encrypted through SSH tunnel
- **File Size Limits**: 100MB maximum file transfer size
- **Path Validation**: Prevents directory traversal attacks
- **Access Control**: Windows file permissions respected

## Protocol Details

The Windows application exposes a JSON HTTP API on localhost:8417:

```json
// Browser control
{"action": "launch_browser", "url": "https://example.com"}

// Shell operations
{"action": "shell_start"}
{"action": "shell_input", "input": "dir"}
{"action": "shell_output"}

// File operations
{"action": "file_upload", "path": "C:/temp/file.txt", "content": "base64_data"}
{"action": "file_download", "path": "C:/temp/file.txt"}
{"action": "file_list", "path": "C:/temp/", "pattern": "*.txt"}
```

## Troubleshooting

**Connection Issues:**
```bash
# Test Windows app directly
curl -X POST http://localhost:8417/ -d '{"action":"launch_browser","url":"https://google.com"}'

# Test MCP server
python tests/test_mcp_server.py

# Verify SSH tunnel
ssh -R 8417:localhost:8417 -N user@remote-machine
```

**Common Solutions:**
- Ensure Windows tray app is running
- Verify SSH tunnel is active (check with `netstat -an | findstr 8417`)
- Check Windows Firewall settings
- Confirm MCP server path in Claude Desktop config

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit a pull request

This project enables seamless integration between Claude Desktop and Windows systems, providing natural language control over remote Windows machines through secure SSH tunneling.
