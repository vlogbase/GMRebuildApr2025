// Specialized Functions
// This file contains various specialized functions like paste handling, login prompts, and utilities

// Handle paste events for images and text
function handlePaste(e) {
    const items = e.clipboardData.items;
    
    for (let i = 0; i < items.length; i++) {
        const item = items[i];
        
        // Handle pasted images
        if (item.type.indexOf('image') !== -1) {
            e.preventDefault();
            const blob = item.getAsFile();
            
            if (blob && window.upload && window.upload.handleImageFile) {
                window.upload.handleImageFile(blob);
            } else if (blob && window.documentManager) {
                const imageUrl = URL.createObjectURL(blob);
                window.documentManager.addImageToAttachments(imageUrl, 'pasted-image.png', blob.size);
            }
            
            console.log('Pasted image detected and processed');
            return;
        }
        
        // Handle pasted text
        if (item.type === 'text/plain') {
            item.getAsString(text => {
                const messageInput = document.getElementById('message-input');
                if (messageInput) {
                    const currentText = messageInput.value;
                    const cursorPos = messageInput.selectionStart;
                    const newText = currentText.slice(0, cursorPos) + text + currentText.slice(messageInput.selectionEnd);
                    messageInput.value = newText;
                    messageInput.setSelectionRange(cursorPos + text.length, cursorPos + text.length);
                    
                    // Trigger auto-resize if available
                    if (window.autoResizeTextarea) {
                        window.autoResizeTextarea();
                    }
                }
            });
        }
    }
}

// Create upload indicator for file operations
function createUploadIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'upload-indicator';
    indicator.innerHTML = `
        <div class="upload-spinner"></div>
        <span class="upload-text">Processing file...</span>
    `;
    
    return indicator;
}

// Show upload indicator
function showUploadIndicator(text = 'Processing file...') {
    const existingIndicator = document.querySelector('.upload-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    const indicator = createUploadIndicator();
    if (text) {
        indicator.querySelector('.upload-text').textContent = text;
    }
    
    document.body.appendChild(indicator);
    return indicator;
}

// Hide upload indicator
function hideUploadIndicator() {
    const indicator = document.querySelector('.upload-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Refresh model prices from server
function refreshModelPrices() {
    console.log('Refreshing model prices...');
    
    return fetch('/api/refresh-prices', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            csrf_token: window.utils ? window.utils.getCSRFToken() : null
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Model prices refreshed successfully');
            
            // Reload models with updated pricing
            if (window.models && window.models.loadModelsFromServer) {
                window.models.loadModelsFromServer();
            }
            
            showNotification('Model prices updated successfully', 'success');
        } else {
            console.error('Failed to refresh model prices');
            showNotification('Failed to refresh model prices', 'error');
        }
    })
    .catch(error => {
        console.error('Error refreshing model prices:', error);
        showNotification('Error refreshing model prices', 'error');
    });
}

// Filter model list based on search term
function filterModelList(searchTerm) {
    const modelList = document.getElementById('model-list');
    if (!modelList) return;
    
    const modelItems = modelList.querySelectorAll('.model-item');
    const term = searchTerm.toLowerCase();
    
    modelItems.forEach(item => {
        const modelName = item.querySelector('.model-name');
        if (modelName) {
            const nameText = modelName.textContent.toLowerCase();
            const modelId = item.getAttribute('data-model-id') || '';
            
            const matches = nameText.includes(term) || modelId.toLowerCase().includes(term);
            item.style.display = matches ? 'block' : 'none';
        }
    });
}

// Show login prompt for non-authenticated users
window.showLoginPrompt = function() {
    const existingPrompt = document.querySelector('.login-prompt-overlay');
    if (existingPrompt) return;
    
    const overlay = document.createElement('div');
    overlay.className = 'login-prompt-overlay';
    overlay.innerHTML = `
        <div class="login-prompt-modal">
            <div class="login-prompt-content">
                <h3>Sign in to continue</h3>
                <p>You need to sign in to access premium features and save your conversations.</p>
                <div class="login-buttons">
                    <button onclick="window.location.href='/login'" class="login-btn primary">
                        <i class="fab fa-google"></i> Sign in with Google
                    </button>
                    <button onclick="hideLoginPrompt()" class="login-btn secondary">
                        Continue as Guest
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';
};

// Hide login prompt
function hideLoginPrompt() {
    const overlay = document.querySelector('.login-prompt-overlay');
    if (overlay) {
        document.body.removeChild(overlay);
        document.body.style.overflow = '';
    }
}

// Show notification (reusable utility)
function showNotification(message, type = 'info') {
    // Use message actions notification if available
    if (window.messageActions && window.messageActions.showNotification) {
        return window.messageActions.showNotification(message, type);
    }
    
    // Fallback notification system
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style the notification
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '12px 16px',
        borderRadius: '4px',
        color: 'white',
        fontSize: '14px',
        zIndex: '10000',
        maxWidth: '300px'
    });
    
    // Set background color based on type
    const colors = {
        success: '#4CAF50',
        error: '#f44336',
        warning: '#ff9800',
        info: '#2196F3'
    };
    notification.style.backgroundColor = colors[type] || colors.info;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.3s';
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }
    }, 3000);
}

// Initialize specialized functions
function initializeSpecialized() {
    // Set up paste event listener
    document.addEventListener('paste', handlePaste);
    
    // Set up model search if it exists
    const modelSearch = document.getElementById('model-search');
    if (modelSearch) {
        modelSearch.addEventListener('input', (e) => {
            filterModelList(e.target.value);
        });
    }
    
    // Set up refresh prices button
    const refreshButton = document.getElementById('refresh-prices-btn');
    if (refreshButton) {
        refreshButton.addEventListener('click', refreshModelPrices);
    }
    
    console.log('Specialized functions initialized');
}

// Make functions globally available
window.handlePaste = handlePaste;
window.createUploadIndicator = createUploadIndicator;
window.showUploadIndicator = showUploadIndicator;
window.hideUploadIndicator = hideUploadIndicator;
window.refreshModelPrices = refreshModelPrices;
window.filterModelList = filterModelList;
window.hideLoginPrompt = hideLoginPrompt;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeSpecialized();
});

// Export for use by other modules
window.specialized = {
    handlePaste,
    createUploadIndicator,
    refreshModelPrices,
    filterModelList,
    showLoginPrompt: window.showLoginPrompt,
    hideLoginPrompt
};