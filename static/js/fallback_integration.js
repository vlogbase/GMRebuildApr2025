/**
 * Model Fallback Integration
 * 
 * This script integrates the model fallback confirmation dialog
 * with the main chat interface script (script.js).
 */

document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on the chat page
    if (!document.getElementById('chat-container')) {
        return;
    }
    
    initializeFallbackIntegration();
});

// Initialize model fallback integration with the main chat interface
function initializeFallbackIntegration() {
    // Wait for the main script to load and initialize
    const checkMainScriptLoaded = setInterval(() => {
        if (window.sendMessage) {
            clearInterval(checkMainScriptLoaded);
            
            // Store the original sendMessage function
            const originalSendMessage = window.sendMessage;
            
            // Override the sendMessage function with our fallback-aware version
            window.sendMessage = function(message, modelId) {
                // Check if we need to confirm model availability first
                if (modelId) {
                    handleModelSendWithFallback(message, modelId);
                } else {
                    // No specific model selected, use the original function
                    originalSendMessage(message);
                }
            };
            
            console.log('Model fallback integration initialized');
        }
    }, 100);
}

// Handle model fallback check before sending message
function handleModelSendWithFallback(msgText, requestedModelId) {
    // First check if auto-fallback is enabled
    shouldAutoFallback(function(autoFallback) {
        if (autoFallback) {
            // Automatically use fallback model if needed (no confirmation)
            checkModelAndSend(msgText, requestedModelId, true);
        } else {
            // Show confirmation dialog if fallback is needed
            checkModelAndSend(msgText, requestedModelId, false);
        }
    });
}

// Check model availability and send with appropriate fallback handling
function checkModelAndSend(msgText, modelId, autoFallback) {
    // Get current message input element
    const messageInput = document.getElementById('message-input');
    
    // Get CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Check model availability on the backend
    fetch(`/api/chat/check_model?model_id=${encodeURIComponent(modelId)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.available) {
                // Model is available, send as normal
                sendWithSelectedModel(msgText, modelId);
            } else {
                // Model is not available, handle fallback
                const fallbackModel = data.fallback_model;
                
                if (autoFallback) {
                    // Auto-fallback enabled, use fallback model without confirmation
                    sendWithSelectedModel(msgText, fallbackModel);
                    
                    // Show non-blocking notification
                    showFallbackNotification(data.model_name, data.fallback_model_name);
                } else {
                    // Show confirmation dialog
                    showFallbackConfirmation(
                        data.model_name, 
                        data.fallback_model_name,
                        msgText,
                        function(confirmed) {
                            if (confirmed) {
                                // User confirmed fallback
                                sendWithSelectedModel(msgText, fallbackModel);
                            } else {
                                // User rejected fallback
                                // Put message back in input field
                                if (messageInput) {
                                    messageInput.value = msgText;
                                    messageInput.focus();
                                }
                                
                                // Highlight the model selector to indicate a change is needed
                                highlightModelSelector();
                            }
                        }
                    );
                }
            }
        })
        .catch(error => {
            console.error('Error checking model availability:', error);
            // On error, proceed with original model as a fallback
            showErrorMessage('Could not check model availability, sending with selected model.');
            sendWithSelectedModel(msgText, modelId);
        });
}

// Send message with the selected model
function sendWithSelectedModel(message, modelId) {
    // Get original sendMessage function
    const origSendMessageFn = window.originalSendMessage || 
                             (typeof sendChatMessage === 'function' ? sendChatMessage : null);
    
    if (origSendMessageFn) {
        // Use the original function with the selected model
        origSendMessageFn(message, modelId);
    } else {
        // Fallback if original function not found
        console.error('Original send function not found, using direct implementation');
        
        // Add user message to UI
        addMessageToUI('user', message);
        
        // Clear input
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.value = '';
        }
        
        // Send API request
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                content: message,
                model: modelId,
                conversation_id: getCurrentConversationId()
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showErrorMessage(data.error);
            } else {
                // Add AI response to UI
                addMessageToUI('assistant', data.message);
            }
        })
        .catch(error => {
            console.error('Error sending message:', error);
            showErrorMessage('Error sending message');
        });
    }
}

// Add message to UI (minimal implementation, should be handled by main chat script)
function addMessageToUI(role, content) {
    // Check if main script has a function for this
    if (typeof addMessage === 'function') {
        addMessage(role, content);
        return;
    }
    
    // Fallback implementation
    const chatContainer = document.querySelector('.chat-messages');
    if (!chatContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.innerHTML = `
        <div class="message-content">
            ${content}
        </div>
    `;
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Get current conversation ID
function getCurrentConversationId() {
    // Try to get from URL
    const urlParams = new URLSearchParams(window.location.search);
    const idFromUrl = urlParams.get('id');
    if (idFromUrl) return idFromUrl;
    
    // Try to get from a data attribute in the DOM
    const conversationElement = document.querySelector('[data-conversation-id]');
    if (conversationElement) {
        return conversationElement.getAttribute('data-conversation-id');
    }
    
    // Fallback to session storage if supported
    if (typeof sessionStorage !== 'undefined') {
        return sessionStorage.getItem('current_conversation_id');
    }
    
    // Last resort
    return null;
}

// Highlight the model selector to indicate user should change model
function highlightModelSelector() {
    const modelSelector = document.getElementById('model-selector');
    if (!modelSelector) return;
    
    // Add highlight class
    modelSelector.classList.add('highlight-model-selector');
    
    // Scroll into view if needed
    modelSelector.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    // Remove highlight after a few seconds
    setTimeout(() => {
        modelSelector.classList.remove('highlight-model-selector');
    }, 3000);
}

// Show error message in UI
function showErrorMessage(message) {
    // Add toast notification
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = 'toast error-toast';
    toast.setAttribute('role', 'alert');
    
    toast.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">Error</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">${message}</div>
    `;
    
    // Add to toast container or create one
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Store a reference to the original sendMessage function
    if (window.sendMessage) {
        window.originalSendMessage = window.sendMessage;
    }
});