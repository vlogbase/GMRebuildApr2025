/**
 * Event Orchestration Module
 * Handles main event listener setup and orchestrates interactions between modules
 */

import { debounce, getCSRFToken, forceRepaint } from './utils.js';
import { messageInput, sendButton, newChatButton, clearConversationsButton, imageUploadButton, imageUploadInput, cameraButton, captureButton, switchCameraButton, refreshPricesBtn } from './uiSetup.js';
import { sendMessage, addMessage, clearChat } from './chatLogic.js';
import { createNewConversation, fetchConversations } from './conversationManagement.js';
import { handleFileUpload, handleImageFile, switchCamera, stopCameraStream } from './fileUpload.js';
import { selectPresetButton } from './modelSelection.js';

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
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Clear conversations button
    if (clearConversationsButton) {
        clearConversationsButton.addEventListener('click', () => {
            console.log('🗑️ Clear conversations button clicked');
            if (confirm('Are you sure you want to clear all conversations? This cannot be undone.')) {
                clearChat();
                fetchConversations(true); // Refresh the conversation list
        
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Refresh prices button
    if (refreshPricesBtn) {
        refreshPricesBtn.addEventListener('click', () => {
            console.log('🔄 Refresh prices button clicked');
            refreshModelPrices();
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Example question buttons
    setupExampleQuestionListeners();
    
    // Model selector close button
    const closeSelectorButton = document.getElementById('close-selector');
    if (closeSelectorButton) {
        closeSelectorButton.addEventListener('click', () => {
            console.log('❌ Model selector close button clicked');
            window.closeModelSelector();
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Send button click event
    if (sendButton) {
        sendButton.addEventListener('click', () => {
            console.log('📤 Send button clicked');
            sendMessage();
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Message input focus/blur events and Enter key handling
    if (messageInput) {
        messageInput.addEventListener('focus', () => {
            console.log('📝 Message input focused');
            // Add focused class for styling
            messageInput.classList.add('focused');
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });
        
        messageInput.addEventListener('blur', () => {
            console.log('📝 Message input blurred');
            // Remove focused class
            messageInput.classList.remove('focused');
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });
        
        // Handle Enter key for sending messages (desktop) vs new line (mobile)
        messageInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                // On mobile (width <= 576px), allow Enter to create new lines
                if (window.innerWidth <= 576) {
                    // Allow default behavior (new line)
                    return;
            
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
                
                // On desktop, send message unless Shift is held
                if (!event.shiftKey) {
                    event.preventDefault();
                    console.log('📤 Enter key pressed - sending message');
                    sendMessage();
            
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    } else {
                    // Shift+Enter creates a new line (allow default behavior)
                    console.log('📝 Shift+Enter pressed - creating new line');
            
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
        
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
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
        
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Image upload input change
    if (imageUploadInput) {
        imageUploadInput.addEventListener('change', event => {
            console.log('📸 Image upload input changed');
            const files = event.target.files;
            if (files && files.length > 0) {
                for (let i = 0; i < files.length; i++) {
                    handleImageFile(files[i]);
            
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
                // Clear the input so the same file can be selected again
                event.target.value = '';
        
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Camera button
    if (cameraButton) {
        cameraButton.addEventListener('click', async () => {
            console.log('📷 Camera button clicked');
            await startCameraCapture();
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Capture button
    if (captureButton) {
        captureButton.addEventListener('click', () => {
            console.log('📷 Capture button clicked');
            capturePhoto();
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Switch camera button
    if (switchCameraButton) {
        switchCameraButton.addEventListener('click', switchCamera);

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
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
    window.addEventListener('pageshow', function(event) {
        console.log('📄 Page show event');
        // Re-apply locks when user navigates back from billing page
        if (!isAuthenticated || userCreditBalance <= 0) {
            lockPremiumFeatures(isAuthenticated, userCreditBalance);
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });
    
    // Handle window resize for responsive behavior
    window.addEventListener('resize', debounce(() => {
        console.log('📱 Window resized');
        handleWindowResize();

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
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
        
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
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
        
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
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
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
        e.preventDefault();

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        console.log('⌨️ Keyboard shortcut: Escape');
        closeAnyOpenModals();

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
}

// Handle clicks outside modals to close them
function handleOutsideClicks(e) {
    // Check if click is outside model selector
    const modelSelector = document.getElementById('model-selector');
    if (modelSelector && modelSelector.style.display === 'block') {
        if (e.target === modelSelector) {
            console.log('🖱️ Clicked outside model selector');
            closeModelSelector();
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Check if click is outside other modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (modal.style.display === 'block' || modal.classList.contains('show')) {
            if (e.target === modal) {
                console.log('🖱️ Clicked outside modal');
                closeModal(modal);
        
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });
}

// Start camera capture
async function startCameraCapture() {
    try {
        console.log('📷 Starting camera capture...');
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'environment' } 
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });
        
        const cameraVideo = document.getElementById('camera-video');
        if (cameraVideo) {
            cameraVideo.srcObject = stream;
            cameraVideo.play();
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
        
        // Show camera interface
        const cameraInterface = document.getElementById('camera-interface');
        if (cameraInterface) {
            cameraInterface.style.display = 'block';
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
        

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    } catch (error) {
        console.error('❌ Error accessing camera:', error);
        alert('Unable to access camera. Please check permissions.');

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
}

// Capture photo from camera
function capturePhoto() {
    console.log('📸 Capturing photo...');
    const cameraVideo = document.getElementById('camera-video');
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
        
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }, 'image/jpeg', 0.8);
        
        // Stop camera and hide interface
        stopCameraStream();
        const cameraInterface = document.getElementById('camera-interface');
        if (cameraInterface) {
            cameraInterface.style.display = 'none';
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
}

// Close any open modals
function closeAnyOpenModals() {
    // Close model selector
    const modelSelector = document.getElementById('model-selector');
    if (modelSelector && modelSelector.style.display === 'block') {
        closeModelSelector();

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
    
    // Close other modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (modal.style.display === 'block' || modal.classList.contains('show')) {
            closeModal(modal);
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });
}

// Close specific modal
function closeModal(modal) {
    modal.style.display = 'none';
    modal.classList.remove('show');
    document.body.classList.remove('modal-open');
}

// Close model selector (imported from modelSelection.js)
function closeModelSelector() {
    const modelSelector = document.getElementById('model-selector');
    if (modelSelector) {
        modelSelector.style.display = 'none';
        document.body.classList.remove('modal-open');

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
}

// Handle window resize
function handleWindowResize() {
    // Update mobile/desktop specific behaviors
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        document.body.classList.add('mobile-view');

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    } else {
        document.body.classList.remove('mobile-view');

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
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

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
}

// Refresh model prices (placeholder function)
function refreshModelPrices() {
    console.log('🔄 Refreshing model prices...');
    // This function would typically call the API to refresh prices
    // For now, it's a placeholder that could dispatch an event or call apiService
}

// Setup premium feature locks (moved from main script)
export function lockPremiumFeatures(isAuthenticated, userCreditBalance) {
    console.log('🔒 Locking premium features...');
    
    // Process all model preset buttons
    document.querySelectorAll('.model-preset-btn').forEach(btn => {
        const presetId = btn.getAttribute('data-preset-id');
        
        // Clone buttons to remove existing event listeners
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        
        // Setup new event listeners based on authentication status
        if (!isAuthenticated || userCreditBalance <= 0) {
            // For non-authenticated users or zero balance, redirect to appropriate action
            newBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                if (!isAuthenticated) {
                    window.location.href = '/login';
            
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    } else {
                    window.location.href = '/billing';
            
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }
        
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    } else {
            // For authenticated users with credits, allow normal preset selection
            newBtn.addEventListener('click', (e) => {
                e.preventDefault();
                selectPresetButton(presetId);
        
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });
    
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    }

    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }
    });
}