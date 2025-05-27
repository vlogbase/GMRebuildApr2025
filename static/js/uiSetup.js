// Import utility functions
import { getCSRFToken } from './utils.js';
// Import API functions
import { fetchConversationsAPI, cleanupEmptyConversationsAPI } from './apiService.js';

// Define necessary elements early to avoid reference errors
export let messageInput;
export let sendButton;
export let newChatButton;
export let clearConversationsButton;
export let imageUploadButton;
export let imageUploadInput;
export let cameraButton;
export let captureButton;
export let switchCameraButton;
export let refreshPricesBtn;

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
    newChatButton = document.getElementById('new-chat-button');
    clearConversationsButton = document.getElementById('clear-conversations-button');
    imageUploadButton = document.getElementById('image-upload-button');
    imageUploadInput = document.getElementById('image-upload');
    cameraButton = document.getElementById('camera-button');
    captureButton = document.getElementById('capture-button');
    switchCameraButton = document.getElementById('switch-camera-button');
    refreshPricesBtn = document.getElementById('refresh-prices-btn');
    
    // Medium priority - important but can be slightly delayed
    setTimeout(() => {
        // Initialize other important features with a small delay
        if (messageInput) {
            messageInput.focus();
        }
    }, 50);
    
    // Lowest priority - can be deferred until after page is fully interactive
    if ('requestIdleCallback' in window) {
        requestIdleCallback(() => {
            // Run cleanup and non-essential initializations during browser idle time
            performIdleCleanup();
        }, { timeout: 2000 }); // 2-second timeout as fallback
    } else {
        // Fallback for browsers without requestIdleCallback
        setTimeout(() => {
            performIdleCleanup();
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
            cleanupEmptyConversationsAPI()
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
            cleanupEmptyConversationsAPI()
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