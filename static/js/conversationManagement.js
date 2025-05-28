// Import required modules
import { fetchConversationsAPI, loadConversationAPI, createNewConversationAPI } from './apiService.js';
import { addMessage, currentConversationId } from './chatLogic.js';

// Conversation management functions
export async function fetchConversations(bustCache = false, metadataOnly = true) {
    try {
        const data = await fetchConversationsAPI(bustCache, metadataOnly);
        
        if (data.conversations) {
            updateConversationsList(data.conversations);
            console.log(`✅ Loaded ${data.conversations.length} conversations`);
        }
        
        return data;
    } catch (error) {
        console.error('Error fetching conversations:', error);
        return { conversations: [] };
    }
}

export async function loadConversation(conversationId) {
    try {
        const data = await loadConversationAPI(conversationId);
        
        if (data.messages) {
            // Clear current chat
            const chatMessages = document.getElementById('chat-messages');
            if (chatMessages) {
                chatMessages.innerHTML = '';
            }
            
            // Load all messages
            data.messages.forEach(message => {
                addMessage(message.content, message.role, false, message.metadata);
            });
            
            console.log(`✅ Loaded conversation ${conversationId} with ${data.messages.length} messages`);
        }
        
        return data;
    } catch (error) {
        console.error('Error loading conversation:', error);
        throw error;
    }
}

export async function createNewConversation() {
    try {
        const data = await createNewConversationAPI();
        
        if (data.conversation_id) {
            currentConversationId = data.conversation_id;
            
            // Clear current chat
            const chatMessages = document.getElementById('chat-messages');
            if (chatMessages) {
                chatMessages.innerHTML = '';
            }
            
            // Update URL if needed
            if (window.history && window.history.pushState) {
                window.history.pushState(null, '', `/chat/${data.conversation_id}`);
            }
            
            console.log(`✅ Created new conversation: ${data.conversation_id}`);
        }
        
        return data;
    } catch (error) {
        console.error('Error creating new conversation:', error);
        throw error;
    }
}

function updateConversationsList(conversations) {
    const conversationsList = document.getElementById('conversations-list');
    if (!conversationsList) return;
    
    // Clear existing conversations
    conversationsList.innerHTML = '';
    
    // Add each conversation
    conversations.forEach(conversation => {
        const conversationElement = document.createElement('div');
        conversationElement.className = 'conversation-item';
        conversationElement.innerHTML = `
            <div class="conversation-title">${conversation.title || 'New Conversation'}</div>
            <div class="conversation-date">${formatDate(conversation.created_at)}</div>
        `;
        
        conversationElement.addEventListener('click', () => {
            // Update the current conversation ID in chat logic
            if (typeof currentConversationId !== 'undefined') {
                currentConversationId = conversation.id;
            }
            
            // Update active state in UI
            document.querySelectorAll('.conversation-item').forEach(item => {
                item.classList.remove('active');
            });
            conversationElement.classList.add('active');
            
            loadConversation(conversation.id);
        });
        
        conversationsList.appendChild(conversationElement);
    });
}

function formatDate(dateString) {
    if (!dateString) {
        return 'No date';
    }
    
    try {
        const date = new Date(dateString);
        
        // Check if date is valid
        if (isNaN(date.getTime())) {
            console.warn('Invalid date string:', dateString);
            return 'Invalid date';
        }
        
        return date.toLocaleDateString();
    } catch (error) {
        console.error('Error formatting date:', error, 'for dateString:', dateString);
        return 'Date error';
    }
}