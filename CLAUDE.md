# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a C# Windows tray application that provides remote browser control, shell access, and file transfer capabilities via HTTP JSON API. It listens on localhost:8417 and accepts JSON commands to launch URLs in the default browser, execute shell commands remotely, and transfer files bidirectionally.

## Build Commands

- **Visual Studio**: Open `RemoteControl.sln` and build via IDE
- **Command Line**: Use `msbuild RemoteControl.sln` with appropriate configuration
- **Configurations**: Debug/Release for AnyCPU, x86, x64 platforms
- **Installer**: Build solution to generate `RemoteControlAppInstaller.msi` in `RemoteControlInstaller\bin\Release\`

## Architecture

### Core Components

- **Program.cs**: Entry point that starts the tray application context
- **TrayApplicationContext**: Manages system tray icon, context menu, HTTP server lifecycle, shell manager, and file manager
- **HttpServer**: HTTP listener on port 8417 with JSON protocol handling and CORS support
- **BrowserLauncher**: URL validation and browser launching using `Process.Start()`
- **ShellManager**: Manages Windows Command Prompt processes with input/output pipes
- **FileManager**: Handles file operations including upload, download, and file system access

### Protocol Structure

JSON API accepts POST requests with format:
```json
{
  "action": "launch_browser",
  "url": "https://example.com"
}
```

#### Shell Commands:
```json
{"action": "shell_start"}
{"action": "shell_input", "input": "dir"}
{"action": "shell_output"}
{"action": "shell_status"}
{"action": "shell_stop"}
```

#### File Commands:
```json
{"action": "file_upload", "path": "C:/temp/file.txt", "content": "base64_content"}
{"action": "file_download", "path": "C:/temp/file.txt"}
{"action": "file_exists", "path": "C:/temp/file.txt"}
{"action": "file_info", "path": "C:/temp/file.txt"}
{"action": "file_delete", "path": "C:/temp/file.txt"}
{"action": "file_list", "path": "C:/temp/", "pattern": "*.txt"}
```

### Dependencies

- **.NET Framework 4.8**: Target framework
- **Newtonsoft.Json 13.0.3**: JSON serialization/deserialization
- **System.Windows.Forms**: Tray icon and UI components
- **System.Net.HttpListener**: HTTP server implementation

### Project Structure

- **RemoteControlApp/**: Main application code and resources
- **RemoteControlInstaller/**: WiX 3 installer project
- **RemoteControl.sln**: Visual Studio solution file
- **remote_control_client.py**: Python client module for API communication
- **launch_browser.py**: Command-line script for launching browsers remotely
- **remote_shell.py**: Interactive remote shell script
- **file_copy.py**: File copy script with local/remote syntax
- **test_shell_client.py**: Test script for shell functionality  
- **test_file_copy.py**: Test script for file copy functionality

## Python Client Integration

### SSH Tunnel Setup

The typical use case involves SSH tunneling from Linux back to the Windows machine you connected from:

```bash
# Create SSH tunnel (Windows -> Linux)
ssh -R 8417:localhost:8417 user@linux-machine

# Launch browser from Linux
python launch_browser.py https://google.com
```

### Python Module Usage

```python
from remote_control_client import RemoteControlClient

# Connect to local port (SSH tunnel)
client = RemoteControlClient(host="localhost", port=8417)

# Test connection
if client.test_connection():
    # Launch browser
    client.launch_browser("https://example.com")
    
    # Shell operations
    client.start_shell()
    client.send_shell_input("dir")
    result = client.get_shell_output()
    print(result["output"])
    client.stop_shell()
    
    # File operations
    client.upload_file("local_file.txt", "C:/temp/remote_file.txt")
    client.download_file("C:/temp/remote_file.txt", "downloaded_file.txt")
    file_info = client.get_file_info("C:/temp/remote_file.txt")
    print(f"File size: {file_info['size']} bytes")
```

### Command Line Usage

```bash
# Launch browser via SSH tunnel
python launch_browser.py https://example.com --port 8417

# Test connection
python launch_browser.py --test --port 8417

# Show status
python launch_browser.py --status --port 8417

# Interactive remote shell
python remote_shell.py --port 8417

# Test shell functionality
python test_shell_client.py

# File copy operations
python file_copy.py document.txt remote:C:/temp/document.txt    # Upload
python file_copy.py remote:C:/temp/document.txt ./downloaded.txt  # Download
python file_copy.py --list remote:C:/temp/ --pattern "*.txt"      # List files
python file_copy.py --info remote:C:/temp/document.txt            # File info
python file_copy.py --delete remote:C:/temp/document.txt          # Delete file

# Test file copy functionality
python test_file_copy.py
```

## Development Notes

- Application runs as Windows Forms app with system tray interface
- HTTP server uses async/await pattern with cancellation token support
- Shell processes managed with input/output pipes for real-time interaction
- File operations use Base64 encoding for binary-safe transfer over JSON
- Maximum file size limit of 100MB for uploads/downloads
- Icon embedded as resource (`app.ico`)
- Error handling includes JSON error responses and graceful degradation
- CORS headers configured for cross-origin requests
- Python client handles connection errors and provides clear error messages
- Shell functionality supports Windows Command Prompt with real-time I/O
- File transfer supports bidirectional copy with integrity checking via SHA256 hashes
