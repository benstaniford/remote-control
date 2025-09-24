"""
Remote Control Client Module

This module provides an API to communicate with the Remote Control Windows tray application
via HTTP JSON protocol. Designed to work through SSH tunnels.
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
import socket
import base64
import os
import hashlib


class RemoteControlClient:
    """Client for communicating with Remote Control tray application."""
    
    def __init__(self, host: str = "localhost", port: int = 8417):
        """
        Initialize the Remote Control client.
        
        Args:
            host: The hostname to connect to (default: localhost)
            port: The port to connect to (default: 8417)
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}/"
    
    def _make_request(self, data: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
        """
        Make an HTTP POST request to the remote control server.
        
        Args:
            data: JSON data to send
            timeout: Request timeout in seconds
            
        Returns:
            JSON response as dictionary
            
        Raises:
            ConnectionError: If unable to connect to server
            ValueError: If server returns invalid JSON
            RuntimeError: If server returns an error response
        """
        try:
            json_data = json.dumps(data).encode('utf-8')
            
            req = urllib.request.Request(
                self.base_url,
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
                
        except urllib.error.URLError as e:
            if isinstance(e.reason, socket.error):
                raise ConnectionError(f"Unable to connect to {self.host}:{self.port}") from e
            raise ConnectionError(f"HTTP request failed: {e}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from server: {e}") from e
    
    def launch_browser(self, url: str) -> bool:
        """
        Launch the default browser with the specified URL.
        
        Args:
            url: The URL to open in the browser
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ConnectionError: If unable to connect to server
            ValueError: If URL is empty or server returns invalid JSON
            RuntimeError: If server returns an error
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")
            
        data = {
            "action": "launch_browser",
            "url": url.strip()
        }
        
        try:
            response = self._make_request(data)
            
            if response.get("success"):
                return True
            else:
                error_msg = response.get("error", "Unknown error")
                raise RuntimeError(f"Server error: {error_msg}")
                
        except (ConnectionError, ValueError) as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Request failed: {e}") from e
    
    def test_connection(self) -> bool:
        """
        Test if the server is reachable.
        
        Returns:
            True if server is reachable, False otherwise
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get connection status information.
        
        Returns:
            Dictionary with connection status
        """
        is_connected = self.test_connection()
        return {
            "host": self.host,
            "port": self.port,
            "connected": is_connected,
            "url": self.base_url
        }
    
    def start_shell(self) -> bool:
        """
        Start a shell process on the remote Windows machine.
        
        Returns:
            True if successful, False otherwise
            
        Raises:
            ConnectionError: If unable to connect to server
            RuntimeError: If server returns an error
        """
        data = {"action": "shell_start"}
        
        try:
            response = self._make_request(data)
            
            if response.get("success"):
                return True
            else:
                error_msg = response.get("error", "Unknown error")
                raise RuntimeError(f"Server error: {error_msg}")
                
        except (ConnectionError, ValueError) as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Request failed: {e}") from e
    
    def send_shell_input(self, command: str) -> bool:
        """
        Send input to the running shell.
        
        Args:
            command: The command to send to the shell
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ConnectionError: If unable to connect to server
            ValueError: If command is empty
            RuntimeError: If server returns an error
        """
        if not command or not command.strip():
            raise ValueError("Command cannot be empty")
            
        data = {
            "action": "shell_input",
            "input": command.strip()
        }
        
        try:
            response = self._make_request(data)
            
            if response.get("success"):
                return True
            else:
                error_msg = response.get("error", "Unknown error")
                raise RuntimeError(f"Server error: {error_msg}")
                
        except (ConnectionError, ValueError) as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Request failed: {e}") from e
    
    def get_shell_output(self) -> Dict[str, str]:
        """
        Get output from the running shell.
        
        Returns:
            Dictionary with 'output' and 'error' keys containing shell output
            
        Raises:
            ConnectionError: If unable to connect to server
            RuntimeError: If server returns an error
        """
        data = {"action": "shell_output"}
        
        try:
            response = self._make_request(data)
            
            if response.get("success"):
                return {
                    "output": response.get("output", ""),
                    "error": response.get("error", "")
                }
            else:
                error_msg = response.get("error", "Unknown error")
                raise RuntimeError(f"Server error: {error_msg}")
                
        except (ConnectionError, ValueError) as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Request failed: {e}") from e
    
    def stop_shell(self) -> bool:
        """
        Stop the running shell process.
        
        Returns:
            True if successful, False otherwise
            
        Raises:
            ConnectionError: If unable to connect to server
            RuntimeError: If server returns an error
        """
        data = {"action": "shell_stop"}
        
        try:
            response = self._make_request(data)
            
            if response.get("success"):
                return True
            else:
                error_msg = response.get("error", "Unknown error")
                raise RuntimeError(f"Server error: {error_msg}")
                
        except (ConnectionError, ValueError) as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Request failed: {e}") from e
    
    def get_shell_status(self) -> bool:
        """
        Check if shell is currently running.
        
        Returns:
            True if shell is running, False otherwise
            
        Raises:
            ConnectionError: If unable to connect to server
            RuntimeError: If server returns an error
        """
        data = {"action": "shell_status"}
        
        try:
            response = self._make_request(data)
            
            if response.get("success"):
                return response.get("running", False)
            else:
                error_msg = response.get("error", "Unknown error")
                raise RuntimeError(f"Server error: {error_msg}")
                
        except (ConnectionError, ValueError) as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Request failed: {e}") from e
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Upload a local file to the remote Windows machine.
        
        Args:
            local_path: Path to the local file to upload
            remote_path: Path where the file should be saved on the remote machine
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            FileNotFoundError: If local file doesn't exist
            ConnectionError: If unable to connect to server
            RuntimeError: If server returns an error
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")
            
        if not os.path.isfile(local_path):
            raise ValueError(f"Path is not a file: {local_path}")
            
        # Check file size (100MB limit)
        file_size = os.path.getsize(local_path)
        if file_size > 100 * 1024 * 1024:
            raise ValueError(f"File too large: {file_size} bytes. Maximum size is 100MB")
            
        try:
            # Read and encode file
            with open(local_path, 'rb') as f:
                file_content = base64.b64encode(f.read()).decode('utf-8')
                
            data = {
                "action": "file_upload",
                "path": remote_path,
                "content": file_content
            }
            
            response = self._make_request(data, timeout=120)  # Longer timeout for file uploads
            
            if response.get("success"):
                return True
            else:
                error_msg = response.get("error", "Unknown error")
                raise RuntimeError(f"Server error: {error_msg}")
                
        except (ConnectionError, ValueError) as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Upload failed: {e}") from e
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download a file from the remote Windows machine.
        
        Args:
            remote_path: Path to the file on the remote machine
            local_path: Path where the file should be saved locally
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ConnectionError: If unable to connect to server
            RuntimeError: If server returns an error
        """
        data = {
            "action": "file_download",
            "path": remote_path
        }
        
        try:
            response = self._make_request(data, timeout=120)  # Longer timeout for file downloads
            
            if response.get("success"):
                file_content = response.get("content", "")
                if not file_content:
                    raise RuntimeError("No file content received")
                    
                # Decode and save file
                file_bytes = base64.b64decode(file_content)
                
                # Ensure local directory exists
                local_dir = os.path.dirname(local_path)
                if local_dir and not os.path.exists(local_dir):
                    os.makedirs(local_dir)
                    
                with open(local_path, 'wb') as f:
                    f.write(file_bytes)
                    
                return True
            else:
                error_msg = response.get("error", "Unknown error")
                raise RuntimeError(f"Server error: {error_msg}")
                
        except (ConnectionError, ValueError) as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Download failed: {e}") from e
    
    def file_exists(self, remote_path: str) -> bool:
        """
        Check if a file exists on the remote machine.
        
        Args:
            remote_path: Path to check on the remote machine
            
        Returns:
            True if file exists, False otherwise
            
        Raises:
            ConnectionError: If unable to connect to server
            RuntimeError: If server returns an error
        """
        data = {
            "action": "file_exists",
            "path": remote_path
        }
        
        try:
            response = self._make_request(data)
            
            if response.get("success"):
                return response.get("exists", False)
            else:
                error_msg = response.get("error", "Unknown error")
                raise RuntimeError(f"Server error: {error_msg}")
                
        except (ConnectionError, ValueError) as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Request failed: {e}") from e
    
    def get_file_info(self, remote_path: str) -> Dict[str, Any]:
        """
        Get information about a file on the remote machine.
        
        Args:
            remote_path: Path to the file on the remote machine
            
        Returns:
            Dictionary with file information (name, size, dates, hash)
            
        Raises:
            ConnectionError: If unable to connect to server
            RuntimeError: If server returns an error
        """
        data = {
            "action": "file_info",
            "path": remote_path
        }
        
        try:
            response = self._make_request(data)
            
            if response.get("success"):
                return {
                    "name": response.get("name", ""),
                    "fullName": response.get("fullName", ""),
                    "size": response.get("size", 0),
                    "created": response.get("created", ""),
                    "modified": response.get("modified", ""),
                    "hash": response.get("hash", "")
                }
            else:
                error_msg = response.get("error", "Unknown error")
                raise RuntimeError(f"Server error: {error_msg}")
                
        except (ConnectionError, ValueError) as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Request failed: {e}") from e
    
    def delete_file(self, remote_path: str) -> bool:
        """
        Delete a file on the remote machine.
        
        Args:
            remote_path: Path to the file to delete on the remote machine
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ConnectionError: If unable to connect to server
            RuntimeError: If server returns an error
        """
        data = {
            "action": "file_delete",
            "path": remote_path
        }
        
        try:
            response = self._make_request(data)
            
            if response.get("success"):
                return True
            else:
                error_msg = response.get("error", "Unknown error")
                raise RuntimeError(f"Server error: {error_msg}")
                
        except (ConnectionError, ValueError) as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Request failed: {e}") from e
    
    def list_files(self, remote_path: str, pattern: str = "*") -> list:
        """
        List files in a directory on the remote machine.
        
        Args:
            remote_path: Path to the directory on the remote machine
            pattern: File pattern to match (default: "*")
            
        Returns:
            List of file paths
            
        Raises:
            ConnectionError: If unable to connect to server
            RuntimeError: If server returns an error
        """
        data = {
            "action": "file_list",
            "path": remote_path,
            "pattern": pattern
        }
        
        try:
            response = self._make_request(data)
            
            if response.get("success"):
                return response.get("files", [])
            else:
                error_msg = response.get("error", "Unknown error")
                raise RuntimeError(f"Server error: {error_msg}")
                
        except (ConnectionError, ValueError) as e:
            raise
        except Exception as e:
            raise RuntimeError(f"Request failed: {e}") from e