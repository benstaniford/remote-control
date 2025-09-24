#!/usr/bin/env python3
"""
Test script for the shell functionality in the remote control client.
This script tests the shell API without requiring the Windows app to be running.
"""

import sys
import time
from remote_control_client import RemoteControlClient


def test_shell_api():
    """Test the shell API methods."""
    print("Testing Remote Control Shell API")
    print("=" * 40)
    
    # Create client (this will work even if server isn't running)
    client = RemoteControlClient(host="localhost", port=8417)
    
    print(f"Client configured for {client.host}:{client.port}")
    
    # Test connection
    print("\n1. Testing connection...")
    if client.test_connection():
        print("✓ Connection successful!")
        
        # Test shell status
        print("\n2. Testing shell status...")
        try:
            is_running = client.get_shell_status()
            print(f"✓ Shell status: {'Running' if is_running else 'Not running'}")
        except Exception as e:
            print(f"✗ Shell status failed: {e}")
            
        # Test starting shell
        print("\n3. Testing shell start...")
        try:
            if not client.get_shell_status():
                client.start_shell()
                print("✓ Shell started successfully!")
            else:
                print("✓ Shell already running!")
        except Exception as e:
            print(f"✗ Shell start failed: {e}")
            
        # Test sending input
        print("\n4. Testing shell input...")
        try:
            client.send_shell_input("echo Hello from remote shell!")
            print("✓ Input sent successfully!")
            
            # Wait and get output
            time.sleep(1)
            result = client.get_shell_output()
            if result["output"]:
                print(f"✓ Output received: {result['output'].strip()}")
            if result["error"]:
                print(f"! Error output: {result['error'].strip()}")
                
        except Exception as e:
            print(f"✗ Shell input/output failed: {e}")
            
        # Test stopping shell
        print("\n5. Testing shell stop...")
        try:
            client.stop_shell()
            print("✓ Shell stopped successfully!")
        except Exception as e:
            print(f"✗ Shell stop failed: {e}")
            
    else:
        print("✗ Connection failed!")
        print("Make sure the Remote Control tray app is running on Windows")
        print("and the SSH tunnel is set up if connecting remotely.")
        
    print("\nTest completed!")


if __name__ == "__main__":
    try:
        test_shell_api()
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Test failed with error: {e}")
        sys.exit(1)