#!/usr/bin/env python3
"""
Interactive Remote Shell

This script provides an interactive shell interface to a remote Windows machine
running the Remote Control tray application. Commands are sent via HTTP and
output is displayed in real-time.

Usage:
    python remote_shell.py [--host HOST] [--port PORT]

Example:
    # Connect to SSH tunnel
    python remote_shell.py --port 8417
    
    # Connect to specific host
    python remote_shell.py --host 192.168.1.100 --port 8417
"""

import argparse
import sys
import time
import signal
from typing import Optional
from remote_control_client import RemoteControlClient


class RemoteShell:
    """Interactive remote shell interface."""
    
    def __init__(self, host: str = "localhost", port: int = 8417):
        """
        Initialize the remote shell.
        
        Args:
            host: The hostname to connect to
            port: The port to connect to
        """
        self.client = RemoteControlClient(host, port)
        self.running = False
        
    def start(self):
        """Start the interactive shell session."""
        print(f"Connecting to Remote Control at {self.client.host}:{self.client.port}")
        
        # Test connection first
        if not self.client.test_connection():
            print(f"Error: Cannot connect to {self.client.host}:{self.client.port}")
            print("Make sure the Remote Control tray application is running and accessible.")
            return False
            
        print("Connection successful!")
        
        # Start the remote shell
        try:
            if self.client.get_shell_status():
                print("Shell is already running on remote machine.")
            else:
                print("Starting shell on remote machine...")
                self.client.start_shell()
                print("Shell started successfully!")
                
        except Exception as e:
            print(f"Error starting shell: {e}")
            return False
            
        # Set up signal handler for clean exit
        signal.signal(signal.SIGINT, self._signal_handler)
        
        print("\nRemote shell is ready. Type 'exit' to quit.")
        print("=" * 50)
        
        self.running = True
        self._run_shell_loop()
        return True
        
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n\nReceived interrupt signal. Shutting down...")
        self.stop()
        
    def _run_shell_loop(self):
        """Main shell interaction loop."""
        while self.running:
            try:
                # Get any pending output first
                self._flush_output()
                
                # Get user input
                try:
                    command = input("remote> ")
                except EOFError:
                    # Handle Ctrl+D
                    print()
                    break
                    
                if command.strip().lower() == 'exit':
                    break
                    
                if command.strip() == '':
                    continue
                    
                # Send command to remote shell
                try:
                    self.client.send_shell_input(command)
                    
                    # Give the command time to execute and get output
                    time.sleep(0.1)
                    self._flush_output()
                    
                except Exception as e:
                    print(f"Error sending command: {e}")
                    break
                    
            except KeyboardInterrupt:
                # Handle Ctrl+C during input
                print()
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                break
                
        self.stop()
        
    def _flush_output(self):
        """Get and display any pending output from the remote shell."""
        try:
            result = self.client.get_shell_output()
            
            # Display stdout
            if result["output"].strip():
                print(result["output"], end='')
                
            # Display stderr in red if available
            if result["error"].strip():
                print(f"\033[91m{result['error']}\033[0m", end='')
                
        except Exception as e:
            print(f"Error getting output: {e}")
            
    def stop(self):
        """Stop the shell session."""
        if not self.running:
            return
            
        self.running = False
        
        try:
            print("\nStopping remote shell...")
            self.client.stop_shell()
            print("Remote shell stopped.")
        except Exception as e:
            print(f"Error stopping shell: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive remote shell for Windows Remote Control app",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Connect to localhost:8417
  %(prog)s --port 8417              # Connect via SSH tunnel
  %(prog)s --host 192.168.1.100     # Connect to specific host
        """
    )
    
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to connect to (default: localhost)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8417,
        help="Port to connect to (default: 8417)"
    )
    
    args = parser.parse_args()
    
    # Create and start the shell
    shell = RemoteShell(args.host, args.port)
    
    try:
        success = shell.start()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nExiting...")
        shell.stop()
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()