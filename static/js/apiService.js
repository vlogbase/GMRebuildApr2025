// Import utility functions
import { getCSRFToken } from './utils.js';

// API Service Module - Centralized backend communication

// Fetch conversations from the backend
export async function fetchConversationsAPI(bustCache = false, metadataOnly = true) {
    const url = `/conversations?_=${Date.now()}&metadata_only=${metadataOnly}`;
    
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching conversations:', error);
        throw error;
    }
}

// Send message to backend
export async function sendMessageAPI(payload) {
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return response;
    } catch (error) {
        console.error('Error sending message:', error);
        throw error;
    }
}

// Load specific conversation
export async function loadConversationAPI(conversationId) {
    try {
        const response = await fetch(`/conversation/${conversationId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error loading conversation:', error);
        throw error;
    }
}

// Create new conversation
export async function createNewConversationAPI() {
    try {
        const response = await fetch('/new_conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error creating new conversation:', error);
        throw error;
    }
}

// Fetch user preferences
export async function fetchUserPreferencesAPI() {
    try {
        const response = await fetch('/api/user_preferences');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching user preferences:', error);
        throw error;
    }
}

// Save model preference
export async function saveModelPreferenceAPI(presetId, modelId) {
    try {
        const response = await fetch('/api/save_model_preference', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                preset_id: presetId,
                model_id: modelId
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error saving model preference:', error);
        throw error;
    }
}

// Upload file (unified endpoint)
export async function uploadFileAPI(file, conversationId) {
    const formData = new FormData();
    formData.append('file', file);
    if (conversationId) {
        formData.append('conversation_id', conversationId);
    }
    
    try {
        const response = await fetch('/upload_file', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error uploading file:', error);
        throw error;
    }
}

// Cleanup empty conversations
export async function cleanupEmptyConversationsAPI() {
    try {
        const response = await fetch('/api/cleanup-empty-conversations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error during cleanup:', error);
        throw error;
    }
}

// Fetch available models
export async function fetchAvailableModelsAPI() {
    try {
        const response = await fetch('/api/models');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching available models:', error);
        throw error;
    }
}