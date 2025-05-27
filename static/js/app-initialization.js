// Main Application Initialization for GloriaMundo Chat

// Define necessary elements early to avoid reference errors
let messageInput;
let sendButton;

// Define essential functions if not already defined
// This ensures they exist before they're called
if (typeof fetchConversations !== 'function') {
    // Placeholder implementation - will be properly defined later
    window.fetchConversations = function(bustCache = false, metadataOnly = true) {
        console.log('Placeholder fetchConversations called');
        return Promise.resolve([]);
    };
}

if (typeof initializeModelSelector !== 'function') {
    // Placeholder implementation - will be properly defined later
    window.initializeModelSelector = function() {
        console.log('Placeholder initializeModelSelector called');
    };
}

if (typeof handleMessageInputKeydown !== 'function') {
    // Placeholder implementation - will be properly defined later
    window.handleMessageInputKeydown = function(event) {
        console.log('Placeholder handleMessageInputKeydown called');
    };
}

if (typeof sendMessage !== 'function') {
    // Placeholder implementation - will be properly defined later
    window.sendMessage = function() {
        console.log('Placeholder sendMessage called');
    };
}

// Set up prioritized loading for better performance
function initializePrioritized() {
    // High priority - critical for immediate UI interaction
    if (typeof setupLazyLoading === 'function') {
        setupLazyLoading();
    }
    
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
            if (typeof performIdleCleanup === 'function') {
                performIdleCleanup();
            }
            
            // Fetch conversations list during idle time if user is authenticated
            const userIsLoggedIn = !!document.getElementById('logout-btn');
            if (userIsLoggedIn) {
                fetchConversations(false, true);
            }
        }, { timeout: 2000 }); // 2-second timeout as fallback
    } else {
        // Fallback for browsers without requestIdleCallback
        setTimeout(() => {
            if (typeof performIdleCleanup === 'function') {
                performIdleCleanup();
            }
            const userIsLoggedIn = !!document.getElementById('logout-btn');
            if (userIsLoggedIn) {
                fetchConversations(false, true);
            }
        }, 2000);
    }
}

// Main initialization function that runs when DOM is loaded
function initializeMainApp() {
    // Check if user is authenticated (look for the logout button which only shows for logged in users)
    const isAuthenticated = !!document.getElementById('logout-btn');
    console.log('User authentication status:', isAuthenticated ? 'Logged in' : 'Not logged in');
    
    // Remove billing query parameters on first load to prevent redirect loops
    const qs = new URLSearchParams(window.location.search);
    if (qs.get("source") === "billing") {
        qs.delete("source");
        qs.delete("feature");
        history.replaceState(null, "", window.location.pathname);
        console.log("Removed billing query parameters to prevent redirect loop");
    }
    
    // Initialize paste handler for file uploads
    if (typeof initializePasteHandler === 'function') {
        initializePasteHandler();
    }
    
    // Update UI based on model capabilities
    if (typeof updateUIForModelCapabilities === 'function') {
        updateUIForModelCapabilities();
    }
}

// Call prioritized initialization when document is loaded
document.addEventListener('DOMContentLoaded', initializePrioritized);

// Call main app initialization when document is loaded
document.addEventListener('DOMContentLoaded', initializeMainApp);

// Make functions globally available
window.initializePrioritized = initializePrioritized;
window.initializeMainApp = initializeMainApp;
window.messageInput = messageInput;
window.sendButton = sendButton;