/**
 * Model Fallback Confirmation Dialog
 * Handles showing a confirmation dialog when a model is unavailable
 * and provides options to accept or reject the fallback model.
 */

// Keep track of the pending message and models during fallback
let pendingFallbackMessage = null;
let pendingOriginalModel = null;
let pendingFallbackModel = null;

/**
 * Initialize the model fallback dialog in the DOM
 * Creates the dialog HTML structure if it doesn't exist
 */
function initFallbackDialog() {
    // Check if dialog already exists
    if (document.getElementById('fallback-dialog')) {
        return;
    }
    
    // Create the dialog HTML structure
    const overlay = document.createElement('div');
    overlay.id = 'fallback-overlay';
    overlay.className = 'fallback-overlay';
    
    const dialog = document.createElement('div');
    dialog.id = 'fallback-dialog';
    dialog.className = 'fallback-dialog';
    
    // Dialog header
    const header = document.createElement('div');
    header.className = 'fallback-dialog-header';
    header.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
    
    const title = document.createElement('h2');
    title.className = 'fallback-dialog-title';
    title.textContent = 'Model Unavailable';
    header.appendChild(title);
    
    // Dialog content
    const content = document.createElement('div');
    content.className = 'fallback-dialog-content';
    content.innerHTML = 'The model you selected is currently unavailable. Would you like to use an alternative model instead?';
    
    // Model info container
    const modelInfo = document.createElement('div');
    modelInfo.className = 'fallback-model-info';
    
    // Requested model row
    const requestedRow = document.createElement('div');
    requestedRow.className = 'fallback-model-row';
    
    const requestedLabel = document.createElement('div');
    requestedLabel.className = 'fallback-model-label';
    requestedLabel.textContent = 'Requested:';
    
    const requestedValue = document.createElement('div');
    requestedValue.className = 'fallback-model-value fallback-requested';
    requestedValue.id = 'fallback-requested-model';
    requestedValue.textContent = '...';
    
    requestedRow.appendChild(requestedLabel);
    requestedRow.appendChild(requestedValue);
    
    // Alternative model row
    const alternativeRow = document.createElement('div');
    alternativeRow.className = 'fallback-model-row';
    
    const alternativeLabel = document.createElement('div');
    alternativeLabel.className = 'fallback-model-label';
    alternativeLabel.textContent = 'Alternative:';
    
    const alternativeValue = document.createElement('div');
    alternativeValue.className = 'fallback-model-value fallback-alternative';
    alternativeValue.id = 'fallback-alternative-model';
    alternativeValue.textContent = '...';
    
    alternativeRow.appendChild(alternativeLabel);
    alternativeRow.appendChild(alternativeValue);
    
    // Add rows to model info
    modelInfo.appendChild(requestedRow);
    modelInfo.appendChild(alternativeRow);
    
    // Dialog actions (buttons)
    const actions = document.createElement('div');
    actions.className = 'fallback-dialog-actions';
    
    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'fallback-btn fallback-btn-cancel';
    cancelBtn.id = 'fallback-cancel-btn';
    cancelBtn.textContent = 'No, Cancel';
    cancelBtn.setAttribute('aria-label', 'Cancel model fallback');
    
    const confirmBtn = document.createElement('button');
    confirmBtn.className = 'fallback-btn fallback-btn-confirm';
    confirmBtn.id = 'fallback-confirm-btn';
    confirmBtn.textContent = 'Yes, Use Alternative';
    confirmBtn.setAttribute('aria-label', 'Accept model fallback');
    
    actions.appendChild(cancelBtn);
    actions.appendChild(confirmBtn);
    
    // Assemble dialog
    dialog.appendChild(header);
    dialog.appendChild(content);
    dialog.appendChild(modelInfo);
    dialog.appendChild(actions);
    
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
    
    // Add event listeners for the buttons
    cancelBtn.addEventListener('click', onFallbackCancel);
    confirmBtn.addEventListener('click', onFallbackConfirm);
    
    // Add ESC key handler to close dialog
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && document.getElementById('fallback-overlay').classList.contains('visible')) {
            onFallbackCancel();
        }
    });
    
    // Click outside dialog to cancel (optional)
    overlay.addEventListener('click', function(event) {
        if (event.target === overlay) {
            onFallbackCancel();
        }
    });
    
    console.log('Model fallback dialog initialized');
}

/**
 * Show the fallback confirmation dialog
 * @param {string} requestedModel - The name of the requested model
 * @param {string} fallbackModel - The name of the suggested fallback model
 * @param {string} originalModelId - The ID of the original model
 * @param {string} fallbackModelId - The ID of the fallback model
 * @param {string} messageText - The message text to send
 */
function showFallbackDialog(requestedModel, fallbackModel, originalModelId, fallbackModelId, messageText) {
    // Store the pending message for later
    pendingFallbackMessage = messageText;
    pendingOriginalModel = originalModelId;
    pendingFallbackModel = fallbackModelId;
    
    // Set the model names in the dialog
    document.getElementById('fallback-requested-model').textContent = requestedModel;
    document.getElementById('fallback-alternative-model').textContent = fallbackModel;
    
    // Show the dialog
    document.getElementById('fallback-overlay').classList.add('visible');
    
    // Focus the confirm button for accessibility
    setTimeout(() => {
        document.getElementById('fallback-confirm-btn').focus();
    }, 100);
    
    console.log(`Showing fallback dialog: ${requestedModel} -> ${fallbackModel}`);
}

/**
 * Handle clicking the "Cancel" button in the fallback dialog
 * This leaves the message in the input field for the user to try again
 */
function onFallbackCancel() {
    console.log('Fallback canceled by user');
    
    // Hide the dialog
    document.getElementById('fallback-overlay').classList.remove('visible');
    
    // Keep the message in the input field for the user to try again
    if (pendingFallbackMessage && document.getElementById('chat-input')) {
        document.getElementById('chat-input').value = pendingFallbackMessage;
        document.getElementById('chat-input').focus();
    }
    
    // Reset pending state
    pendingFallbackMessage = null;
    pendingOriginalModel = null;
    pendingFallbackModel = null;
}

/**
 * Handle clicking the "Confirm" button in the fallback dialog
 * This sends the message with the fallback model
 */
function onFallbackConfirm() {
    console.log('Fallback confirmed by user');
    
    // Hide the dialog
    document.getElementById('fallback-overlay').classList.remove('visible');
    
    // Send the message with the fallback model
    if (pendingFallbackMessage && pendingFallbackModel) {
        console.log(`Sending message with fallback model: ${pendingFallbackModel}`);
        
        // Use the external sendChatMessageWithFallback function defined in script.js
        // This assumes that function exists
        if (typeof sendChatMessageWithFallback === 'function') {
            sendChatMessageWithFallback(pendingFallbackMessage, pendingFallbackModel);
        } else {
            console.error('sendChatMessageWithFallback function not found');
            // Fallback to regular send if the function doesn't exist
            if (typeof sendChatMessage === 'function') {
                sendChatMessage(pendingFallbackMessage, pendingFallbackModel);
            }
        }
    }
    
    // Reset pending state
    pendingFallbackMessage = null;
    pendingOriginalModel = null;
    pendingFallbackModel = null;
}

/**
 * Check if automatic fallback is enabled for the current user
 * @returns {Promise<boolean>} Whether automatic fallback is enabled
 */
async function isAutoFallbackEnabled() {
    try {
        const response = await fetch('/api/fallback/check_preference');
        const data = await response.json();
        return data.auto_fallback_enabled === true;
    } catch (error) {
        console.error('Error checking fallback preference:', error);
        return false; // Default to disabled if we can't check
    }
}

/**
 * Handle a model fallback situation
 * @param {Object} fallbackData - Data about the fallback situation
 * @param {string} messageText - The message text to send
 * @returns {Promise<boolean>} Whether the fallback was handled automatically
 */
async function handleModelFallback(fallbackData, messageText) {
    console.log('Handling model fallback', fallbackData);
    
    // Initialize the dialog if it doesn't exist
    initFallbackDialog();
    
    // Check if auto-fallback is enabled for this user
    const autoFallbackEnabled = await isAutoFallbackEnabled();
    
    if (autoFallbackEnabled) {
        console.log('Auto-fallback is enabled, sending with fallback model automatically');
        // Automatically use the fallback model
        if (typeof sendChatMessageWithFallback === 'function') {
            sendChatMessageWithFallback(messageText, fallbackData.fallback_model_id);
            return true;
        }
    } else {
        // Show the confirmation dialog
        showFallbackDialog(
            fallbackData.requested_model,
            fallbackData.fallback_model,
            fallbackData.original_model_id,
            fallbackData.fallback_model_id,
            messageText
        );
    }
    
    return false;
}

// Initialize the dialog when the script loads
document.addEventListener('DOMContentLoaded', initFallbackDialog);