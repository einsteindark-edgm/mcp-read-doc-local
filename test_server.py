#!/usr/bin/env python
"""Test script for MCP server."""
import json
import subprocess
import sys

def test_mcp_server():
    # Initialize request
    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "0.1.0",
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        },
        "id": 1
    }
    
    # Start the server process
    process = subprocess.Popen(
        [sys.executable, "mcp_documents_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Send initialize request
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        if response:
            print("Initialize response:")
            print(json.dumps(json.loads(response), indent=2))
            
            # Send initialized notification
            initialized = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            process.stdin.write(json.dumps(initialized) + "\n")
            process.stdin.flush()
            
            # List resources
            list_resources = {
                "jsonrpc": "2.0",
                "method": "resources/list",
                "id": 2
            }
            process.stdin.write(json.dumps(list_resources) + "\n")
            process.stdin.flush()
            
            # Read response
            response = process.stdout.readline()
            if response:
                print("\nResources list:")
                print(json.dumps(json.loads(response), indent=2))
        else:
            print("No response from server")
            stderr = process.stderr.read()
            if stderr:
                print("Error output:", stderr)
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        process.terminate()

if __name__ == "__main__":
    test_mcp_server()