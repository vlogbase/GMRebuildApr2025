// Utility Functions - Extracted from original working script.js

// Utility function to debounce function calls
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// Function to get CSRF token from meta tag
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content;
}

// Utility function to force a browser repaint on an element
// This is used to fix rendering issues where content doesn't appear until window focus changes
function forceRepaint(element) {
    if (!element) {
        console.warn('forceRepaint called with null/undefined element');
        return;
    }
    
    // Read layout property to force layout calculation
    const currentHeight = element.offsetHeight;
    // Force a style recalculation with a more substantial change
    element.style.transform = 'translateZ(0)';
    // Use requestAnimationFrame to ensure it processes in the next paint cycle
    requestAnimationFrame(() => {
        element.style.transform = '';
    });
    
    // Log debug info
    console.debug(`forceRepaint applied to element: ${element.className || 'unnamed'}`);
}

// Implement lazy loading for images to improve initial page load
function setupLazyLoading() {
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

// Utility function to perform empty conversation cleanup when browser is idle
// This prevents the cleanup from affecting initial page load performance
function performIdleCleanup() {
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
            .then(cleanupData => {
                if (cleanupData.success) {
                    const cleanedCount = cleanupData.cleaned_count || 0;
                    if (cleanedCount > 0) {
                        console.log(`Idle cleanup: permanently deleted ${cleanedCount} empty conversations`);
                        // Refresh the conversation list if any were deleted
                        // Use window.fetchConversations to ensure it's accessible globally
                        if (typeof window.fetchConversations === 'function') {
                            window.fetchConversations(true);
                        } else {
                            console.log('Conversations will be refreshed on next user interaction');
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error during idle cleanup:', error);
            });
        }, { timeout: 2000 }); // 2 second timeout
    } else {
        // Fallback for browsers that don't support requestIdleCallback
        setTimeout(() => {
            console.log('Performing delayed cleanup of empty conversations (fallback)');
            fetch('/api/cleanup-empty-conversations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(cleanupData => {
                if (cleanupData.success) {
                    const cleanedCount = cleanupData.cleaned_count || 0;
                    if (cleanedCount > 0) {
                        console.log(`Delayed cleanup: permanently deleted ${cleanedCount} empty conversations`);
                        // Refresh the conversation list if any were deleted
                        fetchConversations(true);
                    }
                }
            })
            .catch(error => {
                console.error('Error during delayed cleanup:', error);
            });
        }, 2000);
    }
}

// Make functions available globally
window.debounce = debounce;
window.getCSRFToken = getCSRFToken;
window.forceRepaint = forceRepaint;
window.setupLazyLoading = setupLazyLoading;
window.performIdleCleanup = performIdleCleanup;