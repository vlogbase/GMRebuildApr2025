/**
 * Mobile Model Selector for GloriaMundo Chat
 * 
 * This file handles the mobile-specific UI for model selection:
 * - Numbered buttons (1-6)
 * - Bottom sheet panel with preset details
 * - Model selection interface
 */

document.addEventListener('DOMContentLoaded', function() {
    // Only run on mobile devices
    if (window.innerWidth > 576) return;
    
    console.log('Mobile: Initializing mobile model selector');
    
    // Core Elements
    const mobileModelButtons = document.getElementById('mobile-model-buttons');
    const mobilePresetBtns = document.querySelectorAll('.mobile-preset-btn');
    const mobilePanelToggle = document.getElementById('mobile-model-panel-toggle');
    
    // Debug element presence
    console.log('Mobile: Found model buttons:', mobileModelButtons ? 'yes' : 'no');
    console.log('Mobile: Found preset buttons:', mobilePresetBtns.length);
    console.log('Mobile: Found panel toggle:', mobilePanelToggle ? 'yes' : 'no');
    
    // Panel Elements
    const mobileModelPanel = document.getElementById('mobile-model-panel');
    const mobilePanelClose = document.getElementById('mobile-panel-close');
    const mobilePanelPresetBtns = document.querySelectorAll('.mobile-panel-preset-btn');
    
    // Selection Elements
    const mobileModelSelection = document.getElementById('mobile-model-selection');
    const mobileSelectionBack = document.getElementById('mobile-selection-back');
    const mobileSelectionClose = document.getElementById('mobile-selection-close');
    const mobileModelList = document.getElementById('mobile-model-list');
    const mobileModelSearch = document.getElementById('mobile-model-search');
    const mobileResetToDefault = document.getElementById('mobile-reset-to-default');
    
    // Common Elements
    const mobileBackdrop = document.getElementById('mobile-backdrop');
    
    // Init variables
    let currentPresetId = null;
    
    // Initialize on page load - fetch user preferences and update model names
    console.log('Mobile: Initializing model selections on page load');
    
    // Function to initialize the mobile UI
    function initializeMobileUI() {
        console.log('Mobile: Starting UI initialization');
        
        // Update the UI with current preferences
        updateSelectedModelNames();
        
        // Set the active button based on available information
        if (window.activePresetId) {
            console.log(`Mobile: Setting active button to ${window.activePresetId} from window.activePresetId`);
            updateMobileActiveButton(window.activePresetId);
        } else if (window.userPreferences && Object.keys(window.userPreferences).length > 0) {
            // If no active preset ID but we have preferences, use the first one
            const firstPresetId = Object.keys(window.userPreferences)[0];
            console.log(`Mobile: Setting active button to ${firstPresetId} from first user preference`);
            updateMobileActiveButton(firstPresetId);
        } else {
            // Fallback to preset 1
            console.log('Mobile: Falling back to preset 1 as active button');
            updateMobileActiveButton('1');
        }
        
        console.log('Mobile: Mobile UI initialization complete');
    }
    
    // Track initialization state with timestamps for debugging
    let preferencesReady = false;
    let modelsReady = false;
    let preferencesTimestamp = null;
    let modelsTimestamp = null;
    let initializationAttempts = 0;
    
    // Set up event listeners for synchronization with main script
    document.addEventListener('userPreferencesLoaded', function(event) {
        console.log('Mobile: Received userPreferencesLoaded event', event.detail);
        preferencesReady = true;
        preferencesTimestamp = new Date().getTime();
        
        // Extract preferences from event if available
        if (event.detail && event.detail.preferences) {
            console.log('Mobile: Using preferences data from event payload');
            // Create a shallow copy which is sufficient for this non-nested object
            window.userPreferences = Object.assign({}, event.detail.preferences);
            
            // Validate preferences format
            if (!window.userPreferences || typeof window.userPreferences !== 'object') {
                console.warn('Mobile: Received invalid preferences format, setting empty object');
                window.userPreferences = {};
            }
        } else {
            console.log('Mobile: No preferences in event data, using global state');
            // Ensure we have something valid
            if (!window.userPreferences || typeof window.userPreferences !== 'object') {
                console.warn('Mobile: Global userPreferences not valid, initializing empty object');
                window.userPreferences = {};
            }
        }
        
        // Log the actual preferences we're using
        console.log('Mobile: User preferences after event:', window.userPreferences);
        
        // Always update the model names when preferences change, even after initial load
        if (window.availableModels && window.availableModels.length > 0) {
            updateSelectedModelNames();
        } else {
            displayFallbackModelNames();
        }
        
        attemptInitialization();
    });
    
    document.addEventListener('modelsLoaded', function(event) {
        console.log('Mobile: Received modelsLoaded event', event.detail);
        modelsReady = true;
        modelsTimestamp = new Date().getTime();
        
        // Extract models from event if available
        if (event.detail && event.detail.models && Array.isArray(event.detail.models)) {
            console.log(`Mobile: Using models data from event payload (${event.detail.models.length} models)`);
            // Use array map to create a shallow copy of each model object
            window.availableModels = event.detail.models.map(model => Object.assign({}, model));
            
            // Validate first few models
            if (window.availableModels.length > 0) {
                const sampleModels = window.availableModels.slice(0, 3);
                console.log('Mobile: First few models from event:', sampleModels.map(m => m.id));
            }
        } else {
            console.log('Mobile: No models in event data, using global state');
            // Validate global models
            if (!window.availableModels || !Array.isArray(window.availableModels)) {
                console.warn('Mobile: Global availableModels not valid, initializing empty array');
                window.availableModels = [];
            }
        }
        
        // Update the UI if we have both data points
        if (window.userPreferences && window.availableModels && window.availableModels.length > 0) {
            updateSelectedModelNames();
        }
        
        attemptInitialization();
    });
    
    // Function to check if we can initialize
    function attemptInitialization() {
        initializationAttempts++;
        console.log(`Mobile: Initialization attempt #${initializationAttempts}`);
        
        if (preferencesReady && modelsReady) {
            console.log('Mobile: Both preferences and models are ready, initializing UI');
            console.log(`Mobile: Timing - Preferences: ${preferencesTimestamp}, Models: ${modelsTimestamp}, Diff: ${Math.abs(preferencesTimestamp - modelsTimestamp)}ms`);
            
            // Log data state before initialization
            console.log('Mobile: Data check before initialization:');
            console.log(`- userPreferences: ${window.userPreferences ? 'Available' : 'Missing'}`);
            console.log(`- availableModels: ${window.availableModels ? (window.availableModels.length + ' models') : 'Missing'}`);
            
            // Initialize UI with complete data
            initializeMobileUI();
        } else {
            const waitingFor = [];
            if (!preferencesReady) waitingFor.push('preferences');
            if (!modelsReady) waitingFor.push('models');
            
            console.log(`Mobile: Still waiting for: ${waitingFor.join(', ')}`);
            console.log(`Mobile: Timestamps - Preferences: ${preferencesTimestamp}, Models: ${modelsTimestamp}`);
        }
    }
    
    // Fallback initialization with increasing timeouts to handle possible race conditions
    // First timeout after 2 seconds
    setTimeout(function() {
        if (!preferencesReady || !modelsReady) {
            console.log('Mobile: First fallback check (2s) - some data still not ready');
            console.log(`Mobile: Status - Preferences: ${preferencesReady ? 'Ready' : 'Not ready'}, Models: ${modelsReady ? 'Ready' : 'Not ready'}`);
            
            // If we have user preferences but not models after first timeout, still initialize
            // This handles case where models might be slow to load
            if (preferencesReady && window.userPreferences) {
                console.log('Mobile: First fallback init - have preferences but waiting for models');
                initializeMobileUI();
            }
        }
    }, 2000);
    
    // Final failsafe timeout after 5 seconds
    setTimeout(function() {
        if (!preferencesReady || !modelsReady) {
            console.warn('Mobile: Failsafe initialization (5s) - forced initialization regardless of data state');
            initializeMobileUI();
        }
    }, 5000);
    
    // Handle preset button click (now for model selection only)
    function handlePresetButtonClick(presetId) {
        console.log(`Mobile: Opening model selection for preset ${presetId}`);
        showMobileModelSelection(presetId);
    }
    
    // Handle activating a preset
    function activatePreset(presetId) {
        console.log(`Mobile: Activating preset ${presetId}`);
        // Use the global selectPresetButton function if available
        if (typeof window.selectPresetButton === 'function') {
            window.selectPresetButton(presetId);
            
            // Update the active button in the UI
            updateMobileActiveButton(presetId);
            
            // Get the model name for the notification - first try the data attribute we stored
            const activeBtn = document.querySelector(`.mobile-preset-btn[data-preset-id="${presetId}"]`);
            let modelName = "Unknown Model";
            
            if (activeBtn && activeBtn.getAttribute('data-current-model-name')) {
                // Use the cached model name from the button's data attribute (most up-to-date)
                modelName = activeBtn.getAttribute('data-current-model-name');
                console.log(`Mobile: Using cached model name from button: ${modelName}`);
            } else if (window.userPreferences && window.userPreferences[presetId]) {
                // Fallback to getting it from userPreferences (might be outdated if changed recently)
                const modelId = window.userPreferences[presetId];
                if (window.availableModels) {
                    const model = window.availableModels.find(m => m.id === modelId);
                    if (model) {
                        modelName = model.name || model.id;
                    } else {
                        modelName = modelId; // Fallback to ID if model not found
                    }
                }
            }
            
            // Show notification when preset is activated
            showModelNotification(presetId, `Activated ${modelName}`);
            
            return true;
        } else {
            console.error('Mobile: selectPresetButton function not found');
            return false;
        }
    }
    
    // Update the active button in the numbered row (1-6)
    function updateMobileActiveButton(presetId) {
        if (!mobilePresetBtns) return;
        
        console.log(`Mobile: Updating active button to ${presetId}`);
        
        // Remove active class from all buttons
        mobilePresetBtns.forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Add active class to the selected button
        const activeBtn = document.querySelector(`.mobile-preset-btn[data-preset-id="${presetId}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
    }
    
    // Update the mobile preset button label with the selected model
    function updateMobilePresetButtonLabel(presetId, modelId, modelName) {
        console.log(`Mobile: Updating mobile preset button label for preset ${presetId} with model ${modelId}`);
        
        // Find the mobile preset button
        const mobilePresetBtn = document.querySelector(`.mobile-preset-btn[data-preset-id="${presetId}"]`);
        if (!mobilePresetBtn) {
            console.warn(`Mobile: Could not find mobile preset button for preset ${presetId}`);
            return;
        }
        
        // Set the model ID as data attribute for future reference
        mobilePresetBtn.setAttribute('data-model-id', modelId);
        
        // Store the current model name on the button as a data attribute
        // This will be used by activatePreset to show the correct model name in notifications
        mobilePresetBtn.setAttribute('data-current-model-name', modelName);
        
        // Update the aria-label to include the model name
        // This way the button's accessible name reflects the current model
        mobilePresetBtn.setAttribute('aria-label', `Preset ${presetId}: ${modelName}`);
        
        // Also update the corresponding panel button display
        // This is the more detailed button in the slide-up panel
        const panelButton = document.querySelector(`.mobile-panel-preset-btn[data-preset-id="${presetId}"]`);
        if (panelButton) {
            const selectedModelElement = document.getElementById(`mobile-selected-model-${presetId}`);
            if (selectedModelElement) {
                selectedModelElement.textContent = modelName;
            }
        }
        
        console.log(`Mobile: Updated preset button ${presetId} with model ${modelName}`);
    }
    
    // Select a model for a specific preset
    function selectModelForPreset(presetId, modelId) {
        console.log(`Mobile: Selected model ${modelId} for preset ${presetId}`);
        
        // Get model name for notification
        let modelName = modelId;
        if (window.availableModels) {
            const model = window.availableModels.find(m => m.id === modelId);
            if (model) {
                modelName = model.name || model.id;
            }
        }
        
        // Use the global selectModelForPreset function if available (don't skip activation)
        if (window.selectModelForPreset && typeof window.selectModelForPreset === 'function') {
            console.log(`Mobile: Using global selectModelForPreset for preset ${presetId} with model ${modelId}`);
            
            // Call the global selectModelForPreset with false for skipActivation
            // This will both assign the model AND activate it
            window.selectModelForPreset(presetId, modelId, false);
            
            // Update the UI to reflect the change
            updateSelectedModelNames();
            
            // Update the active button in the numbered row
            updateMobileActiveButton(presetId);
            
            // Update the mobile preset button label directly
            updateMobilePresetButtonLabel(presetId, modelId, modelName);
            
            // Show a confirmation notification
            showModelNotification(presetId, `Selected ${modelName}`);
        } else {
            console.error('Mobile: window.selectModelForPreset function not available, falling back to selectPresetButton');
            
            // Fallback to the old method if selectModelForPreset is not available
            if (window.selectPresetButton && typeof window.selectPresetButton === 'function') {
                window.selectPresetButton(presetId, modelId);
                
                // Update the UI
                updateSelectedModelNames();
                updateMobileActiveButton(presetId);
                
                // Update the mobile preset button label directly
                updateMobilePresetButtonLabel(presetId, modelId, modelName);
                
                // Show notification
                showModelNotification(presetId, `Selected ${modelName}`);
            } else {
                console.error('Mobile: selectPresetButton function not available either');
            }
        }
        
        // Hide both panels
        hideMobileModelSelection();
        hideMobileModelPanel();
    }
    
    // Show a notification when a model is selected
    function showModelNotification(presetId, modelName) {
        console.log(`Mobile: Showing notification for preset ${presetId} with model ${modelName}`);
        
        // Create notification element if it doesn't exist
        let notification = document.getElementById('mobile-model-notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'mobile-model-notification';
            notification.className = 'mobile-model-notification';
            document.body.appendChild(notification);
        }
        
        // Set notification content - show custom message if provided, otherwise use default
        if (modelName.startsWith('Selected ') || modelName.startsWith('Activated ')) {
            notification.textContent = `${modelName} on Preset ${presetId}`;
        } else {
            notification.textContent = `Selected "${modelName}" for Preset ${presetId}`;
        }
        
        // Show notification with the correct 'show' class
        notification.classList.add('show');
        
        // Hide after a delay (3 seconds)
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
    
    // Update selected model names in the panel
    function updateSelectedModelNames() {
        // Check for userPreferences
        if (!window.userPreferences) {
            console.warn('Mobile: updateSelectedModelNames called but window.userPreferences is not set.');
            return;
        }
        
        // Check for availableModels
        if (!window.availableModels || window.availableModels.length === 0) {
            console.warn('Mobile: updateSelectedModelNames called but window.availableModels is empty or not set.');
            
            // Log what's available to help with debugging
            if (window.availableModels) {
                console.log(`Mobile: availableModels exists but has ${window.availableModels.length} items`);
            } else {
                console.log('Mobile: availableModels is undefined');
            }
            
            // Still try to update with fallback text if we have user preferences
            // This at least shows something rather than blank buttons
            displayFallbackModelNames();
            return;
        }
        
        console.log(`Mobile: Updating selected model names in panel with ${window.availableModels.length} available models`);
        
        // Check the first few models to help with debugging
        const sampleModels = window.availableModels.slice(0, 3);
        console.log('Mobile: Sample available models:', sampleModels.map(m => ({ id: m.id, name: m.name })));
        
        for (let i = 1; i <= 6; i++) {
            const presetId = i.toString();
            const modelId = window.userPreferences[presetId];
            
            // Get the model display name
            let displayName = 'Not set';
            
            if (modelId) {
                // Try to find the model in availableModels
                const model = window.availableModels.find(m => m.id === modelId);
                if (model) {
                    displayName = model.name || model.id;
                    console.log(`Mobile: Found model for preset ${presetId}: ${displayName}`);
                } else {
                    // If model not found, use modelId as fallback with warning
                    displayName = modelId;
                    console.warn(`Mobile: Model not found for preset ${presetId} with ID ${modelId}`);
                }
            } else {
                console.warn(`Mobile: No model ID set for preset ${presetId}`);
            }
            
            // Update the display
            const displayElement = document.getElementById(`mobile-selected-model-${presetId}`);
            if (displayElement) {
                displayElement.textContent = displayName;
            } else {
                console.warn(`Mobile: Display element not found for preset ${presetId}`);
            }
        }
        
        console.log('Mobile: Model names updated successfully');
    }
    
    // Fallback display function when models aren't available
    function displayFallbackModelNames() {
        console.log('Mobile: Using fallback model names since availableModels is not available');
        
        for (let i = 1; i <= 6; i++) {
            const presetId = i.toString();
            const modelId = window.userPreferences && window.userPreferences[presetId];
            
            let displayName = modelId || 'Loading...';
            
            // Add a static prefix based on the preset number for better UX while loading
            switch(presetId) {
                case '1': displayName = modelId || 'General Model'; break;
                case '2': displayName = modelId || 'Alternative'; break;
                case '3': displayName = modelId || 'Reasoning'; break;
                case '4': displayName = modelId || 'Vision Model'; break;
                case '5': displayName = modelId || 'Search Model'; break;
                case '6': displayName = modelId || 'Free Model'; break;
            }
            
            // Update the display with fallback
            const displayElement = document.getElementById(`mobile-selected-model-${presetId}`);
            if (displayElement) {
                displayElement.textContent = displayName;
            }
        }
    }
    
    // Fetch and update user preferences from server
    function fetchAndUpdatePreferences(callback) {
        console.log('Mobile: Fetching user preferences');
        
        // If the main script's function exists, use it
        if (window.fetchUserPreferences && typeof window.fetchUserPreferences === 'function') {
            window.fetchUserPreferences()
                .then(() => {
                    console.log('Mobile: User preferences fetched, updating UI');
                    updateSelectedModelNames();
                    
                    // Call callback function if provided
                    if (typeof callback === 'function') {
                        callback();
                    }
                })
                .catch(err => {
                    console.error('Mobile: Error fetching user preferences:', err);
                    
                    // Still call callback even if there was an error
                    if (typeof callback === 'function') {
                        callback();
                    }
                });
        } else {
            console.log('Mobile: fetchUserPreferences not available, using current values');
            // Fallback to just updating from current values
            updateSelectedModelNames();
            
            // Call callback function if provided
            if (typeof callback === 'function') {
                callback();
            }
        }
    }
    
    // Hide mobile model panel
    function hideMobileModelPanel() {
        if (mobileModelPanel) {
            mobileModelPanel.classList.remove('visible');
        }
        if (mobileBackdrop) {
            mobileBackdrop.classList.remove('visible');
        }
    }
    
    // Show mobile model selection for a specific preset
    function showMobileModelSelection(presetId) {
        console.log(`Mobile: Opening model selection for preset ${presetId}`);
        currentPresetId = presetId;
        
        // Hide the model panel
        if (mobileModelPanel) {
            mobileModelPanel.classList.remove('visible');
        }
        
        // Show the selection panel and backdrop
        if (mobileModelSelection) {
            mobileModelSelection.classList.add('visible');
        } else {
            console.error('Mobile: Element mobileModelSelection not found');
            return; // Exit the function if critical elements aren't found
        }
        
        if (mobileBackdrop) {
            mobileBackdrop.classList.add('visible');
        }
        
        // Populate the model list
        populateMobileModelList(presetId);
        
        // Clear search input
        if (mobileModelSearch) {
            mobileModelSearch.value = '';
        }
        
        console.log('Mobile: Model selection panel opened');
    }
    
    // Hide mobile model selection
    function hideMobileModelSelection() {
        if (mobileModelSelection) {
            mobileModelSelection.classList.remove('visible');
        }
        if (mobileBackdrop) {
            mobileBackdrop.classList.remove('visible');
        }
    }
    
    // Back from selection to panel
    function backToModelPanel() {
        if (mobileModelSelection) {
            mobileModelSelection.classList.remove('visible');
        }
        if (mobileModelPanel) {
            mobileModelPanel.classList.add('visible');
        }
        currentPresetId = null;
    }
    
    // Populate the mobile model list for a specific preset
    function populateMobileModelList(presetId) {
        // Clear the current list
        if (mobileModelList) {
            mobileModelList.innerHTML = '';
        }
        
        // Get reference to the loading element
        const loadingElement = document.getElementById('mobile-models-loading');
        
        // Show the loading indicator
        if (loadingElement) {
            loadingElement.classList.remove('hidden');
        }
        
        // If the main script's populateModelList function exists, use it to get the models
        if (window.populateModelList && typeof window.populateModelList === 'function') {
            // We'll use our own list, but let the main script load the data first
            window.populateModelList(presetId);
            
            // Check if models are available immediately
            let allModels = window.availableModels || [];
            
            // Log available models for debugging
            console.log(`Mobile: Found ${allModels.length} models from window.availableModels`);
            
            // If no models are available yet, wait and retry a few times
            if (allModels.length === 0) {
                console.log('Mobile: No models available yet, will retry');
                
                let retryCount = 0;
                const maxRetries = 5;
                const retryInterval = 800; // milliseconds
                
                const checkModels = () => {
                    allModels = window.availableModels || [];
                    console.log(`Mobile: Retry ${retryCount + 1}/${maxRetries} - Found ${allModels.length} models`);
                    
                    if (allModels.length > 0 || retryCount >= maxRetries) {
                        // We have models or have exhausted retries, proceed to filtering and rendering
                        finishPopulatingModels(allModels, presetId);
                        
                        // Hide loading indicator once we have models or have given up
                        if (loadingElement) {
                            loadingElement.classList.add('hidden');
                        }
                    } else {
                        // No models yet and more retries available, try again after interval
                        retryCount++;
                        setTimeout(checkModels, retryInterval);
                    }
                };
                
                // Start the retry process
                setTimeout(checkModels, retryInterval);
            } else {
                // We already have models, proceed immediately
                finishPopulatingModels(allModels, presetId);
                
                // Hide loading indicator
                if (loadingElement) {
                    loadingElement.classList.add('hidden');
                }
            }
        } else {
            console.error('Mobile: populateModelList function not available in window context');
            
            // Hide loading indicator even if we can't load models
            if (loadingElement) {
                loadingElement.classList.add('hidden');
            }
        }
    }
    
    // Helper function to filter and display models after they're loaded
    function finishPopulatingModels(allModels, presetId) {
        let filteredModels;
        
        // Wait for desktop functions to be available and use them for 100% consistency
        const waitForDesktopFunctions = () => {
            return new Promise((resolve) => {
                if (window.presetFilters && window.presetFilters[presetId]) {
                    resolve(true);
                } else {
                    // Check every 100ms for up to 3 seconds
                    let attempts = 0;
                    const maxAttempts = 30;
                    const checkInterval = setInterval(() => {
                        attempts++;
                        if (window.presetFilters && window.presetFilters[presetId]) {
                            clearInterval(checkInterval);
                            resolve(true);
                        } else if (attempts >= maxAttempts) {
                            clearInterval(checkInterval);
                            resolve(false);
                        }
                    }, 100);
                }
            });
        };
        
        waitForDesktopFunctions().then((hasDesktopFunctions) => {
            if (hasDesktopFunctions) {
                // Use the desktop presetFilters for identical filtering
                filteredModels = allModels.filter(window.presetFilters[presetId]);
                console.log(`Mobile: Using desktop presetFilters for preset ${presetId}, filtered to ${filteredModels.length} models`);
                
                // Use desktop sorting function
                if (window.sortModelsByPreset && typeof window.sortModelsByPreset === 'function') {
                    filteredModels = window.sortModelsByPreset(filteredModels, presetId);
                    console.log(`Mobile: Using desktop sortModelsByPreset function for preset ${presetId}`);
                }
                
                // Continue with the rest of the function
                finishModelDisplay(filteredModels, presetId);
            } else {
                console.warn(`Mobile: Desktop functions not available after waiting, using fallback for preset ${presetId}`);
                // Use fallback filtering and sorting
                filteredModels = applyFallbackFiltering(allModels, presetId);
                finishModelDisplay(filteredModels, presetId);
            }
        });
    }
    
    // Helper function to apply fallback filtering when desktop functions aren't available
    function applyFallbackFiltering(allModels, presetId) {
        let filteredModels;
        
        // Updated fallback logic that matches desktop exactly
        switch (presetId) {
            case '1':
            case '2':
                    // All non-free models - include auto model specifically
                    filteredModels = allModels.filter(model => {
                        if (model.id === 'openrouter/auto') return true;
                        const isFree = model.id.includes(':free') || model.cost_band === 'free' || model.is_free === true;
                        return !isFree;
                    });
                    break;
                    
                case '3':
                    // Reasoning models (non-free) - updated to match desktop exactly
                    filteredModels = allModels.filter(model => {
                        const isFree = model.id.includes(':free') || model.cost_band === 'free' || model.is_free === true;
                        if (isFree) return false;
                        
                        if (model.is_reasoning === true) return true;
                        // Updated to include thinking and o4 patterns as requested
                        return model.id.includes('reasoning') || model.id.includes('thinking') || 
                               model.id.includes('o1') || model.id.includes('o3') || model.id.includes('o4');
                    });
                    break;
                    
                case '4':
                    // Multimodal/image-capable models (non-free) - updated to match desktop exactly
                    filteredModels = allModels.filter(model => {
                        const isFree = model.id.includes(':free') || model.cost_band === 'free' || model.is_free === true;
                        const isMultimodal = model.is_multimodal || model.supports_vision || 
                                           model.id.includes('vision') || model.id.includes('image') || 
                                           model.id.includes('multimodal') || model.id.includes('dall-e') || 
                                           model.id.includes('midjourney') || model.id.includes('stable-diffusion') ||
                                           model.id.includes('flux') || model.id.includes('imagen');
                        return !isFree && isMultimodal;
                    });
                    break;
                    
                case '5':
                    // Search models - updated to match desktop exactly
                    filteredModels = allModels.filter(model => {
                        const isFree = model.id.includes(':free') || model.cost_band === 'free' || model.is_free === true;
                        const isSearch = model.id.includes('perplexity') || model.id.includes('search') || 
                                       model.id.includes('sonar');
                        return !isFree && isSearch;
                    });
                    break;
                    
                case '6':
                    // Free models only
                    filteredModels = allModels.filter(model => {
                        return model.id.includes(':free') || model.cost_band === 'free' || model.is_free === true;
                    });
                    break;
                    
                default:
                    filteredModels = allModels;
        }
        
        // Apply fallback sorting since desktop sorting isn't available in fallback mode
        if (presetId === '2') {
            // Preset 2: Sort by context length (highest first)
            filteredModels.sort((a, b) => {
                const contextA = parseInt(a.context_length) || 0;
                const contextB = parseInt(b.context_length) || 0;
                return contextB - contextA;
            });
        } else {
            // All other presets: Sort by ELO score (highest first)
            filteredModels.sort((a, b) => {
                const eloA = parseFloat(a.elo_score) || 0;
                const eloB = parseFloat(b.elo_score) || 0;
                return eloB - eloA;
            });
        }
        
        return filteredModels;
    }
    
    // Helper function to handle the final model display after filtering and sorting
    function finishModelDisplay(filteredModels, presetId) {
        console.log(`Mobile: Displaying ${filteredModels.length} models for preset ${presetId}`);
        
        // Get current selected model for this preset
        const currentModel = window.userPreferences?.[presetId] || window.defaultModels?.[presetId];
        
        // Display empty state message if no models are available after filtering
        if (filteredModels.length === 0) {
            const emptyMessage = document.createElement('li');
            emptyMessage.className = 'mobile-model-item empty-state';
            emptyMessage.innerHTML = `
                <div class="model-info">
                    <span class="model-name">No models available</span>
                    <span class="model-description">Try a different preset or check your connection</span>
                </div>
            `;
            if (mobileModelList) {
                mobileModelList.appendChild(emptyMessage);
            }
            
            // Hide loading indicator
            const loadingElement = document.getElementById('mobile-models-loading');
            if (loadingElement) {
                loadingElement.classList.add('hidden');
            }
            return;
        }
        
        // Create model list items
        
        // Create a DocumentFragment for batch DOM updates
        const fragment = document.createDocumentFragment();
        
        // Create list items and add them to the fragment
        filteredModels.forEach(model => {
            const li = document.createElement('li');
            li.setAttribute('data-model-id', model.id);
            
            if (model.id === currentModel) {
                li.classList.add('active');
            }
            
            // Create model info div
            const modelInfo = document.createElement('div');
            modelInfo.className = 'model-info';
            
            // Model title
            const modelTitle = document.createElement('div');
            modelTitle.className = 'model-title';
            modelTitle.textContent = model.name || model.id;
            modelInfo.appendChild(modelTitle);
            
            // Model description (context window)
            if (model.context_length) {
                const modelDesc = document.createElement('div');
                modelDesc.className = 'model-description';
                modelDesc.textContent = `Context: ${model.context_length.toLocaleString()} tokens`;
                modelInfo.appendChild(modelDesc);
            }
            
            // Cost information
            const modelCost = document.createElement('div');
            modelCost.className = 'model-cost';
            
            // Cost band indicator
            const costBandIndicator = document.createElement('span');
            costBandIndicator.className = 'cost-band-indicator';
            
            // Determine cost band class
            let costBandClass = '';
            if (model.is_free) {
                modelCost.classList.add('free-model');
                modelCost.textContent = 'Free';
            } else if (model.cost_band) {
                // Use the cost_band directly from the model data if it exists
                costBandIndicator.textContent = model.cost_band;
                
                // Apply the appropriate class based on the cost band value
                if (model.cost_band === '$$$$') {
                    costBandClass = 'cost-band-4-danger';
                } else if (model.cost_band === '$$$') {
                    costBandClass = 'cost-band-3-warn';
                } else if (model.cost_band === '$$') {
                    costBandClass = 'cost-band-2';
                } else if (model.cost_band === '$') {
                    costBandClass = 'cost-band-1';
                }
            } else {
                // Fallback to using pricing calculations if cost_band isn't available
                const inputPrice = model.input_price || 0;
                const outputPrice = model.output_price || 0;
                const maxPrice = Math.max(inputPrice, outputPrice);
                
                if (maxPrice >= 100.0) {
                    costBandClass = 'cost-band-4-danger';
                    costBandIndicator.textContent = '$$$$';
                } else if (maxPrice >= 10.0) {
                    costBandClass = 'cost-band-3-warn';
                    costBandIndicator.textContent = '$$$';
                } else if (maxPrice >= 1.0) {
                    costBandClass = 'cost-band-2';
                    costBandIndicator.textContent = '$$';
                } else {
                    costBandClass = 'cost-band-1';
                    costBandIndicator.textContent = '$';
                }
            }
            
            if (costBandClass) {
                costBandIndicator.classList.add(costBandClass);
                modelCost.appendChild(costBandIndicator);
            }
            
            modelInfo.appendChild(modelCost);
            li.appendChild(modelInfo);
            
            // Add click handler
            li.addEventListener('click', function() {
                selectModelForPreset(presetId, model.id);
            });
            
            // Add the list item to the fragment
            fragment.appendChild(li);
        });
        
        // Add the entire fragment to the DOM in one operation
        if (mobileModelList) {
            mobileModelList.appendChild(fragment);
        } else {
            console.error('Mobile: mobileModelList is null, cannot append model items');
        }
    }
    
    // Filter the mobile model list based on search term
    function filterMobileModelList(searchTerm) {
        if (!mobileModelList) return;
        
        const items = mobileModelList.querySelectorAll('li');
        
        items.forEach(item => {
            const modelTitle = item.querySelector('.model-title');
            const modelText = modelTitle ? modelTitle.textContent.toLowerCase() : '';
            const modelId = item.getAttribute('data-model-id').toLowerCase();
            
            // Show item if search term is empty or matches model name or id
            if (!searchTerm || modelText.includes(searchTerm) || modelId.includes(searchTerm)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }
    
    // Reset the current preset to its default model
    async function resetCurrentPresetToDefault() {
        if (!currentPresetId) {
            showMobileNotification('No preset selected', 'error');
            return;
        }
        
        try {
            console.log(`Mobile: Resetting preset ${currentPresetId} to default`);
            
            // Import the reset function from apiService
            const { resetPreferencesAPI } = await import('./apiService.js');
            
            const response = await resetPreferencesAPI(currentPresetId);
            
            if (response && response.success) {
                console.log(`Mobile: Preset ${currentPresetId} reset successfully`);
                
                // Clear local preference for this preset
                if (window.userPreferences) {
                    delete window.userPreferences[currentPresetId];
                }
                
                // Update mobile UI
                updateMobilePresetsDisplay();
                showMobileNotification(`Preset ${currentPresetId} reset to default`);
                
                // Trigger refresh of desktop UI too
                if (typeof window.updatePresetButtonLabels === 'function') {
                    window.updatePresetButtonLabels();
                }
                
                // Close the mobile selection panel
                hideMobileModelSelection();
            } else {
                throw new Error(response?.error || 'Unknown error');
            }
        } catch (error) {
            console.error(`Mobile: Reset failed for preset ${currentPresetId}:`, error);
            showMobileNotification('Failed to reset preset', 'error');
        }
    }
    
    // Set up event listeners
    
    // Mobile preset buttons (1-6) - Clicking directly activates the preset
    mobilePresetBtns.forEach(btn => {
        // Simple click handler - just activate the preset
        btn.addEventListener('click', function(e) {
            const presetId = this.getAttribute('data-preset-id');
            console.log(`Mobile: Preset button ${presetId} clicked`);
            activatePreset(presetId);
        });
    });
    
    // Panel toggle button
    if (mobilePanelToggle) {
        mobilePanelToggle.addEventListener('click', function() {
            showMobileModelPanel();
        });
    }
    
    // Panel preset buttons
    mobilePanelPresetBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const presetId = this.getAttribute('data-preset-id');
            handlePresetButtonClick(presetId);
        });
    });
    
    // Panel close button
    if (mobilePanelClose) {
        mobilePanelClose.addEventListener('click', function() {
            hideMobileModelPanel();
        });
    }
    
    // Selection back button
    if (mobileSelectionBack) {
        mobileSelectionBack.addEventListener('click', function() {
            backToModelPanel();
        });
    }
    
    // Selection close button
    if (mobileSelectionClose) {
        mobileSelectionClose.addEventListener('click', function() {
            hideMobileModelSelection();
            hideMobileModelPanel();
        });
    }
    
    // Reset to default button in selection
    if (mobileResetToDefault) {
        mobileResetToDefault.addEventListener('click', function() {
            resetCurrentPresetToDefault();
        });
    }
    
    // Search input
    if (mobileModelSearch) {
        mobileModelSearch.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase().trim();
            filterMobileModelList(searchTerm);
        });
    }
    
    // Backdrop click
    if (mobileBackdrop) {
        mobileBackdrop.addEventListener('click', function() {
            hideMobileModelSelection();
            hideMobileModelPanel();
        });
    }
    
    // Show mobile model panel
    function showMobileModelPanel() {
        console.log('Mobile: Opening model panel');
        
        // First show the loading state
        if (mobileModelPanel) {
            mobileModelPanel.classList.add('visible');
        } else {
            console.error('Mobile: Element mobileModelPanel not found');
            return; // Exit if critical element is missing
        }
        
        if (mobileBackdrop) {
            mobileBackdrop.classList.add('visible');
        }
        
        // Then update names - this ensures the panel is visible immediately
        // rather than waiting for the data to load first
        fetchAndUpdatePreferences();
    }
    
    // Handle preset selection from other scripts
    document.addEventListener('preset-selected', function(e) {
        if (e.detail && e.detail.presetId) {
            console.log(`Mobile: Detected preset selection: ${e.detail.presetId}`);
            updateMobileActiveButton(e.detail.presetId);
        }
    });
    
    // Listen for model changes from the main script
    document.addEventListener('model-selected', function() {
        updateSelectedModelNames();
    });
    
    // Reset All to Default button in model panel
    const mobileResetAllToDefault = document.getElementById('mobile-reset-all-to-default');
    if (mobileResetAllToDefault) {
        mobileResetAllToDefault.addEventListener('click', function() {
            // Add confirmation dialog
            if (confirm('Are you sure you want to reset all model presets to their defaults? This will clear your custom model selections.')) {
                // Add haptic feedback
                if (navigator.vibrate) {
                    navigator.vibrate(20);
                }
                resetAllPresetsToDefault();
            }
        });
    }

    // Add global reset function for mobile parity with desktop
    window.mobileResetToDefaults = async function() {
        try {
            // Import the reset function from apiService
            const { resetPreferencesAPI } = await import('./apiService.js');
            
            console.log('Mobile: Resetting all presets to defaults');
            showMobileNotification('Resetting all presets...', 'info');
            
            const response = await resetPreferencesAPI();
            
            if (response && response.success) {
                console.log('Mobile: All presets reset successfully');
                
                // Clear local preferences
                window.userPreferences = {};
                
                // Update mobile UI
                updateMobilePresetsDisplay();
                showMobileNotification('All presets reset to defaults');
                
                // Trigger refresh of desktop UI too
                if (typeof window.updatePresetButtonLabels === 'function') {
                    window.updatePresetButtonLabels();
                }
            } else {
                throw new Error(response?.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Mobile: Reset failed:', error);
            showMobileNotification('Failed to reset presets', 'error');
        }
    };

    // Mobile notification system for better user feedback
    function showMobileNotification(message, type = 'success') {
        // Remove any existing notifications
        const existingNotification = document.querySelector('.mobile-notification');
        if (existingNotification) {
            existingNotification.remove();
        }

        // Create notification element
        const notification = document.createElement('div');
        notification.className = `mobile-notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fa-solid ${type === 'error' ? 'fa-exclamation-triangle' : 'fa-check-circle'}"></i>
                <span>${message}</span>
            </div>
        `;

        // Add to body
        document.body.appendChild(notification);

        // Trigger animation
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });

        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }, 3000);

        // Add haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate(type === 'error' ? [100, 50, 100] : 50);
        }
    }

    // Enhanced loading states for better UX
    function showMobileLoadingState(element, text = 'Loading...') {
        if (!element) return;
        
        const originalContent = element.innerHTML;
        element.setAttribute('data-original-content', originalContent);
        element.disabled = true;
        element.classList.add('loading');
        
        element.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <span>${text}</span>
            </div>
        `;
    }

    function hideMobileLoadingState(element) {
        if (!element) return;
        
        const originalContent = element.getAttribute('data-original-content');
        if (originalContent) {
            element.innerHTML = originalContent;
            element.removeAttribute('data-original-content');
        }
        element.disabled = false;
        element.classList.remove('loading');
    }

    // Update mobile presets display with loading states
    function updateMobilePresetsDisplay() {
        if (!window.userPreferences || !window.availableModels) {
            console.log('Mobile: Waiting for preferences and models to load...');
            return;
        }

        // Update each preset button with current model
        for (let i = 1; i <= 6; i++) {
            const button = document.querySelector(`.mobile-preset-btn[data-preset-id="${i}"]`);
            const panelButton = document.querySelector(`.mobile-panel-preset-btn[data-preset-id="${i}"]`);
            
            if (window.userPreferences[i] && window.availableModels) {
                const modelId = window.userPreferences[i];
                const model = window.availableModels.find(m => m.id === modelId);
                const modelName = model ? model.name : modelId;
                
                // Update button data attribute for quick access
                if (button) {
                    button.setAttribute('data-current-model-name', modelName);
                }
                
                // Update panel display
                const selectedModelSpan = document.getElementById(`mobile-selected-model-${i}`);
                if (selectedModelSpan) {
                    selectedModelSpan.textContent = modelName;
                }
            }
        }
    }

    // Expose functions globally for external access
    window.showMobileNotification = showMobileNotification;
    window.showMobileLoadingState = showMobileLoadingState;
    window.hideMobileLoadingState = hideMobileLoadingState;
    window.updateMobilePresetsDisplay = updateMobilePresetsDisplay;
    
    /**
     * Reset all presets to their default models
     * 
     * This function now uses the server's canonical defaults by calling
     * the same resetToDefault function used by the desktop interface
     * without specifying a preset_id, which resets all presets.
     */
    async function resetAllPresetsToDefault() {
        console.log('Mobile: Resetting all presets to canonical server defaults');
        
        // Show loading state in the UI
        const resetBtn = document.getElementById('mobile-reset-all-to-default');
        if (resetBtn) {
            resetBtn.textContent = 'Resetting...';
            resetBtn.disabled = true;
        }
        
        try {
            // Import the reset function from apiService
            const { resetPreferencesAPI } = await import('./apiService.js');
            
            const response = await resetPreferencesAPI();
            
            if (response && response.success) {
                console.log('Mobile: All presets reset successfully');
                
                // Clear local preferences
                window.userPreferences = {};
                
                // Update mobile UI
                updateMobilePresetsDisplay();
                showMobileNotification('All presets reset to defaults');
                
                // Trigger refresh of desktop UI too
                if (typeof window.updatePresetButtonLabels === 'function') {
                    window.updatePresetButtonLabels();
                }
            } else {
                throw new Error(response?.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Mobile: Reset failed:', error);
            showMobileNotification('Failed to reset presets', 'error');
        } finally {
            // Restore button state
            if (resetBtn) {
                resetBtn.textContent = 'Reset All to Default';
                resetBtn.disabled = false;
            }
        }
    }
});