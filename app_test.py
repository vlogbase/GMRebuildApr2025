"""
Test script to check the conversation summary feature in our Flask application.
"""
import os
import logging
import time
from flask import Flask, request, jsonify
from flask_login import LoginManager, UserMixin, AnonymousUserMixin, login_user

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Simple test app
app = Flask(__name__)
app.secret_key = "test_secret_key"

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)

# Create a simple user class for testing
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Anonymous user
class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.id = None
    
    def is_authenticated(self):
        return False

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
def index():
    return """
    <html>
    <head>
        <title>Conversation Summary Test</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #333; }
            .button { background: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; }
            #output { margin-top: 20px; border: 1px solid #ddd; padding: 15px; min-height: 200px; }
            pre { background: #f5f5f5; padding: 10px; overflow: auto; }
        </style>
    </head>
    <body>
        <h1>Conversation Summary Test</h1>
        <p>This page tests the conversation summary generation feature.</p>
        
        <button class="button" id="testBtn">Test Summary Generation</button>
        <div id="output"><em>Results will appear here...</em></div>
        
        <script>
            document.getElementById('testBtn').addEventListener('click', async () => {
                const output = document.getElementById('output');
                output.innerHTML = '<p>Running test...</p>';
                
                try {
                    // Create a new conversation
                    const createConvResponse = await fetch('/api/test/create_conversation', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    const convData = await createConvResponse.json();
                    output.innerHTML = `<p>Created conversation ID: ${convData.conversation_id}</p>`;
                    
                    // Add user message
                    const userMsgResponse = await fetch('/api/test/add_message', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            conversation_id: convData.conversation_id,
                            role: 'user',
                            content: 'Tell me about the best practices for financial compliance in affiliate marketing.'
                        })
                    });
                    const userMsgData = await userMsgResponse.json();
                    output.innerHTML += `<p>Added user message ID: ${userMsgData.message_id}</p>`;
                    
                    // Add assistant message
                    const assistantMsgResponse = await fetch('/api/test/add_message', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            conversation_id: convData.conversation_id,
                            role: 'assistant',
                            content: 'Financial compliance in affiliate marketing involves several best practices. First, always disclose affiliate relationships clearly to your audience. This is both legally required and builds trust. Second, ensure all marketing claims are accurate and can be substantiated. Third, follow data protection regulations when collecting user information. Fourth, understand and adhere to specific industry regulations that might apply to the products you're promoting, such as financial services or healthcare products. Lastly, regularly audit your marketing materials and disclosures to stay compliant with evolving regulations.'
                        })
                    });
                    const assistantMsgData = await assistantMsgResponse.json();
                    output.innerHTML += `<p>Added assistant message ID: ${assistantMsgData.message_id}</p>`;
                    
                    // Trigger summary generation
                    const summaryResponse = await fetch('/api/test/trigger_summary', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            conversation_id: convData.conversation_id
                        })
                    });
                    const summaryData = await summaryResponse.json();
                    output.innerHTML += `<p>Triggered summary generation: ${summaryData.success ? 'Success' : 'Failed'}</p>`;
                    
                    // Wait for summary to be generated
                    output.innerHTML += `<p>Waiting for summary generation (10 seconds)...</p>`;
                    await new Promise(resolve => setTimeout(resolve, 10000));
                    
                    // Check conversation title
                    const checkResponse = await fetch(`/api/test/get_conversation?id=${convData.conversation_id}`);
                    const checkData = await checkResponse.json();
                    
                    output.innerHTML += `
                        <h3>Test Results:</h3>
                        <pre>
Conversation ID: ${checkData.conversation.id}
Title: ${checkData.conversation.title}
Created At: ${checkData.conversation.created_at}
Updated At: ${checkData.conversation.updated_at}
                        </pre>
                        <p><strong>Summary Status:</strong> ${checkData.conversation.title !== 'New Conversation' ? 'Summary Generated ✅' : 'Still "New Conversation" ❌'}</p>
                    `;
                    
                } catch (error) {
                    output.innerHTML = `<p>Error: ${error.message}</p>`;
                    console.error(error);
                }
            });
        </script>
    </body>
    </html>
    """

# Test API endpoints
@app.route('/api/test/create_conversation', methods=['POST'])
def create_conversation():
    from app import db
    from models import Conversation, User as AppUser
    
    try:
        # Create a test user if needed
        test_user = None
        test_user = AppUser.query.filter_by(username='test_user').first()
        if not test_user:
            test_user = AppUser(username='test_user', email='test@example.com')
            db.session.add(test_user)
            db.session.commit()
        
        # Create a conversation
        conversation = Conversation(
            user_id=test_user.id,
            title='New Conversation',
            model_id='google/gemini-flash:free'
        )
        db.session.add(conversation)
        db.session.commit()
        return jsonify({'success': True, 'conversation_id': conversation.id})
    except Exception as e:
        logger.exception("Error creating conversation")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test/add_message', methods=['POST'])
def add_message():
    from app import db
    from models import Message
    
    try:
        data = request.json
        conv_id = data.get('conversation_id')
        role = data.get('role', 'user')
        content = data.get('content', '')
        
        message = Message(
            conversation_id=conv_id,
            role=role,
            content=content
        )
        db.session.add(message)
        db.session.commit()
        return jsonify({'success': True, 'message_id': message.id})
    except Exception as e:
        logger.exception("Error adding message")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test/trigger_summary', methods=['POST'])
def trigger_summary():
    from app import generate_summary
    
    try:
        data = request.json
        conv_id = data.get('conversation_id')
        
        # Call the generate_summary function
        generate_summary(conv_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.exception("Error triggering summary")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test/get_conversation')
def get_conversation():
    from app import db
    from models import Conversation
    
    try:
        conv_id = request.args.get('id')
        conversation = db.session.get(Conversation, conv_id)
        
        if not conversation:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404
            
        return jsonify({
            'success': True, 
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'created_at': conversation.created_at.isoformat() if conversation.created_at else None,
                'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None
            }
        })
    except Exception as e:
        logger.exception("Error getting conversation")
        return jsonify({'success': False, 'error': str(e)}), 500

def main():
    with app.app_context():
        # Import necessary modules
        from app import db
        
        # Ensure the database is initialized
        db.create_all()
        
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)

if __name__ == '__main__':
    main()