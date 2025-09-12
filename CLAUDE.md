# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a C# Windows tray application that provides remote browser control via HTTP JSON API. It listens on localhost:417 and accepts JSON commands to launch URLs in the default browser.

## Build Commands

- **Visual Studio**: Open `RemoteControl.sln` and build via IDE
- **Command Line**: Use `msbuild RemoteControl.sln` with appropriate configuration
- **Configurations**: Debug/Release for AnyCPU, x86, x64 platforms
- **Installer**: Build solution to generate `RemoteControlAppInstaller.msi` in `RemoteControlInstaller\bin\Release\`

## Architecture

### Core Components

- **Program.cs**: Entry point that starts the tray application context
- **TrayApplicationContext**: Manages system tray icon, context menu, and HTTP server lifecycle
- **HttpServer**: HTTP listener on port 417 with JSON protocol handling and CORS support
- **BrowserLauncher**: URL validation and browser launching using `Process.Start()`

### Protocol Structure

JSON API accepts POST requests with format:
```json
{
  "action": "launch_browser",
  "url": "https://example.com"
}
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

## Python Client Integration

### SSH Tunnel Setup

The typical use case involves SSH tunneling from Linux to Windows:

```bash
# Create SSH tunnel (Linux -> Windows)
ssh -L 8417:localhost:417 user@windows-machine

# Launch browser from Linux
python launch_browser.py https://google.com --port 8417
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
```

### Command Line Usage

```bash
# Launch browser via SSH tunnel
python launch_browser.py https://example.com --port 8417

# Test connection
python launch_browser.py --test --port 8417

# Show status
python launch_browser.py --status --port 8417
```

## Development Notes

- Application runs as Windows Forms app with system tray interface
- HTTP server uses async/await pattern with cancellation token support
- Icon embedded as resource (`app.ico`)
- Error handling includes JSON error responses and graceful degradation
- CORS headers configured for cross-origin requests
- Python client handles connection errors and provides clear error messages