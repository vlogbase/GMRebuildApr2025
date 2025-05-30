// Import UI setup functions
import { initializePrioritized, performIdleCleanup } from './uiSetup.js';
// Import chat logic functions
import { setUserIsLoggedIn } from './chatLogic.js';
// Import model selection functions
import { initializeModelSelectionLogic, openModelSelector, closeModelSelector } from './modelSelection.js';
// Import conversation management functions
import { fetchConversations, loadConversation, createNewConversation } from './conversationManagement.js';
// Import event orchestration functions
import { initializeMainEventListeners, lockPremiumFeatures } from './eventOrchestration.js';

// Enable debug mode by default to help troubleshoot mobile issues
window.debugMode = true;

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is authenticated using template variables or DOM fallback
    const isAuthenticated = (typeof window.userIsLoggedIn !== 'undefined' && window.userIsLoggedIn) || 
                           !!document.getElementById('logout-btn');
    console.log('User authentication status:', isAuthenticated ? 'Logged in' : 'Not logged in');
    
    // Get user's credit balance if logged in
    let userCreditBalance = 0;
    if (isAuthenticated) {
        // Use template-provided credit balance or fallback to DOM extraction
        if (typeof window.userCreditBalance !== 'undefined') {
            userCreditBalance = window.userCreditBalance;
        } else {
            // Fallback: extract from the account link in the sidebar
            const accountLink = document.querySelector('.account-link');
            if (accountLink) {
                const balanceText = accountLink.textContent.trim();
                const matches = balanceText.match(/Credits: \$([0-9.]+)/);
                if (matches && matches[1]) {
                    userCreditBalance = parseFloat(matches[1]);
                }
            }
        }
        console.log('User credit balance:', userCreditBalance);
    }
    
    // Remove billing query parameters on first load to prevent redirect loops
    const qs = new URLSearchParams(window.location.search);
    if (qs.get("source") === "billing") {
        qs.delete("source");
        qs.delete("feature");
        history.replaceState(null, "", window.location.pathname);
        console.log("Removed billing query parameters to prevent redirect loop");
    }
    
    // Initialize prioritized UI components first
    initializePrioritized();
    
    // Initialize model selection functionality
    initializeModelSelectionLogic();
    
    // Set authentication state in chat logic
    setUserIsLoggedIn(isAuthenticated);
    
    // Initialize main event listeners
    initializeMainEventListeners(isAuthenticated, userCreditBalance);
    
    // For users without credits, auto-select the free model (preset 6) before locking features
    if (!isAuthenticated || userCreditBalance <= 0) {
        // Import and set the default preset to 6 (free model) for users without credits
        import('./modelSelection.js').then(({ selectPresetButton }) => {
            console.log('Auto-selecting preset 6 (free model) for user without credits');
            selectPresetButton('6');
        }).catch(err => {
            console.error('Failed to auto-select free preset:', err);
        });
        
        lockPremiumFeatures(isAuthenticated, userCreditBalance);
    }
    
    // Check for initial conversation ID from Flask template (for direct chat links)
    // The initialConversationId variable is set in the template
    const initialConversationIdFromTemplate = typeof initialConversationId !== 'undefined' ? initialConversationId : null;
    
    // Skip API initialization for guest users viewing shared conversations
    if (typeof window.isGuestShare !== 'undefined' && window.isGuestShare === true && !isAuthenticated) {
        console.log('Guest share mode detected - skipping conversation initialization');
        return;
    }
    
    // Initialize conversations and handle initial loading
    fetchConversations().then(() => {
        if (initialConversationIdFromTemplate) {
            // Load specific conversation if provided (from direct chat link)
            console.log(`Loading initial conversation from template: ${initialConversationIdFromTemplate}`);
            loadConversation(initialConversationIdFromTemplate);
        } else {
            // Create new conversation if none specified, but don't update URL (keep homepage at /)
            console.log('Creating default conversation for homepage without URL update');
            createNewConversation(false);
        }
    });
    
    // Perform idle cleanup (original behavior)
    setTimeout(() => {
        performIdleCleanup();
    }, 1000);
    
    console.log('Script.js initialization complete');
});

// Export global functions for HTML compatibility (original behavior)
// These are needed for any inline HTML event handlers or mobile compatibility
window.openModelSelector = openModelSelector;
window.closeModelSelector = closeModelSelector;