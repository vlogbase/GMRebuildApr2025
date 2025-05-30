/**
 * Event Orchestration Module
 * Handles main event listener setup and orchestrates interactions between modules
 */

import { debounce } from './utils.js';
import { messageInput, sendButton, newChatButton, clearConversationsButton, imageUploadButton, imageUploadInput, cameraButton, captureButton, switchCameraButton, refreshPricesBtn } from './uiSetup.js';
import { sendMessage, clearChat } from './chatLogic.js';
import { createNewConversation, fetchConversations } from './conversationManagement.js';
import { handleImageFile, handlePdfFile, handleFileUpload, switchCamera, stopCameraStream, loadCameraDevices } from './fileUpload.js';
import { selectPresetButton, fetchUserPreferences, updatePresetButtonLabels, closeModelSelector, allModels, currentModel } from './modelSelection.js';
import { resetPreferencesAPI } from './apiService.js';

// Initialize main event listeners
export function initializeMainEventListeners(isAuthenticated, userCreditBalance) {
    console.log('🎯 Initializing main event listeners...');
    
    // Setup core UI event listeners
    setupCoreUIEventListeners();
    
    // Setup file upload event listeners
    setupFileUploadEventListeners();
    
    // Setup document-level event listeners
    setupDocumentEventListeners();
    
    // Setup page navigation event listeners
    setupPageNavigationEventListeners(isAuthenticated, userCreditBalance);
}

// Setup core UI event listeners
function setupCoreUIEventListeners() {
    // New chat button
    if (newChatButton) {
        newChatButton.addEventListener('click', () => {
            console.log('🆕 New chat button clicked');
            createNewConversation();
        });
    }
    
    // Clear conversations button
    if (clearConversationsButton) {
        clearConversationsButton.addEventListener('click', () => {
            console.log('🗑️ Clear conversations button clicked');
            if (confirm('Are you sure you want to clear all conversations? This cannot be undone.')) {
                clearChat();
                fetchConversations(true); // Refresh the conversation list
            }
        });
    }
    
    // Reset all presets button
    if (refreshPricesBtn) {
        refreshPricesBtn.addEventListener('click', async () => {
            console.log('🔄 Reset all presets button clicked');
            if (confirm('Are you sure you want to reset all model presets to their defaults? This will clear your custom model selections.')) {
                // Reset all presets by calling resetToDefault without arguments (resets all)
                try {
                    const success = await resetAllPresets();
                    if (success) {
                        console.log('✅ All presets reset successfully');
                    }
                } catch (error) {
                    console.error('❌ Error resetting presets:', error);
                }
            }
        });
    }
    
    // Example question buttons
    setupExampleQuestionListeners();
    
    // Send button click event
    if (sendButton) {
        sendButton.addEventListener('click', () => {
            console.log('📤 Send button clicked');
            sendMessage();
        });
    }
    
    // Message input focus/blur events and Enter key handling
    if (messageInput) {
        messageInput.addEventListener('focus', () => {
            console.log('📝 Message input focused');
            // Add focused class for styling
            messageInput.classList.add('focused');
        });
        
        messageInput.addEventListener('blur', () => {
            console.log('📝 Message input blurred');
            // Remove focused class
            messageInput.classList.remove('focused');
        });
        
        // Handle Enter key for sending messages (desktop) vs new line (mobile)
        messageInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                // On mobile (width <= 576px), allow Enter to create new lines
                if (window.innerWidth <= 576) {
                    // Allow default behavior (new line)
                    return;
                }
                
                // On desktop, send message unless Shift is held
                if (!event.shiftKey) {
                    event.preventDefault();
                    console.log('📤 Enter key pressed - sending message');
                    sendMessage();
                } else {
                    // Shift+Enter creates a new line (allow default behavior)
                    console.log('📝 Shift+Enter pressed - creating new line');
                }
            }
        });
    }
}

// Setup file upload event listeners
function setupFileUploadEventListeners() {
    // Image upload button
    if (imageUploadButton) {
        imageUploadButton.addEventListener('click', () => {
            console.log('📸 Image upload button clicked');
            if (imageUploadInput) {
                imageUploadInput.click();
            }
        });
    }
    
    // File upload input change (handles both images and PDFs)
    if (imageUploadInput) {
        imageUploadInput.addEventListener('change', event => {
            console.log('📁 File upload input changed');
            const files = event.target.files;
            if (files && files.length > 0) {
                for (let i = 0; i < files.length; i++) {
                    const file = files[i];
                    const modelInfo = allModels.find(m => m.id === currentModel);
                    
                    // Check model capabilities before processing
                    if (file.type === 'application/pdf' && (!modelInfo || !modelInfo.supports_pdf)) {
                        alert('This model does not support PDF input. Please select a different model.');
                        event.target.value = '';
                        return;
                    }
                    if (file.type.startsWith('image/') && (!modelInfo || (!modelInfo.supports_vision && !modelInfo.is_multimodal))) {
                        alert('This model does not support image input. Please select a different model.');
                        event.target.value = '';
                        return;
                    }
                    
                    // Detect file type and call appropriate handler
                    if (file.type.startsWith('image/')) {
                        console.log('📸 Image file detected:', file.name);
                        handleImageFile(file);
                    } else if (file.type === 'application/pdf') {
                        console.log('📄 PDF file detected:', file.name);
                        handlePdfFile(file);
                    } else {
                        console.log('📁 Unknown file type, trying unified handler:', file.name);
                        // Use unified handler for unknown types
                        handleFileUpload(file);
                    }
                }
                // Clear the input so the same file can be selected again
                event.target.value = '';
            }
        });
    }
    
    // Camera button
    if (cameraButton) {
        cameraButton.addEventListener('click', async () => {
            console.log('📷 Camera button clicked');
            await startCameraCapture();
        });
        
        cameraButton.addEventListener('touchstart', async (e) => {
            e.preventDefault();
            console.log('📷 Camera button tapped (touchstart)');
            await startCameraCapture();
        });
    }
    
    // Capture button
    if (captureButton) {
        captureButton.addEventListener('click', () => {
            console.log('📷 Capture button clicked');
            capturePhoto();
        });
    }
    
    // Switch camera button
    if (switchCameraButton) {
        switchCameraButton.addEventListener('click', switchCamera);
    }
    
    // Close camera button
    const closeCameraButton = document.getElementById('close-camera-button');
    if (closeCameraButton) {
        closeCameraButton.addEventListener('click', () => {
            console.log('❌ Close camera button clicked');
            stopCameraStream();
            const cameraModal = document.getElementById('camera-modal');
            if (cameraModal) {
                cameraModal.style.display = 'none';
            }
        });
    }
}

// Setup document-level event listeners
function setupDocumentEventListeners() {
    // Handle paste events for file uploads
    document.addEventListener('paste', handlePaste);
    
    // Handle keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // Handle click outside to close modals
    document.addEventListener('click', handleOutsideClicks);
}

// Setup page navigation event listeners
function setupPageNavigationEventListeners(isAuthenticated, userCreditBalance) {
    // Handle browser back/forward navigation
    window.addEventListener('pageshow', function() {
        console.log('📄 Page show event');
        // Re-apply locks when user navigates back from billing page
        if (!isAuthenticated || userCreditBalance <= 0) {
            lockPremiumFeatures(isAuthenticated, userCreditBalance);
        }
    });
    
    // Handle window resize for responsive behavior
    window.addEventListener('resize', debounce(() => {
        console.log('📱 Window resized');
        handleWindowResize();
    }, 250));
}

// Setup example question button listeners
function setupExampleQuestionListeners() {
    const exampleButtons = document.querySelectorAll('.example-question');
    exampleButtons.forEach(button => {
        button.addEventListener('click', () => {
            const question = button.textContent.trim();
            console.log(`❓ Example question clicked: ${question}`);
            
            // Fill the message input with the example question
            if (messageInput) {
                messageInput.value = question;
                messageInput.focus();
                
                // Trigger input event to update send button state
                messageInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });
    });
}

// Handle paste events for file uploads
function handlePaste(e) {
    console.log('📋 Paste event detected');
    const items = e.clipboardData?.items;
    if (!items) return;
    
    for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.type.indexOf('image') !== -1) {
            console.log('📸 Image pasted from clipboard');
            const blob = item.getAsFile();
            if (blob) {
                handleImageFile(blob);
            }
        }
    }
}

// Handle keyboard shortcuts
function handleKeyboardShortcuts(e) {
    // Ctrl/Cmd + Enter to send message
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        console.log('⌨️ Keyboard shortcut: Send message');
        if (sendButton && !sendButton.disabled) {
            sendButton.click();
        }
        e.preventDefault();
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        console.log('⌨️ Keyboard shortcut: Escape');
        closeAnyOpenModals();
    }
}

// Handle clicks outside modals to close them
function handleOutsideClicks(e) {
    // Check if click is outside model selector (using original logic from script.js.backup)
    const modelSelector = document.getElementById('model-selector');
    if (modelSelector && modelSelector.style.display === 'block' && 
        !modelSelector.contains(e.target) && 
        !e.target.matches('.model-preset-btn') && 
        !e.target.closest('.model-preset-btn')) {
        console.log('🖱️ Clicked outside model selector');
        closeModelSelector();
    }
    
    // Check if click is outside other modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (modal.style.display === 'block' || modal.classList.contains('show')) {
            if (e.target === modal) {
                console.log('🖱️ Clicked outside modal');
                closeModal(modal);
            }
        }
    });
}

// Start camera capture
async function startCameraCapture() {
    try {
        console.log('📷 Starting camera capture...');
        
        // Load camera devices first to check how many are available
        await loadCameraDevices();
        
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'environment' } 
        });
        
        const cameraVideo = document.getElementById('camera-stream');
        if (cameraVideo) {
            cameraVideo.srcObject = stream;
            cameraVideo.play();
        }
        
        // Show camera modal
        const cameraModal = document.getElementById('camera-modal');
        if (cameraModal) {
            cameraModal.style.display = 'block';
        }
        
    } catch (error) {
        console.error('❌ Error accessing camera:', error);
        if (error.name === 'NotAllowedError') {
            alert('Camera access denied. Please allow camera permissions and try again.');
        } else if (error.name === 'NotFoundError') {
            alert('No camera found on this device.');
        } else {
            alert('Unable to access camera. Please check permissions and try again.');
        }
    }
}

// Capture photo from camera
function capturePhoto() {
    console.log('📸 Capturing photo...');
    const cameraVideo = document.getElementById('camera-stream');
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    
    if (cameraVideo && cameraVideo.videoWidth && cameraVideo.videoHeight) {
        canvas.width = cameraVideo.videoWidth;
        canvas.height = cameraVideo.videoHeight;
        context.drawImage(cameraVideo, 0, 0);
        
        // Convert to blob and handle as image
        canvas.toBlob(blob => {
            if (blob) {
                handleImageFile(blob);
            }
        }, 'image/jpeg', 0.8);
        
        // Stop camera and hide modal
        stopCameraStream();
        const cameraModal = document.getElementById('camera-modal');
        if (cameraModal) {
            cameraModal.style.display = 'none';
        }
    }
}

// Close any open modals
function closeAnyOpenModals() {
    // Close model selector
    const modelSelector = document.getElementById('model-selector');
    if (modelSelector && modelSelector.style.display === 'block') {
        closeModelSelector();
    }
    
    // Close other modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (modal.style.display === 'block' || modal.classList.contains('show')) {
            closeModal(modal);
        }
    });
}

// Close specific modal
function closeModal(modal) {
    modal.style.display = 'none';
    modal.classList.remove('show');
    document.body.classList.remove('modal-open');
}

// Note: closeModelSelector is now imported from modelSelection.js

// Handle window resize
function handleWindowResize() {
    // Update mobile/desktop specific behaviors
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        document.body.classList.add('mobile-view');
    } else {
        document.body.classList.remove('mobile-view');
    }
    
    // Update any layout-dependent elements
    updateLayoutForScreenSize();
}

// Update layout for screen size
function updateLayoutForScreenSize() {
    // Adjust chat container height on mobile
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer && window.innerWidth <= 768) {
        // Mobile-specific adjustments
        chatContainer.style.maxHeight = `${window.innerHeight - 100}px`;
    }
}

// Reset all model presets to defaults
async function resetAllPresets() {
    console.log('🔄 Resetting all model presets to defaults...');
    
    try {
        // Make a single API call to reset all preferences
        const response = await resetPreferencesAPI();
        
        if (response && response.success) {
            console.log('✅ All presets reset successfully');
            
            // Refresh user preferences and update UI
            await fetchUserPreferences();
            updatePresetButtonLabels();
            
            return true;
        } else {
            console.error('❌ Failed to reset presets:', response?.error || 'Unknown error');
            return false;
        }
    } catch (error) {
        console.error('❌ Error resetting all presets:', error);
        return false;
    }
}

// Setup premium feature locks with visual padlock indicators
export function lockPremiumFeatures(isAuthenticated, userCreditBalance) {
    console.log('🔒 Locking premium features...');
    console.log('🔍 Authentication status:', isAuthenticated);
    console.log('💰 Credit balance received:', userCreditBalance);
    console.log('🎯 Should lock features?', (!isAuthenticated || userCreditBalance <= 0));
    
    // Process all model preset buttons
    document.querySelectorAll('.model-preset-btn').forEach(btn => {
        const presetId = btn.getAttribute('data-preset-id');
        
        // Clone buttons to remove existing event listeners
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        
        // Check if this is a free model - multiple ways to detect
        const isFreeModel = newBtn.querySelector('.cost-band-free') !== null || 
                           newBtn.classList.contains('free-preset') ||
                           presetId === '6'; // Preset 6 is always the free model
        const shouldLock = !isAuthenticated || (userCreditBalance <= 0 && !isFreeModel);
        
        console.log(`🎯 Preset ${presetId}: isFree=${isFreeModel}, authenticated=${isAuthenticated}, credits=${userCreditBalance}, shouldLock=${shouldLock}`);
        
        if (shouldLock) {
            // Add visual padlock indicators
            addPadlockIndicator(newBtn, !isAuthenticated);
            
            // Add locked state styling
            newBtn.classList.add('model-locked');
            newBtn.setAttribute('data-locked', 'true');
            
            // Setup click handler for locked models
            newBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                if (!isAuthenticated) {
                    showCreditMessage('Please log in to use AI models', '/login');
                } else {
                    showCreditMessage('Buy credits to use premium features', '/billing/account');
                }
            });
        } else {
            // Remove any existing padlock indicators
            removePadlockIndicator(newBtn);
            
            // Remove locked state styling
            newBtn.classList.remove('model-locked');
            newBtn.removeAttribute('data-locked');
            
            // Allow access: either has credits OR it's a free model
            newBtn.addEventListener('click', (e) => {
                e.preventDefault();
                selectPresetButton(presetId);
            });
            
            // Re-add dropdown handler for free preset (Preset 6)
            if (presetId === '6') {
                const selectorContainer = newBtn.querySelector('.selector-icon-container');
                if (selectorContainer) {
                    selectorContainer.addEventListener('click', e => {
                        e.preventDefault(); e.stopPropagation();
                        window.openModelSelector(presetId, newBtn);
                    });
                }
            }
        }
    });
}

// Add padlock indicator to a button
function addPadlockIndicator(button, isLoginRequired) {
    // Remove any existing padlock
    removePadlockIndicator(button);
    
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        // Mobile: Show padlock overlay on entire button
        const overlay = document.createElement('div');
        overlay.className = 'padlock-overlay mobile-padlock';
        overlay.innerHTML = `
            <div class="padlock-icon">🔒</div>
            <div class="padlock-text">${isLoginRequired ? 'Login Required' : 'Credits Required'}</div>
        `;
        button.appendChild(overlay);
    } else {
        // Desktop: Show padlock where price band would be
        const costBand = button.querySelector('.cost-band');
        if (costBand) {
            const padlock = document.createElement('div');
            padlock.className = 'padlock-indicator desktop-padlock';
            padlock.innerHTML = '🔒';
            padlock.title = isLoginRequired ? 'Login required to use this model' : 'Credits required to use this model';
            
            // Replace cost band with padlock
            costBand.style.display = 'none';
            costBand.parentNode.insertBefore(padlock, costBand);
        }
    }
}

// Remove padlock indicator from a button
function removePadlockIndicator(button) {
    // Remove mobile padlock overlay
    const mobileOverlay = button.querySelector('.padlock-overlay');
    if (mobileOverlay) {
        mobileOverlay.remove();
    }
    
    // Remove desktop padlock and restore cost band
    const desktopPadlock = button.querySelector('.padlock-indicator');
    if (desktopPadlock) {
        desktopPadlock.remove();
    }
    
    // Restore cost band visibility
    const costBand = button.querySelector('.cost-band');
    if (costBand) {
        costBand.style.display = '';
    }
}

// Show credit purchase message
function showCreditMessage(message, redirectUrl) {
    // Create or update message element
    let messageEl = document.getElementById('credit-message');
    if (!messageEl) {
        messageEl = document.createElement('div');
        messageEl.id = 'credit-message';
        messageEl.className = 'credit-message';
        document.body.appendChild(messageEl);
    }
    
    messageEl.innerHTML = `
        <div class="credit-message-content">
            <p>${message}</p>
            <button class="credit-message-btn" onclick="window.location.href='${redirectUrl}'">
                ${redirectUrl === '/login' ? 'Log In' : 'Buy Credits'}
            </button>
            <button class="credit-message-close" onclick="this.parentElement.parentElement.style.display='none'">×</button>
        </div>
    `;
    
    messageEl.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (messageEl && messageEl.style.display === 'block') {
            messageEl.style.display = 'none';
        }
    }, 5000);
}