#!/usr/bin/env python3
"""
Test WebSocket connectivity to EchoNest server.
Run: python test_websocket.py wss://echone.st/socket/
"""

import sys
import time
import json
import websocket

def test_websocket(url):
    print(f"Testing WebSocket connection to: {url}")

    # We need to include a session cookie for authentication
    # This test is for verifying raw WebSocket connectivity

    ws = websocket.create_connection(url)
    print(f"Connected! Socket state: {ws.connected}")

    # Test 1: Send fetch_playlist (this is known to work)
    msg1 = '1["fetch_playlist"]'
    print(f"\nSending: {msg1}")
    ws.send(msg1)

    # Wait for response
    print("Waiting for response...")
    try:
        response = ws.recv()
        print(f"Received: {response[:200]}..." if len(response) > 200 else f"Received: {response}")
    except Exception as e:
        print(f"Error receiving: {e}")

    time.sleep(1)

    # Test 2: Send heartbeat
    msg2 = '0'
    print(f"\nSending heartbeat: {msg2}")
    ws.send(msg2)
    print("Heartbeat sent (no response expected)")

    time.sleep(1)

    # Test 3: Send airhorn (this is known to NOT work)
    msg3 = '1["airhorn","reemix"]'
    print(f"\nSending airhorn: {msg3}")
    ws.send(msg3)

    # Wait to see if we get any response or error
    print("Waiting for any response or airhorn event...")
    ws.settimeout(5)
    try:
        response = ws.recv()
        print(f"Received: {response[:200]}..." if len(response) > 200 else f"Received: {response}")
    except websocket.WebSocketTimeoutException:
        print("No response within 5 seconds (might be normal for airhorn)")
    except Exception as e:
        print(f"Error: {e}")

    # Test 4: Send another fetch_playlist to see if connection is still alive
    msg4 = '1["fetch_playlist"]'
    print(f"\nSending another fetch_playlist to test connection: {msg4}")
    ws.send(msg4)

    ws.settimeout(5)
    try:
        response = ws.recv()
        print(f"Received: {response[:100]}..." if len(response) > 100 else f"Received: {response}")
        print("Connection is still alive after airhorn!")
    except websocket.WebSocketTimeoutException:
        print("No response - connection may have died")
    except Exception as e:
        print(f"Error: {e}")

    ws.close()
    print("\nTest complete!")

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else 'wss://echone.st/socket/'
    test_websocket(url)
