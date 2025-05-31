// Import required modules
import { fetchConversationsAPI, loadConversationAPI, createNewConversationAPI } from './apiService.js';
import { addMessage, setCurrentConversationId, clearChat } from './chatLogic.js';

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
            
            // Update URL to reflect the current conversation
            if (window.history && window.history.pushState) {
                window.history.pushState(null, '', `/chat/${conversationId}`);
                console.log(`🔗 Updated URL to /chat/${conversationId}`);
            }
            
            console.log(`✅ Loaded conversation ${conversationId} with ${data.messages.length} messages`);
        }
        
        return data;
    } catch (error) {
        console.error('Error loading conversation:', error);
        
        // Check if this is a 404 error (conversation not found)
        if (error.message.includes('404')) {
            console.warn(`Conversation ${conversationId} not found, removing from sidebar`);
            // Remove the conversation from the sidebar since it doesn't exist
            const conversationElement = document.querySelector(`[data-conversation-id="${conversationId}"]`);
            if (conversationElement) {
                conversationElement.remove();
            }
            // Redirect to home page
            window.location.href = '/';
            return;
        }
        
        throw error;
    }
}

export async function createNewConversation(updateURL = true) {
    try {
        // Clear chat UI first (using the same function as the original)
        clearChat();
        
        // Reset conversation ID to null as fallback
        setCurrentConversationId(null);
        
        const data = await createNewConversationAPI();
        
        if (data.conversation && data.conversation.id) {
            // Set the new conversation ID using the setter function
            setCurrentConversationId(data.conversation.id);
            
            // Only update URL if explicitly requested (e.g., when user clicks "New Chat")
            // Don't update URL during initial page load or default conversation creation
            if (updateURL && window.history && window.history.pushState) {
                window.history.pushState(null, '', `/chat/${data.conversation.id}`);
                console.log(`🔗 Updated URL to /chat/${data.conversation.id}`);
            } else {
                console.log(`📝 Created conversation ${data.conversation.id} without URL update`);
            }
            
            // Refresh sidebar to show new conversation (mirroring original behavior)
            await fetchConversations(true, true);
            
            console.log(`✅ Created new conversation: ${data.conversation.id}`);
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
            // Update the current conversation ID using setter function
            setCurrentConversationId(conversation.id);
            
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