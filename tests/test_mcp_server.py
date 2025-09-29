#!/usr/bin/env python3
"""
Test script for the WinRemoteMcpServer MCP server.
This script tests the MCP server functionality by simulating tool calls.
"""

import json
import sys
import asyncio
import os
from typing import Any, Dict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import the MCP server
try:
    from WinRemoteMcpServer import WinRemoteMCPServer
    from mcp.types import TextContent
except ImportError as e:
    print(f"Error importing MCP components: {e}")
    print("Please install the MCP package: pip install mcp")
    sys.exit(1)


async def test_mcp_server():
    """Test the MCP server functionality."""
    print("Testing Windows Remote Control MCP Server")
    print("=" * 50)
    
    # Create server instance
    server = WinRemoteMCPServer()
    print("✓ MCP Server created successfully")
    
    # Test tool listing
    print("\n1. Testing tool listing...")
    try:
        # Check the newer MCP server API
        server_obj = server.server
        
        # Check if handlers are registered in the request_handlers (newer MCP API uses classes)
        from mcp.types import ListToolsRequest, CallToolRequest
        
        has_list_tools = ListToolsRequest in server_obj.request_handlers
        has_call_tool = CallToolRequest in server_obj.request_handlers
        
        if has_list_tools and has_call_tool:
            print("✓ Tool handlers registered successfully")
            print("✓ Server appears to have tools configured")
            print(f"✓ Request handlers: {list(server_obj.request_handlers.keys())}")
            
            # Check tool cache if available
            if hasattr(server_obj, '_tool_cache') and server_obj._tool_cache:
                print(f"✓ Tool cache contains {len(server_obj._tool_cache)} tools")
        else:
            print(f"✗ Tool handlers not properly registered")
            print(f"  has_list_tools (ListToolsRequest): {has_list_tools}")
            print(f"  has_call_tool (CallToolRequest): {has_call_tool}")
            print(f"  Available handlers: {list(server_obj.request_handlers.keys())}")
            return False
            
    except Exception as e:
        print(f"✗ Tool listing failed: {e}")
        return False
    
    # Test connection configuration
    print("\n2. Testing connection configuration...")
    try:
        # Simulate configure_connection tool call
        result = await server._configure_connection({
            "host": "localhost",
            "port": 8417
        })
        response_text = result[0].text
        response_data = json.loads(response_text)
        print(f"✓ Connection configured: {response_data['host']}:{response_data['port']}")
    except Exception as e:
        print(f"✗ Connection configuration failed: {e}")
    
    # Test connection test
    print("\n3. Testing connection test...")
    try:
        result = await server._test_connection({})
        response_text = result[0].text
        response_data = json.loads(response_text)
        
        if response_data["connected"]:
            print("✓ Connection test successful - Remote Control app is running")
            
            # If connected, test more functionality
            await test_connected_functionality(server)
        else:
            print(f"! Connection test failed: {response_data.get('message', 'Unknown error')}")
            print("  This is expected if the Windows Remote Control app is not running")
            
    except Exception as e:
        print(f"✗ Connection test failed with error: {e}")
    
    print("\nMCP Server test completed!")
    return True


async def test_connected_functionality(server):
    """Test functionality that requires a connection."""
    print("\n4. Testing connected functionality...")
    
    # Test status
    try:
        result = await server._get_status({})
        response_text = result[0].text
        response_data = json.loads(response_text)
        print(f"✓ Status retrieved - Shell running: {response_data.get('shell_running', False)}")
    except Exception as e:
        print(f"✗ Status test failed: {e}")
    
    # Test shell status
    try:
        result = await server._shell_status({})
        response_text = result[0].text
        response_data = json.loads(response_text)
        print(f"✓ Shell status: {response_data.get('status', 'unknown')}")
    except Exception as e:
        print(f"✗ Shell status test failed: {e}")
    
    # Test file existence check (safe operation)
    try:
        result = await server._file_exists({"path": "C:/Windows/System32"})
        response_text = result[0].text
        response_data = json.loads(response_text)
        print(f"✓ File exists check - C:/Windows/System32 exists: {response_data.get('exists', False)}")
    except Exception as e:
        print(f"✗ File exists test failed: {e}")


def test_tool_schemas():
    """Test that tool schemas are valid."""
    print("\n5. Testing tool schemas...")
    
    try:
        server = WinRemoteMCPServer()
        
        # Check the newer MCP server API
        server_obj = server.server
        
        # Check that handlers are registered
        from mcp.types import ListToolsRequest, CallToolRequest
        
        has_list_tools = ListToolsRequest in server_obj.request_handlers
        has_call_tool = CallToolRequest in server_obj.request_handlers
        
        if has_list_tools and has_call_tool:
            print("✓ Tool schemas appear to be valid (handlers registered successfully)")
            print("✓ Server structure is correct")
        else:
            print("✗ Tool handlers not properly registered")
            print(f"  Available handlers: {list(server_obj.request_handlers.keys())}")
            
    except Exception as e:
        print(f"✗ Schema validation failed: {e}")


def main():
    """Main test function."""
    try:
        # Test schemas
        test_tool_schemas()
        
        # Test server functionality
        success = asyncio.run(test_mcp_server())
        
        print("\n" + "=" * 50)
        if success:
            print("✓ MCP Server tests completed successfully")
            print("\nTo use with Claude Desktop:")
            print("1. Install MCP: pip install mcp")
            print("2. Add to Claude Desktop MCP config:")
            print("   {")
            print('     "mcpServers": {')
            print('       "windows-remote": {')
            print('         "command": "python",')
            print(f'         "args": ["{__file__.replace("test_mcp_server.py", "WinRemoteMcpServer.py")}"]')
            print('       }')
            print('     }')
            print("   }")
            sys.exit(0)
        else:
            print("✗ MCP Server tests failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()