#!/usr/bin/env python3
"""
Remote File Copy Script

This script provides file copy functionality between local and remote Windows machines
using the Remote Control tray application. Supports both directions:
- Local to remote: ./file_copy.py local_file remote:remote_file
- Remote to local: ./file_copy.py remote:remote_file local_file

Usage:
    python file_copy.py <source> <destination> [--host HOST] [--port PORT]
    python file_copy.py --list remote:<directory> [--pattern PATTERN]
    python file_copy.py --info remote:<file>
    python file_copy.py --delete remote:<file>

Examples:
    # Upload file to remote
    python file_copy.py document.txt remote:C:/temp/document.txt
    
    # Download file from remote  
    python file_copy.py remote:C:/temp/document.txt ./downloaded_document.txt
    
    # List remote files
    python file_copy.py --list remote:C:/temp/ --pattern "*.txt"
    
    # Get file info
    python file_copy.py --info remote:C:/temp/document.txt
    
    # Delete remote file
    python file_copy.py --delete remote:C:/temp/document.txt
"""

import argparse
import sys
import os
import time
from typing import Tuple, Optional
from remote_control_client import RemoteControlClient


class FileCopyTool:
    """File copy tool for remote operations."""
    
    def __init__(self, host: str = "localhost", port: int = 8417):
        """
        Initialize the file copy tool.
        
        Args:
            host: The hostname to connect to
            port: The port to connect to
        """
        self.client = RemoteControlClient(host, port)
        
    def parse_path(self, path: str) -> Tuple[bool, str]:
        """
        Parse a path to determine if it's remote or local.
        
        Args:
            path: Path string, either local or remote:path format
            
        Returns:
            Tuple of (is_remote, actual_path)
        """
        if path.startswith("remote:"):
            return True, path[7:]  # Remove "remote:" prefix
        else:
            return False, path
    
    def copy_file(self, source: str, destination: str, verbose: bool = True) -> bool:
        """
        Copy a file between local and remote locations.
        
        Args:
            source: Source path (local or remote:path)
            destination: Destination path (local or remote:path)
            verbose: Whether to print progress messages
            
        Returns:
            True if successful, False otherwise
        """
        src_is_remote, src_path = self.parse_path(source)
        dst_is_remote, dst_path = self.parse_path(destination)
        
        if src_is_remote == dst_is_remote:
            print("Error: One path must be local and one must be remote", file=sys.stderr)
            return False
            
        if verbose:
            print(f"Connecting to {self.client.host}:{self.client.port}...")
            
        # Test connection
        if not self.client.test_connection():
            print(f"Error: Cannot connect to {self.client.host}:{self.client.port}", file=sys.stderr)
            return False
            
        try:
            if src_is_remote:
                # Download: remote -> local
                if verbose:
                    print(f"Downloading {src_path} to {dst_path}...")
                    
                # Check if remote file exists
                if not self.client.file_exists(src_path):
                    print(f"Error: Remote file not found: {src_path}", file=sys.stderr)
                    return False
                    
                # Get file info for progress
                if verbose:
                    try:
                        file_info = self.client.get_file_info(src_path)
                        size_mb = file_info["size"] / (1024 * 1024)
                        print(f"File size: {size_mb:.2f} MB")
                    except:
                        pass
                        
                start_time = time.time()
                success = self.client.download_file(src_path, dst_path)
                elapsed = time.time() - start_time
                
                if success:
                    if verbose:
                        print(f"✓ Download completed in {elapsed:.2f} seconds")
                    return True
                else:
                    print("✗ Download failed", file=sys.stderr)
                    return False
                    
            else:
                # Upload: local -> remote
                if verbose:
                    print(f"Uploading {src_path} to {dst_path}...")
                    
                # Check if local file exists
                if not os.path.exists(src_path):
                    print(f"Error: Local file not found: {src_path}", file=sys.stderr)
                    return False
                    
                # Get file info for progress
                if verbose:
                    try:
                        size_mb = os.path.getsize(src_path) / (1024 * 1024)
                        print(f"File size: {size_mb:.2f} MB")
                    except:
                        pass
                        
                start_time = time.time()
                success = self.client.upload_file(src_path, dst_path)
                elapsed = time.time() - start_time
                
                if success:
                    if verbose:
                        print(f"✓ Upload completed in {elapsed:.2f} seconds")
                    return True
                else:
                    print("✗ Upload failed", file=sys.stderr)
                    return False
                    
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False
    
    def list_files(self, remote_path: str, pattern: str = "*") -> bool:
        """
        List files in a remote directory.
        
        Args:
            remote_path: Remote directory path
            pattern: File pattern to match
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.client.test_connection():
                print(f"Error: Cannot connect to {self.client.host}:{self.client.port}", file=sys.stderr)
                return False
                
            files = self.client.list_files(remote_path, pattern)
            
            if not files:
                print("No files found")
                return True
                
            print(f"Files in remote:{remote_path} (pattern: {pattern}):")
            for file_path in files:
                filename = os.path.basename(file_path)
                print(f"  {filename}")
                
            print(f"\nTotal: {len(files)} files")
            return True
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False
    
    def get_file_info(self, remote_path: str) -> bool:
        """
        Get information about a remote file.
        
        Args:
            remote_path: Remote file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.client.test_connection():
                print(f"Error: Cannot connect to {self.client.host}:{self.client.port}", file=sys.stderr)
                return False
                
            if not self.client.file_exists(remote_path):
                print(f"Error: Remote file not found: {remote_path}", file=sys.stderr)
                return False
                
            file_info = self.client.get_file_info(remote_path)
            
            size_mb = file_info["size"] / (1024 * 1024)
            
            print(f"File: remote:{remote_path}")
            print(f"Name: {file_info['name']}")
            print(f"Size: {file_info['size']} bytes ({size_mb:.2f} MB)")
            print(f"Created: {file_info['created']}")
            print(f"Modified: {file_info['modified']}")
            print(f"Hash: {file_info['hash']}")
            
            return True
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False
    
    def delete_file(self, remote_path: str) -> bool:
        """
        Delete a remote file.
        
        Args:
            remote_path: Remote file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.client.test_connection():
                print(f"Error: Cannot connect to {self.client.host}:{self.client.port}", file=sys.stderr)
                return False
                
            if not self.client.file_exists(remote_path):
                print(f"Error: Remote file not found: {remote_path}", file=sys.stderr)
                return False
                
            print(f"Deleting remote:{remote_path}...")
            success = self.client.delete_file(remote_path)
            
            if success:
                print("✓ File deleted successfully")
                return True
            else:
                print("✗ Delete failed", file=sys.stderr)
                return False
                
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Copy files between local and remote Windows machine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.txt remote:C:/temp/document.txt    # Upload
  %(prog)s remote:C:/temp/doc.txt ./downloaded.txt     # Download
  %(prog)s --list remote:C:/temp/                      # List files
  %(prog)s --info remote:C:/temp/document.txt          # File info
  %(prog)s --delete remote:C:/temp/document.txt        # Delete file
        """
    )
    
    parser.add_argument(
        "source",
        nargs="?",
        help="Source path (local or remote:path)"
    )
    
    parser.add_argument(
        "destination", 
        nargs="?",
        help="Destination path (local or remote:path)"
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
        "--list", "-l",
        metavar="PATH",
        help="List files in remote directory (remote:path)"
    )
    
    parser.add_argument(
        "--pattern",
        default="*",
        help="File pattern for listing (default: *)"
    )
    
    parser.add_argument(
        "--info", "-i",
        metavar="PATH",
        help="Get file information (remote:path)"
    )
    
    parser.add_argument(
        "--delete", "-d",
        metavar="PATH",
        help="Delete remote file (remote:path)"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    operations = sum([
        bool(args.source and args.destination),
        bool(args.list),
        bool(args.info),
        bool(args.delete)
    ])
    
    if operations != 1:
        parser.error("Specify exactly one operation: copy, --list, --info, or --delete")
    
    # Create file copy tool
    tool = FileCopyTool(args.host, args.port)
    
    try:
        if args.list:
            # Validate remote path
            if not args.list.startswith("remote:"):
                parser.error("List path must be in format remote:path")
            _, remote_path = tool.parse_path(args.list)
            success = tool.list_files(remote_path, args.pattern)
            
        elif args.info:
            # Validate remote path
            if not args.info.startswith("remote:"):
                parser.error("Info path must be in format remote:path")
            _, remote_path = tool.parse_path(args.info)
            success = tool.get_file_info(remote_path)
            
        elif args.delete:
            # Validate remote path
            if not args.delete.startswith("remote:"):
                parser.error("Delete path must be in format remote:path")
            _, remote_path = tool.parse_path(args.delete)
            success = tool.delete_file(remote_path)
            
        else:
            # Copy operation
            success = tool.copy_file(args.source, args.destination, verbose=not args.quiet)
            
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()