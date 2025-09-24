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
        # Access the tool list function directly
        tools = await server.server._tool_list_handler()
        print(f"✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
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
    
    server = WinRemoteMCPServer()
    
    # Check that all tools have required fields
    async def check_schemas():
        tools = await server.server._tool_list_handler()
        schema_errors = []
        
        for tool in tools:
            # Check required fields
            if not tool.name:
                schema_errors.append(f"Tool missing name: {tool}")
            if not tool.description:
                schema_errors.append(f"Tool {tool.name} missing description")
            if not hasattr(tool, 'inputSchema'):
                schema_errors.append(f"Tool {tool.name} missing inputSchema")
            
            # Check schema structure
            if hasattr(tool, 'inputSchema'):
                schema = tool.inputSchema
                if not isinstance(schema, dict):
                    schema_errors.append(f"Tool {tool.name} inputSchema is not a dict")
                elif schema.get("type") != "object":
                    schema_errors.append(f"Tool {tool.name} inputSchema type is not 'object'")
        
        return schema_errors
    
    try:
        errors = asyncio.run(check_schemas())
        if errors:
            print("✗ Schema validation errors found:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✓ All tool schemas are valid")
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