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