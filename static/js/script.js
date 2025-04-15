document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const modelButtons = document.querySelectorAll('.model-btn');
    const newChatButton = document.getElementById('new-chat-btn');
    const clearConversationsButton = document.getElementById('clear-conversations-btn');
    const exampleQuestionButton = document.getElementById('example-question-btn');
    const conversationsList = document.getElementById('conversations-list');
    
    // Current selected model
    let currentModel = 'gemini-1.5-pro';
    
    // Current conversation ID
    let currentConversationId = null;
    
    // Conversation history
    let messageHistory = [];
    
    // Fetch conversations on load
    fetchConversations();
    
    // Event Listeners
    messageInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
        
        // Auto-resize textarea
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    sendButton.addEventListener('click', sendMessage);
    
    // Model selection buttons
    modelButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            modelButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Update current model
            currentModel = this.getAttribute('data-model');
            console.log('Selected model:', currentModel);
        });
    });
    
    // New chat button
    newChatButton.addEventListener('click', function() {
        // Clear chat messages except the welcome message
        clearChat();
    });
    
    // Clear conversations button
    clearConversationsButton.addEventListener('click', function() {
        // Clear chat and reset conversation items in sidebar
        clearChat();
        // In a real app, you would also clear the storage/backend
    });
    
    // Example question button
    exampleQuestionButton.addEventListener('click', function() {
        const exampleQuestions = [
            "What are the major differences between renewable and fossil fuel energy sources?",
            "Can you explain how artificial intelligence works in simple terms?",
            "What are some effective strategies for reducing carbon emissions?",
            "How does quantum computing differ from classical computing?",
            "What are the potential implications of gene editing technologies?"
        ];
        
        // Select a random example question
        const randomQuestion = exampleQuestions[Math.floor(Math.random() * exampleQuestions.length)];
        
        // Set the input value and trigger sending
        messageInput.value = randomQuestion;
        sendMessage();
    });
    
    // Function to send message
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Clear input
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        // First time? Clear welcome message
        if (document.querySelector('.welcome-container')) {
            chatMessages.innerHTML = '';
        }
        
        // Add user message to chat
        addMessage(message, 'user');
        
        // Show typing indicator
        const typingIndicator = addTypingIndicator();
        
        // Send message to backend
        sendMessageToBackend(message, currentModel, typingIndicator);
    }
    
    // Function to add message to chat
    function addMessage(content, sender, isTyping = false) {
        const messageElement = document.createElement('div');
        messageElement.className = `message message-${sender}`;
        
        const avatar = document.createElement('div');
        avatar.className = `message-avatar ${sender}`;
        
        if (sender === 'user') {
            avatar.textContent = 'U';
        } else {
            avatar.textContent = 'A';
        }
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (isTyping) {
            messageContent.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        } else {
            // Process markdown and code blocks if needed
            messageContent.innerHTML = formatMessage(content);
        }
        
        messageElement.appendChild(avatar);
        messageElement.appendChild(messageContent);
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageElement;
    }
    
    // Function to add typing indicator
    function addTypingIndicator() {
        return addMessage('', 'assistant', true);
    }
    
    // Function to fetch conversations from the backend
    function fetchConversations() {
        fetch('/conversations')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.conversations && data.conversations.length > 0) {
                    // Clear existing conversations
                    if (conversationsList) {
                        conversationsList.innerHTML = '';
                        
                        // Add each conversation to the sidebar
                        data.conversations.forEach(conversation => {
                            const conversationItem = document.createElement('div');
                            conversationItem.className = 'conversation-item';
                            conversationItem.dataset.id = conversation.id;
                            conversationItem.textContent = conversation.title;
                            
                            // Add click event to load conversation
                            conversationItem.addEventListener('click', function() {
                                loadConversation(conversation.id);
                            });
                            
                            conversationsList.appendChild(conversationItem);
                        });
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching conversations:', error);
            });
    }
    
    // Function to load a specific conversation
    function loadConversation(conversationId) {
        // Clear the current chat
        chatMessages.innerHTML = '';
        messageHistory = [];
        currentConversationId = conversationId;
        
        // In a full implementation, you would fetch the messages for this conversation
        // For now, simply set the current conversation ID
        console.log(`Loading conversation ID: ${conversationId}`);
    }
    
    // Function to send message to backend and process streaming response
    function sendMessageToBackend(message, model, typingIndicator) {
        // Add user message to history
        messageHistory.push({
            role: 'user',
            content: message
        });
        
        // Create fetch request to /chat endpoint
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                model: model,
                history: messageHistory,
                conversation_id: currentConversationId
            })
        }).then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            // Setup event source for streaming
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let responseText = '';
            
            // Remove typing indicator
            if (typingIndicator) {
                chatMessages.removeChild(typingIndicator);
            }
            
            // Add empty assistant message
            const assistantMessageElement = addMessage('', 'assistant');
            const messageContent = assistantMessageElement.querySelector('.message-content');
            
            // Function to process chunks
            function processChunks() {
                return reader.read().then(({ done, value }) => {
                    if (done) {
                        // Add the complete assistant response to the message history
                        if (responseText) {
                            messageHistory.push({
                                role: 'assistant',
                                content: responseText
                            });
                        }
                        return;
                    }
                    
                    // Decode the chunk and add to buffer
                    buffer += decoder.decode(value, { stream: true });
                    
                    // Process each line in the buffer
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop(); // Keep the last incomplete line in the buffer
                    
                    // Process each complete line
                    for (const line of lines) {
                        if (line.trim() === '') continue;
                        
                        // Check if line starts with 'data: '
                        if (line.startsWith('data: ')) {
                            const data = line.substring(6); // Remove 'data: ' prefix
                            
                            // Check for [DONE] marker
                            if (data.trim() === '[DONE]') {
                                continue;
                            }
                            
                            try {
                                const parsedData = JSON.parse(data);
                                
                                if (parsedData.error) {
                                    messageContent.innerHTML = `<span class="error">Error: ${parsedData.error}</span>`;
                                    return;
                                }
                                
                                // Update conversation ID if provided
                                if (parsedData.conversation_id && !currentConversationId) {
                                    currentConversationId = parsedData.conversation_id;
                                    console.log(`Setting conversation ID: ${currentConversationId}`);
                                    
                                    // Refresh conversations list to show the new conversation
                                    fetchConversations();
                                }
                                
                                // Handle done marker
                                if (parsedData.done) {
                                    console.log("Conversation finished");
                                    return;
                                }
                                
                                // Handle content
                                if (parsedData.content) {
                                    responseText += parsedData.content;
                                    messageContent.innerHTML = formatMessage(responseText);
                                    chatMessages.scrollTop = chatMessages.scrollHeight;
                                }
                            } catch (error) {
                                console.error('Error parsing SSE data:', error, data);
                            }
                        }
                    }
                    
                    // Continue reading
                    return processChunks();
                });
            }
            
            return processChunks();
        }).catch(error => {
            console.error('Error sending message:', error);
            
            // Remove typing indicator if it exists
            if (typingIndicator && typingIndicator.parentNode) {
                chatMessages.removeChild(typingIndicator);
            }
            
            // Add error message
            const errorMessage = addMessage(`Error: ${error.message}`, 'assistant');
            errorMessage.querySelector('.message-content').classList.add('error');
        });
    }
    
    // Function to format message with markdown, code blocks, etc.
    function formatMessage(text) {
        // Simple markdown-like formatting (this could be expanded or replaced with a proper markdown library)
        
        // Code blocks
        text = text.replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>');
        
        // Inline code
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Bold
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Italic
        text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        // Line breaks
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }
    
    // Function to clear chat
    function clearChat() {
        // Clear the message history
        messageHistory = [];
        
        // Keep only the welcome container or create it if it doesn't exist
        if (!document.querySelector('.welcome-container')) {
            chatMessages.innerHTML = `
                <div class="welcome-container">
                    <div class="welcome-icon">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                        </svg>
                    </div>
                    <h1 class="welcome-heading">Welcome to GloriaMundo!</h1>
                    <p class="welcome-text">
                        Ask me anything and I'll provide helpful, accurate responses. Sign in to 
                        save your conversations and access them from any device.
                    </p>
                    <button class="example-question-btn" id="example-question-btn">
                        <i class="fa-regular fa-lightbulb"></i> Try an example question
                    </button>
                </div>
            `;
            
            // Re-attach event listener to the new example question button
            document.getElementById('example-question-btn').addEventListener('click', function() {
                const exampleQuestions = [
                    "What are the major differences between renewable and fossil fuel energy sources?",
                    "Can you explain how artificial intelligence works in simple terms?",
                    "What are some effective strategies for reducing carbon emissions?",
                    "How does quantum computing differ from classical computing?",
                    "What are the potential implications of gene editing technologies?"
                ];
                
                const randomQuestion = exampleQuestions[Math.floor(Math.random() * exampleQuestions.length)];
                messageInput.value = randomQuestion;
                sendMessage();
            });
        }
    }
    
    // Initialize by focusing on the input
    messageInput.focus();
});
