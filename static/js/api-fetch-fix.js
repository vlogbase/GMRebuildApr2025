/**
 * API Fetch Fixes for GloriaMundo
 * 
 * This script adds enhanced fetch error handling to improve reliability
 * of API calls and prevent "Failed to fetch" errors in the browser.
 */

// Create a more reliable fetch wrapper for API calls
window.apiFetch = function(url, options = {}) {
    // Set default options for better reliability
    const defaultOptions = {
        credentials: 'same-origin',
        cache: 'no-cache',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
        }
    };
    
    // Merge options
    const fetchOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...(options.headers || {})
        }
    };
    
    // Add diagnostics
    console.log(`API Request to: ${url}`, fetchOptions);
    
    // Perform fetch with improved error handling
    return fetch(url, fetchOptions)
        .then(response => {
            if (!response.ok) {
                // Enhanced error with status and statusText
                const error = new Error(`HTTP error ${response.status}: ${response.statusText}`);
                error.status = response.status;
                error.response = response;
                throw error;
            }
            return response.json();
        })
        .catch(error => {
            console.error(`API Error for ${url}:`, error);
            // Rethrow to let calling code handle the error
            throw error;
        });
};

// Check if WorkspaceAvailableModels exists and fix if needed
if (typeof WorkspaceAvailableModels !== 'function') {
    console.log('Patching missing WorkspaceAvailableModels function');
    window.WorkspaceAvailableModels = function(callback) {
        return window.apiFetch('/api/available-models')
            .then(data => {
                if (typeof callback === 'function') {
                    callback(data);
                }
                return data;
            })
            .catch(error => {
                console.error('Error fetching available models:', error);
                // Return empty array as fallback
                if (typeof callback === 'function') {
                    callback([]);
                }
                return [];
            });
    };
}

// Update saveModelPreference to use the enhanced fetch
const originalSaveModelPreference = window.saveModelPreference;
window.saveModelPreference = function(presetId, modelId, buttonElement) {
    // Log the request for debugging
    console.log('Saving model preference:', { preset_id: presetId, model_id: modelId });
    
    // Show loading state
    if (buttonElement) {
        buttonElement.classList.add('loading');
    }
    
    // Use enhanced fetch for better reliability
    return window.apiFetch('/save_preference', {
        method: 'POST',
        body: JSON.stringify({
            preset_id: presetId,
            model_id: modelId
        })
    })
    .then(data => {
        console.log('Preference saved:', data);
        
        // Show success feedback
        if (buttonElement) {
            buttonElement.classList.remove('loading');
            buttonElement.classList.add('save-success');
            setTimeout(() => {
                buttonElement.classList.remove('save-success');
            }, 1000);
        }
        
        return data;
    })
    .catch(error => {
        console.error('Error saving preference:', error);
        
        // Show error state
        if (buttonElement) {
            buttonElement.classList.remove('loading');
            buttonElement.classList.add('save-error');
            setTimeout(() => {
                buttonElement.classList.remove('save-error');
            }, 1000);
        }
        
        // Store preference locally as fallback
        try {
            localStorage.setItem(`model_preference_${presetId}`, modelId);
            console.log('Saved preference to localStorage as fallback');
        } catch (storageError) {
            console.error('Failed to save to localStorage:', storageError);
        }
        
        throw error;
    });
};

// Patch createNewConversation function to use enhanced fetch
// Will apply if the function exists in the global scope
if (typeof createNewConversation === 'function') {
    const originalCreateNewConversation = createNewConversation;
    window.createNewConversation = function() {
        // Clear chat UI (assuming clearChat is defined)
        if (typeof clearChat === 'function') {
            clearChat();
        }
        
        // Reset conversation ID
        window.currentConversationId = null;
        
        // Check if user is logged in
        const userIsLoggedIn = !!document.getElementById('logout-btn');
        if (!userIsLoggedIn) {
            // Restore button state if needed
            const newChatButton = document.getElementById('new-chat-btn');
            if (newChatButton) {
                const originalContent = newChatButton.getAttribute('data-original-content') || 'New Chat';
                newChatButton.innerHTML = originalContent;
                newChatButton.disabled = false;
            }
            return;
        }
        
        // Clean up old conversations
        if (typeof performIdleCleanup === 'function') {
            performIdleCleanup();
        }
        
        // Create a new conversation with enhanced error handling
        return window.apiFetch('/api/create-conversation', {
            method: 'POST'
        })
        .then(data => {
            // Restore button state
            const newChatButton = document.getElementById('new-chat-btn');
            if (newChatButton) {
                const originalContent = newChatButton.getAttribute('data-original-content') || 'New Chat';
                newChatButton.innerHTML = originalContent;
                newChatButton.disabled = false;
            }
            
            if (data.success && data.conversation) {
                // Set current conversation ID
                window.currentConversationId = data.conversation.id;
                console.log(`Created new conversation with ID: ${window.currentConversationId}`);
                
                // Update sidebar
                if (typeof fetchConversations === 'function') {
                    fetchConversations(true);
                }
            } else {
                console.error('Failed to create conversation:', data.error || 'Unknown error');
            }
            
            return data;
        })
        .catch(error => {
            console.error('Error creating conversation:', error);
            
            // Restore button state
            const newChatButton = document.getElementById('new-chat-btn');
            if (newChatButton) {
                const originalContent = newChatButton.getAttribute('data-original-content') || 'New Chat';
                newChatButton.innerHTML = originalContent;
                newChatButton.disabled = false;
            }
            
            // Create fallback local ID
            window.currentConversationId = 'local-' + Date.now();
            console.log(`Created fallback local conversation ID: ${window.currentConversationId}`);
        });
    };
}