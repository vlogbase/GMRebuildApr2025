/**
 * Model Fallback Confirmation Handler
 * 
 * This script handles showing a confirmation dialog when a model is unavailable
 * and allows the user to choose whether to use the fallback model.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Create the fallback modal if it doesn't exist
    if (!document.getElementById('fallback-modal')) {
        const modalHtml = `
            <div id="fallback-modal" class="fallback-modal">
                <div class="fallback-modal-content">
                    <div class="fallback-modal-header">
                        <h3>Model Unavailable</h3>
                        <span class="fallback-close">&times;</span>
                    </div>
                    <div class="fallback-modal-body">
                        <p id="fallback-message">The selected model is currently unavailable.</p>
                        <p>Would you like to use the suggested fallback model instead?</p>
                    </div>
                    <div class="fallback-modal-footer">
                        <label class="fallback-checkbox">
                            <input type="checkbox" id="auto-fallback-checkbox">
                            Always use fallback models automatically
                        </label>
                        <div class="fallback-buttons">
                            <button id="cancel-fallback" class="btn btn-secondary">No, Cancel</button>
                            <button id="use-fallback" class="btn btn-primary">Yes, Use Fallback</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Append the modal to the body
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        document.body.appendChild(modalContainer.firstElementChild);
        
        // Add event listeners to the modal
        document.querySelector('.fallback-close').addEventListener('click', closeModal);
        document.getElementById('cancel-fallback').addEventListener('click', handleCancelFallback);
        document.getElementById('use-fallback').addEventListener('click', handleUseFallback);
    }
    
    // Add the CSS if it doesn't exist
    if (!document.getElementById('fallback-modal-styles')) {
        const styles = document.createElement('style');
        styles.id = 'fallback-modal-styles';
        styles.textContent = `
            .fallback-modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
            }
            
            .fallback-modal-content {
                background-color: var(--bg-color, #fff);
                margin: 15% auto;
                padding: 20px;
                border: 1px solid var(--border-color, #ddd);
                border-radius: 8px;
                width: 80%;
                max-width: 500px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            
            .fallback-modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            
            .fallback-modal-header h3 {
                margin: 0;
                color: var(--text-color, #333);
            }
            
            .fallback-close {
                color: var(--text-secondary, #aaa);
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
            }
            
            .fallback-close:hover {
                color: var(--text-color, #333);
            }
            
            .fallback-modal-body {
                margin-bottom: 20px;
                color: var(--text-color, #333);
            }
            
            .fallback-modal-footer {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            
            .fallback-checkbox {
                display: flex;
                align-items: center;
                gap: 8px;
                color: var(--text-color, #333);
                font-size: 14px;
            }
            
            .fallback-buttons {
                display: flex;
                justify-content: flex-end;
                gap: 10px;
            }
            
            @media (max-width: 600px) {
                .fallback-modal-content {
                    width: 90%;
                    margin: 25% auto;
                }
            }
        `;
        document.head.appendChild(styles);
    }
    
    // Initialize the stored message data for fallback handling
    window.fallbackData = null;
    
    /**
     * Show the fallback confirmation modal with the relevant model information
     */
    window.showFallbackModal = function(fallbackData, messageData) {
        const modal = document.getElementById('fallback-modal');
        if (!modal) return;
        
        // Store the data for when the user confirms
        window.fallbackData = fallbackData;
        window.messageData = messageData;
        
        // Update the modal message with model names
        const fallbackMessage = document.getElementById('fallback-message');
        fallbackMessage.textContent = `${fallbackData.requested_model} is not currently available. Use ${fallbackData.fallback_model} instead?`;
        
        // Show the modal
        modal.style.display = 'block';
    }
    
    /**
     * Close the fallback modal
     */
    function closeModal() {
        const modal = document.getElementById('fallback-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    /**
     * Handle the user canceling the fallback
     */
    function handleCancelFallback() {
        closeModal();
        
        // Return the message text to the input box
        if (window.messageData && window.messageData.message) {
            const userInput = document.getElementById('user-input');
            if (userInput) {
                userInput.value = window.messageData.message;
                userInput.focus();
            }
        }
        
        // Reset any in-progress indicators
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        
        // Re-enable input
        const messageInput = document.getElementById('user-input');
        const sendButton = document.getElementById('send-button');
        if (messageInput) messageInput.disabled = false;
        if (sendButton) sendButton.disabled = false;
        
        // Reset the stored data
        window.fallbackData = null;
        window.messageData = null;
    }
    
    /**
     * Handle the user confirming to use the fallback model
     */
    function handleUseFallback() {
        // Check if the user wants to save this preference
        const autoFallbackCheckbox = document.getElementById('auto-fallback-checkbox');
        if (autoFallbackCheckbox && autoFallbackCheckbox.checked) {
            saveAutoFallbackPreference(true);
        }
        
        closeModal();
        
        // If we have fallback data, send the message with the fallback model
        if (window.fallbackData && window.messageData) {
            // Create a copy of the message data with the fallback model
            const fallbackMessageData = { ...window.messageData };
            fallbackMessageData.model = window.fallbackData.fallback_model;
            
            // Call the original send message function with the fallback model
            if (typeof sendMessageToBackend === 'function') {
                sendMessageToBackend(
                    fallbackMessageData.message,
                    window.fallbackData.fallback_model,
                    document.querySelector('.typing-indicator')
                );
            }
        }
        
        // Reset the stored data
        window.fallbackData = null;
        window.messageData = null;
    }
    
    /**
     * Save the auto-fallback preference to the user settings
     */
    function saveAutoFallbackPreference(autoFallbackEnabled) {
        fetch('/api/user/chat_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                auto_fallback_enabled: autoFallbackEnabled
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Auto-fallback preference saved:', data);
        })
        .catch(error => {
            console.error('Error saving auto-fallback preference:', error);
        });
    }
});