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
    
    // The free model preset ID
    const FREE_PRESET_ID = '6';
    
    // checkPremiumAccess is now imported from utils.js
    
    // checkModelCapabilities is now imported from utils.js
    
    // updateUIForModelCapabilities is now imported from utils.js
    

    
    // createUploadIndicator is now imported from fileUpload.js

    

    

    

    
    // Initialize model selection functionality
    initializeModelSelectionLogic();
    
    // Initialize main event listeners
    initializeMainEventListeners();
    
    // For non-authenticated users or users with no credits, lock premium features
    if (!isAuthenticated || userCreditBalance <= 0) {
        lockPremiumFeatures();
    }
    

    

    

    

    

    
    // Image handling functions

    

    
    // Unified file upload handler for both images and PDFs

    
    // Removed updateImagePreviews function as we now use only the unified document preview area
    // All image previews are now handled by updateDocumentPreviews function
    
    // Function to generate the unified document preview area containing both images and PDFs
    

    

    

    

    

    

    

    
    // updateSendButtonState is now imported from chatLogic.js
    
    
    // Event listeners are now handled by initializeMainEventListeners() from eventOrchestration.js
    
    // Model selector functionality is now handled by initializeModelSelectionLogic() from modelSelection.js
    
    // Function to select a preset button and update the current model
    // Expose this function globally for mobile.js
    
    // Function to update multimodal controls (image upload, camera) based on model capability
    // Expose this function globally for mobile UI
    
    // Function to fetch user preferences for model presets
    // Expose this globally for the mobile UI
    
    // Function to update the model preset button labels

    
    // Function to format model ID into a display name
    // Expose this function globally for mobile UI
    
    // Function to manually refresh model prices from the server
    
    // Function to fetch available models from OpenRouter
    
    // Function to open the model selector for a specific preset
    // Expose this function globally for mobile.js
    
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
    
    // Function to format message with markdown, code blocks, etc.
    function formatMessage(text) {
        if (!text) return '';
        
        // Convert markdown-style formatting
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        text = text.replace(/`(.*?)`/g, '<code>$1</code>');
        
        // Convert line breaks to HTML
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }
});
