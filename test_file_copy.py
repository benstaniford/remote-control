#!/usr/bin/env python3
"""
Test script for the file copy functionality.
This script tests file operations without requiring the Windows app to be running.
"""

import sys
import os
import tempfile
import time
from remote_control_client import RemoteControlClient


def test_file_operations():
    """Test the file operation methods."""
    print("Testing Remote Control File Operations")
    print("=" * 50)
    
    # Create client
    client = RemoteControlClient(host="localhost", port=8417)
    
    print(f"Client configured for {client.host}:{client.port}")
    
    # Test connection
    print("\n1. Testing connection...")
    if client.test_connection():
        print("✓ Connection successful!")
        
        # Create a test file
        test_content = "Hello from the remote control file copy test!\nThis is a test file.\n"
        test_filename = "test_file_copy.txt"
        
        with open(test_filename, 'w') as f:
            f.write(test_content)
        print(f"✓ Created local test file: {test_filename}")
        
        # Test file upload
        print("\n2. Testing file upload...")
        try:
            remote_path = "C:/temp/remote_test_file.txt"
            success = client.upload_file(test_filename, remote_path)
            if success:
                print(f"✓ File uploaded to remote:{remote_path}")
            else:
                print("✗ File upload failed")
                
        except Exception as e:
            print(f"✗ File upload failed: {e}")
            
        # Test file exists
        print("\n3. Testing file exists check...")
        try:
            exists = client.file_exists(remote_path)
            print(f"✓ Remote file exists: {exists}")
        except Exception as e:
            print(f"✗ File exists check failed: {e}")
            
        # Test file info
        print("\n4. Testing file info...")
        try:
            if client.file_exists(remote_path):
                file_info = client.get_file_info(remote_path)
                print(f"✓ File info retrieved:")
                print(f"  Name: {file_info['name']}")
                print(f"  Size: {file_info['size']} bytes")
                print(f"  Modified: {file_info['modified']}")
                print(f"  Hash: {file_info['hash'][:16]}...")
            else:
                print("! Remote file doesn't exist, skipping file info test")
                
        except Exception as e:
            print(f"✗ File info failed: {e}")
            
        # Test file download
        print("\n5. Testing file download...")
        try:
            download_path = "downloaded_test_file.txt"
            if client.file_exists(remote_path):
                success = client.download_file(remote_path, download_path)
                if success:
                    print(f"✓ File downloaded to {download_path}")
                    
                    # Verify content
                    with open(download_path, 'r') as f:
                        downloaded_content = f.read()
                    
                    if downloaded_content == test_content:
                        print("✓ Downloaded content matches original")
                    else:
                        print("✗ Downloaded content doesn't match original")
                        print(f"Original: {repr(test_content)}")
                        print(f"Downloaded: {repr(downloaded_content)}")
                else:
                    print("✗ File download failed")
            else:
                print("! Remote file doesn't exist, skipping download test")
                
        except Exception as e:
            print(f"✗ File download failed: {e}")
            
        # Test file listing
        print("\n6. Testing file listing...")
        try:
            files = client.list_files("C:/temp/", "*.txt")
            print(f"✓ Found {len(files)} .txt files in C:/temp/:")
            for file_path in files[:5]:  # Show first 5 files
                filename = os.path.basename(file_path)
                print(f"  {filename}")
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more")
                
        except Exception as e:
            print(f"✗ File listing failed: {e}")
            
        # Test file deletion
        print("\n7. Testing file deletion...")
        try:
            if client.file_exists(remote_path):
                success = client.delete_file(remote_path)
                if success:
                    print(f"✓ Remote file deleted")
                    
                    # Verify deletion
                    exists_after = client.file_exists(remote_path)
                    if not exists_after:
                        print("✓ File deletion verified")
                    else:
                        print("✗ File still exists after deletion")
                else:
                    print("✗ File deletion failed")
            else:
                print("! Remote file doesn't exist, skipping deletion test")
                
        except Exception as e:
            print(f"✗ File deletion failed: {e}")
            
        # Cleanup local files
        try:
            if os.path.exists(test_filename):
                os.remove(test_filename)
            if os.path.exists(download_path):
                os.remove(download_path)
            print("\n✓ Cleaned up local test files")
        except:
            pass
            
    else:
        print("✗ Connection failed!")
        print("Make sure the Remote Control tray app is running on Windows")
        print("and the SSH tunnel is set up if connecting remotely.")
        
    print("\nFile operations test completed!")


def test_file_copy_script():
    """Test the file_copy.py script functionality."""
    print("\n" + "=" * 50)
    print("Testing file_copy.py Script Functionality")
    print("=" * 50)
    
    # Import the FileCopyTool
    try:
        from file_copy import FileCopyTool
        
        # Create tool
        tool = FileCopyTool(host="localhost", port=8417)
        
        print("✓ FileCopyTool imported successfully")
        
        # Test path parsing
        is_remote, path = tool.parse_path("remote:C:/temp/test.txt")
        assert is_remote == True and path == "C:/temp/test.txt"
        
        is_remote, path = tool.parse_path("./local_file.txt")
        assert is_remote == False and path == "./local_file.txt"
        
        print("✓ Path parsing works correctly")
        
        # Test connection in tool
        print(f"\nTesting connection via FileCopyTool...")
        if tool.client.test_connection():
            print("✓ FileCopyTool can connect to server")
            print("\nYou can now test the script manually with:")
            print("  python file_copy.py --help")
            print("  python file_copy.py --list remote:C:/temp/")
        else:
            print("✗ FileCopyTool cannot connect to server")
            
    except ImportError as e:
        print(f"✗ Failed to import FileCopyTool: {e}")
    except Exception as e:
        print(f"✗ FileCopyTool test failed: {e}")


if __name__ == "__main__":
    try:
        test_file_operations()
        test_file_copy_script()
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Test failed with error: {e}")
        sys.exit(1)