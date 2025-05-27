// Message Actions and Interactions
// This file handles message-related actions like copying, sharing, rating, and citations

// Copy message text to clipboard
function copyMessageText(messageElement) {
    const messageContent = messageElement.querySelector('.message-content');
    if (!messageContent) {
        console.error('Message content not found');
        return;
    }
    
    const textToCopy = messageContent.textContent || messageContent.innerText;
    
    if (navigator.clipboard && window.isSecureContext) {
        // Modern clipboard API
        navigator.clipboard.writeText(textToCopy).then(() => {
            showNotification('Message copied to clipboard', 'success');
        }).catch(err => {
            console.error('Failed to copy text: ', err);
            fallbackCopyText(textToCopy);
        });
    } else {
        // Fallback for older browsers
        fallbackCopyText(textToCopy);
    }
}

// Fallback copy method for older browsers
function fallbackCopyText(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showNotification('Message copied to clipboard', 'success');
    } catch (err) {
        console.error('Fallback copy failed: ', err);
        showNotification('Failed to copy message', 'error');
    }
    
    document.body.removeChild(textArea);
}

// Share conversation
function shareConversation(messageElement) {
    const conversationId = getCurrentConversationId();
    if (!conversationId) {
        showNotification('No conversation to share', 'error');
        return;
    }
    
    // Create share link for the conversation
    fetch(`/conversation/${conversationId}/share`, {
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
        if (data.success && data.share_url) {
            // Copy share URL to clipboard
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(data.share_url).then(() => {
                    showNotification('Share link copied to clipboard', 'success');
                }).catch(() => {
                    showShareDialog(data.share_url);
                });
            } else {
                showShareDialog(data.share_url);
            }
        } else {
            showNotification('Failed to create share link', 'error');
        }
    })
    .catch(error => {
        console.error('Error sharing conversation:', error);
        showNotification('Failed to share conversation', 'error');
    });
}

// Show share dialog with URL
function showShareDialog(shareUrl) {
    const dialog = document.createElement('div');
    dialog.className = 'share-dialog';
    dialog.innerHTML = `
        <div class="share-dialog-content">
            <h3>Share Conversation</h3>
            <p>Copy this link to share your conversation:</p>
            <input type="text" value="${shareUrl}" readonly class="share-url-input">
            <div class="share-dialog-buttons">
                <button onclick="copyShareUrl('${shareUrl}')" class="copy-btn">Copy Link</button>
                <button onclick="closeShareDialog()" class="close-btn">Close</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(dialog);
    
    // Auto-select the URL for easy copying
    const urlInput = dialog.querySelector('.share-url-input');
    urlInput.select();
}

// Copy share URL from dialog
function copyShareUrl(url) {
    const urlInput = document.querySelector('.share-url-input');
    if (urlInput) {
        urlInput.select();
        try {
            document.execCommand('copy');
            showNotification('Share link copied to clipboard', 'success');
            closeShareDialog();
        } catch (err) {
            console.error('Failed to copy share URL:', err);
        }
    }
}

// Close share dialog
function closeShareDialog() {
    const dialog = document.querySelector('.share-dialog');
    if (dialog) {
        document.body.removeChild(dialog);
    }
}

// Rate a message
function rateMessage(messageElement, rating) {
    const messageId = messageElement.getAttribute('data-message-id');
    if (!messageId) {
        console.error('Message ID not found');
        return;
    }
    
    // Send rating to server
    fetch('/api/rate-message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message_id: messageId,
            rating: rating,
            csrf_token: window.utils ? window.utils.getCSRFToken() : null
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI to show rating
            updateMessageRatingUI(messageElement, rating);
            showNotification(`Message rated: ${rating === 1 ? 'Good' : 'Poor'}`, 'success');
        } else {
            showNotification('Failed to rate message', 'error');
        }
    })
    .catch(error => {
        console.error('Error rating message:', error);
        showNotification('Failed to rate message', 'error');
    });
}

// Update message rating UI
function updateMessageRatingUI(messageElement, rating) {
    const ratingButtons = messageElement.querySelectorAll('.rating-btn');
    ratingButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-rating') == rating) {
            btn.classList.add('active');
        }
    });
}

// Add Perplexity citations to message
function addPerplexityCitationsToMessage(messageElement, citations) {
    if (!citations || citations.length === 0) return;
    
    const messageContent = messageElement.querySelector('.message-content');
    if (!messageContent) return;
    
    // Create citations container
    const citationsContainer = document.createElement('div');
    citationsContainer.className = 'perplexity-citations';
    citationsContainer.innerHTML = '<h4>Sources:</h4>';
    
    const citationsList = document.createElement('ul');
    citationsList.className = 'citations-list';
    
    citations.forEach((citation, index) => {
        const citationItem = document.createElement('li');
        citationItem.className = 'citation-item';
        citationItem.innerHTML = `
            <a href="${citation.url}" target="_blank" rel="noopener noreferrer" class="citation-link">
                <span class="citation-number">${index + 1}</span>
                <span class="citation-title">${citation.title || citation.url}</span>
            </a>
        `;
        citationsList.appendChild(citationItem);
    });
    
    citationsContainer.appendChild(citationsList);
    messageElement.appendChild(citationsContainer);
}

// Get current conversation ID
function getCurrentConversationId() {
    // Try to get from window variable first
    if (window.chat && window.chat.getCurrentConversationId) {
        return window.chat.getCurrentConversationId();
    }
    
    // Fallback to URL parsing
    const path = window.location.pathname;
    const match = path.match(/\/conversation\/(\d+)/);
    return match ? match[1] : null;
}

// Show notification to user
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.add('fade-out');
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }
    }, 3000);
}

// Initialize message actions
function initializeMessageActions() {
    // Set up event delegation for message action buttons
    document.addEventListener('click', function(e) {
        const messageElement = e.target.closest('.message');
        if (!messageElement) return;
        
        // Copy button
        if (e.target.closest('.copy-btn')) {
            e.preventDefault();
            copyMessageText(messageElement);
        }
        
        // Share button
        if (e.target.closest('.share-btn')) {
            e.preventDefault();
            shareConversation(messageElement);
        }
        
        // Rating buttons
        if (e.target.closest('.rating-btn')) {
            e.preventDefault();
            const rating = parseInt(e.target.closest('.rating-btn').getAttribute('data-rating'));
            rateMessage(messageElement, rating);
        }
    });
    
    console.log('Message actions initialized');
}

// Make functions globally available
window.copyMessageText = copyMessageText;
window.shareConversation = shareConversation;
window.rateMessage = rateMessage;
window.addPerplexityCitationsToMessage = addPerplexityCitationsToMessage;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeMessageActions();
});

// Export for use by other modules
window.messageActions = {
    copyMessageText,
    shareConversation,
    rateMessage,
    addPerplexityCitationsToMessage
};