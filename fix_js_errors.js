/**
 * JavaScript Fixes for GloriaMundo Application
 * 
 * This script contains the fixes for the "Failed to fetch" errors 
 * in the application's JavaScript code.
 */

// Improved saveModelPreference function with better error handling
window.saveModelPreference = function(presetId, modelId, buttonElement) {
    // Log request details for debugging
    console.log('Saving model preference:', { preset_id: presetId, model_id: modelId });
    
    // Add defensive parameters to improve reliability of the fetch request
    fetch('/save_preference', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            preset_id: presetId,
            model_id: modelId
        }),
        // Add these options to improve fetch reliability
        credentials: 'same-origin',
        cache: 'no-cache'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Preference saved:', data);
        
        // Show success feedback if button element was provided
        if (buttonElement) {
            buttonElement.classList.remove('loading');
            
            // Optional: Show a brief success indicator
            buttonElement.classList.add('save-success');
            setTimeout(() => {
                buttonElement.classList.remove('save-success');
            }, 1000);
        }
    })
    .catch(error => {
        console.error('Error saving preference:', error);
        
        // Remove loading state and show error if button element was provided
        if (buttonElement) {
            buttonElement.classList.remove('loading');
            buttonElement.classList.add('save-error');
            setTimeout(() => {
                buttonElement.classList.remove('save-error');
            }, 1000);
        }
        
        // Store in localStorage as fallback if server request fails
        try {
            localStorage.setItem(`model_preference_${presetId}`, modelId);
            console.log('Saved preference to localStorage as fallback');
        } catch (storageError) {
            console.error('Failed to save to localStorage:', storageError);
        }
    });
};

// Improved createNewConversation function with better error handling
function createNewConversation() {
    // Clear chat UI
    clearChat();
    
    // Reset currentConversationId as a fallback in case API call fails
    currentConversationId = null;
    
    // Check authentication status directly
    const userIsLoggedIn = !!document.getElementById('logout-btn');
    if (!userIsLoggedIn) {
        // No authentication, just restore button state
        if (newChatButton) {
            newChatButton.innerHTML = originalContent || 'New Chat';
            newChatButton.disabled = false;
        }
        return;
    }
    
    // Schedule idle cleanup instead of blocking with synchronous cleanup
    performIdleCleanup();
    
    // Create a new conversation immediately with improved error handling
    fetch('/api/create-conversation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        credentials: 'same-origin',
        cache: 'no-cache'
    })
    .then(response => {
        if (!response.ok) {
            console.error(`Error creating conversation: ${response.status}`);
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Restore button state
        if (newChatButton) {
            newChatButton.innerHTML = originalContent || 'New Chat';
            newChatButton.disabled = false;
        }
        
        if (data.success && data.conversation) {
            // Set the current conversation ID to the new one
            currentConversationId = data.conversation.id;
            console.log(`Created new conversation with ID: ${currentConversationId}`);
            
            // Update the sidebar with the new conversation
            if (typeof fetchConversations === 'function') {
                fetchConversations(true);
            }
        } else {
            console.error('Failed to create new conversation:', data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Error creating conversation:', error);
        
        // Restore button state
        if (newChatButton) {
            newChatButton.innerHTML = originalContent || 'New Chat';
            newChatButton.disabled = false;
        }
        
        // Create a local conversation ID as a fallback
        currentConversationId = 'local-' + Date.now();
        console.log(`Created fallback local conversation ID: ${currentConversationId}`);
    });
}

// Function to handle potential WorkspaceAvailableModels issues
// This is a fallback implementation if the function is missing or errors out
if (typeof WorkspaceAvailableModels !== 'function') {
    window.WorkspaceAvailableModels = function(callback) {
        console.log('Using fallback WorkspaceAvailableModels function');
        
        // Try to load models from a different endpoint as fallback
        fetch('/api/available-models', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin',
            cache: 'no-cache'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Models loaded from fallback endpoint:', data);
            if (typeof callback === 'function') {
                callback(data);
            }
        })
        .catch(error => {
            console.error('Error loading models from fallback endpoint:', error);
            
            // If all else fails, use default models from localStorage or hardcoded fallback
            const fallbackModels = localStorage.getItem('fallbackModels') 
                ? JSON.parse(localStorage.getItem('fallbackModels')) 
                : [{ id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo (Fallback)' }];
                
            console.log('Using fallback models:', fallbackModels);
            if (typeof callback === 'function') {
                callback(fallbackModels);
            }
        });
    };
}