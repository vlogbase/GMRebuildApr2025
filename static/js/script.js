// Import utility functions from utils module
import { debounce, getCSRFToken, forceRepaint } from './utils.js';
// Import UI setup functions
import { setupLazyLoading, initializePrioritized, performIdleCleanup, messageInput, sendButton } from './uiSetup.js';
// Import API service functions
import { fetchConversationsAPI, sendMessageAPI, loadConversationAPI, createNewConversationAPI, fetchUserPreferencesAPI, saveModelPreferenceAPI, uploadFileAPI, fetchAvailableModelsAPI } from './apiService.js';
// Import chat logic functions
import { sendMessage, addMessage, formatMessage, addTypingIndicator, clearAttachedImages, clearAttachedPdf, messageHistory, currentConversationId, attachedImageUrls, attachedPdfUrl, attachedPdfName, setUserIsLoggedIn } from './chatLogic.js';
// Import file upload functions
import { handleFileUpload, handleImageFile, handlePdfFile, showImagePreview, showPdfPreview, createUploadIndicator, isUploadingFile } from './fileUpload.js';
// Import model selection functions
import { initializeModelSelectionLogic, selectPresetButton, allModels, userPreferences, currentModel, currentPresetId, updatePresetButtonLabels, fetchUserPreferences, fetchAvailableModels, openModelSelector, closeModelSelector, updateUIForModelCapabilities } from './modelSelection.js';
// Import conversation management functions
import { fetchConversations, loadConversation, createNewConversation } from './conversationManagement.js';
// Import event orchestration functions
import { initializeMainEventListeners, lockPremiumFeatures } from './eventOrchestration.js';

// Enable debug mode by default to help troubleshoot mobile issues
window.debugMode = true;

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is authenticated (look for the logout button which only shows for logged in users)
    const isAuthenticated = !!document.getElementById('logout-btn');
    console.log('User authentication status:', isAuthenticated ? 'Logged in' : 'Not logged in');
    
    // Get user's credit balance if logged in
    let userCreditBalance = 0;
    if (isAuthenticated) {
        // Try to extract the credit amount from the account link in the sidebar
        const accountLink = document.querySelector('.account-link');
        if (accountLink) {
            const balanceText = accountLink.textContent.trim();
            const matches = balanceText.match(/Credits: \$([0-9.]+)/);
            if (matches && matches[1]) {
                userCreditBalance = parseFloat(matches[1]);
                console.log('User credit balance:', userCreditBalance);
            }
        }
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
    
    // For non-authenticated users or users with no credits, lock premium features
    if (!isAuthenticated || userCreditBalance <= 0) {
        lockPremiumFeatures(isAuthenticated, userCreditBalance);
    }
    
    // Check for initial conversation ID from URL (for shared links or direct conversation access)
    const pathParts = window.location.pathname.split('/');
    const initialConversationId = pathParts.includes('chat') && pathParts[pathParts.indexOf('chat') + 1] 
        ? pathParts[pathParts.indexOf('chat') + 1] : null;
    
    // Initialize conversations and handle initial loading
    fetchConversations().then(() => {
        if (initialConversationId) {
            // Load specific conversation if provided (from shared link or direct access)
            console.log(`Loading initial conversation: ${initialConversationId}`);
            loadConversation(initialConversationId);
        } else {
            // Create new conversation if none specified (original behavior)
            createNewConversation();
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