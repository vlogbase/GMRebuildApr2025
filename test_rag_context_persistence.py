"""
Test RAG Context Persistence

Simple application to test OpenRouter annotations and context persistence.
This script focuses on testing scenarios with both direct API calls and UI interactions.
"""

import os
import sys
import json
import logging
import argparse
import requests
import time
from datetime import datetime
from sqlalchemy import create_engine, text
from flask import Flask, request, jsonify, render_template, Response
import webbrowser

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rag_context_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app for the test interface
app = Flask(__name__, template_folder='test_templates')

# Test configuration
APP_BASE_URL = "http://localhost:5000"  # URL of the main application
TEST_FILES_DIR = "test_files"           # Directory for test files
SESSION_FILE = "test_session.json"      # File to store session data

def setup_test_files():
    """Set up test files for the test application."""
    os.makedirs(TEST_FILES_DIR, exist_ok=True)
    os.makedirs("test_templates", exist_ok=True)
    
    # Create a test HTML template
    with open("test_templates/index.html", "w") as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>RAG Context Persistence Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .section { margin-bottom: 20px; padding: 20px; border: 1px solid #ccc; border-radius: 5px; }
        .response { white-space: pre-wrap; background-color: #f5f5f5; padding: 10px; border-radius: 5px; }
        .annotation { background-color: #e6f7ff; padding: 10px; border-radius: 5px; margin-top: 10px; }
        .controls { margin-bottom: 10px; }
        button, input[type="submit"] { padding: 8px 16px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover, input[type="submit"]:hover { background-color: #45a049; }
        textarea { width: 100%; padding: 10px; margin-bottom: 10px; }
        .message { margin-bottom: 10px; padding: 10px; border-radius: 5px; }
        .user { background-color: #e6f7ff; }
        .assistant { background-color: #f5f5f5; }
        .flex-row { display: flex; gap: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>RAG Context Persistence Test</h1>
        
        <div class="section">
            <h2>Test Configuration</h2>
            <div class="controls">
                <form id="configForm">
                    <label for="modelId">Model ID:</label>
                    <input type="text" id="modelId" name="modelId" value="openai/gpt-4o" style="width: 300px;">
                    <button type="button" id="createConversation">Create New Conversation</button>
                </form>
            </div>
        </div>
        
        <div class="section">
            <h2>Document Upload</h2>
            <div class="controls">
                <form id="uploadForm" enctype="multipart/form-data">
                    <input type="file" id="file" name="file">
                    <input type="submit" value="Upload Document for RAG">
                </form>
            </div>
            <div id="uploadResponse" class="response"></div>
            <div id="activeDocuments" class="response">
                <h3>Active RAG Documents</h3>
                <ul id="documentList"></ul>
            </div>
        </div>
        
        <div class="section">
            <h2>Chat Messages</h2>
            <div class="controls">
                <form id="chatForm">
                    <textarea id="message" name="message" rows="4" placeholder="Enter your message here..."></textarea>
                    <div class="flex-row">
                        <input type="submit" value="Send Message">
                        <button type="button" id="sendWithoutDocs">Send Without Documents</button>
                    </div>
                </form>
            </div>
            <div id="chatHistory"></div>
            <div id="chatResponse" class="response"></div>
        </div>
        
        <div class="section">
            <h2>Message Inspection</h2>
            <div class="controls">
                <button type="button" id="inspectLastMessage">Inspect Last Message Annotations</button>
                <button type="button" id="inspectConversation">Inspect Conversation Annotations</button>
            </div>
            <div id="inspectionResponse" class="response"></div>
        </div>
        
        <div class="section">
            <h2>Test Results Log</h2>
            <div id="testLog" class="response"></div>
        </div>
    </div>
    
    <script>
        // Store session data
        let sessionData = {
            conversationId: null,
            documentUrls: [],
            messages: [],
            lastMessageId: null
        };
        
        // Load session data if available
        fetch('/session')
            .then(response => response.json())
            .then(data => {
                sessionData = data;
                updateUI();
            })
            .catch(error => console.error('Error loading session:', error));
        
        // Create new conversation
        document.getElementById('createConversation').addEventListener('click', () => {
            fetch('/api/create_conversation')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        sessionData.conversationId = data.conversation_id;
                        sessionData.messages = [];
                        sessionData.documentUrls = [];
                        logTest(`Created new conversation with ID: ${data.conversation_id}`);
                        updateUI();
                    } else {
                        logTest(`Error creating conversation: ${data.error}`);
                    }
                })
                .catch(error => logTest(`Error: ${error}`));
        });
        
        // Upload document
        document.getElementById('uploadForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            fetch('/api/upload_document', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('uploadResponse').textContent = JSON.stringify(data, null, 2);
                if (data.success) {
                    sessionData.documentUrls = data.document_urls;
                    logTest(`Uploaded document(s). Total active documents: ${sessionData.documentUrls.length}`);
                    updateUI();
                } else {
                    logTest(`Error uploading document: ${data.error}`);
                }
            })
            .catch(error => logTest(`Error: ${error}`));
        });
        
        // Send chat message
        document.getElementById('chatForm').addEventListener('submit', (e) => {
            e.preventDefault();
            sendMessage(true);
        });
        
        // Send without documents
        document.getElementById('sendWithoutDocs').addEventListener('click', () => {
            sendMessage(false);
        });
        
        function sendMessage(includeDocuments) {
            const messageText = document.getElementById('message').value;
            const modelId = document.getElementById('modelId').value;
            
            if (!sessionData.conversationId) {
                logTest('Please create a conversation first');
                return;
            }
            
            const payload = {
                message: messageText,
                conversation_id: sessionData.conversationId,
                model_id: modelId
            };
            
            if (includeDocuments && sessionData.documentUrls.length > 0) {
                payload.document_urls = sessionData.documentUrls;
                logTest(`Sending message with ${sessionData.documentUrls.length} documents`);
            } else {
                logTest('Sending message without documents');
            }
            
            // Add user message to history
            const userMessage = {
                role: 'user',
                content: messageText
            };
            sessionData.messages.push(userMessage);
            updateChatHistory();
            
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('chatResponse').textContent = JSON.stringify(data, null, 2);
                if (data.success) {
                    // Add assistant message to history
                    const assistantMessage = {
                        role: 'assistant',
                        content: data.content,
                        has_annotations: data.has_annotations
                    };
                    sessionData.messages.push(assistantMessage);
                    sessionData.lastMessageId = data.message_id;
                    
                    logTest(`Received response. Message ID: ${data.message_id}, Has annotations: ${data.has_annotations}`);
                    updateUI();
                    
                    // Save session
                    saveSession();
                } else {
                    logTest(`Error sending message: ${data.error}`);
                }
            })
            .catch(error => logTest(`Error: ${error}`));
            
            // Clear message input
            document.getElementById('message').value = '';
        }
        
        // Inspect last message
        document.getElementById('inspectLastMessage').addEventListener('click', () => {
            if (!sessionData.lastMessageId) {
                logTest('No messages to inspect');
                return;
            }
            
            fetch(`/api/inspect_message/${sessionData.lastMessageId}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('inspectionResponse').textContent = JSON.stringify(data, null, 2);
                    logTest(`Inspected message ${sessionData.lastMessageId}`);
                })
                .catch(error => logTest(`Error: ${error}`));
        });
        
        // Inspect conversation
        document.getElementById('inspectConversation').addEventListener('click', () => {
            if (!sessionData.conversationId) {
                logTest('No conversation to inspect');
                return;
            }
            
            fetch(`/api/inspect_conversation/${sessionData.conversationId}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('inspectionResponse').textContent = JSON.stringify(data, null, 2);
                    logTest(`Inspected conversation ${sessionData.conversationId}`);
                })
                .catch(error => logTest(`Error: ${error}`));
        });
        
        // Update UI based on session data
        function updateUI() {
            // Update document list
            const documentList = document.getElementById('documentList');
            documentList.innerHTML = '';
            sessionData.documentUrls.forEach(url => {
                const li = document.createElement('li');
                li.textContent = url.substring(url.lastIndexOf('/') + 1);
                documentList.appendChild(li);
            });
            
            // Update chat history
            updateChatHistory();
        }
        
        function updateChatHistory() {
            const chatHistory = document.getElementById('chatHistory');
            chatHistory.innerHTML = '';
            
            sessionData.messages.forEach(message => {
                const div = document.createElement('div');
                div.className = `message ${message.role}`;
                div.textContent = `${message.role}: ${message.content}`;
                
                if (message.has_annotations) {
                    const annotationBadge = document.createElement('span');
                    annotationBadge.className = 'annotation';
                    annotationBadge.textContent = 'Has annotations';
                    div.appendChild(document.createElement('br'));
                    div.appendChild(annotationBadge);
                }
                
                chatHistory.appendChild(div);
            });
        }
        
        // Log test results
        function logTest(message) {
            const testLog = document.getElementById('testLog');
            const timestamp = new Date().toISOString();
            const logEntry = document.createElement('div');
            logEntry.textContent = `${timestamp} - ${message}`;
            testLog.insertBefore(logEntry, testLog.firstChild);
            
            // Also log to console
            console.log(`TEST: ${message}`);
        }
        
        // Save session
        function saveSession() {
            fetch('/session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(sessionData)
            })
            .catch(error => console.error('Error saving session:', error));
        }
    </script>
</body>
</html>
        """)
    
    logger.info("Created test files")
    return True

def get_database_connection():
    """Get a database connection."""
    try:
        # Get database URL from environment
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL environment variable not set")
            return None
            
        # Create engine
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        logger.error(f"Error creating database connection: {e}")
        return None

# Session data
session_data = {
    "conversationId": None,
    "documentUrls": [],
    "messages": [],
    "lastMessageId": None
}

# Routes
@app.route('/')
def index():
    """Render the test interface."""
    return render_template('index.html')

@app.route('/session', methods=['GET', 'POST'])
def session():
    """Get or update session data."""
    global session_data
    
    if request.method == 'POST':
        session_data = request.get_json()
        return jsonify({"success": True})
    else:
        return jsonify(session_data)

@app.route('/api/create_conversation', methods=['GET'])
def create_conversation():
    """Create a new conversation."""
    try:
        response = requests.post(f"{APP_BASE_URL}/conversations")
        if response.status_code == 200:
            data = response.json()
            conversation_id = data.get("id")
            return jsonify({
                "success": True,
                "conversation_id": conversation_id
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to create conversation: {response.status_code} {response.text}"
            })
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/upload_document', methods=['POST'])
def upload_document():
    """Upload a document for RAG."""
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({
                "success": False,
                "error": "No file provided"
            })
        
        # Save the file to a temporary location
        temp_path = os.path.join(TEST_FILES_DIR, file.filename)
        file.save(temp_path)
        
        # Upload to the main application
        with open(temp_path, 'rb') as f:
            files = {"file": (file.filename, f)}
            response = requests.post(f"{APP_BASE_URL}/attach_file_for_rag", files=files)
            
        if response.status_code == 200:
            result = response.json()
            document_urls = [item["url"] for item in result.get("results", []) 
                            if item.get("status") == "success"]
            
            return jsonify({
                "success": True,
                "document_urls": document_urls,
                "raw_response": result
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to upload document: {response.status_code} {response.text}"
            })
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Send a chat message."""
    try:
        data = request.get_json()
        
        # Forward to the main application
        response = requests.post(f"{APP_BASE_URL}/chat", json=data)
        
        if response.status_code == 200:
            # For SSE responses, we need to parse the chunks
            result = []
            full_content = ""
            message_id = None
            has_annotations = False
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        try:
                            chunk_data = json.loads(data_str)
                            result.append(chunk_data)
                            
                            # Extract content
                            if chunk_data.get('type') == 'content':
                                full_content += chunk_data.get('content', '')
                            
                            # Extract message ID from metadata
                            if chunk_data.get('type') == 'metadata':
                                message_id = chunk_data.get('id')
                        except json.JSONDecodeError:
                            pass
            
            # Check if the message has annotations
            if message_id:
                engine = get_database_connection()
                if engine:
                    with engine.connect() as conn:
                        query = text("""
                            SELECT annotations FROM message 
                            WHERE id = :message_id
                        """)
                            
                        result = conn.execute(query, {"message_id": message_id})
                        row = result.fetchone()
                        
                        if row and row[0]:
                            has_annotations = True
            
            return jsonify({
                "success": True,
                "message_id": message_id,
                "content": full_content,
                "has_annotations": has_annotations,
                "raw_chunks": result[:5]  # Limit to first 5 chunks for brevity
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to send chat message: {response.status_code} {response.text}"
            })
    except Exception as e:
        logger.error(f"Error sending chat message: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/inspect_message/<int:message_id>', methods=['GET'])
def inspect_message(message_id):
    """Inspect a message for annotations."""
    try:
        engine = get_database_connection()
        if not engine:
            return jsonify({
                "success": False,
                "error": "Failed to connect to database"
            })
        
        with engine.connect() as conn:
            query = text("""
                SELECT id, role, content, annotations, created_at
                FROM message 
                WHERE id = :message_id
            """)
                
            result = conn.execute(query, {"message_id": message_id})
            row = result.fetchone()
            
            if row:
                message_id, role, content, annotations, created_at = row
                return jsonify({
                    "success": True,
                    "message": {
                        "id": message_id,
                        "role": role,
                        "content_preview": content[:100] + "..." if len(content) > 100 else content,
                        "has_annotations": annotations is not None,
                        "annotations": annotations,
                        "created_at": created_at.isoformat() if created_at else None
                    }
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"Message with ID {message_id} not found"
                })
    except Exception as e:
        logger.error(f"Error inspecting message: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/inspect_conversation/<int:conversation_id>', methods=['GET'])
def inspect_conversation(conversation_id):
    """Inspect all messages in a conversation."""
    try:
        engine = get_database_connection()
        if not engine:
            return jsonify({
                "success": False,
                "error": "Failed to connect to database"
            })
        
        with engine.connect() as conn:
            query = text("""
                SELECT id, role, content, annotations, created_at
                FROM message 
                WHERE conversation_id = :conversation_id
                ORDER BY created_at ASC
            """)
                
            result = conn.execute(query, {"conversation_id": conversation_id})
            messages = []
            
            for row in result:
                message_id, role, content, annotations, created_at = row
                messages.append({
                    "id": message_id,
                    "role": role,
                    "content_preview": content[:100] + "..." if len(content) > 100 else content,
                    "has_annotations": annotations is not None,
                    "annotations_size": len(json.dumps(annotations)) if annotations else 0,
                    "created_at": created_at.isoformat() if created_at else None
                })
            
            return jsonify({
                "success": True,
                "conversation_id": conversation_id,
                "message_count": len(messages),
                "messages": messages
            })
    except Exception as e:
        logger.error(f"Error inspecting conversation: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

def main():
    parser = argparse.ArgumentParser(description='Test RAG Context Persistence')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the test application on')
    
    args = parser.parse_args()
    
    # Set up test files
    setup_test_files()
    
    # Start the test application
    logger.info(f"Starting RAG Context Persistence Test Application on port {args.port}")
    logger.info(f"Test interface: http://localhost:{args.port}/")
    
    # Open the browser
    webbrowser.open(f"http://localhost:{args.port}/")
    
    app.run(host='localhost', port=args.port, debug=True)

if __name__ == "__main__":
    main()