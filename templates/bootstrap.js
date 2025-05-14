/**
 * Bootstrap script for critical UI initialization
 * This file handles only the essential UI setup needed for initial rendering
 * All data fetching, API calls, and heavy operations are deferred to script.js
 */

// Initialize essential UI elements as soon as possible
(function() {
  // Global UI state indicators
  window.isInitialized = false;
  window.isLoadingConversation = true;

  // Set conversation loading placeholder
  function initConversationsList() {
    const conversationsList = document.getElementById('conversations-list');
    if (conversationsList) {
      // Check if user is logged in - userIsLoggedIn is set in the template
      if (typeof userIsLoggedIn !== 'undefined' && userIsLoggedIn) {
        conversationsList.innerHTML = `
          <div class="loading-indicator">
            <div class="loading-spinner"></div>
            <div class="loading-text">Loading conversations...</div>
          </div>
        `;
      } else {
        conversationsList.innerHTML = `
          <div class="login-prompt">
            <p>Sign in to save your conversations and access them from any device.</p>
            <a href="/login" class="btn auth-btn">Sign in</a>
          </div>
        `;
      }
    }
  }

  // Initialize UI state for message controls
  function initMessageControls() {
    const sendButton = document.getElementById('send-btn');
    const fileUploadButton = document.getElementById('file-upload-button');
    const cameraButton = document.getElementById('camera-button');
    
    // If user is logged in, show controls in loading state until conversation is created
    if (typeof userIsLoggedIn !== 'undefined' && userIsLoggedIn) {
      if (sendButton) {
        sendButton.classList.add('waiting');
        sendButton.setAttribute('aria-label', 'Loading...');
        sendButton.disabled = true;
      }
      
      if (fileUploadButton) {
        fileUploadButton.classList.add('waiting');
        fileUploadButton.disabled = true;
      }
      
      if (cameraButton) {
        cameraButton.classList.add('waiting');
        cameraButton.disabled = true;
      }
    }
  }

  // Initialize welcome message placeholder
  function initWelcomeMessage() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages && chatMessages.querySelector('.welcome-container')) {
      // Welcome message is already in the template, no action needed
      return;
    }
  }

  // Initialize model buttons placeholder states
  function initModelButtons() {
    const modelButtons = document.querySelectorAll('.model-preset-btn');
    if (modelButtons.length > 0) {
      // Add active state to first model button as default
      modelButtons[0].classList.add('active');
    }
  }

  // Run critical UI initialization
  document.addEventListener('DOMContentLoaded', function() {
    initConversationsList();
    initMessageControls();
    initWelcomeMessage();
    initModelButtons();
    
    // Signal that the bootstrap initialization is complete
    window.isBootstrapComplete = true;
    document.body.classList.add('bootstrap-initialized');
    
    console.log('Bootstrap initialization complete');
  });
})();