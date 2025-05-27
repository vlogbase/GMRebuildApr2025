// File Upload and Paste Handling for GloriaMundo Chat

// Global variables for upload state
let isUploadingFile = false;
let currentImageUrl = null;
let attachedImageUrl = null;

// Setup clipboard paste event listener for the entire document
function initializePasteHandler() {
    document.addEventListener('paste', handlePaste);
}

// Paste handler function
function handlePaste(e) {
    // Only handle paste if the chat input area is focused
    const activeElement = document.activeElement;
    const chatInput = document.getElementById('user-input');
    
    if (activeElement !== chatInput && !activeElement.closest('.chat-input-container')) {
        return; // Not focused on chat input, ignore paste event
    }
    
    // Check if clipboard contains images
    const items = e.clipboardData.items;
    for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf('image') !== -1) {
            console.log('Image found in clipboard');
            
            // Check premium access before handling the pasted image
            if (typeof checkPremiumAccess === 'function' && !checkPremiumAccess('image_upload')) {
                // Prevent default paste behavior
                e.preventDefault();
                return;
            }
            
            // Get the image as a file
            const file = items[i].getAsFile();
            if (!file) continue;
            
            // Prevent the default paste behavior
            e.preventDefault();
            
            // Set upload flag to true and disable send button
            isUploadingFile = true;
            if (typeof updateSendButtonState === 'function') {
                updateSendButtonState();
            }
            
            // Show upload indicator
            const uploadIndicator = document.getElementById('upload-indicator') || createUploadIndicator();
            uploadIndicator.style.display = 'block';
            uploadIndicator.textContent = 'Uploading file from clipboard...';
            
            // Create FormData and upload the image
            const formData = new FormData();
            formData.append('file', file, 'clipboard-image.png');
            
            // Get the currently selected model
            const activeModel = document.querySelector('.model-btn.active');
            const modelId = activeModel ? activeModel.dataset.modelId : null;
            
            // Add model parameter if available
            let uploadUrl = '/upload_image';
            if (modelId) {
                uploadUrl += `?model=${encodeURIComponent(modelId)}`;
            }
            
            fetch(uploadUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Set upload flag to false and re-enable send button
                isUploadingFile = false;
                if (typeof updateSendButtonState === 'function') {
                    updateSendButtonState();
                }
                
                if (data.success && data.image_url) {
                    // Set the current image URL for sending with the message
                    currentImageUrl = data.image_url;
                    attachedImageUrl = data.image_url;
                    
                    // Show the image preview
                    if (typeof showImagePreview === 'function') {
                        showImagePreview(data.image_url);
                    }
                    
                    // Update upload indicator
                    uploadIndicator.textContent = 'Image ready to send!';
                    setTimeout(() => {
                        uploadIndicator.style.display = 'none';
                    }, 1500);
                } else {
                    uploadIndicator.textContent = 'Error uploading image: ' + (data.error || 'Unknown error');
                    uploadIndicator.style.color = 'red';
                    setTimeout(() => {
                        uploadIndicator.style.display = 'none';
                        uploadIndicator.style.color = '';
                    }, 3000);
                }
            })
            .catch(error => {
                console.error('Error uploading image:', error);
                
                // Set upload flag to false and re-enable send button
                isUploadingFile = false;
                if (typeof updateSendButtonState === 'function') {
                    updateSendButtonState();
                }
                
                uploadIndicator.textContent = 'Error uploading image';
                uploadIndicator.style.color = 'red';
                setTimeout(() => {
                    uploadIndicator.style.display = 'none';
                    uploadIndicator.style.color = '';
                }, 3000);
            });
            
            // Only process the first image
            break;
        }
    }
}

// Create upload indicator if it doesn't exist
function createUploadIndicator() {
    // Check if it already exists
    let indicator = document.getElementById('upload-indicator');
    if (indicator) return indicator;
    
    // Create new indicator with the appropriate styling
    indicator = document.createElement('div');
    indicator.id = 'upload-indicator';
    indicator.className = 'upload-indicator';
    indicator.style.display = 'none';
    indicator.style.transition = 'opacity 0.5s ease';
    
    // Add it before the chat input
    const chatInputContainer = document.querySelector('.chat-input-container');
    if (chatInputContainer) {
        chatInputContainer.insertBefore(indicator, chatInputContainer.firstChild);
    } else {
        // Fallback - add to body
        document.body.appendChild(indicator);
        console.warn('Chat input container not found, added upload indicator to body');
    }
    
    return indicator;
}

// Make functions and variables globally available
window.isUploadingFile = isUploadingFile;
window.currentImageUrl = currentImageUrl;
window.attachedImageUrl = attachedImageUrl;
window.handlePaste = handlePaste;
window.createUploadIndicator = createUploadIndicator;
window.initializePasteHandler = initializePasteHandler;