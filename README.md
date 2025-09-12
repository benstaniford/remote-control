# Remote Control App

A Windows tray application that listens on localhost:417 and provides a JSON-based protocol for launching the default browser to specified URLs.

## Features

- Runs as a system tray application
- HTTP server listening on localhost:417
- JSON-based protocol for browser control
- Automatic startup with Windows (via installer)
- WiX 3 based installer

## Building

### Prerequisites

1. Visual Studio 2019 or later
2. .NET Framework 4.8
3. WiX Toolset v3.11 or later

### Build Steps

1. Open `RemoteControl.sln` in Visual Studio
2. Restore NuGet packages
3. Build the solution in Release mode
4. The installer will be generated in `RemoteControlInstaller\bin\Release\RemoteControlAppInstaller.msi`

## Usage

### JSON Protocol

Send POST requests to `http://localhost:417/` with JSON payloads:

#### Launch Browser
```json
{
  "action": "launch_browser",
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Browser launched successfully"
}
```

### Example using curl
```bash
curl -X POST http://localhost:417/ -H "Content-Type: application/json" -d '{"action":"launch_browser","url":"https://google.com"}'
```

### Example using PowerShell
```powershell
$body = @{
    action = "launch_browser"
    url = "https://google.com"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:417/" -Method Post -Body $body -ContentType "application/json"
```

## Installation

1. Build the solution
2. Run the generated MSI installer: `RemoteControlAppInstaller.msi`
3. The application will start automatically and add itself to Windows startup

## System Tray

- Right-click the tray icon to see status and exit options
- Double-click to show current status
- The application runs silently in the background
