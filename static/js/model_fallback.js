/**
 * Model Fallback Dialog Handler
 * 
 * This script handles the model fallback confirmation dialog when
 * a requested AI model is unavailable and needs fallback to another model.
 */

let currentFallbackData = null;
let pendingChatRequest = null;

/**
 * Show the model fallback confirmation dialog
 * @param {Object} fallbackData - Data about the fallback model
 * @param {Object} chatRequest - The original chat request
 */
function showFallbackModal(fallbackData, chatRequest) {
    console.log('Showing fallback modal', fallbackData);
    
    // Store the data for later use
    currentFallbackData = fallbackData;
    pendingChatRequest = chatRequest;
    
    // Create modal if it doesn't exist
    let modal = document.getElementById('model-fallback-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'model-fallback-modal';
        modal.className = 'fallback-modal';
        modal.innerHTML = `
            <div class="fallback-modal-content">
                <div class="fallback-modal-header">
                    <h3>Model Unavailable</h3>
                </div>
                <div class="fallback-modal-body">
                    <p id="fallback-message">The requested model is currently unavailable.</p>
                </div>
                <div class="fallback-modal-footer">
                    <button id="cancel-fallback" class="fallback-btn fallback-btn-secondary">Cancel</button>
                    <button id="use-fallback" class="fallback-btn fallback-btn-primary">Use Alternative</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Set up event listeners
        document.getElementById('cancel-fallback').addEventListener('click', cancelFallback);
        document.getElementById('use-fallback').addEventListener('click', useFallback);
    }
    
    // Update the message
    const messageElement = document.getElementById('fallback-message');
    messageElement.innerHTML = `
        <strong>${fallbackData.requested_model}</strong> is not currently available. 
        <br><br>
        Would you like to use <strong>${fallbackData.fallback_model}</strong> instead?
    `;
    
    // Show the modal
    modal.style.display = 'block';
}

/**
 * Cancel the fallback and return the message to the input box
 */
function cancelFallback() {
    if (!pendingChatRequest) return;
    
    // Close the modal
    const modal = document.getElementById('model-fallback-modal');
    if (modal) {
        modal.style.display = 'none';
    }
    
    // Put the message back in the input box
    const chatInput = document.getElementById('chat-input');
    if (chatInput && pendingChatRequest.message) {
        chatInput.value = pendingChatRequest.message;
        chatInput.focus();
    }
    
    // Clear the stored data
    currentFallbackData = null;
    pendingChatRequest = null;
    
    // Update the model selector to show the text "Model Unavailable"
    const modelSelector = document.querySelector('.model-selector select, #model-select');
    if (modelSelector) {
        const option = Array.from(modelSelector.options).find(
            opt => opt.value === currentFallbackData?.original_model_id
        );
        
        if (option) {
            option.text = option.text + ' (Unavailable)';
        }
    }
}

/**
 * Use the fallback model
 */
function useFallback() {
    if (!pendingChatRequest || !currentFallbackData) return;
    
    console.log('Using fallback model', currentFallbackData.fallback_model_id);
    
    // Close the modal
    const modal = document.getElementById('model-fallback-modal');
    if (modal) {
        modal.style.display = 'none';
    }
    
    // Modify the request to use the fallback model
    const updatedRequest = {...pendingChatRequest};
    updatedRequest.model = currentFallbackData.fallback_model_id;
    
    // Send the request
    sendMessageToBackend(updatedRequest);
    
    // Clear the stored data
    currentFallbackData = null;
    pendingChatRequest = null;
}

/**
 * Check user preferences for auto-fallback
 * @returns {Promise<boolean>} Whether auto-fallback is enabled
 */
async function isAutoFallbackEnabled() {
    try {
        const response = await fetch('/api/user/chat_settings');
        const data = await response.json();
        
        if (data.success && data.settings) {
            return !!data.settings.auto_fallback_enabled;
        }
        return false;
    } catch (error) {
        console.error('Error checking auto-fallback setting:', error);
        return false;
    }
}

/**
 * Process a fallback event from the server
 * @param {Object} eventData - The event data
 * @param {Object} originalRequest - The original chat request
 */
async function handleModelFallback(eventData, originalRequest) {
    console.log('Handling model fallback event', eventData);
    
    // Check if auto-fallback is enabled
    const autoFallbackEnabled = await isAutoFallbackEnabled();
    
    if (autoFallbackEnabled) {
        console.log('Auto-fallback enabled, using fallback model automatically');
        // Modify the request to use the fallback model
        const updatedRequest = {...originalRequest};
        updatedRequest.model = eventData.fallback_model_id;
        
        // Send the request
        sendMessageToBackend(updatedRequest);
    } else {
        // Show the confirmation dialog
        showFallbackModal(eventData, originalRequest);
    }
}

// Add some minimal CSS for the modal
const style = document.createElement('style');
style.textContent = `
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
    border: 1px solid var(--border-color, #888);
    width: 80%;
    max-width: 500px;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.fallback-modal-header {
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border-color, #eee);
}

.fallback-modal-header h3 {
    margin: 0;
    color: var(--text-color, #333);
}

.fallback-modal-body {
    padding: 15px 0;
    color: var(--text-color, #333);
}

.fallback-modal-footer {
    padding-top: 10px;
    border-top: 1px solid var(--border-color, #eee);
    display: flex;
    justify-content: flex-end;
}

.fallback-btn {
    padding: 8px 16px;
    margin-left: 10px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.fallback-btn-primary {
    background-color: var(--primary-color, #007bff);
    color: white;
}

.fallback-btn-secondary {
    background-color: var(--secondary-color, #6c757d);
    color: white;
}
`;

document.head.appendChild(style);

// Export functions for use in other scripts
window.showFallbackModal = showFallbackModal;
window.handleModelFallback = handleModelFallback;
window.isAutoFallbackEnabled = isAutoFallbackEnabled;