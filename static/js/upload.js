// Upload Module
// Handles file uploads for images and PDFs

// Global variables for upload functionality
let selectedFiles = [];
let currentUploadedFile = null;

// Initialize upload functionality
function initializeUpload() {
    setupImageUploadButton();
    setupFileUploadInput();
    setupUploadIndicator();
    
    // Setup drag and drop functionality
    setupDragAndDrop();
}

// Setup image upload button functionality
function setupImageUploadButton() {
    const imageUploadButton = document.getElementById('imageUploadButton');
    const fileUploadInput = document.getElementById('fileUpload');
    
    if (imageUploadButton && fileUploadInput) {
        imageUploadButton.addEventListener('click', function() {
            // Disable the button temporarily to prevent multiple clicks
            this.disabled = true;
            
            // Trigger file input
            fileUploadInput.click();
            
            // Re-enable after a short delay
            setTimeout(() => {
                this.disabled = false;
            }, 500);
        });
    }
}

// Setup file upload input functionality
function setupFileUploadInput() {
    const fileUploadInput = document.getElementById('fileUpload');
    
    if (fileUploadInput) {
        fileUploadInput.addEventListener('change', function() {
            const files = this.files;
            if (files && files.length > 0) {
                const file = files[0];
                handleFileUpload(file);
            }
        });
    }
}

// Handle file upload for both images and PDFs
async function handleFileUpload(file) {
    // Check if user is authenticated
    if (window.auth && !window.auth.isLoggedIn) {
        if (window.showLoginPrompt) {
            window.showLoginPrompt();
        }
        return;
    }
    
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
        if (window.utils) {
            window.utils.showToast('Please select an image (JPEG, PNG, GIF) or PDF file.', 'error');
        }
        return;
    }
    
    // Show upload indicator
    showUploadIndicator('Uploading file...');
    
    try {
        const conversationId = window.chat ? window.chat.getCurrentConversationId() : null;
        const result = await uploadFile(file, conversationId);
        
        if (result.success) {
            currentUploadedFile = result;
            handleUploadSuccess(result);
        } else {
            handleUploadError(result.error || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        handleUploadError('Network error during upload');
    }
}

// Upload file to server
async function uploadFile(file, conversationId) {
    const formData = new FormData();
    formData.append('file', file);
    
    if (conversationId) {
        formData.append('conversation_id', conversationId);
    }
    
    // Add CSRF token if available
    const csrfToken = window.utils ? window.utils.getCSRFToken() : null;
    if (csrfToken) {
        formData.append('csrf_token', csrfToken);
    }
    
    const response = await fetch('/upload_file', {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    // Add file type information for the UI
    if (result.file_type === 'pdf') {
        result.isPdf = true;
    } else if (result.file_type === 'image') {
        result.isImage = true;
    }
    
    return result;
}

// Handle successful upload
function handleUploadSuccess(data) {
    if (data.isPdf) {
        // Handle PDF upload
        showPdfPreview(data);
        updateUploadIndicator('PDF ready to send!');
        
        // Set default question for PDFs
        const userInput = document.getElementById('user-input');
        if (userInput && !userInput.value.trim()) {
            userInput.value = `What's in this document?`;
        }
    } else if (data.isImage) {
        // Handle image upload
        showImagePreview(data.image_url);
        updateUploadIndicator('Image ready to send!');
        
        // Set default question for images
        const userInput = document.getElementById('user-input');
        if (userInput && !userInput.value.trim()) {
            userInput.value = `What's in this image?`;
        }
    }
    
    // Enable the send button
    const sendButton = document.getElementById('send-button');
    if (sendButton) {
        sendButton.disabled = false;
    }
    
    // Hide upload indicator after delay
    setTimeout(() => {
        hideUploadIndicator();
    }, 1500);
}

// Handle upload error
function handleUploadError(errorMessage) {
    updateUploadIndicator(`Error: ${errorMessage}`, 'error');
    
    setTimeout(() => {
        hideUploadIndicator();
    }, 3000);
    
    if (window.utils) {
        window.utils.showToast(errorMessage, 'error');
    }
}

// Show image preview
function showImagePreview(imageUrl) {
    const existingPreview = document.querySelector('.image-preview-container');
    if (existingPreview) {
        existingPreview.remove();
    }
    
    const chatContainer = document.getElementById('chat-container') || document.querySelector('.chat-container');
    if (!chatContainer) return;
    
    const previewContainer = document.createElement('div');
    previewContainer.className = 'image-preview-container';
    previewContainer.innerHTML = `
        <div class="image-preview">
            <img src="${imageUrl}" alt="Uploaded image" style="max-width: 200px; max-height: 200px; border-radius: 8px;">
            <button type="button" class="remove-image" onclick="removeImagePreview()">&times;</button>
        </div>
    `;
    
    chatContainer.appendChild(previewContainer);
}

// Show PDF preview
function showPdfPreview(data) {
    const existingPreview = document.querySelector('.pdf-preview-container');
    if (existingPreview) {
        existingPreview.remove();
    }
    
    const chatContainer = document.getElementById('chat-container') || document.querySelector('.chat-container');
    if (!chatContainer) return;
    
    const previewContainer = document.createElement('div');
    previewContainer.className = 'pdf-preview-container';
    previewContainer.innerHTML = `
        <div class="pdf-preview" style="border: 2px solid rgba(76, 217, 100, 0.5); background: rgba(76, 217, 100, 0.1); padding: 15px; border-radius: 8px; margin: 10px 0;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" fill="#4cd964"/>
                    <polyline points="14,2 14,8 20,8" fill="#4cd964"/>
                    <line x1="16" y1="13" x2="8" y2="13" stroke="white" stroke-width="2"/>
                    <line x1="16" y1="17" x2="8" y2="17" stroke="white" stroke-width="2"/>
                    <polyline points="10,9 9,9 8,9" stroke="white" stroke-width="2"/>
                </svg>
                <div>
                    <div style="font-weight: bold; color: #4cd964;">${data.filename || 'PDF Document'}</div>
                    <div style="font-size: 0.9em; color: #666;">Ready to analyze</div>
                </div>
                <button type="button" class="remove-pdf" onclick="removePdfPreview()" style="margin-left: auto; background: none; border: none; font-size: 18px; cursor: pointer;">&times;</button>
            </div>
        </div>
    `;
    
    chatContainer.appendChild(previewContainer);
}

// Remove image preview
function removeImagePreview() {
    const preview = document.querySelector('.image-preview-container');
    if (preview) {
        preview.remove();
    }
    currentUploadedFile = null;
    hideUploadIndicator();
}

// Remove PDF preview
function removePdfPreview() {
    const preview = document.querySelector('.pdf-preview-container');
    if (preview) {
        preview.remove();
    }
    currentUploadedFile = null;
    hideUploadIndicator();
}

// Setup upload indicator
function setupUploadIndicator() {
    if (!document.getElementById('upload-indicator')) {
        const indicator = document.createElement('div');
        indicator.id = 'upload-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #007bff;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            display: none;
            z-index: 1000;
            animation: fadein 0.3s;
        `;
        document.body.appendChild(indicator);
    }
}

// Show upload indicator
function showUploadIndicator(message) {
    const indicator = document.getElementById('upload-indicator');
    if (indicator) {
        indicator.textContent = message;
        indicator.style.display = 'block';
        indicator.style.background = '#007bff';
    }
}

// Update upload indicator
function updateUploadIndicator(message, type = 'success') {
    const indicator = document.getElementById('upload-indicator');
    if (indicator) {
        indicator.textContent = message;
        indicator.style.background = type === 'error' ? '#dc3545' : '#28a745';
    }
}

// Hide upload indicator
function hideUploadIndicator() {
    const indicator = document.getElementById('upload-indicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

// Setup drag and drop functionality
function setupDragAndDrop() {
    const chatContainer = document.getElementById('chat-container') || document.querySelector('.chat-container');
    if (!chatContainer) return;
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        chatContainer.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        chatContainer.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        chatContainer.addEventListener(eventName, unhighlight, false);
    });
    
    // Handle dropped files
    chatContainer.addEventListener('drop', handleDrop, false);
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight(e) {
        chatContainer.classList.add('drag-over');
    }
    
    function unhighlight(e) {
        chatContainer.classList.remove('drag-over');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    }
}

// Export upload functions
window.upload = {
    initializeUpload,
    handleFileUpload,
    removeImagePreview,
    removePdfPreview,
    getCurrentUploadedFile: () => currentUploadedFile
};

// Make removal functions globally available
window.removeImagePreview = removeImagePreview;
window.removePdfPreview = removePdfPreview;

// Initialize upload functionality when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeUpload();
});