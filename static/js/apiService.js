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
        const response = await fetch(`/conversation/${conversationId}/messages`);
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
        const response = await fetch('/api/create-conversation', {
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
        console.log('Fetching user preferences from /get_preferences');
        const response = await fetch('/get_preferences');
        
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        console.log('Response headers:', response.headers);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Non-OK response body:', errorText);
            throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
        }
        
        const responseText = await response.text();
        console.log('Raw response text:', responseText);
        
        try {
            const data = JSON.parse(responseText);
            console.log('Parsed JSON data:', data);
            return data;
        } catch (parseError) {
            console.error('JSON parse error:', parseError);
            console.error('Failed to parse response text:', responseText);
            throw new Error(`Invalid JSON response: ${parseError.message}`);
        }
    } catch (error) {
        console.error('Complete error object:', error);
        console.error('Error name:', error.name);
        console.error('Error message:', error.message);
        console.error('Error stack:', error.stack);
        throw error;
    }
}

// Save model preference
export async function saveModelPreferenceAPI(presetId, modelId) {
    try {
        const response = await fetch('/save_preference', {
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

// Reset preferences (unified function for both single preset and all presets)
export async function resetPreferencesAPI(presetId = null) {
    try {
        const requestBody = {};
        if (presetId !== null && presetId !== undefined) {
            requestBody.preset_id = presetId;
        }
        
        const response = await fetch('/reset_preferences', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error resetting preferences:', error);
        throw error;
    }
}

// Legacy function for backward compatibility (now uses unified API)
export async function resetModelPreferenceAPI(presetId) {
    console.warn('resetModelPreferenceAPI is deprecated, use resetPreferencesAPI instead');
    return resetPreferencesAPI(presetId);
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
        console.log('🔍 Calling /api/get_model_prices...');
        const response = await fetch('/api/get_model_prices');
        
        console.log('📡 Response status:', response.status, response.statusText);
        console.log('📡 Response headers:', response.headers.get('content-type'));
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status} ${response.statusText}`);
        }
        
        const responseText = await response.text();
        console.log('📄 Raw response text:', responseText);
        
        const data = JSON.parse(responseText);
        console.log('📦 Parsed JSON data:', data);
        
        return data;
    } catch (error) {
        console.error('❌ Error in fetchAvailableModelsAPI:', {
            name: error.name,
            message: error.message,
            stack: error.stack,
            fullError: error
        });
        throw error;
    }
}

// Share conversation
export async function shareConversationAPI(conversationId) {
    try {
        const response = await fetch(`/conversation/${conversationId}/share`, {
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
        console.error('Error sharing conversation:', error);
        throw error;
    }
}

// Rate message
export async function rateMessageAPI(messageId, rating) {
    try {
        const response = await fetch(`/message/${messageId}/rate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ rating })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error rating message:', error);
        throw error;
    }
}