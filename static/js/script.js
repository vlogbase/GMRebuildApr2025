// Import utility functions from utils module
import { debounce, getCSRFToken, forceRepaint } from './utils.js';
// Import UI setup functions
import { setupLazyLoading, initializePrioritized, performIdleCleanup, messageInput, sendButton } from './uiSetup.js';
// Import API service functions
import { fetchConversationsAPI, sendMessageAPI, loadConversationAPI, createNewConversationAPI, fetchUserPreferencesAPI, saveModelPreferenceAPI, uploadFileAPI, fetchAvailableModelsAPI } from './apiService.js';
// Import chat logic functions
import { sendMessage, addMessage, formatMessage, addTypingIndicator, clearAttachedImages, clearAttachedPdf, messageHistory, currentConversationId, attachedImageUrls, attachedPdfUrl, attachedPdfName } from './chatLogic.js';
// Import file upload functions
import { handleFileUpload, handleImageFile, handlePdfFile, showImagePreview, showPdfPreview, createUploadIndicator, isUploadingFile } from './fileUpload.js';
// Import model selection functions
import { initializeModelSelectionLogic, selectPresetButton, allModels, userPreferences, currentModel, currentPresetId, updatePresetButtonLabels, fetchUserPreferences, fetchAvailableModels } from './modelSelection.js';
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
    
    // Initialize main event listeners
    initializeMainEventListeners(isAuthenticated, userCreditBalance);
    
    // For non-authenticated users or users with no credits, lock premium features
    if (!isAuthenticated || userCreditBalance <= 0) {
        lockPremiumFeatures(isAuthenticated, userCreditBalance);
    }
    
    // Initialize conversations
    fetchConversations();
    
    console.log('Script.js initialization complete');
});