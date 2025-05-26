// Chat Module
// Handles messaging, conversations, and chat functionality

// Global variables for chat functionality
let currentConversationId = null;
let conversations = [];
let isStreaming = false;
let messageInput = null;
let sendButton = null;
let chatMessages = null;

// Initialize chat functionality
function initializeChat() {
    // Get essential DOM elements
    messageInput = document.getElementById('user-input');
    sendButton = document.getElementById('send-button');
    chatMessages = document.getElementById('chat-messages');
    
    // Setup chat controls
    setupSendButton();
    setupMessageInput();
    setupNewChatButton();
    setupExampleQuestions();
    
    // Load conversations and handle initial state
    handleInitialChatState();
}

// Handle initial chat state on page load
function handleInitialChatState() {
    // Check if we have a conversation ID from the URL
    const urlConversationId = getConversationIdFromUrl();
    
    if (urlConversationId) {
        currentConversationId = urlConversationId;
        console.log('Loading conversation from URL:', urlConversationId);
        
        // Load the specific conversation
        loadConversation(urlConversationId);
        
        // Defer loading conversation list to improve initial load
        setTimeout(() => {
            fetchConversations(true, true);
        }, 700);
    } else {
        // No conversation in URL, create a new one after page loads
        setTimeout(() => {
            createNewConversation().then(() => {
                // Load conversation list after creating new conversation
                setTimeout(() => {
                    fetchConversations();
                }, 500);
            });
        }, 800);
    }
}

// Setup send button functionality
function setupSendButton() {
    if (sendButton) {
        sendButton.addEventListener('click', function(e) {
            e.preventDefault();
            sendMessage();
        });
    }
}

// Setup message input functionality
function setupMessageInput() {
    if (messageInput) {
        // Handle Enter key
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Auto-resize textarea
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
    }
}

// Setup new chat button
function setupNewChatButton() {
    const newChatButton = document.getElementById('new-chat-btn');
    if (newChatButton) {
        newChatButton.addEventListener('click', function(e) {
            e.preventDefault();
            createNewConversation();
        });
    }
}

// Setup example questions
function setupExampleQuestions() {
    const exampleButton = document.getElementById('example-question-btn');
    if (exampleButton && messageInput) {
        exampleButton.addEventListener('click', function() {
            const exampleQuestions = [
                "What's the weather like today?",
                "Explain quantum computing in simple terms",
                "Help me write a professional email",
                "What are the benefits of exercise?",
                "How does artificial intelligence work?"
            ];
            
            const randomQuestion = exampleQuestions[Math.floor(Math.random() * exampleQuestions.length)];
            messageInput.value = randomQuestion;
            messageInput.focus();
        });
    }
}

// Send message
async function sendMessage() {
    if (isStreaming) {
        console.log('Message sending blocked - streaming in progress');
        return;
    }
    
    const message = messageInput.value.trim();
    if (!message && !getCurrentUploadedFile()) {
        return;
    }
    
    // Check authentication for non-authenticated users
    if (window.auth && !window.auth.isLoggedIn) {
        if (window.showLoginPrompt) {
            window.showLoginPrompt();
        }
        return;
    }
    
    // Disable send button and clear input
    if (sendButton) sendButton.disabled = true;
    if (messageInput) {
        messageInput.value = '';
        messageInput.style.height = 'auto';
    }
    
    // Create conversation if needed
    if (!currentConversationId) {
        await createNewConversation();
    }
    
    try {
        // Add user message to chat
        if (message) {
            addMessageToChat(message, 'user');
        }
        
        // Handle file uploads
        const uploadedFile = getCurrentUploadedFile();
        if (uploadedFile) {
            addFileToChat(uploadedFile);
        }
        
        // Send to server
        await sendMessageToServer(message, uploadedFile);
        
    } catch (error) {
        console.error('Error sending message:', error);
        if (window.utils) {
            window.utils.showToast('Error sending message. Please try again.', 'error');
        }
    } finally {
        // Re-enable send button
        if (sendButton) sendButton.disabled = false;
        
        // Clear uploaded file
        if (uploadedFile && window.upload) {
            if (uploadedFile.isImage) {
                window.upload.removeImagePreview();
            } else if (uploadedFile.isPdf) {
                window.upload.removePdfPreview();
            }
        }
    }
}

// Send message to server
async function sendMessageToServer(message, uploadedFile) {
    const formData = new FormData();
    
    if (message) {
        formData.append('message', message);
    }
    
    if (currentConversationId) {
        formData.append('conversation_id', currentConversationId);
    }
    
    if (uploadedFile) {
        if (uploadedFile.isImage) {
            formData.append('image_url', uploadedFile.image_url);
        } else if (uploadedFile.isPdf) {
            formData.append('pdf_url', uploadedFile.pdf_url);
        }
    }
    
    // Add CSRF token
    const csrfToken = window.utils ? window.utils.getCSRFToken() : null;
    if (csrfToken) {
        formData.append('csrf_token', csrfToken);
    }
    
    const response = await fetch('/chat', {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    // Handle streaming response
    await handleStreamingResponse(response);
}

// Handle streaming response from server
async function handleStreamingResponse(response) {
    isStreaming = true;
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    // Create assistant message container
    const assistantMessageDiv = createAssistantMessageDiv();
    
    try {
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') {
                        return;
                    }
                    
                    try {
                        const parsed = JSON.parse(data);
                        if (parsed.content) {
                            appendToAssistantMessage(assistantMessageDiv, parsed.content);
                        }
                        if (parsed.conversation_id) {
                            currentConversationId = parsed.conversation_id;
                            updateUrlWithConversation(currentConversationId);
                        }
                    } catch (e) {
                        console.warn('Failed to parse chunk:', data);
                    }
                }
            }
        }
    } finally {
        isStreaming = false;
        finalizeAssistantMessage(assistantMessageDiv);
    }
}

// Create assistant message div
function createAssistantMessageDiv() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message';
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <div class="avatar-circle">AI</div>
        </div>
        <div class="message-content"></div>
    `;
    
    if (chatMessages) {
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    return messageDiv;
}

// Append content to assistant message
function appendToAssistantMessage(messageDiv, content) {
    const messageContent = messageDiv.querySelector('.message-content');
    if (messageContent) {
        messageContent.textContent += content;
        
        // Auto-scroll if user is at bottom
        if (chatMessages) {
            const isAtBottom = chatMessages.scrollTop >= chatMessages.scrollHeight - chatMessages.clientHeight - 50;
            if (isAtBottom) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }
    }
}

// Finalize assistant message
function finalizeAssistantMessage(messageDiv) {
    const messageContent = messageDiv.querySelector('.message-content');
    if (messageContent && window.utils) {
        // Apply formatting to final message
        const formattedContent = window.utils.formatMessage(messageContent.textContent);
        messageContent.innerHTML = formattedContent;
        
        // Force repaint
        window.utils.forceRepaint(messageContent);
    }
    
    // Update conversations list
    setTimeout(() => {
        fetchConversations();
    }, 1000);
}

// Add message to chat display
function addMessageToChat(message, sender) {
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatarText = sender === 'user' ? 'U' : 'AI';
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <div class="avatar-circle">${avatarText}</div>
        </div>
        <div class="message-content">${window.utils ? window.utils.formatMessage(message) : message}</div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add file to chat display
function addFileToChat(fileData) {
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    
    let fileContent = '';
    if (fileData.isImage) {
        fileContent = `<img src="${fileData.image_url}" alt="Uploaded image" style="max-width: 300px; border-radius: 8px;">`;
    } else if (fileData.isPdf) {
        fileContent = `<div class="pdf-indicator">📄 ${fileData.filename || 'PDF Document'}</div>`;
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <div class="avatar-circle">U</div>
        </div>
        <div class="message-content">${fileContent}</div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Create new conversation
async function createNewConversation() {
    try {
        const response = await fetch('/new_conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                csrf_token: window.utils ? window.utils.getCSRFToken() : null
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            currentConversationId = data.conversation_id;
            
            // Clear chat messages
            if (chatMessages) {
                chatMessages.innerHTML = '';
            }
            
            // Update URL
            updateUrlWithConversation(currentConversationId);
            
            console.log('Created new conversation:', currentConversationId);
            return currentConversationId;
        }
    } catch (error) {
        console.error('Error creating new conversation:', error);
    }
    return null;
}

// Load specific conversation
async function loadConversation(conversationId) {
    try {
        const response = await fetch(`/conversation/${conversationId}`);
        if (response.ok) {
            const data = await response.json();
            displayConversationMessages(data.messages);
            currentConversationId = conversationId;
        }
    } catch (error) {
        console.error('Error loading conversation:', error);
    }
}

// Display conversation messages
function displayConversationMessages(messages) {
    if (!chatMessages) return;
    
    chatMessages.innerHTML = '';
    
    messages.forEach(message => {
        addMessageToChat(message.content, message.role);
    });
}

// Fetch conversations list
async function fetchConversations(bustCache = false, metadataOnly = true) {
    try {
        const url = `/conversations?bust_cache=${bustCache}&metadata_only=${metadataOnly}`;
        const response = await fetch(url);
        
        if (response.ok) {
            const data = await response.json();
            conversations = data.conversations || [];
            updateConversationsList();
        }
    } catch (error) {
        console.error('Error fetching conversations:', error);
    }
}

// Update conversations list in sidebar
function updateConversationsList() {
    const conversationsList = document.getElementById('conversations-list');
    if (!conversationsList) return;
    
    conversationsList.innerHTML = '';
    
    conversations.forEach(conversation => {
        const listItem = document.createElement('li');
        listItem.innerHTML = `
            <a href="/conversation/${conversation.id}" 
               class="conversation-link ${conversation.id === currentConversationId ? 'active' : ''}"
               data-conversation-id="${conversation.id}">
                ${conversation.title || 'New Conversation'}
            </a>
        `;
        conversationsList.appendChild(listItem);
    });
}

// Utility functions
function getConversationIdFromUrl() {
    const path = window.location.pathname;
    const match = path.match(/\/conversation\/(.+)/);
    return match ? match[1] : null;
}

function updateUrlWithConversation(conversationId) {
    const newUrl = `/conversation/${conversationId}`;
    window.history.pushState({ conversationId }, '', newUrl);
}

function getCurrentUploadedFile() {
    return window.upload ? window.upload.getCurrentUploadedFile() : null;
}

// Export chat functions
window.chat = {
    initializeChat,
    sendMessage,
    createNewConversation,
    loadConversation,
    fetchConversations,
    getCurrentConversationId: () => currentConversationId
};

// Initialize chat when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeChat();
});