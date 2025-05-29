#!/usr/bin/env python3
"""
Debug script to test chat endpoint and trace metadata issues
"""

import requests
import json
import time
import threading
import sys
from app import app

def start_server():
    """Start the Flask server in debug mode"""
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)

def test_chat_metadata():
    """Test the chat endpoint and check for metadata"""
    time.sleep(3)  # Wait for server to start
    
    print("Testing chat endpoint for metadata...")
    
    payload = {
        "messages": [{"role": "user", "content": "test"}],
        "model_id": "google/gemini-2.0-flash-exp:free",
        "conversation_id": None
    }
    
    try:
        print(f"Sending request with model: {payload['model_id']}")
        
        response = requests.post(
            'http://localhost:5001/chat',
            json=payload,
            stream=True,
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("\n--- STREAMING RESPONSE ---")
            content_chunks = []
            metadata_received = False
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    print(f"RAW LINE: {repr(line_str)}")
                    
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        
                        if data_str.strip() == '[DONE]':
                            continue
                            
                        try:
                            parsed = json.loads(data_str)
                            print(f"PARSED DATA: {parsed}")
                            
                            if parsed.get('type') == 'content':
                                content_chunks.append(parsed.get('content', ''))
                                print(f"  -> Content chunk: {repr(parsed.get('content', ''))}")
                                
                            elif parsed.get('type') == 'metadata':
                                metadata_received = True
                                metadata = parsed.get('metadata', {})
                                print(f"  -> METADATA FOUND: {metadata}")
                                print(f"     Model used: {metadata.get('model_id_used')}")
                                print(f"     Prompt tokens: {metadata.get('prompt_tokens')}")
                                print(f"     Completion tokens: {metadata.get('completion_tokens')}")
                                
                            elif parsed.get('type') == 'done':
                                print(f"  -> Stream completed")
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"  -> JSON decode error: {e}")
                            print(f"     Raw data: {repr(data_str)}")
            
            print(f"\n--- SUMMARY ---")
            print(f"Full response: {''.join(content_chunks)}")
            print(f"Metadata received: {metadata_received}")
            
            if not metadata_received:
                print("❌ NO METADATA WAS RECEIVED - This is the bug!")
                return False
            else:
                print("✅ Metadata was received correctly")
                return True
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during request: {e}")
        return False

if __name__ == "__main__":
    print("Starting debug test for chat metadata...")
    
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Test the endpoint
    success = test_chat_metadata()
    
    if success:
        print("\n✅ Test passed - metadata is working")
        sys.exit(0)
    else:
        print("\n❌ Test failed - metadata issue confirmed")
        sys.exit(1)