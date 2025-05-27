// Import utility functions
import { getCSRFToken } from './utils.js';

// Define necessary elements early to avoid reference errors
export let messageInput;
export let sendButton;

// Implement lazy loading for images to improve initial page load
export function setupLazyLoading() {
    if ('loading' in HTMLImageElement.prototype) {
        // Browser supports native lazy loading
        console.debug('Using native lazy loading for images');
        const images = document.querySelectorAll('img:not([loading])');
        images.forEach(img => {
            img.loading = 'lazy';
        });
    } else {
        // Fallback for browsers that don't support native lazy loading
        console.debug('Using IntersectionObserver for lazy loading images');
        const lazyImages = document.querySelectorAll('img[data-src]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.onload = () => img.classList.add('loaded');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            lazyImages.forEach(img => imageObserver.observe(img));
        } else {
            // No IntersectionObserver support - load all images immediately
            lazyImages.forEach(img => {
                img.src = img.dataset.src;
            });
        }
    }
}

// Set up prioritized loading for better performance
export function initializePrioritized() {
    // High priority - critical for immediate UI interaction
    setupLazyLoading();
    
    // Initialize basic UI elements
    messageInput = document.getElementById('user-input') || document.getElementById('message-input');
    sendButton = document.getElementById('send-button');
    
    // Medium priority - important but can be slightly delayed
    setTimeout(() => {
        // Initialize other important features with a small delay
        if (messageInput) {
            messageInput.focus();
        }
        
        // Setup essential event listeners for user interaction
        if (sendButton) {
            sendButton.addEventListener('click', sendMessage);
        }
        
        if (messageInput) {
            messageInput.addEventListener('keydown', handleMessageInputKeydown);
        }
    }, 50);
    
    // Lower priority - can be deferred until shortly after page loads
    setTimeout(() => {
        // Fetch model preferences only after the page is visibly loaded
        const modelSelector = document.getElementById('model-selector');
        if (modelSelector) {
            initializeModelSelector();
        }
    }, 100);
    
    // Lowest priority - can be deferred until after page is fully interactive
    if ('requestIdleCallback' in window) {
        requestIdleCallback(() => {
            // Run cleanup and non-essential initializations during browser idle time
            performIdleCleanup();
            
            // Fetch conversations list during idle time if user is authenticated
            const userIsLoggedIn = !!document.getElementById('logout-btn');
            if (userIsLoggedIn) {
                fetchConversations(false, true);
            }
        }, { timeout: 2000 }); // 2-second timeout as fallback
    } else {
        // Fallback for browsers without requestIdleCallback
        setTimeout(() => {
            performIdleCleanup();
            const userIsLoggedIn = !!document.getElementById('logout-btn');
            if (userIsLoggedIn) {
                fetchConversations(false, true);
            }
        }, 2000);
    }
}

// Utility function to perform empty conversation cleanup when browser is idle
// This prevents the cleanup from affecting initial page load performance
export function performIdleCleanup() {
    // Check if user is authenticated by looking for the logout button
    // Using this approach allows the function to work regardless of where it's called
    const userIsLoggedIn = !!document.getElementById('logout-btn');
    
    // Only run if user is authenticated
    if (!userIsLoggedIn) return;
    
    // Check if requestIdleCallback is supported
    if ('requestIdleCallback' in window) {
        requestIdleCallback(() => {
            console.log('Performing idle cleanup of empty conversations');
            fetch('/api/cleanup-empty-conversations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log(`Cleaned up ${data.deleted_count} empty conversations`);
                }
            })
            .catch(error => {
                console.error('Error during cleanup:', error);
            });
        });
    } else {
        // Fallback for browsers without requestIdleCallback
        setTimeout(() => {
            console.log('Performing delayed cleanup of empty conversations');
            fetch('/api/cleanup-empty-conversations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log(`Cleaned up ${data.deleted_count} empty conversations`);
                }
            })
            .catch(error => {
                console.error('Error during cleanup:', error);
            });
        }, 5000);
    }
}