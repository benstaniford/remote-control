#!/usr/bin/env python3
"""
Remote Browser Launcher Script

Command-line script to launch URLs in a Windows browser via SSH tunnel.
Uses the Remote Control tray application running on Windows.

Usage:
    python launch_browser.py <url> [--port PORT] [--host HOST]
    python launch_browser.py --test [--port PORT] [--host HOST]
    python launch_browser.py --status [--port PORT] [--host HOST]

Examples:
    # Launch browser with SSH tunnel (typical usage)
    ssh -L 8417:localhost:8417 user@windows-machine
    python launch_browser.py https://google.com
    
    # Test connection
    python launch_browser.py --test
    
    # Check status
    python launch_browser.py --status
"""

import argparse
import sys
from typing import Optional
from remote_control_client import RemoteControlClient


def main():
    """Main entry point for the browser launcher script."""
    parser = argparse.ArgumentParser(
        description="Launch URLs in Windows browser via Remote Control app",
        epilog="""
Examples:
  %(prog)s https://google.com
  %(prog)s --test  
  %(prog)s --status
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "url",
        nargs="?",
        help="URL to open in browser"
    )
    
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to connect to (default: localhost)"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8417,
        help="Port to connect to (default: 8417)"
    )
    
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Test connection to remote control server"
    )
    
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Show connection status information"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.test and not args.status and not args.url:
        parser.error("URL is required unless using --test or --status")
    
    if (args.test or args.status) and args.url:
        parser.error("Cannot specify URL with --test or --status")
    
    # Create client
    client = RemoteControlClient(host=args.host, port=args.port)
    
    try:
        if args.test:
            return test_connection(client)
        elif args.status:
            return show_status(client)
        else:
            return launch_browser(client, args.url, args.timeout)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def test_connection(client: RemoteControlClient) -> int:
    """Test connection to the remote control server."""
    print(f"Testing connection to {client.host}:{client.port}...")
    
    if client.test_connection():
        print("✓ Connection successful")
        return 0
    else:
        print("✗ Connection failed")
        print(f"Make sure the Remote Control app is running on {client.host}:{client.port}")
        if client.port != 8417:
            print("If using direct connection, verify the app is running on the correct port")
        else:
            print("If using SSH tunnel, verify the tunnel is active:")
            print(f"  ssh -L {client.port}:localhost:8417 user@windows-machine")
        return 1


def show_status(client: RemoteControlClient) -> int:
    """Show connection status information."""
    status = client.get_status()
    
    print("Remote Control Client Status:")
    print(f"  Host: {status['host']}")
    print(f"  Port: {status['port']}")
    print(f"  URL: {status['url']}")
    print(f"  Connected: {'Yes' if status['connected'] else 'No'}")
    
    if not status['connected']:
        print("\nTroubleshooting:")
        print("1. Ensure Remote Control app is running on Windows")
        print("2. If using SSH tunnel, verify tunnel is active:")
        if status['port'] == 8417:
            print(f"   ssh -L {status['port']}:localhost:8417 user@windows-machine")
        print("3. Check Windows firewall settings")
        return 1
    
    return 0


def launch_browser(client: RemoteControlClient, url: str, timeout: int) -> int:
    """Launch browser with the specified URL."""
    print(f"Launching browser with URL: {url}")
    print(f"Connecting to {client.host}:{client.port}...")
    
    try:
        success = client.launch_browser(url)
        if success:
            print("✓ Browser launched successfully")
            return 0
        else:
            print("✗ Failed to launch browser")
            return 1
            
    except ConnectionError as e:
        print(f"✗ Connection failed: {e}")
        if client.port != 8417:
            print("If using direct connection, verify the app is running on the correct port")
        else:
            print("If using SSH tunnel, verify the tunnel is active:")
            print(f"  ssh -L {client.port}:localhost:8417 user@windows-machine")
        return 1
    except ValueError as e:
        print(f"✗ Invalid URL: {e}")
        return 1
    except RuntimeError as e:
        print(f"✗ Server error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())