#!/usr/bin/env python3
"""
Simple test to verify the metadata issue and fix
"""

import requests
import json
import threading
import time
from app import app

def test_chat():
    """Test chat endpoint with logging"""
    print("Testing chat endpoint...")
    
    payload = {
        "messages": [{"role": "user", "content": "test"}],
        "model_id": "google/gemini-2.0-flash-exp:free"
    }
    
    try:
        response = requests.post(
            'http://localhost:5002/chat',
            json=payload,
            stream=True,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        metadata_found = False
        content_chunks = []
        
        for line in response.iter_lines():
            if line and line.startswith(b'data: '):
                data_str = line[6:].decode('utf-8')
                if data_str.strip() == '[DONE]':
                    continue
                    
                try:
                    parsed = json.loads(data_str)
                    
                    if parsed.get('type') == 'content':
                        content_chunks.append(parsed.get('content', ''))
                        
                    elif parsed.get('type') == 'metadata':
                        metadata_found = True
                        metadata = parsed.get('metadata', {})
                        print(f"✅ METADATA: {metadata}")
                        break
                        
                except json.JSONDecodeError:
                    continue
        
        full_content = ''.join(content_chunks)
        print(f"Content received: {len(full_content)} chars")
        print(f"Metadata received: {metadata_found}")
        
        return metadata_found
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_server():
    app.run(host='0.0.0.0', port=5002, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Start server
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(3)
    
    # Test
    success = test_chat()
    print(f"Result: {'PASS' if success else 'FAIL'}")