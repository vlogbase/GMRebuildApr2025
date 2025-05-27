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

// Call prioritized initialization when document is loaded
document.addEventListener('DOMContentLoaded', initializePrioritized);



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
    
    // The free model preset ID
    const FREE_PRESET_ID = '6';
    
    // Helper function to check premium access and fallback to free model if needed
    function checkPremiumAccess(featureName) {
        if (!isAuthenticated) {
            console.log(`Access denied: Not logged in, redirecting to login for ${featureName}`);
            window.location.href = '/login?redirect=chat&feature=' + featureName;
            return false;
        }
        
        if (userCreditBalance <= 0) {
            console.log(`Access denied: Insufficient credits, switching to free model in-place for ${featureName}`);
            if (featureName === 'premium_model') {
                // Use in-place fallback instead of redirecting
                console.warn("No credits – switching to free model in-place.");
                selectPresetButton(FREE_PRESET_ID);
            }
            return false;
        }
        
        return true;
    }
    
    // Function to check if current model supports specific capabilities
    function checkModelCapabilities(capabilityType) {
        // Get current model ID
        const activeModel = document.querySelector('.model-btn.active, .model-preset-btn.active');
        if (!activeModel) {
            console.warn('No active model found when checking capabilities');
            return false;
        }
        
        const modelId = activeModel.getAttribute('data-model-id');
        if (!modelId) {
            console.warn('Active model has no model ID attribute');
            return false;
        }
        
        console.log(`Checking ${capabilityType} capability for model: ${modelId}`);
        
        // Find the model in our allModels array
        const modelInfo = allModels.find(m => m.id === modelId);
        if (!modelInfo) {
            console.warn(`Model ${modelId} not found in allModels array`);
            return false;
        }
        
        // Check for the requested capability
        switch (capabilityType) {
            case 'image':
            case 'is_multimodal':
                return modelInfo.is_multimodal === true;
            case 'pdf':
            case 'supports_pdf':
                return modelInfo.supports_pdf === true;
            default:
                console.warn(`Unknown capability type: ${capabilityType}`);
                return false;
        }
    }
    
    // Function to update UI based on current model capabilities
    function updateUIForModelCapabilities() {
        const supportsImages = checkModelCapabilities('image');
        const supportsPDFs = checkModelCapabilities('pdf');
        
        console.log(`Current model capabilities - Images: ${supportsImages}, PDFs: ${supportsPDFs}`);
        
        // Update upload buttons visibility/state based on capabilities
        if (imageUploadButton) {
            if (supportsImages) {
                imageUploadButton.style.display = 'inline-flex';
                imageUploadButton.classList.remove('disabled');
                
                // Update button title based on supported file types
                if (supportsPDFs) {
                    imageUploadButton.title = 'Upload an image or PDF';
                    
                    // Update file input accept attribute to include PDFs
                    if (fileUploadInput) {
                        fileUploadInput.accept = "image/*,.pdf";
                    }
                } else {
                    imageUploadButton.title = 'Upload an image';
                    
                    // Update file input accept attribute to only accept images
                    if (fileUploadInput) {
                        fileUploadInput.accept = "image/*";
                    }
                }
            } else {
                imageUploadButton.style.display = 'none';
                // Alternative: Keep visible but disabled with explanation
                // imageUploadButton.classList.add('disabled');
                // imageUploadButton.title = 'Current model does not support images';
            }
        }
        
        // Update file upload interface for PDFs if we have a document upload button
        if (uploadDocumentsBtn) {
            if (supportsPDFs) {
                uploadDocumentsBtn.style.display = 'inline-flex';
                uploadDocumentsBtn.classList.remove('disabled');
                uploadDocumentsBtn.title = 'Upload documents to enhance responses';
            } else {
                uploadDocumentsBtn.style.display = 'none';
                // Alternative: Keep visible but disabled with explanation
                // uploadDocumentsBtn.classList.add('disabled');
                // uploadDocumentsBtn.title = 'Current model does not support documents';
            }
        }
    }
    

    
    // Create upload indicator if it doesn't exist
    function createUploadIndicator() {
        // Check if it already exists
        let indicator = document.getElementById('upload-indicator');
        if (indicator) return indicator;
        
        // Create new indicator with the appropriate styling
        indicator = document.createElement('div');
        indicator.id = 'upload-indicator';
        indicator.className = 'upload-indicator';
        indicator.style.display = 'none';
        indicator.style.transition = 'opacity 0.5s ease';
        
        // Add it before the chat input
        const chatInputContainer = document.querySelector('.chat-input-container');
        if (chatInputContainer) {
            chatInputContainer.insertBefore(indicator, chatInputContainer.firstChild);
        } else {
            // Fallback - add to body
            document.body.appendChild(indicator);
            console.warn('Chat input container not found, added upload indicator to body');
        }
        
        return indicator;
    }
    // DOM Elements
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const modelPresetButtons = document.querySelectorAll('.model-preset-btn');
    const newChatButton = document.getElementById('new-chat-btn');
    const clearConversationsButton = document.getElementById('clear-conversations-btn');
    const exampleQuestionButton = document.getElementById('example-question-btn');
    const conversationsList = document.getElementById('conversations-list');
    const modelSelector = document.getElementById('model-selector');
    const modelList = document.getElementById('model-list');
    const modelSearch = document.getElementById('model-search');
    const closeSelector = document.getElementById('close-selector');
    
    // Document upload elements - Legacy RAG system elements are now null
    const uploadDocumentsBtn = null; // Removed button - replaced with unified upload
    const refreshPricesBtn = document.getElementById('refresh-prices-btn');
    const documentUploadModal = null; // Removed modal - using unified file upload instead
    const closeUploadModal = null; // Removed with modal
    const uploadDropzone = null; // Removed with modal
    const uploadFileList = null; // Removed with modal
    const uploadFilesBtn = null; // Removed with modal
    const uploadStatus = null; // Removed with modal
    
    // Image upload and camera elements
    const imageUploadInput = document.getElementById('file-upload-input');
    const imageUploadButton = document.getElementById('file-upload-button');
    const cameraButton = document.getElementById('camera-button');
    const cameraModal = document.getElementById('camera-modal');
    const cameraStream = document.getElementById('camera-stream');
    const imageCanvas = document.getElementById('image-canvas');
    const captureButton = document.getElementById('capture-button');
    const switchCameraButton = document.getElementById('switch-camera-button');
    const closeCameraButton = document.getElementById('close-camera-button');
    // Legacy image preview area has been removed in favor of the unified document preview
    // const imagePreviewArea = document.getElementById('image-preview-area');
    // const imagePreview = document.getElementById('image-preview');
    // const removeImageButton = document.getElementById('remove-image-button');
    
    // App state
    let activePresetButton = null; // Currently selected preset button
    let currentConversationId = null;
    let messageHistory = [];
    let attachedPdfUrl = null; // URL for attached PDF
    let attachedPdfName = null; // Name of attached PDF
    
    // Document handling state
    let attachedImageBlob = null;
    let attachedImageUrls = []; // Array to hold multiple image URLs
    let attachedDocuments = []; // Array to hold all document metadata (both images and PDFs)
    let isUploadingFile = false; // Track if a file (image or PDF) is currently being uploaded
    let uploadingImageCount = 0; // Track number of images currently uploading
    let cameras = [];
    let currentCameraIndex = 0;
    

    
    // Fetch conversations on load - rely on userIsLoggedIn from server
    // userIsLoggedIn is set in the template and more reliable than DOM checks
    if (typeof userIsLoggedIn !== 'undefined') {
        if (userIsLoggedIn) {
            console.log("User is logged in according to server, creating conversation");
            
            // Delay cleanup to run after page load is complete
            setTimeout(() => {
                performIdleCleanup();
            }, 3000);
            
            // Check if we have an initial conversation ID from a shared link redirect
            if (typeof initialConversationId !== 'undefined' && initialConversationId) {
                console.log(`Loading initial conversation ID from redirect: ${initialConversationId}`);
                currentConversationId = initialConversationId;
                
                // Delay loading the specific conversation to improve initial page load time
                setTimeout(() => {
                    // Load the conversation after a short delay
                    loadConversation(initialConversationId);
                    
                    // Fetch other conversations after a longer delay (optimization)
                    setTimeout(() => {
                        console.log('Deferred loading of conversation history (after initial conversation loaded)');
                        fetchConversations(true, true);  // bust cache, metadata on
                    }, 2000);
                }, 700); // Give page time to render first
                
                // Skip the other initialization paths since we've already loaded a conversation
                return;
            }
            // Create a new conversation if we don't have one already
            else if (!currentConversationId) {
                console.log("No current conversation, will create a new one after page loads");
                
                // Delay creating a new conversation to improve initial page load
                setTimeout(() => {
                    console.log("Creating new conversation after page load");
                    // Create a new conversation
                    fetch('/api/create-conversation', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCSRFToken()
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success && data.conversation) {
                            // Set the current conversation ID to the new one
                            currentConversationId = data.conversation.id;
                            console.log(`Created initial conversation with ID: ${currentConversationId}`);
                            
                            // Defer fetching conversations to improve initial load time
                            setTimeout(() => {
                                console.log('Deferred loading of conversation list after page render');
                                fetchConversations(true);
                            }, 500);
                        } else {
                            console.error('Failed to create initial conversation:', data.error || 'Unknown error');
                            // Fetch conversations anyway in case there are existing ones, but defer
                            setTimeout(() => {
                                fetchConversations();
                            }, 500);
                        }
                    })
                    .catch(error => {
                        console.error('Error creating initial conversation:', error);
                        // Fetch conversations anyway in case there are existing ones, but defer
                        setTimeout(() => {
                            fetchConversations();
                        }, 500);
                    });
                }, 800); // Delay to improve initial page load
                
                } else {
                    // We already have a conversation ID, just fetch conversations with longer delay
                    setTimeout(() => {
                        console.log('Deferred loading of conversation history');
                        fetchConversations();
                    }, 800);
                }
        } else {
            console.log("User is not logged in according to server, showing login prompt");
            // For non-logged in users, show the login prompt in the sidebar
            if (conversationsList) {
                conversationsList.innerHTML = `
                    <div class="login-prompt">
                        <p>Sign in to save your conversations and access them from any device.</p>
                        <a href="/login" class="btn auth-btn">Sign in</a>
                    </div>
                `;
            }
        }
    } else {
        // Fallback to DOM check if userIsLoggedIn is not defined
        if (isAuthenticated) {
            // Schedule cleanup to run when browser is idle (won't impact page load)
            performIdleCleanup();
            
            // Create a new conversation if we don't have one already (fallback case)
            if (!currentConversationId) {
                console.log("No current conversation (fallback case), creating a new one on page load");
                
                // Create a new conversation immediately (no blocking cleanup)
                fetch('/api/create-conversation', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.conversation) {
                        currentConversationId = data.conversation.id;
                        console.log(`Created initial conversation (fallback) with ID: ${currentConversationId}`);
                        fetchConversations(true);
                    } else {
                        console.error('Failed to create initial conversation (fallback):', data.error || 'Unknown error');
                        fetchConversations();
                    }
                })
                .catch(error => {
                    console.error('Error creating initial conversation (fallback):', error);
                    fetchConversations();
                });
            } else {
                // We already have a conversation ID, just fetch conversations
                setTimeout(() => {
                    console.log('Deferred loading of conversation history (fallback)');
                    fetchConversations();
                }, 200);
            }
        } else {
            // Show login prompt as a fallback
            if (conversationsList) {
                conversationsList.innerHTML = `
                    <div class="login-prompt">
                        <p>Sign in to save your conversations and access them from any device.</p>
                        <a href="/login" class="btn auth-btn">Sign in</a>
                    </div>
                `;
            }
        }
    }
    
    // Initialize model selection functionality
    initializeModelSelectionLogic();
    
    // Initialize main event listeners
    initializeMainEventListeners();
    
    // For non-authenticated users or users with no credits, lock premium features
    if (!isAuthenticated || userCreditBalance <= 0) {
        lockPremiumFeatures();
    }
    

    
    // Function to lock premium features for non-authenticated users or those with zero balance
    function lockPremiumFeatures() {
        // Process all model preset buttons
        document.querySelectorAll('.model-preset-btn').forEach(btn => {
            const presetId = btn.getAttribute('data-preset-id');
            // Selector icon container - we'll preserve its functionality
            const selectorContainer = btn.querySelector('.selector-icon-container');
            // Button overlay - this will be clickable for disabled states
            const buttonOverlay = btn.querySelector('.button-overlay');
            
            // Clone all buttons to remove existing event listeners, regardless of preset
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            btn = newBtn;
            
            // Re-query the selector container in the cloned button
            const newSelectorContainer = btn.querySelector('.selector-icon-container');
            const newButtonOverlay = btn.querySelector('.button-overlay');
            
            if (presetId === '6') { // Free model button - always enabled for everyone
                // Make sure it's set as active for non-logged in users
                if (!isAuthenticated) {
                    btn.classList.add('active');
                }
                
                // Add click handler to select this preset
                btn.addEventListener('click', function(e) {
                    // If the click target is the selector or its container, do nothing
                    if (e.target.classList.contains('selector-icon') || 
                        e.target.classList.contains('selector-icon-container') ||
                        e.target.closest('.selector-icon-container')) {
                        return;
                    }
                    
                    selectPresetButton('6');
                });
                
                // Add click event for the selector dropdown
                if (newSelectorContainer) {
                    newSelectorContainer.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation(); // Prevent button click from firing
                        openModelSelector('6', btn);
                    });
                }
            } else { // Premium models (1-5)
                // Reset classes first
                btn.classList.remove('disabled', 'disabled-login', 'disabled-payment');
                
                if (!isAuthenticated) {
                    // User is not logged in - show login requirement
                    btn.classList.add('disabled', 'disabled-login');
                    
                    // Keep the selector functionality separate
                    if (newSelectorContainer) {
                        // Preserve the selector container click functionality
                        newSelectorContainer.addEventListener('click', (e) => {
                            e.stopPropagation(); // Prevent button click
                            // We still want to keep the dropdown disabled in login-required state
                            // Add login redirect here 
                            window.location.href = '/login?redirect=chat&feature=premium_model';
                        });
                    }
                    
                    // Make the overlay clickable for login
                    if (newButtonOverlay) {
                        newButtonOverlay.addEventListener('click', (e) => {
                            e.stopPropagation();
                            window.location.href = '/login?redirect=chat&feature=premium_model';
                        });
                    }
                    
                    // Add tooltip if it doesn't exist
                    if (!btn.querySelector('.locked-tooltip')) {
                        const tooltip = document.createElement('span');
                        tooltip.className = 'locked-tooltip';
                        tooltip.textContent = 'Premium feature - Sign in to unlock';
                        btn.appendChild(tooltip);
                    }
                } else if (userCreditBalance <= 0) {
                    // User is logged in but has no credits - show payment requirement
                    btn.classList.add('premium-locked');
                    
                    // Make the entire button clickable to redirect to billing
                    btn.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        // Redirect to billing page to buy credits
                        window.location.href = '/billing/account?source=premium_model&preset=' + presetId;
                    });
                    
                    // Keep the selector functionality separate - also redirect to billing
                    if (newSelectorContainer) {
                        newSelectorContainer.addEventListener('click', (e) => {
                            e.stopPropagation(); // Prevent button click
                            // Redirect to billing page to buy credits
                            window.location.href = '/billing/account?source=premium_model&preset=' + presetId;
                        });
                    }
                    
                    // Make the overlay clickable for payment
                    if (newButtonOverlay) {
                        newButtonOverlay.addEventListener('click', (e) => {
                            e.stopPropagation();
                            // Redirect to billing page to buy credits
                            window.location.href = '/billing/account?source=premium_model&preset=' + presetId;
                        });
                    }
                    
                    // Add tooltip if it doesn't exist
                    if (!btn.querySelector('.locked-tooltip')) {
                        const tooltip = document.createElement('span');
                        tooltip.className = 'locked-tooltip';
                        tooltip.textContent = 'Add credits to use premium models';
                        btn.appendChild(tooltip);
                    }
                }
            }
        });
        
        // Lock document upload button
        if (uploadDocumentsBtn) {
            // Clean up existing classes
            uploadDocumentsBtn.classList.remove('disabled', 'disabled-login', 'disabled-payment');
            
            // Clone to remove existing event listeners
            const newUploadBtn = uploadDocumentsBtn.cloneNode(true);
            uploadDocumentsBtn.parentNode.replaceChild(newUploadBtn, uploadDocumentsBtn);
            const uploadBtn = newUploadBtn;
            
            // Check for button overlay
            const buttonOverlay = uploadBtn.querySelector('.button-overlay');
            
            if (!isAuthenticated) {
                // User not logged in
                uploadBtn.classList.add('disabled', 'disabled-login');
                
                // Make button and overlay redirect to login
                uploadBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    window.location.href = '/login?redirect=chat&feature=document_upload';
                });
                
                // Make overlay clickable too
                if (buttonOverlay) {
                    buttonOverlay.addEventListener('click', (e) => {
                        e.stopPropagation();
                        window.location.href = '/login?redirect=chat&feature=document_upload';
                    });
                }
                
                // Add tooltip if it doesn't exist
                if (!uploadBtn.querySelector('.locked-tooltip')) {
                    const tooltip = document.createElement('span');
                    tooltip.className = 'locked-tooltip';
                    tooltip.textContent = 'Premium feature - Sign in to unlock';
                    uploadBtn.appendChild(tooltip);
                }
            } else if (userCreditBalance <= 0) {
                // User logged in but no credits
                uploadBtn.classList.add('disabled', 'disabled-payment');
                
                // Show a message about insufficient credits instead of redirecting
                uploadBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    alert('Insufficient credits. Please add credits to use document upload feature.');
                });
                
                // Make overlay clickable too with the same message
                if (buttonOverlay) {
                    buttonOverlay.addEventListener('click', (e) => {
                        e.stopPropagation();
                        alert('Insufficient credits. Please add credits to use document upload feature.');
                    });
                }
                
                // Add tooltip if it doesn't exist
                if (!uploadBtn.querySelector('.locked-tooltip')) {
                    const tooltip = document.createElement('span');
                    tooltip.className = 'locked-tooltip';
                    tooltip.textContent = 'Add credits to use document upload';
                    uploadBtn.appendChild(tooltip);
                }
            }
            
            // Reassign uploadDocumentsBtn for subsequent operations
            uploadDocumentsBtn = uploadBtn;
        }
        
        // Lock image upload and camera buttons
        if (imageUploadButton) {
            imageUploadButton.classList.add('premium-locked');
            imageUploadButton.style.display = 'none'; // Initially hidden, so hide it
        }
        
        if (cameraButton) {
            cameraButton.classList.add('premium-locked');
            cameraButton.style.display = 'none'; // Initially hidden, so hide it
        }
    }
    
    // Image upload and camera event listeners with premium access checks
    if (imageUploadButton) {
        imageUploadButton.addEventListener('click', () => {
            // Check premium access before allowing file upload
            if (!checkPremiumAccess('image_upload')) {
                return; // Stop if access check failed
            }
            
            // Get the active model
            const activeModel = document.querySelector('.model-btn.active, .model-preset-btn.active');
            const modelId = activeModel ? activeModel.getAttribute('data-model-id') : null;
            console.log(`🧠 Active model ID: ${modelId || 'null'}`);
            
            // Debug all available models
            if (allModels && allModels.length > 0) {
                console.log(`📚 Available models:`, allModels.map(m => `${m.id} (PDF: ${m.supports_pdf})`));
            }
            
            // Check if selected model supports PDF
            const supportsPdf = checkModelCapabilities('pdf');
            console.log(`📄 Model supports PDF: ${supportsPdf}`);
            
            // Update the file input's accept attribute based on model capabilities
            if (imageUploadInput) {
                if (supportsPdf) {
                    imageUploadInput.accept = "image/*,.pdf";
                    imageUploadButton.title = "Upload images or PDF documents";
                } else {
                    imageUploadInput.accept = "image/*";
                    imageUploadButton.title = "Upload images (current model doesn't support PDFs)";
                }
            }
            
            imageUploadInput.click();
        });
    }
    
    if (imageUploadInput) {
        imageUploadInput.addEventListener('change', event => {
            const file = event.target.files[0];
            if (!file) return;
            
            // Check premium access before processing the file
            if (!checkPremiumAccess('image_upload')) {
                return; // Stop if access check failed
            }
            
            console.log(`📂 File selected: ${file.name}, type: ${file.type}`);
            
            // Check if it's a PDF file
            if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
                console.log('📄 PDF file detected');
                
                // Check if model supports PDF
                if (!checkModelCapabilities('pdf')) {
                    alert('The current model does not support PDF documents. Please select a model with PDF support or upload an image instead.');
                    return;
                }
                
                // Handle PDF file with dedicated PDF handler
                handleFileUpload(file, 'pdf');
                
            } else if (file.type.startsWith('image/')) {
                // Handle image file
                handleImageFile(file);
            } else {
                // Unsupported file type
                console.warn(`Unsupported file type: ${file.type}`);
                alert(`Unsupported file type: ${file.type}. Please upload an image or PDF document.`);
                return;
            }
            
            // Reset the input so the same file can be selected again
            event.target.value = null;
        });
    }
    
    if (cameraButton) {
        cameraButton.addEventListener('click', async () => {
            // Check premium access before allowing camera use
            if (!checkPremiumAccess('camera')) {
                return; // Stop if access check failed
            }
            
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                cameraStream.srcObject = stream;
                cameraModal.style.display = 'block';
                loadCameraDevices();
            } catch (err) {
                console.error('Camera access error:', err);
                alert('Camera access denied or not available');
            }
        });
    }
    
    if (captureButton) {
        captureButton.addEventListener('click', () => {
            // Set canvas dimensions to match video
            const width = cameraStream.videoWidth;
            const height = cameraStream.videoHeight;
            imageCanvas.width = width;
            imageCanvas.height = height;
            
            // Draw video frame to canvas
            const ctx = imageCanvas.getContext('2d');
            ctx.drawImage(cameraStream, 0, 0, width, height);
            
            // Convert canvas to blob
            imageCanvas.toBlob(blob => {
                handleImageFile(blob);
                
                // Stop camera stream and close modal
                stopCameraStream();
                cameraModal.style.display = 'none';
            }, 'image/jpeg', 0.85);
        });
    }
    
    if (switchCameraButton) {
        switchCameraButton.addEventListener('click', switchCamera);
    }
    
    if (closeCameraButton) {
        closeCameraButton.addEventListener('click', () => {
            stopCameraStream();
            cameraModal.style.display = 'none';
        });
    }
    
    // Legacy removeImageButton event listener removed since we now use the unified document preview
    // if (removeImageButton) {
    //     removeImageButton.addEventListener('click', clearAttachedImage);
    // }
    
    // Add event listener for refresh prices button
    if (refreshPricesBtn) {
        refreshPricesBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Call resetToDefault with no presetId to reset all models to defaults
            resetToDefault();
        });
    }
    
    // Image handling functions

    

    
    // Unified file upload handler for both images and PDFs
    async function handleFileUpload(file, fileType = 'auto') {
        console.log(`🔄 handleFileUpload(), file:`, file, `fileType: ${fileType}`);
        if (!file) return;
        
        // Check if already uploading
        if (isUploadingFile) {
            console.warn('Already uploading a file, please wait');
            return false;
        }
        
        try {
            // Set upload flag to true - this will disable the send button
            isUploadingFile = true;
            
            // For images, track the count of uploading images
            if (fileType === 'image' || 
                (fileType === 'auto' && file.type && file.type.startsWith('image/'))) {
                uploadingImageCount++;
                // Update image button UI
                if (imageUploadButton) {
                    imageUploadButton.classList.add('loading');
                }
            }
            
            // Update send button state
            updateSendButtonState();
            
            // Create an upload indicator
            const uploadIndicator = document.getElementById('upload-indicator') || createUploadIndicator();
            uploadIndicator.style.display = 'flex';
            
            // Determine file type if set to auto
            if (fileType === 'auto') {
                if (file.type) {
                    // Use MIME type if available
                    if (file.type.startsWith('image/')) {
                        fileType = 'image';
                    } else if (file.type === 'application/pdf') {
                        fileType = 'pdf';
                    } else {
                        throw new Error(`Unsupported file type: ${file.type}`);
                    }
                } else if (file.name) {
                    // Use file extension as fallback
                    const extension = file.name.split('.').pop().toLowerCase();
                    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(extension)) {
                        fileType = 'image';
                    } else if (extension === 'pdf') {
                        fileType = 'pdf';
                    } else {
                        throw new Error(`Unsupported file extension: .${extension}`);
                    }
                } else {
                    // Default to image for blobs without type/name (e.g., camera captures)
                    fileType = 'image';
                }
            }
            
            // Set appropriate indicator text
            if (file.name) {
                uploadIndicator.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Uploading ${fileType}: ${file.name}...`;
            } else {
                uploadIndicator.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Uploading ${fileType}...`;
            }
            
            // Create FormData and append file
            const formData = new FormData();
            formData.append('file', file, file.name || `photo.${fileType === 'pdf' ? 'pdf' : 'jpg'}`);
            
            // Add current model as a hint to optimize file processing
            const activeModel = document.querySelector('.model-btn.active, .model-preset-btn.active');
            if (activeModel) {
                const modelId = activeModel.getAttribute('data-model-id');
                if (modelId) {
                    formData.append('model', modelId);
                }
            }
            
            console.log(`📤 Uploading ${fileType} to server...`);
            
            // Get the current conversation ID if available
            const conversationId = currentConversationId || '';
            console.log(`🔗 Current conversation ID: ${conversationId}`);
            
            // Upload to server - use the unified endpoint with conversation ID
            const uploadUrl = `/upload_file${conversationId ? `?conversation_id=${conversationId}` : ''}`;
            console.log(`📤 Uploading to: ${uploadUrl}`);
            
            const response = await fetch(uploadUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                },
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.status}`);
            }
            
            const data = await response.json();
            console.log(`↩️ ${fileType} upload response:`, data);
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Process based on response type
            if (data.image_url) {
                // Handle image response
                attachedImageUrls.push(data.image_url);
                // updateImagePreviews(); // Removed in favor of unified document preview
                updateDocumentPreviews(); // Update unified document display
                console.log(`📸 Image uploaded successfully (${attachedImageUrls.length} total):`, data.image_url);
                
                // Remove the indicator for images - we show them in the preview area
                uploadIndicator.remove();
            } else if (data.pdf_data_url) {
                // Handle PDF response
                attachedPdfUrl = data.pdf_data_url;
                attachedPdfName = file.name || data.filename || 'document.pdf';
                
                // For debugging: verify we have a proper data URL starting with data:application/pdf;base64,
                if (!attachedPdfUrl.startsWith('data:application/pdf;base64,')) {
                    console.error('Invalid PDF data URL format:', attachedPdfUrl.substring(0, 50) + '...');
                } else {
                    console.log('Valid base64 PDF data URL received (truncated):', attachedPdfUrl.substring(0, 50) + '...');
                }
                
                // Update the document preview area
                updateDocumentPreviews();
                
                // Also keep the legacy indicator for backward compatibility
                uploadIndicator.innerHTML = `
                    <i class="fa-solid fa-file-pdf"></i>
                    <span class="pdf-filename">${attachedPdfName}</span>
                    <button class="remove-file-btn" title="Remove PDF">
                        <i class="fa-solid fa-times"></i>
                    </button>
                `;
                uploadIndicator.classList.add('pdf-indicator');
                
                // Make sure the indicator is visible
                uploadIndicator.style.display = 'flex';
                
                // Add event listener to remove button
                const removeBtn = uploadIndicator.querySelector('.remove-file-btn');
                if (removeBtn) {
                    removeBtn.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('PDF remove button clicked');
                        clearAttachedPdf();
                    });
                }
                
                // Add MutationObserver to monitor when the indicator is removed
                const pdfObserver = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        if (mutation.type === 'childList' && mutation.removedNodes.length > 0) {
                            for (let i = 0; i < mutation.removedNodes.length; i++) {
                                const node = mutation.removedNodes[i];
                                if (node.classList && node.classList.contains('pdf-indicator')) {
                                    console.warn('PDF indicator was removed by:', 
                                        new Error().stack.split('\n')[2].trim());
                                }
                            }
                        }
                    });
                });
                
                // Start observing the parent element for PDF indicator removals
                const chatInputContainer = document.querySelector('.chat-input-container');
                if (chatInputContainer) {
                    pdfObserver.observe(chatInputContainer, { childList: true, subtree: true });
                }
                
                console.log(`📄 PDF uploaded successfully:`, attachedPdfName, 'Base64 data URL available');
            } else {
                console.warn('Response did not contain expected image_url or pdf_data_url');
                uploadIndicator.remove();
            }
            
            return true;
        } catch (error) {
            console.error(`Error uploading ${fileType}:`, error);
            alert(`Upload failed: ${error.message}`);
            
            // Clear attachments based on type
            if (fileType === 'pdf') {
                clearAttachedPdf();
            }
            
            // Remove the indicator
            const uploadIndicator = document.getElementById('upload-indicator');
            if (uploadIndicator) uploadIndicator.remove();
            
            return false;
        } finally {
            // Reset flags based on file type
            if (fileType === 'image' || 
                (fileType === 'auto' && file.type && file.type.startsWith('image/'))) {
                // Decrement upload counter for images
                uploadingImageCount--;
                
                // Only disable uploading flag if all uploads are complete
                if (uploadingImageCount === 0) {
                    // Reset image button UI
                    if (imageUploadButton) {
                        imageUploadButton.classList.remove('loading');
                    }
                }
            }
            
            // Reset the overall upload flag
            isUploadingFile = false;
            
            // Update send button state
            updateSendButtonState();
        }
    }
    

    
    // Removed updateImagePreviews function as we now use only the unified document preview area
    // All image previews are now handled by updateDocumentPreviews function
    
    // Function to generate the unified document preview area containing both images and PDFs
    function updateDocumentPreviews() {
        const documentPreviewArea = document.getElementById('document-preview-area');
        if (!documentPreviewArea) {
            console.warn('Document preview area not found');
            return;
        }
        
        // Build combined documents array from both images and PDF (if present)
        let attachedDocuments = [];
        
        // Add image documents
        attachedImageUrls.forEach((url, index) => {
            attachedDocuments.push({
                type: 'image',
                url: url,
                name: `Image ${index + 1}`
            });
        });
        
        // Add PDF document if present
        if (attachedPdfUrl && attachedPdfName) {
            attachedDocuments.push({
                type: 'pdf',
                url: attachedPdfUrl,
                name: attachedPdfName
            });
        }
        
        // Clear existing previews
        documentPreviewArea.innerHTML = '';
        
        // If no documents, hide the preview area
        if (attachedDocuments.length === 0) {
            documentPreviewArea.style.display = 'none';
            return;
        }
        
        // Show the preview area
        documentPreviewArea.style.display = 'flex';
        documentPreviewArea.classList.add('document-preview-area');
        
        // Create header with document count
        const header = document.createElement('div');
        header.className = 'document-preview-header';
        header.textContent = `${attachedDocuments.length} document${attachedDocuments.length > 1 ? 's' : ''}`;
        documentPreviewArea.appendChild(header);
        
        // Add previews for each document (limit display to first 4)
        const displayLimit = Math.min(attachedDocuments.length, 4);
        
        for (let i = 0; i < displayLimit; i++) {
            const docItem = attachedDocuments[i];
            
            // Create a container for each preview
            const previewContainer = document.createElement('div');
            previewContainer.className = 'document-preview-container';
            previewContainer.dataset.index = i;
            
            // Create the preview element based on document type
            if (docItem.type === 'image') {
                // Add image-specific class to container
                previewContainer.classList.add('image-document');
                
                // Create thumbnail for image
                const img = document.createElement('img');
                img.className = 'document-preview-thumbnail';
                img.src = docItem.url;
                img.alt = docItem.name || `Image ${i+1}`;
                previewContainer.appendChild(img);
            } else if (docItem.type === 'pdf') {
                // Add PDF-specific class to container
                previewContainer.classList.add('pdf-document');
                
                // Create PDF icon for PDF
                const pdfPreview = document.createElement('div');
                pdfPreview.className = 'pdf-preview-thumbnail';
                pdfPreview.innerHTML = `
                    <i class="fa-solid fa-file-pdf"></i>
                    <span class="pdf-filename">${docItem.name}</span>
                `;
                previewContainer.appendChild(pdfPreview);
            }
            
            // Add a remove button for each document
            const removeBtn = document.createElement('button');
            removeBtn.className = 'remove-document-btn';
            removeBtn.innerHTML = '×';
            removeBtn.setAttribute('data-index', i);
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                // Remove this specific document
                removeDocument(i);
            });
            
            // Make the whole container clickable to open/preview the document
            previewContainer.addEventListener('click', () => {
                openDocumentViewer(i);
            });
            
            // Add remove button to container
            previewContainer.appendChild(removeBtn);
            documentPreviewArea.appendChild(previewContainer);
        }
        
        // If there are more documents than we're showing, add a count indicator
        if (attachedDocuments.length > displayLimit) {
            const moreIndicator = document.createElement('div');
            moreIndicator.className = 'more-documents-indicator';
            moreIndicator.textContent = `+${attachedDocuments.length - displayLimit} more`;
            documentPreviewArea.appendChild(moreIndicator);
        }
        
        // Add a "clear all" button if we have multiple documents
        if (attachedDocuments.length > 1) {
            const clearAllBtn = document.createElement('button');
            clearAllBtn.className = 'clear-all-documents-btn';
            clearAllBtn.textContent = 'Clear All';
            clearAllBtn.addEventListener('click', () => {
                clearAttachedImages();
                clearAttachedPdf();
            });
            documentPreviewArea.appendChild(clearAllBtn);
        }
        
        // Store the documents array globally for reference in other functions
        window.attachedDocuments = attachedDocuments;
    }
    

    

    

    

    

    

    

    
    // Function to update send button state based on image upload status
    function updateSendButtonState() {
        const uploadIndicator = document.getElementById('upload-indicator') || createUploadIndicator();
        const messageText = messageInput.value.trim();
        const hasImages = attachedImageUrls.length > 0;
        const hasPdf = attachedPdfUrl !== null;
        
        if (isUploadingFile) {
            // Disable send button while file is uploading
            sendButton.disabled = true;
            sendButton.classList.add('disabled');
            sendButton.title = 'Please wait for file to finish uploading';
            
            // Show upload indicator with spinner icon
            uploadIndicator.style.display = 'flex';
            uploadIndicator.innerHTML = '<i class="fa-solid fa-spinner"></i> Uploading file...';
            
            // Also disable the image upload button during upload
            if (imageUploadButton) {
                imageUploadButton.disabled = true;
                imageUploadButton.classList.add('disabled');
            }
            
            // Disable camera button during upload
            if (cameraButton) {
                cameraButton.disabled = true;
                cameraButton.classList.add('disabled');
            }
            
            // Disable PDF upload button during upload
            if (uploadDocumentsBtn) {
                uploadDocumentsBtn.disabled = true;
                uploadDocumentsBtn.classList.add('disabled');
            }
        } else {
            // Enable or disable send button based on content
            const canSend = messageText !== '' || hasImages || hasPdf;
            sendButton.disabled = !canSend;
            
            if (canSend) {
                sendButton.classList.remove('disabled');
                sendButton.title = '';
            } else {
                sendButton.classList.add('disabled');
                sendButton.title = 'Please enter a message or upload an image/document';
            }
            
            // Hide the upload indicator
            uploadIndicator.style.display = 'none';
            
            // Re-enable image upload button
            if (imageUploadButton) {
                imageUploadButton.disabled = false;
                imageUploadButton.classList.remove('disabled');
            }
            
            // Re-enable camera button
            if (cameraButton) {
                cameraButton.disabled = false;
                cameraButton.classList.remove('disabled');
            }
        }
    }
    
    function stopCameraStream() {
        if (cameraStream && cameraStream.srcObject) {
            const tracks = cameraStream.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            cameraStream.srcObject = null;
        }
    }
    
    async function switchCamera() {
        if (cameras.length > 1 && cameraStream) {
            stopCameraStream();
            currentCameraIndex = (currentCameraIndex + 1) % cameras.length;
            
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { deviceId: { exact: cameras[currentCameraIndex].deviceId } }
                });
                if (cameraStream) {
                    cameraStream.srcObject = stream;
                }
            } catch (err) {
                console.error('Error switching camera:', err);
                alert('Failed to switch camera');
            }
        }
    }
    
    async function loadCameraDevices() {
        if (!navigator.mediaDevices?.enumerateDevices) {
            console.warn('enumerateDevices() not supported');
            return;
        }
        
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            cameras = devices.filter(device => device.kind === 'videoinput');
            
            // Enable/disable switch camera button based on available cameras
            if (switchCameraButton) {
                switchCameraButton.style.display = cameras.length > 1 ? 'block' : 'none';
            }
        } catch (err) {
            console.error('Error enumerating devices:', err);
        }
    }
    
    // Event Listeners
    if (messageInput) {
        // Function to auto-resize the textarea - making it globally accessible for mobile.js
        window.autoResizeTextarea = function() {
            // Reset height to auto first to get the correct scrollHeight
            messageInput.style.height = 'auto';
            
            // Calculate available space based on device type and viewport
            const viewportHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;
            const appHeader = document.querySelector('.app-header');
            const headerHeight = appHeader ? appHeader.offsetHeight : 60;
            
            // Get other elements that affect the available space
            const chatInputContainer = messageInput.closest('.chat-input-container');
            const modelButtonsContainerDesktop = document.querySelector('.model-buttons.desktop-only');
            const modelButtonsContainerMobile = document.querySelector('.mobile-model-buttons');
            const messageActionsContainer = document.querySelector('.message-actions-container');
            const chatMessages = document.getElementById('chat-messages');
            
            // Calculate height of other UI elements in the input area
            let otherInputBarElementsHeight = 0;
            const inputGroup = messageInput.closest('.input-group');
            
            // Add height of model buttons and other UI elements
            if (modelButtonsContainerDesktop && modelButtonsContainerDesktop.offsetParent !== null) {
                otherInputBarElementsHeight += modelButtonsContainerDesktop.offsetHeight;
                otherInputBarElementsHeight += parseInt(window.getComputedStyle(modelButtonsContainerDesktop).marginBottom || 0);
            } else if (modelButtonsContainerMobile && modelButtonsContainerMobile.offsetParent !== null) {
                otherInputBarElementsHeight += modelButtonsContainerMobile.offsetHeight;
                otherInputBarElementsHeight += parseInt(window.getComputedStyle(modelButtonsContainerMobile).marginBottom || 0);
            }
            
            // Add padding from input group and height of message actions
            if (inputGroup) {
                const inputGroupStyle = window.getComputedStyle(inputGroup);
                otherInputBarElementsHeight += parseInt(inputGroupStyle.paddingTop) + parseInt(inputGroupStyle.paddingBottom);
                if (messageActionsContainer && messageActionsContainer.offsetParent !== null) {
                    otherInputBarElementsHeight += messageActionsContainer.offsetHeight;
                }
            }
            
            // Safety margin for overall layout
            const safetyMargin = 20;
            
            // Calculate total available height for chat and input
            const availableHeightForChatAndInput = viewportHeight - headerHeight - safetyMargin;
            
            // Determine max percentage based on device type
            const isMobile = window.innerWidth <= 576;
            const maxPercentageOfViewableArea = isMobile ? 0.75 : 0.50; // 75% for mobile, 50% for desktop
            
            // Calculate max height based on percentage of available space
            const calculatedMaxTextareaHeight = (availableHeightForChatAndInput - otherInputBarElementsHeight) * maxPercentageOfViewableArea;
            
            // Ensure the max height is not too small
            const absoluteMinAllowableMaxHeight = 500; // Increased from 100px to 500px
            const effectiveMaxHeight = Math.max(absoluteMinAllowableMaxHeight, calculatedMaxTextareaHeight);
            
            // Debug logging for mobile
            if (isMobile && window.debugMode) {
                console.log("MOBILE autoResizeTextarea:", {
                    viewportHeight,
                    headerHeight,
                    otherInputBarElementsHeight,
                    availableHeightForChatAndInput,
                    calculatedMaxTextareaHeight,
                    effectiveMaxHeight,
                    currentScrollHeight: messageInput.scrollHeight,
                    minHeight: 80 // minimum height value
                });
            }
            
            // Special handling for mobile
            if (isMobile) {
                // For mobile, use a more aggressive approach to ensure textarea expands properly
                const isKeyboardVisible = window.visualViewport && 
                    window.visualViewport.height < window.innerHeight - 100;
                
                if (isKeyboardVisible) {
                    console.log("Mobile keyboard is visible, setting fixed max height");
                    // When keyboard is visible, use our minimum guaranteed height
                    messageInput.style.maxHeight = absoluteMinAllowableMaxHeight + 'px';
                } else {
                    // When keyboard is not visible, use the calculated height
                    messageInput.style.maxHeight = effectiveMaxHeight + 'px';
                }
            } else {
                // For desktop, use the calculated max height
                messageInput.style.maxHeight = effectiveMaxHeight + 'px';
            }
            
            // Set the height based on scrollHeight (with minimum and maximum constraints)
            const minHeight = 80; // Minimum height to start with
            const newHeight = Math.max(minHeight, Math.min(messageInput.scrollHeight, effectiveMaxHeight));
            messageInput.style.height = newHeight + 'px';
            
            // Dynamically adjust padding-bottom of chatMessages to prevent the last message from being hidden
            if (chatMessages && chatInputContainer) {
                const currentInputBarTotalHeight = chatInputContainer.offsetHeight;
                chatMessages.style.paddingBottom = (currentInputBarTotalHeight + 20) + 'px'; // 20px for extra space
            }
            
            // Log effective heights in debug mode
            if (window.debugMode) {
                console.log(`Auto-resize: scrollHeight=${messageInput.scrollHeight}, newHeight=${newHeight}, maxHeight=${effectiveMaxHeight}`);
            }
        }
        
        // Handle input event for continuous resizing as user types
        messageInput.addEventListener('input', function() {
            autoResizeTextarea();
            updateSendButtonState(); // Update send button state when input changes
        });
        
        // Add resize listener for window to adjust textarea size when window changes
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(function() {
                if (typeof window.autoResizeTextarea === 'function') {
                    window.autoResizeTextarea();
                }
            }, 100);
        });
        
        // Handle keydown for Enter key and special cases
        messageInput.addEventListener('keydown', function(event) {
            const isMobile = window.innerWidth <= 576; // Match mobile breakpoint
            
            if (event.key === 'Enter') {
                if (isMobile) {
                    // On mobile, we want Enter to create a new line
                    // So we DON'T prevent default and DON'T send the message
                    console.log('Mobile: Enter key pressed, allowing new line');
                    // If Shift is pressed on mobile (external keyboard), also allow new line
                } else {
                    // Desktop behavior: Enter sends, Shift+Enter creates new line
                    if (!event.shiftKey) {
                        event.preventDefault();
                        sendMessage();
                    }
                }
            }
            
            // For Backspace and Delete keys, resize after a brief delay to allow the content to update
            if (event.key === 'Backspace' || event.key === 'Delete') {
                setTimeout(autoResizeTextarea, 10);
            }
        });
        
        // Initial resize in case there's content already
        autoResizeTextarea();
    }
    
    // Add clipboard paste event listener to the message input
    document.addEventListener('paste', function(event) {
        // Only process if we're focused on the message input or inside the chat container
        if (document.activeElement === messageInput || 
            document.activeElement.closest('.chat-input-container')) {
            
            // Get clipboard data
            const clipboardData = event.clipboardData || window.clipboardData;
            const items = clipboardData.items;
            
            // Check for images in clipboard data
            for (let i = 0; i < items.length; i++) {
                if (items[i].type.indexOf('image') !== -1) {
                    console.log('📎 Image found in clipboard');
                    
                    // Convert image data to a blob
                    const blob = items[i].getAsFile();
                    if (blob) {
                        // Prevent default paste behavior for images
                        event.preventDefault();
                        
                        // Process the image
                        handleImageFile(blob);
                        return;
                    }
                }
            }
        }
    });
    
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    // Initialize model data only if on the chat page
    if (modelSelector) {
        console.log('Model selector found, initializing selector functionality');
        
        // Defer model data loading to improve initial page load speed
        // This allows the UI to render first before loading large model datasets
        setTimeout(() => {
            console.log('Deferred loading of model preferences and data');
            window.fetchUserPreferences();
        }, 100);
        
        // Model preset button click handlers
        if (modelPresetButtons && modelPresetButtons.length > 0) {
            modelPresetButtons.forEach(button => {
                // Find selector icon container within this button
                const selectorIconContainer = button.querySelector('.selector-icon-container');
                const selectorIcon = button.querySelector('.selector-icon');
                
                // Add debounced click event to the model button
                button.addEventListener('click', debounce(function(e) {
                    const presetId = this.getAttribute('data-preset-id');
                    
                    // If the button is already in loading state, do nothing
                    if (this.classList.contains('loading')) {
                        return;
                    }
                    
                    // If the click target is the selector icon or its container, do nothing
                    // as those have their own handlers
                    if (e.target.classList.contains('selector-icon') || 
                        e.target.classList.contains('selector-icon-container') ||
                        e.target.closest('.selector-icon-container')) {
                        return;
                    }
                    
                    // If shift key or right-click, open model selector
                    if (e.shiftKey || e.button === 2) {
                        e.preventDefault();
                        openModelSelector(presetId, this);
                        return;
                    }
                    
                    // Otherwise, select this preset
                    selectPresetButton(presetId);
                }, 300)); // 300ms debounce
                
                // Add context menu to open selector
                button.addEventListener('contextmenu', function(e) {
                    e.preventDefault();
                    const presetId = this.getAttribute('data-preset-id');
                    openModelSelector(presetId, this);
                });
                
                // Add click event to the selector icon or container
                if (selectorIconContainer) {
                    selectorIconContainer.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation(); // Prevent button click from firing
                        
                        const presetId = button.getAttribute('data-preset-id');
                        openModelSelector(presetId, button);
                    });
                } else if (selectorIcon) {
                    // Fallback to direct icon if container not found
                    selectorIcon.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation(); // Prevent button click from firing
                        
                        const presetId = button.getAttribute('data-preset-id');
                        openModelSelector(presetId, button);
                    });
                }
            });
        }
        
        // Close model selector on button click (only if close button exists)
        if (closeSelector) {
            closeSelector.addEventListener('click', function() {
                closeModelSelector();
            });
        }
        
        // Setup Reset to Default button
        const resetToDefaultBtn = document.getElementById('reset-to-default');
        if (resetToDefaultBtn) {
            resetToDefaultBtn.addEventListener('click', function() {
                resetToDefault(currentlyEditingPresetId);
            });
        }
        
        // Close model selector when clicking outside
        document.addEventListener('click', function(e) {
            if (modelSelector.style.display === 'block' && 
                !modelSelector.contains(e.target) && 
                !e.target.matches('.model-preset-btn') && 
                !e.target.closest('.model-preset-btn')) {
                closeModelSelector();
            }
        });
        
        // Search functionality for model selector (only if search input exists)
        if (modelSearch) {
            modelSearch.addEventListener('input', function() {
                filterModelList(this.value.toLowerCase());
            });
        }
    } else {
        console.log('Model selector not found on this page, skipping selector initialization');
    }
    
    // Function to select a preset button and update the current model
    // Expose this function globally for mobile.js
    window.selectPresetButton = function(presetId) {
        // Check if this is a premium preset (all except preset 6)
        if (presetId !== '6') {
            // Check premium access before allowing selection of premium model
            if (!checkPremiumAccess('premium_model')) {
                // If access check failed, select the free model instead
                console.log('Premium access denied, selecting free model instead');
                selectPresetButton('6');
                return;
            }
        }
        
        // Dispatch event for the mobile UI
        document.dispatchEvent(new CustomEvent('preset-button-selected', {
            detail: { presetId }
        }));
        
        // Remove active class from all buttons
        modelPresetButtons.forEach(btn => btn.classList.remove('active'));
        
        // Add active class to selected button
        const activeButton = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
        if (activeButton) {
            // Add loading state
            activeButton.classList.add('loading');
            
            // Add active class
            activeButton.classList.add('active');
            activePresetButton = activeButton;
            currentPresetId = presetId;
            
            // Get the model ID for this preset
            currentModel = userPreferences[presetId] || defaultModels[presetId];
            console.log(`Selected preset ${presetId} with model: ${currentModel}`);
            
            // Update multimodal controls based on the selected model
            updateMultimodalControls(currentModel);
            
            // Update the cost indicator for the selected model
            updateSelectedModelCostIndicator(currentModel);
            
            // Save preference - passing the button element to handle loading state
            saveModelPreference(presetId, currentModel, activeButton);
        }
    }
    
    // Function to update the selected model's cost indicator in the UI
    // Expose this function globally for mobile UI
    window.updateSelectedModelCostIndicator = function(modelId) {
        if (!modelId) return;
        
        // Find the model in allModels to get its cost band
        const model = allModels?.find(m => m.id === modelId);
        if (!model || !model.cost_band) return;
        
        // Find the active model button
        const activeButton = document.querySelector('.model-preset-btn.active');
        if (!activeButton) return;
        
        // Check if this is the free preset
        const isFreeBand = activeButton.getAttribute('data-preset-id') === '6';
        if (isFreeBand) return; // Don't show cost band on free preset
        
        // Update cost indicator in the active button
        const nameSpan = activeButton.querySelector('.model-name');
        if (!nameSpan) return;
        
        // Remove any existing cost band indicators
        const existingCostBand = nameSpan.querySelector('.cost-band-indicator');
        if (existingCostBand) {
            existingCostBand.remove();
        }
        
        // Create the cost indicator
        const costSpan = document.createElement('span');
        costSpan.textContent = model.cost_band;
        costSpan.className = 'cost-band-indicator';
        
        // Add the specific band class based on the band value
        if (model.cost_band === '$$$$') {
            costSpan.classList.add('cost-band-4-danger');
        } else if (model.cost_band === '$$$') {
            costSpan.classList.add('cost-band-3-warn');
        } else if (model.cost_band === '$$') {
            costSpan.classList.add('cost-band-2');
        } else if (model.cost_band === '$') {
            costSpan.classList.add('cost-band-1');
        } else {
            costSpan.classList.add('cost-band-free');
        }
        
        nameSpan.appendChild(costSpan);
    }
    
    // Function to update multimodal controls (image upload, camera) based on model capability
    // Expose this function globally for mobile UI
    window.updateMultimodalControls = function(modelId) {
        // Store the current model ID globally for capability checks
        currentModel = modelId;
        
        // Find the model in allModels
        const model = allModels.find(m => m.id === modelId);
        if (!model) {
            console.warn(`Model ${modelId} not found in allModels array`);
            return;
        }
        
        // Get model capabilities
        const isMultimodalModel = model.is_multimodal === true;
        const supportsPDF = model.supports_pdf === true;
        
        console.log(`🖼️ Model capabilities for ${modelId}: 
            - Multimodal/images: ${isMultimodalModel ? 'Yes' : 'No'}
            - PDF documents: ${supportsPDF ? 'Yes' : 'No'}`);
        
        // Show/hide image upload and camera buttons based on multimodal capability
        if (imageUploadButton) {
            imageUploadButton.style.display = isMultimodalModel ? 'inline-flex' : 'none';
        }
        
        // Only show camera button if browser supports it and model supports images
        const hasCamera = !!navigator.mediaDevices?.getUserMedia;
        if (cameraButton) {
            cameraButton.style.display = isMultimodalModel && hasCamera ? 'inline-flex' : 'none';
        }
        
        // Show/hide document upload button based on PDF capability
        if (uploadDocumentsBtn) {
            uploadDocumentsBtn.style.display = supportsPDF ? 'inline-flex' : 'none';
        }
        
        // If switching to a non-multimodal model, clear any attached image
        if (!isMultimodalModel) {
            clearAttachedImage();
        }
        
        // If switching to a model that doesn't support PDFs, clear any attached PDF
        if (!supportsPDF) {
            clearAttachedPdf();
        }
        
        return isMultimodalModel; // Return for testing purposes
    }
    
    // Function to fetch user preferences for model presets
    // Expose this globally for the mobile UI
    window.fetchUserPreferences = function() {
        return fetch('/get_preferences')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.preferences) {
                    // Validate preferences to ensure presets 1-5 don't have free models
                    const validatedPreferences = {};
                    
                    for (const presetId in data.preferences) {
                        const modelId = data.preferences[presetId];
                        const isFreeModel = modelId.includes(':free');
                        
                        // If it's preset 1-5 and has a free model, use the default non-free model
                        if (presetId !== '6' && isFreeModel) {
                            console.warn(`Preset ${presetId} has a free model (${modelId}), reverting to default`);
                            validatedPreferences[presetId] = defaultModels[presetId];
                            
                            // Note: Preset 4 is our vision model (openai/gpt-4o) for multimodal capabilities
                            if (presetId === '4') {
                                console.log(`Ensuring preset 4 uses vision-capable model: ${defaultModels['4']}`);
                            }
                        } else {
                            validatedPreferences[presetId] = modelId;
                        }
                    }
                    
                    userPreferences = validatedPreferences;
                    console.log('Loaded user preferences:', userPreferences);
                    
                    // Make sure the global window.userPreferences is set before dispatching event
                    window.userPreferences = userPreferences;
                    
                    // Update button text to reflect preferences
                    updatePresetButtonLabels();
                    
                    // Select default preset - use preset 6 (free) for non-authenticated users
                    selectPresetButton(isAuthenticated ? '1' : '6');
                    
                    // Dispatch an event to notify other scripts that preferences are loaded
                    // This helps mobile scripts synchronize their initialization
                    console.log('Script.js: User preferences successfully loaded, dispatching event');
                    // Dispatch to both window (legacy) and document (standard approach)
                    const userPrefsEvent = new CustomEvent('userPreferencesLoaded', {
                        detail: { 
                            preferences: userPreferences,
                            success: true 
                        }
                    });
                    
                    // Dispatch on window for backward compatibility
                    window.dispatchEvent(userPrefsEvent);
                    
                    // Dispatch on document (recommended approach)
                    document.dispatchEvent(userPrefsEvent);
                } else {
                    // Handle case where data.preferences is empty
                    console.warn('Script.js: data.preferences is empty, using defaults');
                    
                    // Use defaults
                    userPreferences = {};
                    for (const presetId in defaultModels) {
                        userPreferences[presetId] = defaultModels[presetId];
                    }
                    window.userPreferences = userPreferences;
                    
                    // Update UI
                    updatePresetButtonLabels();
                    selectPresetButton(isAuthenticated ? '1' : '6');
                    
                    // Dispatch with defaults
                    // Create event for both window and document
                    const userPrefsEvent = new CustomEvent('userPreferencesLoaded', {
                        detail: { 
                            preferences: userPreferences,
                            success: false,
                            defaultsUsed: true
                        }
                    });
                    
                    // Dispatch to both targets
                    window.dispatchEvent(userPrefsEvent);
                    document.dispatchEvent(userPrefsEvent);
                }
                
                // After loading preferences, fetch available models
                // Return this promise to maintain the chain
                return fetchAvailableModels().then(models => {
                    // Return a combined result
                    return {
                        preferences: userPreferences,
                        models: models,
                        preferencesSuccess: !!data.preferences
                    };
                });
            })
            .catch(error => {
                console.error('Error fetching preferences:', error);
                
                // Use defaults for user preferences
                userPreferences = {};
                for (const presetId in defaultModels) {
                    userPreferences[presetId] = defaultModels[presetId];
                }
                window.userPreferences = userPreferences;
                
                // Dispatch event to notify that preferences are ready (with defaults)
                console.log('Script.js: User preferences set to defaults due to error, dispatching event');
                // Create event for user preferences error case
                const userPrefsErrorEvent = new CustomEvent('userPreferencesLoaded', {
                    detail: { 
                        preferences: userPreferences, 
                        error: true,
                        defaultsUsed: true
                    }
                });
                
                // Dispatch to both targets
                window.dispatchEvent(userPrefsErrorEvent);
                document.dispatchEvent(userPrefsErrorEvent);
                
                // Select the appropriate preset - free for non-authenticated users
                selectPresetButton(isAuthenticated ? '1' : '6');
                
                // Important: Return the fetchAvailableModels promise to maintain the chain
                return fetchAvailableModels().then(models => {
                    // After models are loaded, return a combined result
                    return {
                        preferences: userPreferences,
                        models: models,
                        preferencesError: true
                    };
                });
            });
    }
    
    // Function to update the model preset button labels

    
    // Function to format model ID into a display name
    // Expose this function globally for mobile UI
    window.formatModelName = function(modelId, isFreePrefixed = false) {
        if (!modelId) return 'Unknown';
        
        // Check if we have a custom display name for this model
        if (defaultModelDisplayNames[modelId]) {
            return defaultModelDisplayNames[modelId];
        }
        
        // Handle special cases for free models
        if (modelId.includes(':free') && !isFreePrefixed) {
            return 'Free Model';
        }
        
        // Split by / and get the last part
        const parts = modelId.split('/');
        let name = parts[parts.length - 1];
        
        // Remove the :free suffix if present
        name = name.replace(':free', '');
        
        // Replace dashes with spaces and capitalize
        name = name.replace(/-/g, ' ');
        
        // Shorten common prefixes
        name = name
            .replace('claude ', 'Claude ')
            .replace('gemini ', 'Gemini ')
            .replace('gpt ', 'GPT ')
            .replace('mistral ', 'Mistral ')
            .replace('llama ', 'Llama ');
        
        // Truncate if too long - different lengths depending on context
        // Increase max length to avoid excessive truncation
        const maxLength = isFreePrefixed ? 12 : 20;
        if (name.length > maxLength) {
            name = name.substring(0, maxLength - 3) + '...';
        }
        
        return name;
    }
    
    // Function to manually refresh model prices from the server
    function refreshModelPrices() {
        console.log("Manually refreshing model prices from the server...");
        
        // Show a visual indicator that refresh is in progress
        const modelButtons = document.querySelectorAll('.model-preset-btn');
        modelButtons.forEach(btn => {
            const originalHtml = btn.innerHTML;
            btn.dataset.originalHtml = originalHtml;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Refreshing...';
            btn.disabled = true;
        });
        
        // Call the refresh endpoint
        return fetch('/api/refresh_model_prices', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Refresh response:", data);
            if (data.success) {
                // Fetch the updated models
                return fetchAvailableModels();
            } else {
                throw new Error(data.error || "Failed to refresh model prices");
            }
        })
        .catch(error => {
            console.error("Error refreshing model prices:", error);
            alert("Failed to refresh model prices. Check the console for details.");
        })
        .finally(() => {
            // Restore the original button state
            modelButtons.forEach(btn => {
                if (btn.dataset.originalHtml) {
                    btn.innerHTML = btn.dataset.originalHtml;
                    delete btn.dataset.originalHtml;
                }
                btn.disabled = false;
            });
        });
    }
    
    // Function to calculate cost band based on model pricing data
    function calculateCostBand(modelData) {
        // If the model already has a valid cost band, use it
        if (modelData.cost_band && ['$$$$', '$$$', '$$', '$'].includes(modelData.cost_band)) {
            return modelData.cost_band;
        }
        
        // Otherwise calculate based on input and output prices
        const inputPrice = modelData.input_price || 0;
        const outputPrice = modelData.output_price || 0;
        const maxPrice = Math.max(inputPrice, outputPrice);
        
        // Determine if this is a free model
        const isFreeModel = (inputPrice === 0 || inputPrice <= 0.01) && 
                           (outputPrice === 0 || outputPrice <= 0.01);
        
        if (isFreeModel) {
            return '';  // Free models don't show a cost band
        }
        
        // Calculate band based on maximum price
        if (maxPrice >= 100.0) {
            return '$$$$';
        } else if (maxPrice >= 10.0) {
            return '$$$';
        } else if (maxPrice >= 1.0) {
            return '$$';
        } else if (maxPrice >= 0.01) {
            return '$';
        }
        
        return '';  // Default for very low prices
    }
    
    // Function to fetch available models from OpenRouter
    function fetchAvailableModels() {
        console.log('Fetching available models...');
        // Create a promise that will resolve with the fetched models
        // Fetch ONLY from the endpoint that includes cost bands
        // IMPORTANT: This function must always return a promise that resolves with the models
        // to maintain proper promise chaining and event synchronization
        return fetch('/api/get_model_prices')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Check if the API call was successful and returned prices
                if (data.success && data.prices) {
                    // Log 1: Raw API response
                    console.log('[Debug] Raw API Response:', JSON.stringify(data, null, 2));
                    
                    // Debug logging for cost bands in the API response
                    console.log('[Debug] Cost band examples from API:');
                    const sampleModelIds = Object.keys(data.prices).slice(0, 5);
                    sampleModelIds.forEach(modelId => {
                        console.log(`Model ${modelId} cost band: ${data.prices[modelId].cost_band}`);
                    });
                    
                    // Create model data array directly from pricing data
                    const modelDataArray = [];
                    for (const modelId in data.prices) {
                        const modelData = data.prices[modelId];
                        // Format the model name if it doesn't exist in the pricing data
                        const formatModelName = (id) => {
                            return id.split('/').pop().replace(/-/g, ' ').replace(/(^\w|\s\w)/g, m => m.toUpperCase());
                        };
                        
                        // Construct the model object directly from pricing data
                        modelDataArray.push({
                            id: modelId,
                            // Use name from pricing data, fallback to parsing ID
                            name: modelData.model_name || formatModelName(modelId),
                            // Determine if free based on pricing or explicit flag
                            is_free: modelData.is_free === true || (modelData.input_price === 0 && modelData.output_price === 0),
                            // Get multimodal status from pricing data - check both boolean and string formats
                            is_multimodal: modelData.is_multimodal === true || modelData.multimodal === "Yes",
                            // Use accurate reasoning flag from API response
                            is_reasoning: modelData.is_reasoning === true,
                            // Add perplexity flag based on model ID
                            is_perplexity: modelId.includes('perplexity'),
                            // Add PDF support flag from pricing data
                            supports_pdf: modelData.supports_pdf || false,
                            // Include context length for display elsewhere
                            context_length: modelData.context_length,
                            // Store pricing info if needed elsewhere
                            pricing: {
                                prompt: modelData.input_price,
                                completion: modelData.output_price
                            },
                            // Calculate cost band if not provided by API or if it's empty
                            cost_band: calculateCostBand(modelData)
                        });
                    }

                    // Assign the fully processed data to the global variable
                    allModels = modelDataArray;
                    
                    // Validate that we have actual model data
                    const hasValidModels = allModels && allModels.length > 0 && allModels.some(m => m.id && m.name);
                    
                    if (!hasValidModels) {
                        console.warn('Script.js: Processed model data appears invalid or empty');
                    }
                    
                    // Expose the models to window object for mobile interface
                    window.availableModels = allModels;
                    
                    // Dispatch an event to notify other scripts that models are loaded
                    // Include detailed data about the models in the event
                    console.log(`Script.js: Models loaded (${allModels.length}), dispatching event`);
                    // Create event with model data
                    const modelsEvent = new CustomEvent('modelsLoaded', {
                        detail: { 
                            models: allModels,
                            count: allModels.length,
                            success: hasValidModels
                        }
                    });
                    
                    // Dispatch to both window and document
                    window.dispatchEvent(modelsEvent);
                    document.dispatchEvent(modelsEvent);
                    
                    // For non-authenticated users, ensure we have at least the default free models available
                    if (!isAuthenticated) {
                        console.log('[Debug] User is not authenticated, ensuring fallback free models are available');
                        
                        // Check if we have any free models
                        const hasFreeModels = allModels.some(model => model.is_free === true || model.id.includes(':free'));
                        
                        if (!hasFreeModels) {
                            console.log('[Debug] No free models found, adding fallback free models');
                            
                            // Add fallback free models directly to allModels
                            const fallbackFreeModels = [
                                {
                                    id: 'google/gemini-2.0-flash-exp:free',
                                    name: 'Gemini 2.0 Flash',
                                    is_free: true,
                                    is_multimodal: false,
                                    pricing: { prompt: 0, completion: 0 },
                                    input_price: 0,
                                    output_price: 0,
                                    cost_band: ''
                                },
                                {
                                    id: 'qwen/qwq-32b:free',
                                    name: 'Qwen 32B',
                                    is_free: true,
                                    is_multimodal: false,
                                    pricing: { prompt: 0, completion: 0 },
                                    input_price: 0,
                                    output_price: 0,
                                    cost_band: ''
                                },
                                {
                                    id: 'deepseek/deepseek-r1-distill-qwen-32b:free',
                                    name: 'Deepseek R1 Qwen 32B', 
                                    is_free: true,
                                    is_multimodal: false,
                                    pricing: { prompt: 0, completion: 0 },
                                    input_price: 0,
                                    output_price: 0,
                                    cost_band: ''
                                }
                            ];
                            
                            // Add the fallback free models to allModels
                            allModels = allModels.concat(fallbackFreeModels);
                            console.log(`[Debug] Added ${fallbackFreeModels.length} fallback free models. New total: ${allModels.length}`);
                        }
                    }
                    
                    // Log 2: Transformed model array info
                    console.log(`[Debug] Transformed allModels array created. Count: ${allModels.length}`);
                    if (allModels.length > 0) {
                        console.log('[Debug] First model object in allModels:', JSON.stringify(allModels[0], null, 2));
                        // Log properties relevant to filtering for the first model
                        console.log(`[Debug] First model flags: is_free=${allModels[0].is_free}, is_reasoning=${allModels[0].is_reasoning || 'undefined'}, is_perplexity=${allModels[0].is_perplexity}, is_multimodal=${allModels[0].is_multimodal}`);
                    }
                    
                    console.log(`Loaded ${allModels.length} models with cost bands from /api/get_model_prices`);

                    // Log 3: Before UI updates
                    console.log('[Debug] About to update UI elements based on fetched models.');
                    
                    // Update UI elements that depend on allModels
                    if (currentModel) {
                        // Update controls for the initially selected model
                        updateMultimodalControls(currentModel);
                        updateSelectedModelCostIndicator(currentModel);
                    }
                    
                    // Update preset buttons now that we have cost bands
                    updatePresetButtonLabels();
                    
                    // If model selector is open, refresh it with complete data
                    if (modelSelector && modelSelector.style.display === 'block' && currentlyEditingPresetId) {
                        populateModelList(currentlyEditingPresetId);
                    }
                } else {
                    // Handle case where API call succeeded but returned no data
                    console.error('API call succeeded but no valid pricing data received:', data);
                    
                    // If not authenticated, provide fallback free models so the free preset works
                    if (!isAuthenticated) {
                        console.log('[Debug] No models returned from API, adding fallback free models for non-authenticated user');
                        allModels = [
                            {
                                id: 'google/gemini-2.0-flash-exp:free',
                                name: 'Gemini 2.0 Flash',
                                is_free: true,
                                is_multimodal: false,
                                pricing: { prompt: 0, completion: 0 },
                                cost_band: ''
                            },
                            {
                                id: 'qwen/qwq-32b:free',
                                name: 'Qwen 32B',
                                is_free: true,
                                is_multimodal: false,
                                pricing: { prompt: 0, completion: 0 },
                                cost_band: ''
                            },
                            {
                                id: 'deepseek/deepseek-r1-distill-qwen-32b:free',
                                name: 'Deepseek R1 Qwen 32B', 
                                is_free: true,
                                is_multimodal: false,
                                pricing: { prompt: 0, completion: 0 },
                                cost_band: ''
                            }
                        ];
                    } else {
                        allModels = []; // Clear models if fetch failed for authenticated users
                    }
                }
            })
            .catch(error => {
                // Log 4: Error in fetch
                console.error('[Debug] Error occurred in fetchAvailableModels:', error);
                console.error('Error fetching models and prices:', error);
                // For non-authenticated users, still provide fallback free models
                if (!isAuthenticated) {
                    console.log('[Debug] Error fetching models, adding fallback free models for non-authenticated user');
                    allModels = [
                        {
                            id: 'google/gemini-2.0-flash-exp:free',
                            name: 'Gemini 2.0 Flash',
                            is_free: true,
                            is_multimodal: false,
                            pricing: { prompt: 0, completion: 0 },
                            cost_band: ''
                        },
                        {
                            id: 'qwen/qwq-32b:free',
                            name: 'Qwen 32B',
                            is_free: true,
                            is_multimodal: false,
                            pricing: { prompt: 0, completion: 0 },
                            cost_band: ''
                        },
                        {
                            id: 'deepseek/deepseek-r1-distill-qwen-32b:free',
                            name: 'Deepseek R1 Qwen 32B', 
                            is_free: true,
                            is_multimodal: false,
                            pricing: { prompt: 0, completion: 0 },
                            cost_band: ''
                        }
                    ];
                } else {
                    // Clear models only for authenticated users who need accurate model data
                    allModels = []; 
                }
                
                // Show error in UI if model list is visible
                if (modelList && modelList.innerHTML === '') {
                    if (!isAuthenticated && currentlyEditingPresetId === '6') {
                        // For free preset, just populate with fallback models
                        populateModelList('6');
                    } else {
                        modelList.innerHTML = '<li>Error loading models.</li>';
                    }
                }
                
                // Even in case of error, expose models to window and dispatch event to notify mobile UI
                window.availableModels = allModels;
                console.log(`Script.js: Error fetching models, dispatching event with ${allModels.length} models`);
                // Create event for models error case
                const modelsErrorEvent = new CustomEvent('modelsLoaded', {
                    detail: { 
                        models: allModels,
                        count: allModels.length, 
                        error: true,
                        success: false
                    }
                });
                
                // Dispatch to both window and document
                window.dispatchEvent(modelsErrorEvent);
                document.dispatchEvent(modelsErrorEvent);
                
                // Return the models for promise chaining
                return allModels;
            });
    }
    
    // Function to open the model selector for a specific preset
    // Expose this function globally for mobile.js
    window.openModelSelector = function(presetId, buttonElement) {
        // Set current editing preset
        currentlyEditingPresetId = presetId;
        
        // For mobile: add a class to body when selector is active
        if (window.innerWidth <= 576) {
            document.body.classList.add('model-selector-active');
        }
        
        // Position the selector relative to the button
        const button = buttonElement || document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
        if (button) {
            const rect = button.getBoundingClientRect();
            const selectorRect = modelSelector.getBoundingClientRect();
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;
            
            // Calculate position with a gap
            const gap = 10; // Gap in pixels
            
            // Set default dimensions for selector
            const selectorWidth = 300; // Width of the selector
            const selectorHeight = selectorRect.height || 300; // Default if not visible yet
            
            // Mobile-specific positioning (centered in viewport)
            if (window.innerWidth <= 576) {
                // Center horizontally on the screen
                const leftPosition = Math.max(10, Math.floor((viewportWidth - selectorWidth) / 2));
                
                // Position vertically in the middle of the viewport
                const topPosition = Math.floor((viewportHeight - selectorHeight) / 2);
                
                // Apply centered position
                modelSelector.style.top = `${topPosition}px`;
                modelSelector.style.left = `${leftPosition}px`;
            } else {
                // Desktop positioning (relative to button)
                // Try to position above the button first
                let topPosition = rect.top - selectorHeight - gap;
                
                // Check if there's enough space above
                if (topPosition < 0) {
                    // Not enough space above, position below the button
                    topPosition = rect.bottom + gap;
                }
                
                // Center horizontally relative to the button
                let leftPosition = rect.left + (rect.width / 2) - (selectorWidth / 2);
                
                // Ensure the selector doesn't go off-screen
                if (leftPosition < 10) leftPosition = 10;
                if (leftPosition + selectorWidth > viewportWidth - 10) {
                    leftPosition = viewportWidth - selectorWidth - 10;
                }
                
                // Apply the position
                modelSelector.style.top = `${topPosition}px`;
                modelSelector.style.left = `${leftPosition}px`;
            }
            
            // Make visible
            modelSelector.style.display = 'block';
            
            // Clear search input
            modelSearch.value = '';
            
            // Populate model list for this preset
            populateModelList(presetId);
        }
    }
    
    // Function to close the model selector

    
    // Function to populate the model list based on preset filters
    // Expose this function globally for mobile UI
    window.populateModelList = function(presetId) {
        // Log 5: At function start
        console.log(`[Debug] populateModelList called for presetId: ${presetId}`);
        console.log(`[Debug] Current global allModels count: ${allModels ? allModels.length : 'undefined'}`);
        
        // Clear existing items
        modelList.innerHTML = '';
        
        // For FREE models (preset 6), ensure there's always at least the default free models available
        // This is especially important for non-logged in users where the API might not return models
        if (presetId === '6' && (!allModels || allModels.length === 0 || !allModels.some(m => m.is_free === true || m.id.includes(':free')))) {
            console.log('[Debug] No free models found in allModels, using fallback models for preset 6');
            
            // Create fallback list of free models
            const fallbackFreeModels = [
                {
                    id: 'google/gemini-2.0-flash-exp:free',
                    name: 'Gemini 2.0 Flash',
                    is_free: true,
                    is_multimodal: false,
                    pricing: { prompt: 0, completion: 0 },
                    cost_band: ''
                },
                {
                    id: 'qwen/qwq-32b:free',
                    name: 'Qwen 32B',
                    is_free: true,
                    is_multimodal: false,
                    pricing: { prompt: 0, completion: 0 },
                    cost_band: ''
                },
                {
                    id: 'deepseek/deepseek-r1-distill-qwen-32b:free',
                    name: 'Deepseek R1 Qwen 32B',
                    is_free: true,
                    is_multimodal: false,
                    pricing: { prompt: 0, completion: 0 },
                    cost_band: ''
                }
            ];
            
            // Use DocumentFragment for batch DOM updates
            const fragment = document.createDocumentFragment();
            
            // Add these fallback models to the fragment
            fallbackFreeModels.forEach(model => {
                const li = document.createElement('li');
                li.dataset.modelId = model.id;
                
                // Create free tag
                const freeTag = document.createElement('span');
                freeTag.className = 'free-tag';
                freeTag.textContent = 'FREE';
                
                // Create model name element
                const nameSpan = document.createElement('span');
                nameSpan.className = 'model-name';
                nameSpan.textContent = model.name;
                
                // Create provider span
                const providerSpan = document.createElement('span');
                providerSpan.className = 'model-provider';
                providerSpan.textContent = model.id.split('/')[0];
                
                // Assemble the elements
                li.appendChild(freeTag);
                li.appendChild(nameSpan);
                li.appendChild(providerSpan);
                
                // Add click handler to select this model
                li.addEventListener('click', function() {
                    selectModelForPreset(presetId, model.id);
                });
                
                // Add to the fragment instead of directly to DOM
                fragment.appendChild(li);
            });
            
            // Add the fragment to the DOM in one operation
            modelList.appendChild(fragment);
            
            // Exit early as we've already populated the list with fallback models
            return;
        }
        
        // Standard case - API returned models properly
        if (!allModels || allModels.length === 0) {
            const placeholder = document.createElement('li');
            placeholder.textContent = 'Loading models...';
            modelList.appendChild(placeholder);
            return;
        }
        
        // Get filter function for this preset
        const filterFn = presetFilters[presetId] || (() => true);
        
        // Filter and sort models
        const filteredModels = allModels
            .filter(filterFn)
            .sort((a, b) => {
                // Preset 2 ONLY: Sort by context length first (for context-focused models)
                if (presetId === '2') {
                    // Primary sort: Context Length (descending)
                    const aContext = parseInt(a.context_length) || 0;
                    const bContext = parseInt(b.context_length) || 0;
                    if (aContext !== bContext) {
                        return bContext - aContext;
                    }
                    
                    // Secondary sort: Input Price (ascending)
                    const aPrice = a.pricing?.prompt || 0;
                    const bPrice = b.pricing?.prompt || 0;
                    if (aPrice !== bPrice) {
                        return aPrice - bPrice;
                    }
                    
                    // Tertiary sort: Model Name (alphabetical)
                    return a.name.localeCompare(b.name);
                }
                
                // For Presets 1, 3, 4, 5, and 6: ELO-based sorting
                
                // Primary sort: ELO Score (descending, higher is better)
                const aElo = a.elo_score || 0;
                const bElo = b.elo_score || 0;
                
                // Models with ELO scores come before models without ELO scores
                if (aElo > 0 && bElo === 0) return -1;
                if (aElo === 0 && bElo > 0) return 1;
                
                // Both have ELO scores - sort by ELO (descending)
                if (aElo !== bElo) {
                    return bElo - aElo;
                }
                
                // Secondary sort: Context Length (descending)
                const aContext = parseInt(a.context_length) || 0;
                const bContext = parseInt(b.context_length) || 0;
                if (aContext !== bContext) {
                    return bContext - aContext;
                }
                
                // Tertiary sort: Input Price (ascending)
                const aPrice = a.pricing?.prompt || 0;
                const bPrice = b.pricing?.prompt || 0;
                if (aPrice !== bPrice) {
                    return aPrice - bPrice;
                }
                
                // Quaternary sort: Model Name (alphabetical)
                return a.name.localeCompare(b.name);
            });
        
        // Log 6: After filtering
        console.log(`[Debug] Filtered models count for preset ${presetId}: ${filteredModels.length}`);
        if (filteredModels.length === 0 && allModels && allModels.length > 0) {
            console.warn(`[Debug] Filtering for preset ${presetId} resulted in 0 models. Check filter logic and model properties.`);
            // Log the filter function itself if possible
            console.log('[Debug] Filter function:', filterFn.toString());
            // Log the first few models from allModels again for comparison
            console.log('[Debug] First few models in allModels before filtering:', JSON.stringify(allModels.slice(0, 3), null, 2));
        }
        
        // Use DocumentFragment for batch DOM updates
        const fragment = document.createDocumentFragment();
        
        // Add each model to the fragment
        filteredModels.forEach(model => {
            // Log 7: Inside rendering loop
            console.log(`[Debug] Rendering list item for model: ${model.id}, Band: ${model.cost_band}`);
            
            const li = document.createElement('li');
            li.dataset.modelId = model.id;
            
            // Create model name element
            const nameSpan = document.createElement('span');
            nameSpan.className = 'model-name';
            // Use our display name mapping if available
            if (defaultModelDisplayNames[model.id]) {
                nameSpan.textContent = defaultModelDisplayNames[model.id];
            } else {
                nameSpan.textContent = model.name;
            }
            
            // Add cost band indicator if available
            if (model.cost_band) {
                const costSpan = document.createElement('span');
                costSpan.textContent = model.cost_band;
                costSpan.className = 'cost-band-indicator';
                
                // Add the specific band class based on the band value
                if (model.cost_band === '$$$$') {
                    costSpan.classList.add('cost-band-4-danger');
                } else if (model.cost_band === '$$$') {
                    costSpan.classList.add('cost-band-3-warn');
                } else if (model.cost_band === '$$') {
                    costSpan.classList.add('cost-band-2');
                } else if (model.cost_band === '$') {
                    costSpan.classList.add('cost-band-1');
                } else {
                    // For empty band (free models)
                    costSpan.classList.add('cost-band-free');
                }
                
                nameSpan.appendChild(costSpan);
            }
            
            // Create provider badge
            const providerSpan = document.createElement('span');
            providerSpan.className = 'model-provider';
            providerSpan.textContent = model.id.split('/')[0];
            
            // Add badge for free models
            if (model.is_free === true || model.id.includes(':free')) {
                const freeTag = document.createElement('span');
                freeTag.className = 'free-tag';
                freeTag.textContent = 'FREE';
                li.appendChild(freeTag);
            }
            
            li.appendChild(nameSpan);
            li.appendChild(providerSpan);
            
            // Add click handler to select this model
            li.addEventListener('click', function() {
                selectModelForPreset(currentlyEditingPresetId, model.id);
            });
            
            // Add to fragment instead of directly to DOM
            fragment.appendChild(li);
        });
        
        // Add the fragment to the DOM in one operation
        modelList.appendChild(fragment);
        
        // If no models match the filter
        if (filteredModels.length === 0) {
            const noResults = document.createElement('li');
            noResults.textContent = 'No models found';
            modelList.appendChild(noResults);
        }
    }
    

    
    // Function to select a model for a preset and save the preference
    // Expose this function globally for mobile UI
window.selectModelForPreset = function(presetId, modelId, skipActivation) {
        // Check if trying to assign a free model to a non-free preset
        const isFreeModel = modelId.includes(':free') || allModels.some(m => m.id === modelId && m.is_free === true);
        if (presetId !== '6' && isFreeModel) {
            alert('Free models can only be selected for Preset 6');
            return;
        }
        
        // Update the UI
        const button = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
        if (button) {
            const nameSpan = button.querySelector('.model-name');
            if (nameSpan) {
                // Special handling for preset 6 (Free Model)
                if (presetId === '6') {
                    if (defaultModelDisplayNames[modelId]) {
                        nameSpan.textContent = 'FREE - ' + defaultModelDisplayNames[modelId];
                    } else {
                        nameSpan.textContent = 'FREE - ' + formatModelName(modelId, true);
                    }
                } else {
                    if (defaultModelDisplayNames[modelId]) {
                        nameSpan.textContent = defaultModelDisplayNames[modelId];
                    } else {
                        nameSpan.textContent = formatModelName(modelId);
                    }
                }
            }
        }
        
        // Update local state
        userPreferences[presetId] = modelId;
        
        // If this is the active preset, update the current model
        if (presetId === currentPresetId) {
            currentModel = modelId;
            
            // Update multimodal controls based on the selected model
            updateMultimodalControls(modelId);
        }
        
        // Save preference to server
        saveModelPreference(presetId, modelId);
        
        // Close the selector
        closeModelSelector();
        
        // For the desktop flow, automatically activate the preset we just updated
        // For mobile, we'll handle this separately to avoid duplicate calls
        if (!skipActivation && presetId !== currentPresetId) {
            // Log for debugging
            console.log(`Auto-activating preset ${presetId} after model selection`);
            
            // Select the preset button to actually use this model
            window.selectPresetButton(presetId);
        }
    }
    
    // Function to reset a preset or all presets to default
    // Expose this function globally for mobile UI
window.resetToDefault = function(presetId) {
        if (!confirm(presetId ? `Reset preset ${presetId} to its default model?` : 'Reset all model presets to their defaults?')) {
            return;
        }
        
        // Prepare the request data
        const requestData = presetId ? { preset_id: presetId } : {};
        
        // Show loading state on button
        const resetBtn = document.getElementById('reset-to-default');
        if (resetBtn) {
            resetBtn.classList.add('loading');
            resetBtn.disabled = true;
        }
        
        // Call the API to reset preference(s)
        fetch('/reset_preferences', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Reset preferences response:', data);
            
            // If reset was successful, reload the preferences
            if (data.success) {
                // If resetting a specific preset, update it locally
                if (presetId) {
                    userPreferences[presetId] = defaultModels[presetId];
                    
                    // Update the button label right away
                    const button = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
                    if (button) {
                        const nameSpan = button.querySelector('.model-name');
                        if (nameSpan) {
                            // Special handling for preset 6 (Free Model)
                            if (presetId === '6') {
                                if (defaultModelDisplayNames[defaultModels[presetId]]) {
                                    nameSpan.textContent = 'FREE - ' + defaultModelDisplayNames[defaultModels[presetId]];
                                } else {
                                    nameSpan.textContent = 'FREE - ' + formatModelName(defaultModels[presetId], true);
                                }
                            } else {
                                if (defaultModelDisplayNames[defaultModels[presetId]]) {
                                    nameSpan.textContent = defaultModelDisplayNames[defaultModels[presetId]];
                                } else {
                                    nameSpan.textContent = formatModelName(defaultModels[presetId]);
                                }
                            }
                        }
                    }
                    
                    // If the reset preset is the active one, update the model
                    if (presetId === currentPresetId) {
                        currentModel = defaultModels[presetId];
                        updateMultimodalControls(currentModel);
                    }
                } else {
                    // Full reset - reload all preferences from server
                    window.fetchUserPreferences();
                }
                
                // Show feedback
                alert(data.message || 'Reset successful!');
                
                // Close the model selector
                closeModelSelector();
            }
        })
        .catch(error => {
            console.error('Error resetting preferences:', error);
            alert('Error resetting preferences. Please try again.');
        })
        .finally(() => {
            // Remove loading state
            if (resetBtn) {
                resetBtn.classList.remove('loading');
                resetBtn.disabled = false;
            }
        });
    }
    
    // Function to save model preference to the server
    // Expose this function globally for mobile UI
    window.saveModelPreference = function(presetId, modelId, buttonElement) {
        fetch('/save_preference', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                preset_id: presetId,
                model_id: modelId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Preference saved:', data);
            
            // Show success feedback if button element was provided
            if (buttonElement) {
                buttonElement.classList.remove('loading');
                
                // Optional: Show a brief success indicator
                buttonElement.classList.add('save-success');
                setTimeout(() => {
                    buttonElement.classList.remove('save-success');
                }, 1000);
            }
        })
        .catch(error => {
            console.error('Error saving preference:', error);
            
            // Remove loading state and show error if button element was provided
            if (buttonElement) {
                buttonElement.classList.remove('loading');
                buttonElement.classList.add('save-error');
                
                // Remove error state after a short time
                setTimeout(() => {
                    buttonElement.classList.remove('save-error');
                }, 2000);
            }
            
            // Optionally display an error notification
            console.warn('Could not save preference. Please try again.');
        });
    }
    
    // New chat button
    if (newChatButton) {
        newChatButton.addEventListener('click', function() {
            // Add a loading effect to the button
            const originalContent = newChatButton.innerHTML;
            newChatButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating...';
            newChatButton.disabled = true;
            
            // First, check if the current conversation is already empty
            // If it is, we can just reuse it instead of creating a new one
            const userIsLoggedIn = !!document.getElementById('logout-btn');
            if (userIsLoggedIn && currentConversationId) {
                fetch(`/api/conversation/${currentConversationId}/is-empty`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success && data.is_empty) {
                            // Current conversation is already empty, just reuse it
                            console.log(`Current conversation ${currentConversationId} is already empty, reusing it`);
                            
                            // Clear chat UI
                            clearChat();
                            
                            // Restore button state
                            newChatButton.innerHTML = originalContent;
                            newChatButton.disabled = false;
                            
                            // No need to refresh the conversation list since we're using the same conversation
                            return;
                        } else {
                            // Current conversation has messages, create a new one
                            createNewConversation();
                        }
                    })
                    .catch(error => {
                        console.error('Error checking if conversation is empty:', error);
                        // On error, just create a new conversation
                        createNewConversation();
                    });
            } else {
                // No current conversation, create a new one
                createNewConversation();
            }
            
            // Function to create a new conversation
            function createNewConversation() {
                // Clear chat UI
                clearChat();
                
                // Reset currentConversationId as a fallback in case API call fails
                currentConversationId = null;
                
                // Check authentication status directly
                const userIsLoggedIn = !!document.getElementById('logout-btn');
                if (!userIsLoggedIn) {
                    // No authentication, just restore button state
                    newChatButton.innerHTML = originalContent;
                    newChatButton.disabled = false;
                    return;
                }
                
                // Schedule idle cleanup instead of blocking with synchronous cleanup
                performIdleCleanup();
                
                // Create a new conversation immediately
                fetch('/api/create-conversation', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    }
                })
                .then(response => response.json())
                .then(data => {
                    // Restore button state
                    newChatButton.innerHTML = originalContent;
                    newChatButton.disabled = false;
                    
                    if (data.success && data.conversation) {
                        // Set the current conversation ID to the new one
                        currentConversationId = data.conversation.id;
                        console.log(`Created new conversation with ID: ${currentConversationId}`);
                        
                        // Update the sidebar with the new conversation
                        fetchConversations(true);
                    } else {
                        console.error('Failed to create new conversation:', data.error || 'Unknown error');
                    }
                })
                .catch(error => {
                    // Restore button state
                    newChatButton.innerHTML = originalContent;
                    newChatButton.disabled = false;
                    
                    console.error('Error creating new conversation:', error);
                });
            }
        });
    }
    
    // Clear conversations button
    if (clearConversationsButton) {
        clearConversationsButton.addEventListener('click', function() {
            // Clear chat and reset conversation items in sidebar
            clearChat();
            // In a real app, you would also clear the storage/backend
        });
    }
    
    // Example question button
    if (exampleQuestionButton) {
        exampleQuestionButton.addEventListener('click', function() {
            const exampleQuestions = [
                "What are the major differences between renewable and fossil fuel energy sources?",
                "Can you explain how artificial intelligence works in simple terms?",
                "What are some effective strategies for reducing carbon emissions?",
                "How does quantum computing differ from classical computing?",
                "What are the potential implications of gene editing technologies?"
            ];
            
            // Select a random example question
            const randomQuestion = exampleQuestions[Math.floor(Math.random() * exampleQuestions.length)];
            
            // Set the input value and trigger sending
            if (messageInput) {
                messageInput.value = randomQuestion;
                sendMessage();
            }
        });
    }
    

    
    // Function to add Perplexity citations to a message
    function addPerplexityCitationsToMessage(messageElement, citations) {
        if (!citations || !citations.length) return;
        
        // Find or create the citations container
        let citationsContainer = messageElement.querySelector('.perplexity-citations');
        if (!citationsContainer) {
            citationsContainer = document.createElement('div');
            citationsContainer.className = 'perplexity-citations';
            
            // Add header
            const header = document.createElement('div');
            header.className = 'citations-header';
            header.innerHTML = '<i class="fa-solid fa-link"></i> Sources';
            citationsContainer.appendChild(header);
            
            // Add the container to the message
            const messageWrapper = messageElement.querySelector('.message-wrapper');
            if (messageWrapper) {
                messageWrapper.appendChild(citationsContainer);
            } else {
                messageElement.appendChild(citationsContainer);
            }
        }
        
        // Clear existing citations list
        const linksList = citationsContainer.querySelector('ul') || document.createElement('ul');
        linksList.innerHTML = '';
        
        // Add each citation as a link
        citations.forEach((citation, index) => {
            const li = document.createElement('li');
            const link = document.createElement('a');
            link.href = citation;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            
            // Create a display URL (truncate if too long)
            let displayUrl = citation;
            if (citation.length > 50) {
                // Extract domain for better display
                try {
                    const url = new URL(citation);
                    displayUrl = url.hostname + url.pathname.substring(0, 20) + '...';
                } catch (e) {
                    displayUrl = citation.substring(0, 47) + '...';
                }
            }
            
            link.textContent = displayUrl;
            li.appendChild(link);
            linksList.appendChild(li);
        });
        
        // Add the links list to the container if it's not already there
        if (!citationsContainer.querySelector('ul')) {
            citationsContainer.appendChild(linksList);
        }
    }
    
    // Function to add message to chat
    // Function to create a message element without adding it to the DOM
    function createMessageElement(content, sender, isTyping = false, metadata = null) {
        // Create the main message container
        const messageElement = document.createElement('div');
        messageElement.className = `message message-${sender}`;
        messageElement.dataset.messageId = metadata ? metadata.id : Date.now(); // Use actual message ID if available
        
        // Create avatar
        const avatar = document.createElement('div');
        avatar.className = `message-avatar ${sender}`;
        
        if (sender === 'user') {
            avatar.textContent = 'U';
        } else {
            avatar.textContent = 'A';
        }
        
        // Create wrapper for content, actions, and metadata
        const messageWrapper = document.createElement('div');
        messageWrapper.className = 'message-wrapper';
        
        // Create content container
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        return {
            messageElement,
            avatar,
            messageWrapper,
            messageContent
        };
    }
    
    // Function to add a message to the chat

    
    // Function to add typing indicator
    function addTypingIndicator() {
        return addMessage('', 'assistant', true);
    }
    
    // Function to fetch conversations from the backend
    function fetchConversations(bustCache = false, metadataOnly = true) {
        // Make this function globally available for other scripts
        window.fetchConversations = fetchConversations;
        // Check if user is logged in - if not, show login prompt instead of loading
        // userIsLoggedIn is passed from the template
        if (typeof userIsLoggedIn !== 'undefined' && !userIsLoggedIn) {
            console.log("User is not logged in, showing login prompt");
            
            // Display login prompt in the conversations list
            if (conversationsList) {
                conversationsList.innerHTML = `
                    <div class="login-prompt">
                        <p>Sign in to save your conversations and access them from any device.</p>
                        <a href="/login" class="btn auth-btn">Sign in</a>
                    </div>
                `;
            }
            return; // Exit early if user is not logged in
        }
        
        // Build URL with parameters
        // 1. Always use cache busting to ensure we get the latest titles
        // 2. Use metadata_only to optimize initial loading (titles only, without content)
        const url = `/conversations?_=${Date.now()}&metadata_only=${metadataOnly}`;
        
        console.log(`Fetching conversations list with cache busting (metadata_only=${metadataOnly})`);
        
        // Show loading indicator if conversations list element exists
        if (conversationsList) {
            // Check if loading indicator already exists
            let loadingIndicator = conversationsList.querySelector('.loading-indicator');
            if (!loadingIndicator) {
                // Create loading indicator if it doesn't exist
                loadingIndicator = document.createElement('div');
                loadingIndicator.className = 'loading-indicator';
                loadingIndicator.innerHTML = `
                    <div class="loading-spinner"></div>
                    <div class="loading-text">Loading conversations...</div>
                `;
                conversationsList.innerHTML = '';
                conversationsList.appendChild(loadingIndicator);
            }
        }
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("Got conversations data:", data);
                if (data.conversations && data.conversations.length > 0) {
                    // Clear existing conversations
                    if (conversationsList) {
                        console.log("Clearing and rebuilding conversation list...");
                        conversationsList.innerHTML = '';
                        
                        // Add each conversation to the sidebar
                        data.conversations.forEach(conversation => {
                            console.log(`Adding conversation to UI: ID=${conversation.id}, Title='${conversation.title}'`);
                            const conversationItem = document.createElement('div');
                            conversationItem.className = 'conversation-item';
                            conversationItem.dataset.id = conversation.id;
                            
                            // Add 'active' class if this is the current conversation
                            if (conversation.id.toString() === currentConversationId?.toString()) {
                                conversationItem.classList.add('active');
                                console.log(`Marked conversation ${conversation.id} as active`);
                            }
                            
                            // Create title and date elements to match the HTML structure
                            const titleDiv = document.createElement('div');
                            titleDiv.className = 'conversation-title';
                            titleDiv.textContent = conversation.title;
                            
                            // Add edit button for renaming conversations
                            const editButton = document.createElement('button');
                            editButton.className = 'edit-conversation-btn';
                            editButton.title = 'Rename conversation';
                            editButton.innerHTML = '<i class="fa-solid fa-edit"></i>';
                            
                            // Add click event to edit button
                            editButton.addEventListener('click', function(e) {
                                e.stopPropagation(); // Prevent triggering the conversation item click
                                openRenameModal(conversation.id, conversation.title);
                            });
                            
                            const dateDiv = document.createElement('div');
                            dateDiv.className = 'conversation-date';
                            
                            // Format the date (using relative time if possible)
                            const createdDate = new Date(conversation.created_at);
                            const now = new Date();
                            const diffDays = Math.floor((now - createdDate) / (1000 * 60 * 60 * 24));
                            
                            if (diffDays < 1) {
                                dateDiv.textContent = 'Today';
                            } else if (diffDays === 1) {
                                dateDiv.textContent = 'Yesterday';
                            } else if (diffDays < 7) {
                                dateDiv.textContent = `${diffDays} days ago`;
                            } else {
                                dateDiv.textContent = createdDate.toLocaleDateString();
                            }
                            
                            // Append title, edit button, and date to conversation item
                            conversationItem.appendChild(titleDiv);
                            conversationItem.appendChild(editButton);
                            conversationItem.appendChild(dateDiv);
                            
                            // Add click event to load conversation
                            conversationItem.addEventListener('click', function() {
                                console.log(`Loading conversation: ${conversation.id}`);
                                
                                // Remove active class from all conversation items
                                const allItems = conversationsList.querySelectorAll('.conversation-item');
                                allItems.forEach(item => item.classList.remove('active'));
                                
                                // Add active class to this item
                                conversationItem.classList.add('active');
                                
                                // Load the conversation
                                loadConversation(conversation.id);
                            });
                            
                            conversationsList.appendChild(conversationItem);
                        });
                        
                        // Verify the DOM was updated correctly
                        const itemsAdded = conversationsList.querySelectorAll('.conversation-item');
                        console.log(`Conversation list rebuilt with ${itemsAdded.length} items`);
                    } else {
                        console.error("Cannot update conversation list - conversationsList element not found");
                    }
                } else {
                    console.warn("No conversations returned from server or empty array");
                }
            })
            .catch(error => {
                console.error('Error fetching conversations:', error);
            });
    }
    
    // Function to load a specific conversation
    function loadConversation(conversationId) {
        // Make sure chatMessages exists
        if (!chatMessages) {
            console.error('Chat messages container not found');
            return;
        }
        
        // Clear the current chat
        chatMessages.innerHTML = '';
        messageHistory = [];
        currentConversationId = conversationId;
        
        console.log(`Loading conversation ID: ${conversationId}`);
        
        // Highlight active conversation in sidebar
        if (conversationsList) {
            const allConversations = conversationsList.querySelectorAll('.conversation-item');
            allConversations.forEach(item => {
                item.classList.remove('active');
                if (item.dataset.id === conversationId.toString()) {
                    item.classList.add('active');
                }
            });
        }
        
        // Add a loading indicator to chat area
        const loadingMessage = document.createElement('div');
        loadingMessage.className = 'system-message';
        loadingMessage.textContent = 'Loading conversation...';
        chatMessages.appendChild(loadingMessage);
        
        // Show chat interface immediately with loading indicator
        // This allows UI to be responsive while messages load
        
        // Fetch conversation messages from the server (with a slight delay for UI responsiveness)
        setTimeout(() => {
            fetch(`/conversation/${conversationId}/messages`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    // Remove loading indicator
                    if (chatMessages && chatMessages.contains(loadingMessage)) {
                        chatMessages.removeChild(loadingMessage);
                    }
                    
                    console.log(`Loaded ${data.messages.length} messages for conversation ${conversationId}`);
                    
                    // Check if there are messages
                    if (data.messages.length === 0) {
                        // Display empty conversation message
                        const emptyMessage = document.createElement('div');
                        emptyMessage.className = 'system-message';
                        emptyMessage.textContent = 'This conversation is empty. Start chatting now!';
                        chatMessages.appendChild(emptyMessage);
                        return;
                    }
                    
                    // Progressive message loading
                    // First add only the most recent messages for immediate visibility
                    const MAX_INITIAL_MESSAGES = 10;
                    const messagesToRender = data.messages.slice(-MAX_INITIAL_MESSAGES);
                    const remainingMessages = data.messages.slice(0, -MAX_INITIAL_MESSAGES);
                    
                    // Process all messages for the message history (needed for context)
                    data.messages.forEach(message => {
                        // Add to message history (skip system messages)
                        if (message.role !== 'system') {
                            messageHistory.push({
                                role: message.role,
                                content: message.content
                            });
                        }
                    });
                    
                    // Render the most recent messages first
                    messagesToRender.forEach(message => {
                        // Add message to UI (skip system messages)
                        if (message.role !== 'system') {
                            const metadata = {
                                id: message.id,
                                model: message.model,
                                rating: message.rating,
                                created_at: message.created_at,
                                image_url: message.image_url // Include image URL if available
                            };
                            addMessage(message.content, message.role, false, metadata);
                        }
                    });
                    
                    // Scroll to bottom to show the most recent messages
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                    
                    // If there are older messages, add them after a short delay
                    if (remainingMessages.length > 0) {
                        setTimeout(() => {
                            // Create a document fragment to reduce reflows
                            const fragment = document.createDocumentFragment();
                            
                            // Add older messages in reverse chronological order (newest first)
                            for (let i = remainingMessages.length - 1; i >= 0; i--) {
                                const message = remainingMessages[i];
                                
                                // Skip system messages
                                if (message.role !== 'system') {
                                    // Get message elements
                                    const elements = createMessageElement(
                                        message.content, 
                                        message.role, 
                                        false, 
                                        {
                                            id: message.id,
                                            model: message.model,
                                            rating: message.rating,
                                            created_at: message.created_at,
                                            image_url: message.image_url
                                        }
                                    );
                                    
                                    // Set up message content like in addMessage
                                    const { messageElement, avatar, messageWrapper, messageContent } = elements;
                                    
                                    // Format message content based on type
                                    if (typeof message.content === 'object' && Array.isArray(message.content)) {
                                        // Handle content array format (same as in addMessage)
                                        // Processing would go here
                                        messageContent.innerHTML = formatMessage(message.content);
                                    } else {
                                        // Format regular text content
                                        messageContent.innerHTML = formatMessage(message.content);
                                    }
                                    
                                    // Add message action buttons, metadata etc.
                                    // This would be similar to addMessage implementation
                                    
                                    // Assemble message
                                    messageWrapper.appendChild(messageContent);
                                    messageElement.appendChild(avatar);
                                    messageElement.appendChild(messageWrapper);
                                    
                                    // Add to fragment
                                    fragment.appendChild(messageElement);
                                }
                            }
                            
                            // Insert the older messages at the beginning of the chat
                            if (chatMessages.firstChild) {
                                chatMessages.insertBefore(fragment, chatMessages.firstChild);
                            } else {
                                chatMessages.appendChild(fragment);
                            }
                            
                            // We don't scroll to these older messages since they're above the viewport
                        }, 100); // Short delay to prioritize UI responsiveness
                    }
                })
                .catch(error => {
                    console.error('Error loading conversation:', error);
                    
                    // Remove loading indicator and show error message
                    if (chatMessages && chatMessages.contains(loadingMessage)) {
                        chatMessages.removeChild(loadingMessage);
                    }
                    
                    const errorMessage = document.createElement('div');
                    errorMessage.className = 'system-message error';
                    errorMessage.textContent = `Error loading conversation: ${error.message}`;
                    chatMessages.appendChild(errorMessage);
                });
        }, 50); // Small delay to allow UI to render first
    }
    
    // Function to send message to backend and process streaming response
    function sendMessageToBackend(message, modelId, typingIndicator) {
        // Check if we need to make a multimodal message or have any attachments
        const hasImages = attachedImageUrls && attachedImageUrls.length > 0;
        const hasPdf = attachedPdfUrl !== null;
        const hasAttachments = hasImages || hasPdf;
        
        // Always create a content array (OpenRouter's unified format)
        // Even for text-only messages, this ensures consistent payload structure
        let userMessageContent = [
            { type: 'text', text: message }
        ];
        
        // Create payload object with model and conversation info
        const payload = {
            model: modelId,
            stream: true,
            message: message,
            conversation_id: currentConversationId
        };
        
        // Add attachments to content array if available
        if (hasAttachments) {
            // Add each image URL to the content array
            if (hasImages) {
                for (const imageUrl of attachedImageUrls) {
                    userMessageContent.push({ 
                        type: 'image_url', 
                        image_url: { url: imageUrl } 
                    });
                }
                
                // Add first image URL separately for backward compatibility with backend
                // This ensures older endpoints still work
                payload.image_url = attachedImageUrls[0];
                
                // Add an array of all image URLs as well
                payload.image_urls = attachedImageUrls;
                
                console.log(`📸 Including ${attachedImageUrls.length} images in message`);
            }
            
            // Add PDF to content array if present
            if (hasPdf) {
                userMessageContent.push({
                    type: 'file',
                    file: { 
                        filename: attachedPdfName || 'document.pdf',
                        file_data: attachedPdfUrl
                    }
                });
                
                // Add PDF URL to payload for backend compatibility
                payload.pdf_url = attachedPdfUrl;
                payload.pdf_filename = attachedPdfName;
                
                console.log(`📄 Including PDF document in message: ${attachedPdfName}`);
            }
            
            // Check if the model supports images and PDFs
            const model = allModels.find(m => m.id === modelId);
            const isMultimodalModel = model && model.is_multimodal === true;
            const supportsPdf = model && model.supports_pdf === true;
            
            // Warn if trying to send images to a non-multimodal model
            if (hasImages && !isMultimodalModel) {
                console.warn(`⚠️ Warning: Model ${modelId} does not support images, but images are being sent`);
            }
            
            // Warn if trying to send PDFs to a model that doesn't support them
            if (hasPdf && !supportsPdf) {
                console.warn(`⚠️ Warning: Model ${modelId} does not support PDF documents, but a PDF is being sent`);
            }
            
            // No longer clearing attachments here
            // We'll clear them after the full call is complete in sendMessage()
            // This ensures the data is available during the API call
        }
        
        // Add user message to history with standardized content array format
        messageHistory.push({
            role: 'user',
            content: userMessageContent
        });
        
        // If no model selected, use default
        if (!modelId) {
            modelId = defaultModels['1'];
            console.warn('No model selected, using default:', modelId);
        }
        
        // Add structured message format to payload
        payload.messages = [
            { 
                role: 'user', 
                content: userMessageContent
            }
        ];
        
        // Log the full payload for debugging
        console.log('📤 Sending payload to backend:', JSON.stringify(payload, null, 2));
        
        // Safari-compatible chunk handler function
        function handleStreamChunk(data, messageContent, assistantMessageElement, responseTextRef) {
            if (data.type === 'content' && data.content) {
                responseTextRef += data.content;
                if (messageContent) {
                    messageContent.innerHTML = formatMessage(responseTextRef);
                }
                
                // Auto-scroll if user is near bottom
                if (chatMessages) {
                    const shouldScroll = chatMessages.scrollTop + chatMessages.clientHeight >= chatMessages.scrollHeight - 10;
                    if (shouldScroll) {
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                    }
                }
            } else if (data.type === 'reasoning' && data.reasoning) {
                // Handle reasoning display similar to original implementation
                if (assistantMessageElement) {
                    let reasoningContainer = assistantMessageElement.querySelector('.reasoning-container');
                    if (!reasoningContainer) {
                        reasoningContainer = document.createElement('div');
                        reasoningContainer.className = 'reasoning-container';
                        assistantMessageElement.insertBefore(reasoningContainer, messageContent);
                    }
                    
                    let reasoningContent = reasoningContainer.querySelector('.reasoning-content');
                    if (!reasoningContent) {
                        const reasoningHeader = document.createElement('div');
                        reasoningHeader.className = 'reasoning-header';
                        reasoningHeader.innerHTML = '<span class="reasoning-toggle">▼</span> Reasoning';
                        
                        reasoningContent = document.createElement('div');
                        reasoningContent.className = 'reasoning-content';
                        
                        reasoningContainer.appendChild(reasoningHeader);
                        reasoningContainer.appendChild(reasoningContent);
                        
                        // Add toggle functionality
                        reasoningHeader.addEventListener('click', () => {
                            const toggle = reasoningHeader.querySelector('.reasoning-toggle');
                            if (reasoningContent.style.display === 'none') {
                                reasoningContent.style.display = 'block';
                                toggle.textContent = '▼';
                                reasoningContainer.classList.add('reasoning-expanded');
                            } else {
                                reasoningContent.style.display = 'none';
                                toggle.textContent = '▶';
                                reasoningContainer.classList.remove('reasoning-expanded');
                            }
                        });
                    }
                    
                    reasoningContent.innerHTML = formatMessage(data.reasoning);
                }
            } else if (data.type === 'metadata') {
                console.log('Received metadata:', data.metadata);
                // Handle conversation saving and other metadata processing
                if (data.metadata && data.metadata.id) {
                    currentConversationId = data.metadata.id;
                    fetchConversations(true, true);
                }
            } else if (data.type === 'error') {
                console.error('Stream error:', data.error);
                if (messageContent) {
                    messageContent.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
                }
            }
        }
        
        // Remove typing indicator - with extra safe checks
        if (typingIndicator && chatMessages) {
            try {
                if (chatMessages.contains(typingIndicator)) {
                    chatMessages.removeChild(typingIndicator);
                }
            } catch (e) {
                console.warn('Error removing typing indicator:', e);
            }
        }
        
        // Add empty assistant message
        const assistantMessageElement = addMessage('', 'assistant');
        const messageContent = assistantMessageElement.querySelector('.message-content');
        let responseText = '';
        
        // Use Safari-compatible streaming
        if (window.safariStreamingCompat) {
            window.safariStreamingCompat.handleStreamingResponse(
                '/chat',
                payload,
                // onChunk callback
                (data) => {
                    handleStreamChunk(data, messageContent, assistantMessageElement, responseText);
                },
                // onError callback
                (error) => {
                    console.error('Streaming error:', error);
                    if (messageContent) {
                        messageContent.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
                    }
                },
                // onComplete callback
                () => {
                    console.log('Streaming completed');
                }
            );
        } else {
            // Fallback to original fetch method if Safari compatibility not loaded
            console.warn('Safari compatibility layer not loaded, using standard fetch');
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify(payload)
            }).then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                
                // Setup event source for streaming
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                
                // Function to process chunks
                function processChunks() {
                    return reader.read().then(({ done, value }) => {
                        if (done) {
                            console.log("Stream closed by server");
                            return;
                        }
                        
                        // Decode the chunk and add to buffer
                        buffer += decoder.decode(value, { stream: true });
                    
                    // Split by double newlines (SSE standard)
                    const potentialMessages = buffer.split('\n\n');
                    // Keep the last (potentially incomplete) chunk in the buffer
                    buffer = potentialMessages.pop(); // Keep incomplete message in buffer

                    // Process each complete message
                    for (const message of potentialMessages) {
                        if (message.trim() === '') continue;
                        
                        if (message.startsWith('data: ')) {
                            const data = message.substring(6).trim(); // Remove 'data: ' and trim
                            
                            if (!data) continue; // Skip empty data lines

                            try {
                                // Trim the data to ensure there's no whitespace causing parsing issues
                                const trimmedData = data.trim();
                                if (!trimmedData) {
                                    console.log("Empty data after trimming, skipping");
                                    continue;
                                }
                                
                                const parsedData = JSON.parse(trimmedData);
                                console.log("==> Received SSE Data:", parsedData); // ADD THIS LOG
                                
                                // --- Handle different data types ---
                                if (parsedData.type === 'error' || parsedData.error) {
                                    console.log("==> Processing type: error"); // ADD THIS LOG
                                    const errorMsg = parsedData.error || 'Unknown error occurred';
                                    messageContent.innerHTML = `<span class="error">Error: ${errorMsg}</span>`;
                                    
                                    // Apply the repaint to ensure error content is visible
                                    forceRepaint(messageContent);
                                    
                                    console.error("Received error from backend:", errorMsg);
                                    // Optionally re-enable input/button here if desired
                                    // messageInput.disabled = false;
                                    // sendButton.disabled = false;
                                    return; // Stop processing on error
                                
                                } else if (parsedData.type === 'content') {
                                    console.log("==> Processing type: content"); // ADD THIS LOG
                                    
                                    // If this is the first content chunk, collapse the reasoning section if it exists
                                    if (!responseText && parsedData.content) {
                                        // Find the reasoning container for this message
                                        const reasoningContainer = assistantMessageElement.querySelector('.message-reasoning');
                                        if (reasoningContainer) {
                                            const reasoningContent = reasoningContainer.querySelector('.reasoning-content');
                                            const reasoningToggle = reasoningContainer.querySelector('.reasoning-toggle');
                                            
                                            if (reasoningContent && reasoningContent.style.display === 'block') {
                                                // Collapse the reasoning section
                                                reasoningContent.style.display = 'none';
                                                if (reasoningToggle) {
                                                    reasoningToggle.textContent = '▶';
                                                }
                                                reasoningContainer.classList.remove('reasoning-expanded');
                                                console.log("==> Automatically collapsed reasoning as content begins streaming");
                                            }
                                        }
                                    }
                                    
                                    // Append content
                                    if (parsedData.content) {
                                        // Track if we need to scroll (check if chatMessages exists first)
                                        let shouldScroll = false;
                                        if (chatMessages) {
                                            shouldScroll = chatMessages.scrollTop + chatMessages.clientHeight >= chatMessages.scrollHeight - 10;
                                        }
                                        
                                        responseText += parsedData.content;
                                        // Use your existing formatMessage function
                                        messageContent.innerHTML = formatMessage(responseText);
                                        
                                        // Apply the repaint to ensure content is visible
                                        forceRepaint(messageContent);
                                        
                                        // Only auto-scroll if user was already at the bottom and chatMessages exists
                                        if (shouldScroll && chatMessages) {
                                            try {
                                                chatMessages.scrollTop = chatMessages.scrollHeight;
                                            } catch (e) {
                                                console.warn('Error scrolling chat messages:', e);
                                            }
                                        }
                                    }
                                    // Update conversation ID if it's the first message
                                    if (parsedData.conversation_id) {
                                        // Always update the current conversation ID to ensure it's correct
                                        currentConversationId = parsedData.conversation_id;
                                        console.log(`Setting conversation ID: ${currentConversationId}`);
                                        // Store conversation ID on the message element for reference
                                        assistantMessageElement.dataset.conversationId = currentConversationId;
                                        
                                        // If this is a new conversation, refresh the list immediately
                                        if (!document.querySelector(`.conversation-item[data-id="${currentConversationId}"]`)) {
                                            console.log("New conversation detected, refreshing list");
                                            fetchConversations(true);
                                        }
                                    }
                                } else if (parsedData.type === 'reasoning') {
                                    console.log("==> Processing type: reasoning");
                                    
                                    if (parsedData.reasoning) {
                                        // Get or create the reasoning container
                                        let reasoningContainer = assistantMessageElement.querySelector('.message-reasoning');
                                        if (!reasoningContainer) {
                                            reasoningContainer = document.createElement('div');
                                            reasoningContainer.className = 'message-reasoning';
                                            
                                            // Create a collapsible header
                                            const reasoningHeader = document.createElement('div');
                                            reasoningHeader.className = 'reasoning-header';
                                            reasoningHeader.innerHTML = '<span class="reasoning-toggle">▶</span> View Reasoning';
                                            reasoningHeader.addEventListener('click', function() {
                                                const reasoningContent = this.nextElementSibling;
                                                const toggle = this.querySelector('.reasoning-toggle');
                                                
                                                if (reasoningContent.style.display === 'none' || !reasoningContent.style.display) {
                                                    reasoningContent.style.display = 'block';
                                                    toggle.textContent = '▼';
                                                    this.parentElement.classList.add('reasoning-expanded');
                                                } else {
                                                    reasoningContent.style.display = 'none';
                                                    toggle.textContent = '▶';
                                                    this.parentElement.classList.remove('reasoning-expanded');
                                                }
                                            });
                                            
                                            // Create content container
                                            const reasoningContent = document.createElement('div');
                                            reasoningContent.className = 'reasoning-content';
                                            reasoningContent.style.display = 'block'; // Initially visible when streaming
                                            
                                            reasoningContainer.appendChild(reasoningHeader);
                                            reasoningContainer.appendChild(reasoningContent);
                                            
                                            // Insert BEFORE the main message content (at the top of the message)
                                            const messageWrapper = assistantMessageElement.querySelector('.message-wrapper');
                                            const messageContent = assistantMessageElement.querySelector('.message-content');
                                            if (messageWrapper && messageContent) {
                                                // Insert before the message content
                                                messageWrapper.insertBefore(reasoningContainer, messageContent);
                                            } else if (messageWrapper) {
                                                // Fallback: insert at the beginning of message wrapper
                                                messageWrapper.insertBefore(reasoningContainer, messageWrapper.firstChild);
                                            }
                                        }
                                        
                                        // Append the reasoning chunk to the content
                                        const reasoningContent = reasoningContainer.querySelector('.reasoning-content');
                                        reasoningContent.textContent += parsedData.reasoning;
                                    }
                                
                                } else if (parsedData.type === 'citations') {
                                    console.log("==> Processing type: citations");
                                    
                                    if (parsedData.citations && parsedData.citations.length > 0) {
                                        console.log(`Received ${parsedData.citations.length} citations from Perplexity`);
                                        
                                        // Store citations for this message
                                        if (!assistantMessageElement._perplexityCitations) {
                                            assistantMessageElement._perplexityCitations = parsedData.citations;
                                        } else {
                                            // Append new citations
                                            assistantMessageElement._perplexityCitations = 
                                                assistantMessageElement._perplexityCitations.concat(parsedData.citations);
                                        }
                                        
                                        // Add citations to the message
                                        addPerplexityCitationsToMessage(assistantMessageElement, assistantMessageElement._perplexityCitations);
                                    }
                                } else if (parsedData.type === 'metadata') {
                                    console.log("==> Processing type: metadata"); 
                                    // Metadata received (usually after content stream ends)
                                    console.log("Received metadata:", parsedData.metadata);
                                    // Debug RAG information
                                    console.log("DEBUG-RAG: Full metadata object:", parsedData.metadata);
                                    console.log("DEBUG-RAG: using_documents flag present?", parsedData.metadata && 'using_documents' in parsedData.metadata);
                                    if (parsedData.metadata && 'using_documents' in parsedData.metadata) {
                                        console.log("DEBUG-RAG: using_documents value =", parsedData.metadata.using_documents);
                                    }
                                    
                                    if (parsedData.metadata) {
                                        const meta = parsedData.metadata;
                                        
                                        // Set the definitive message ID on the element
                                        assistantMessageElement.dataset.messageId = meta.id;
                                        
                                        // Update/Create metadata display section
                                        const messageWrapper = assistantMessageElement.querySelector('.message-wrapper');
                                        if (messageWrapper) { // Check if wrapper exists
                                            let metadataContainer = messageWrapper.querySelector('.message-metadata');
                                            if (!metadataContainer) {
                                                metadataContainer = document.createElement('div');
                                                metadataContainer.className = 'message-metadata message-metadata-outside';
                                                // Insert metadata before action buttons if they exist
                                                const actionsContainer = messageWrapper.querySelector('.message-actions');
                                                if (actionsContainer) {
                                                    messageWrapper.insertBefore(metadataContainer, actionsContainer);
                                                } else {
                                                    // Append if actions aren't there (e.g., if they load later)
                                                    messageWrapper.appendChild(metadataContainer); 
                                                }
                                            }
                                            
                                            // Format metadata text
                                            let metadataText = '';
                                            const modelName = meta.model_id_used ? formatModelName(meta.model_id_used) : 'N/A';
                                            metadataText += `Model: ${modelName}`;
                                            
                                            if (meta.prompt_tokens !== null && meta.completion_tokens !== null) {
                                                 metadataText += ` · Tokens: ${meta.prompt_tokens} prompt + ${meta.completion_tokens} completion`;
                                            }
                                            console.log("Setting metadata text:", metadataText);
                                            
                                            // Create a text node instead of using textContent directly
                                            // This ensures we can append multiple elements to the container
                                            const textNode = document.createTextNode(metadataText);
                                            metadataContainer.innerHTML = ''; // Clear any existing content
                                            metadataContainer.appendChild(textNode);
                                            
                                            // Add a class to highlight the metadata as visible
                                            metadataContainer.classList.add('metadata-visible');
                                            
                                            // Add document reference indicator if using documents
                                            if (meta.using_documents) {
                                                console.log("DEBUG-RAG: Adding document reference indicator");
                                                const documentRef = document.createElement('span');
                                                documentRef.className = 'document-reference';
                                                documentRef.innerHTML = '<i class="fa-solid fa-file-lines"></i> Using your documents';
                                                documentRef.title = 'This response includes information from your uploaded documents';
                                                
                                                // If we have source information, make it expandable
                                                if (meta.document_sources && meta.document_sources.length > 0) {
                                                    console.log("DEBUG-RAG: Adding document sources:", meta.document_sources);
                                                    documentRef.classList.add('has-sources');
                                                    documentRef.addEventListener('click', function() {
                                                        const existingSourceList = messageWrapper.querySelector('.document-sources');
                                                        if (existingSourceList) {
                                                            existingSourceList.remove();
                                                            documentRef.classList.remove('expanded');
                                                        } else {
                                                            const sourceList = document.createElement('div');
                                                            sourceList.className = 'document-sources';
                                                            sourceList.innerHTML = '<h4>Document Sources</h4>';
                                                            const sourceUl = document.createElement('ul');
                                                            meta.document_sources.forEach(source => {
                                                                const li = document.createElement('li');
                                                                li.textContent = source;
                                                                sourceUl.appendChild(li);
                                                            });
                                                            sourceList.appendChild(sourceUl);
                                                            messageWrapper.appendChild(sourceList);
                                                            documentRef.classList.add('expanded');
                                                        }
                                                    });
                                                }
                                                
                                                metadataContainer.appendChild(documentRef);
                                                console.log("DEBUG-RAG: Document reference indicator added");
                                            } else {
                                                console.log("DEBUG-RAG: Not adding document reference - using_documents flag not set");
                                            }
                                        }

                                        // Update action buttons now that we have the final message ID
                                        updateActionButtonsWithMessageId(assistantMessageElement, meta.id);
                                    }
                                
                                } else if (parsedData.type === 'done') {
                                    console.log("==> Processing type: done"); // ADD THIS LOG
                                    // Stream finished successfully
                                    console.log("Stream finished event received.");
                                    
                                    // Ensure the final response text is added to JS history
                                    if (responseText && (!messageHistory.length || messageHistory[messageHistory.length - 1]?.role !== 'assistant')) {
                                         // Add only if history is empty or last message wasn't assistant's
                                         // This prevents duplicates if content was added earlier
                                        messageHistory.push({
                                            role: 'assistant',
                                            content: responseText 
                                        });
                                        console.log("Added final assistant response to JS history.");
                                    } else if (responseText && messageHistory.length > 0 && messageHistory[messageHistory.length - 1]?.role === 'assistant') {
                                        // Update the last history entry's content if needed (less likely needed now)
                                        // messageHistory[messageHistory.length - 1].content = responseText;
                                    }
                                    
                                    // Re-enable input, etc. 
                                    // messageInput.disabled = false;
                                    // sendButton.disabled = false;
                                    
                                    // After conversation completes, refresh the conversation list to get updated titles
                                    // Schedule a single refresh after a 3-second delay
                                    // This gives the backend time to generate the title
                                    console.log("Scheduling a 3-second delayed refresh to fetch updated title...");
                                    
                                    setTimeout(() => {
                                        console.log("Refreshing conversation list after 3s delay to get updated title");
                                        fetchConversations(true);
                                    }, 3000);
                                    
                                    return; // Exit the processing loop
                                } else {
                                    console.warn("==> Received unknown data type:", parsedData.type, parsedData); // ADD THIS LOG
                                }
                                
                            } catch (error) {
                                console.error('Error parsing SSE data JSON:', error, data);
                                // messageContent.innerHTML = `<span class="error">Error processing response data.</span>`;
                                // return; // Stop processing on parsing error
                            }
                        } else {
                            // Handle lines that don't start with 'data: ' if necessary (e.g., comments)
                            // console.log("Received non-data line:", message); 
                        }
                    } // End of loop processing complete messages
                    
                    // Continue reading from the stream
                    return processChunks();
                }); // End of reader.read().then()
            } // End of processChunks function definition

            // Helper function to update action buttons with the message ID
            function updateActionButtonsWithMessageId(messageElement, messageId) {
                // Ensure messageElement is valid
                if (!messageElement) return; 
                
                const upvoteBtn = messageElement.querySelector('.upvote-btn');
                const downvoteBtn = messageElement.querySelector('.downvote-btn');
                const copyBtn = messageElement.querySelector('.copy-btn');
                const shareBtn = messageElement.querySelector('.share-btn');

                // Check if buttons exist before setting dataset properties
                if (upvoteBtn) upvoteBtn.dataset.messageId = messageId;
                if (downvoteBtn) downvoteBtn.dataset.messageId = messageId;
                if (copyBtn) copyBtn.dataset.messageId = messageId; 
                if (shareBtn) shareBtn.dataset.messageId = messageId;
                
                // If using delegated listeners, no need to re-attach handlers.
                // If attaching directly in addMessage, ensure they are attached
                // after the message ID is set.
            }
            
            return processChunks();
        }).catch(error => {
            console.error('Error sending message:', error);
            
            // Remove typing indicator if it exists
            if (typingIndicator && typingIndicator.parentNode) {
                chatMessages.removeChild(typingIndicator);
            }
            
            // Add error message
            const errorMessage = addMessage(`Error: ${error.message}`, 'assistant');
            errorMessage.querySelector('.message-content').classList.add('error');
        });
    }
    
    // Function to format message with markdown, code blocks, etc.
    // Helper function to determine if a message should be truncated
    function shouldTruncateMessage(text) {
        // This function is now disabled in favor of the message-collapse.js implementation
        // Keep it here for backwards compatibility but always return false
        
        // The old logic is preserved in comments for reference:
        // const textWithoutCodeBlocks = text.replace(/```[^`]+```/g, '');
        // const characterCount = textWithoutCodeBlocks.length;
        // const newlineCount = (text.match(/\n/g) || []).length;
        // return characterCount > 500 || newlineCount > 12;
        
        return false; // Never truncate via this method
    }
    

    
    // Function to copy message text to clipboard
    function copyMessageText(messageElement) {
        const messageContent = messageElement.querySelector('.message-content');
        
        // Handle multimodal messages properly by excluding image containers
        const tempElement = document.createElement('div');
        tempElement.innerHTML = messageContent.innerHTML;
        
        // Remove any image containers before copying
        const imageContainers = tempElement.querySelectorAll('.message-image-container');
        imageContainers.forEach(container => container.remove());
        
        // Get the text content without HTML formatting
        const textToCopy = tempElement.textContent || tempElement.innerText;
        
        navigator.clipboard.writeText(textToCopy)
            .then(() => {
                // Visual feedback that copy worked
                const copyButton = messageElement.querySelector('.copy-btn');
                copyButton.innerHTML = '<i class="fa-solid fa-check"></i> Copied';
                copyButton.classList.add('copied');
                
                // Reset after 2 seconds
                setTimeout(() => {
                    copyButton.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
                    copyButton.classList.remove('copied');
                }, 2000);
            })
            .catch(err => {
                console.error('Error copying text: ', err);
                alert('Failed to copy text. Please try again.');
            });
    }
    
    // Function to share conversation
    function shareConversation(messageElement) {
        // Get the current URL and add a share parameter
        const shareButton = messageElement.querySelector('.share-btn');
        
        if (currentConversationId) {
            // Use fetch to get a shareable link from the server
            fetch(`/conversation/${currentConversationId}/share`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.share_url) {
                    const shareUrl = window.location.origin + data.share_url;
                    navigator.clipboard.writeText(shareUrl)
                        .then(() => {
                            // Visual feedback
                            shareButton.innerHTML = '<i class="fa-solid fa-check"></i> Copied link';
                            
                            // Reset after 2 seconds
                            setTimeout(() => {
                                shareButton.innerHTML = '<i class="fa-solid fa-share-nodes"></i> Share';
                            }, 2000);
                        })
                        .catch(err => {
                            console.error('Error copying share link: ', err);
                            alert('Failed to copy share link. Please try again.');
                        });
                } else {
                    console.error('No share URL returned');
                    alert('Could not generate share link. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error sharing conversation:', error);
                alert('Failed to share conversation. Please try again.');
            });
        } else {
            console.error('No conversation ID available for sharing');
            alert('Cannot share this conversation yet. Please send at least one message first.');
        }
    }
    
    // Function to rate a message (upvote/downvote)
    function rateMessage(messageElement, rating) {
        const messageId = messageElement.dataset.messageId;
        const upvoteButton = messageElement.querySelector('.upvote-btn');
        const downvoteButton = messageElement.querySelector('.downvote-btn');
        
        if (!messageId) {
            console.error('No message ID available for rating');
            return;
        }
        
        // Send rating to server
        fetch(`/message/${messageId}/rate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                rating: rating
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update UI based on the rating
                if (rating === 1) {
                    upvoteButton.classList.add('voted');
                    downvoteButton.classList.remove('voted');
                } else if (rating === -1) {
                    downvoteButton.classList.add('voted');
                    upvoteButton.classList.remove('voted');
                }
            } else {
                console.error('Rating was not successful:', data.error);
            }
        })
        .catch(error => {
            console.error('Error rating message:', error);
        });
    }
    
    // Function to clear chat
    function clearChat() {
        // Clear the message history
        messageHistory = [];
        
        // Make sure chatMessages exists
        if (!chatMessages) {
            console.warn('Chat messages container not found - cannot clear chat');
            return;
        }
        
        // Keep only the welcome container or create it if it doesn't exist
        if (!document.querySelector('.welcome-container')) {
            chatMessages.innerHTML = `
                <div class="welcome-container">
                    <div class="welcome-icon">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                        </svg>
                    </div>
                    <h1 class="welcome-heading">Welcome to GloriaMundo!</h1>
                    <p class="welcome-text">
                        Ask me anything and I'll provide helpful, accurate responses. Sign in to 
                        save your conversations and access them from any device.
                    </p>
                    <button class="example-question-btn" id="example-question-btn">
                        <i class="fa-regular fa-lightbulb"></i> Try an example question
                    </button>
                </div>
            `;
            
            // Re-attach event listener to the new example question button
            document.getElementById('example-question-btn').addEventListener('click', function() {
                const exampleQuestions = [
                    "What are the major differences between renewable and fossil fuel energy sources?",
                    "Can you explain how artificial intelligence works in simple terms?",
                    "What are some effective strategies for reducing carbon emissions?",
                    "How does quantum computing differ from classical computing?",
                    "What are the potential implications of gene editing technologies?"
                ];
                
                const randomQuestion = exampleQuestions[Math.floor(Math.random() * exampleQuestions.length)];
                messageInput.value = randomQuestion;
                sendMessage();
            });
        }
    }
    
    // Initialize by focusing on the input if it exists
    if (messageInput) {
        messageInput.focus();
    }
    
    // ====== Document Upload Handlers ======
    
    // Store selected files
    let selectedFiles = [];
    
    // Legacy document upload button - disabled
    // The uploadDocumentsBtn has been removed in favor of the unified file upload button
    // All this functionality has been moved to the imageUploadButton click handler
    
    // Note: This code was previously encapsulated in a false condition block
    // to disable it, but this caused syntax errors. Now it's properly commented out.
    
    // Legacy document upload modal functionality - all disabled
    // The following code was managing the old RAG documents upload modal
    // This has been replaced with the unified file upload approach
    
    /* Legacy code - disabled
    // Close upload modal
    if (closeUploadModal) {
        closeUploadModal.addEventListener('click', function() {
            documentUploadModal.style.display = 'none';
        });
    }
    
    // Close modal when clicking outside
    if (documentUploadModal) {
        documentUploadModal.addEventListener('click', function(e) {
            if (e.target === documentUploadModal) {
                documentUploadModal.style.display = 'none';
            }
        });
    }
    
    // Handle dropzone click
    if (uploadDropzone) {
        uploadDropzone.addEventListener('click', function() {
            fileUploadInput.click();
        });
    }
        
    // Handle file drag over
    if (uploadDropzone) {
        uploadDropzone.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add('dragover');
        });
        
        // Handle file drag leave
        uploadDropzone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('dragover');
        });
        
        // Handle file drop
        uploadDropzone.addEventListener('drop', function(e) {
            e.preventDefault();
    */
    
    // Handle file selection - now handled through the unified upload approach
    // Keeping this code is no longer necessary as we'll use the unified file upload functionality
    
    // Get reference to file upload input if it exists
    const fileUploadInput = document.getElementById('fileUpload');
    
    // Handle file input change if element exists
    if (fileUploadInput) {
        fileUploadInput.addEventListener('change', function() {
            // Only process if we have files
            if (this.files && this.files.length > 0) {
                // Get the first file
                const file = this.files[0];
                const fileExt = file.name.split('.').pop().toLowerCase();
                
                // Determine file type and check if the model supports it
                const isPDF = fileExt === 'pdf';
                const supportsPDF = checkModelCapabilities('pdf');
                const supportsImages = checkModelCapabilities('image');
                
                // Validate file type against model capabilities
                if (isPDF && !supportsPDF) {
                    console.warn('PDF file upload attempted but current model does not support PDFs');
                    alert('The current model does not support PDF documents. Please select a model with PDF support first.');
                    return;
                } else if (!isPDF && !supportsImages) {
                    console.warn('Image file upload attempted but current model does not support images');
                    alert('The current model does not support images. Please select a model with image support first.');
                    return;
                }
                
                // Process different file types
                if (isPDF) {
                    // Handle PDF file
                    handlePdfFile(file);
                } else {
                    // Handle image file using existing function
                    handleImageFile(file);
                }
            }
        });
    }
    
    // Handle file selection
    function handleFileSelection(files) {
        if (!files || files.length === 0) return;
        
        // Add files to the selected files array
        Array.from(files).forEach(file => {
            // Check if file is already in the list
            const isDuplicate = selectedFiles.some(f => f.name === file.name && f.size === file.size);
            if (!isDuplicate) {
                selectedFiles.push(file);
            }
        });
        
        // Update the file list UI
        updateFileList();
    }
    
    // Update file list display
    function updateFileList() {
        if (!uploadFileList) return;
        
        uploadFileList.innerHTML = '';
        
        selectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'upload-file-item';
            
            // Determine file icon based on file type
            let iconClass = 'fa-file';
            const fileExt = file.name.split('.').pop().toLowerCase();
            
            if (['pdf'].includes(fileExt)) {
                iconClass = 'fa-file-pdf';
            } else if (['doc', 'docx'].includes(fileExt)) {
                iconClass = 'fa-file-word';
            } else if (['txt', 'md'].includes(fileExt)) {
                iconClass = 'fa-file-alt';
            } else if (['jpg', 'jpeg', 'png', 'gif'].includes(fileExt)) {
                iconClass = 'fa-file-image';
            } else if (['html', 'htm', 'xml'].includes(fileExt)) {
                iconClass = 'fa-file-code';
            } else if (['csv', 'xls', 'xlsx'].includes(fileExt)) {
                iconClass = 'fa-file-excel';
            }
            
            fileItem.innerHTML = `
                <div class="file-info">
                    <i class="fa-solid ${iconClass} file-icon"></i>
                    <span class="file-name">${file.name}</span>
                </div>
                <button class="remove-file" data-index="${index}">
                    <i class="fa-solid fa-times"></i>
                </button>
            `;
            
            uploadFileList.appendChild(fileItem);
        });
        
        // Add event listeners to remove buttons
        document.querySelectorAll('.remove-file').forEach(button => {
            button.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                selectedFiles.splice(index, 1);
                updateFileList();
            });
        });
        
        // Show or hide the upload button based on file selection
        if (uploadFilesBtn) {
            uploadFilesBtn.style.display = selectedFiles.length > 0 ? 'block' : 'none';
        }
    }
    
    // Handle the upload process
    if (uploadFilesBtn) {
        uploadFilesBtn.addEventListener('click', function() {
            if (selectedFiles.length === 0) return;
            
            uploadStatus.innerHTML = `<p>Uploading ${selectedFiles.length} file(s)...</p>
                                     <div class="upload-progress"><div class="upload-progress-bar"></div></div>`;
            
            const formData = new FormData();
            selectedFiles.forEach(file => {
                formData.append('files[]', file);
            });
            
            // Disable the upload button during upload
            this.disabled = true;
            
            // Send the files to the server
            fetch('/upload', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    uploadStatus.innerHTML = `<p>✅ Successfully processed ${selectedFiles.length} file(s). Your files will now be used to enhance AI responses.</p>`;
                    // Clear selected files
                    selectedFiles = [];
                    updateFileList();
                    
                    // Close modal after 3 seconds
                    setTimeout(() => {
                        documentUploadModal.style.display = 'none';
                        uploadStatus.innerHTML = '';
                    }, 3000);
                } else {
                    uploadStatus.innerHTML = `<p>❌ Error: ${data.error}</p>`;
                }
            })
            .catch(error => {
                uploadStatus.innerHTML = `<p>❌ Upload failed: ${error.message}</p>`;
                console.error('Upload error:', error);
            })
            .finally(() => {
                // Re-enable the upload button
                this.disabled = false;
            });
        });
    }
    
    // Add CSS for disabled button
    const style = document.createElement('style');
    style.textContent = `
        .disabled {
            opacity: 0.5;
            cursor: not-allowed !important;
            pointer-events: none;
        }
        #upload-indicator {
            animation: fadein 0.3s;
        }
        @keyframes fadein {
            from { opacity: 0; }
            to   { opacity: 1; }
        }
    `;
    document.head.appendChild(style);
    
    // Login prompt for non-authenticated users
    if (typeof userIsLoggedIn !== 'undefined' && !userIsLoggedIn) {
        // Initialize login prompt modal elements
        const loginPromptModal = document.getElementById('login-prompt-modal');
        const closeLoginPromptBtn = document.getElementById('close-login-prompt');
        const noThanksBtn = document.getElementById('no-thanks-btn');
        
        // Function to show the login prompt modal
        window.showLoginPrompt = function() {
            if (loginPromptModal) {
                loginPromptModal.style.display = 'flex';
                // Add animation class
                setTimeout(() => {
                    loginPromptModal.style.opacity = '1';
                }, 10);
            }
        };
        
        // Function to hide the login prompt modal
        function hideLoginPrompt() {
            if (loginPromptModal) {
                loginPromptModal.style.opacity = '0';
                setTimeout(() => {
                    loginPromptModal.style.display = 'none';
                }, 300); // Match the CSS transition duration
            }
        }
        
        // Close button event listener
        if (closeLoginPromptBtn) {
            closeLoginPromptBtn.addEventListener('click', hideLoginPrompt);
        }
        
        // "No thanks" button event listener
        if (noThanksBtn) {
            noThanksBtn.addEventListener('click', hideLoginPrompt);
        }
        
        // Close modal when clicking outside the modal content
        if (loginPromptModal) {
            loginPromptModal.addEventListener('click', function(e) {
                if (e.target === loginPromptModal) {
                    hideLoginPrompt();
                }
            });
        }
    }
});
