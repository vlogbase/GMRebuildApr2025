// Conversation Management Functions for GloriaMundo Chat

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
                        if (typeof window.fetchConversations === 'function') {
                            window.fetchConversations(true);
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error during delayed cleanup:', error);
            });
        }, 2000);
    }
}

// Make function globally available
window.performIdleCleanup = performIdleCleanup;