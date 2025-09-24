# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a C# Windows tray application that provides remote browser control and shell access via HTTP JSON API. It listens on localhost:8417 and accepts JSON commands to launch URLs in the default browser and execute shell commands remotely.

## Build Commands

- **Visual Studio**: Open `RemoteControl.sln` and build via IDE
- **Command Line**: Use `msbuild RemoteControl.sln` with appropriate configuration
- **Configurations**: Debug/Release for AnyCPU, x86, x64 platforms
- **Installer**: Build solution to generate `RemoteControlAppInstaller.msi` in `RemoteControlInstaller\bin\Release\`

## Architecture

### Core Components

- **Program.cs**: Entry point that starts the tray application context
- **TrayApplicationContext**: Manages system tray icon, context menu, HTTP server lifecycle, and shell manager
- **HttpServer**: HTTP listener on port 8417 with JSON protocol handling and CORS support
- **BrowserLauncher**: URL validation and browser launching using `Process.Start()`
- **ShellManager**: Manages Windows Command Prompt processes with input/output pipes

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
- **test_shell_client.py**: Test script for shell functionality

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
```

## Development Notes

- Application runs as Windows Forms app with system tray interface
- HTTP server uses async/await pattern with cancellation token support
- Shell processes managed with input/output pipes for real-time interaction
- Icon embedded as resource (`app.ico`)
- Error handling includes JSON error responses and graceful degradation
- CORS headers configured for cross-origin requests
- Python client handles connection errors and provides clear error messages
- Shell functionality supports Windows Command Prompt with real-time I/O
