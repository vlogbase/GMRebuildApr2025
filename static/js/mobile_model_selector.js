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
    
    // Show loading state on all preset buttons initially
    function showLoadingState() {
        console.log('Mobile: Setting initial loading state for buttons');
        // Set loading state on mobile preset buttons
        mobilePresetBtns.forEach(btn => {
            btn.classList.add('loading');
        });
        
        // Set loading state on panel preset buttons
        mobilePanelPresetBtns.forEach(btn => {
            btn.classList.add('loading');
            const modelNameSpan = btn.querySelector('.selected-model-name');
            if (modelNameSpan) {
                modelNameSpan.textContent = 'Loading...';
            }
        });
    }
    
    // Remove loading state when data is ready
    function removeLoadingState() {
        console.log('Mobile: Removing loading state from buttons');
        
        // Remove loading state from mobile preset buttons
        mobilePresetBtns.forEach(btn => {
            btn.classList.remove('loading');
        });
        
        // Remove loading state from panel preset buttons
        mobilePanelPresetBtns.forEach(btn => {
            btn.classList.remove('loading');
        });
    }
    
    // Set initial loading state
    showLoadingState();
    
    // Track if this is the first initialization (to avoid showing notification on first load)
    let isFirstInit = true;
    
    // Function to initialize mobile UI - this is directly called multiple times
    function initializeMobileUI() {
        console.log('Mobile: Running initialization');
        
        // Check if we have access to user preferences
        if (!window.userPreferences) {
            console.log('Mobile: userPreferences not available, trying to load from main script');
            
            // Try to call the main script's fetch function directly to force preferences to load
            if (window.fetchUserPreferences && typeof window.fetchUserPreferences === 'function') {
                console.log('Mobile: Directly calling window.fetchUserPreferences()');
                window.fetchUserPreferences()
                    .then(() => {
                        console.log('Mobile: Preferences loaded from direct call, updating UI');
                        updateSelectedModelNames();
                        setActivePreset();
                        removeLoadingState();
                    })
                    .catch(error => {
                        console.error('Mobile: Error loading preferences:', error);
                        removeLoadingState();
                    });
            } else {
                console.log('Mobile: fetchUserPreferences not available, will retry initialization');
                // If we can't fetch, retry after a delay
                setTimeout(initializeMobileUI, 500);
            }
            return;
        }
        
        // If we have preferences, update UI immediately
        console.log('Mobile: userPreferences available, updating UI directly');
        updateSelectedModelNames();
        setActivePreset();
        removeLoadingState();
        
        // Reset first init flag after successful initialization
        isFirstInit = false;
    }
    
    // Set the active preset based on available data
    function setActivePreset() {
        if (window.activePresetId) {
            console.log(`Mobile: Setting active button to ${window.activePresetId}`);
            updateMobileActiveButton(window.activePresetId);
        } else if (window.userPreferences && Object.keys(window.userPreferences).length > 0) {
            // If no active preset ID but we have preferences, use the first one
            const firstPresetId = Object.keys(window.userPreferences)[0];
            console.log(`Mobile: Setting active button to ${firstPresetId}`);
            updateMobileActiveButton(firstPresetId);
        } else {
            // Fallback to preset 1
            console.log('Mobile: Falling back to preset 1 as active button');
            updateMobileActiveButton('1');
        }
    }
    
    // Run initialization immediately and then again after a delay
    initializeMobileUI();
    
    // Also set up a backup initialization after a delay to catch any late-loading data
    setTimeout(initializeMobileUI, 800);
    
    // Handle preset button click
    function handlePresetButtonClick(presetId) {
        console.log(`Mobile: Preset button ${presetId} clicked`);
        showMobileModelSelection(presetId);
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
    
    // Select a model for a specific preset
    function selectModelForPreset(presetId, modelId) {
        console.log(`Mobile: Selected model ${modelId} for preset ${presetId}`);
        
        // If the main script's selectPresetButton function exists, use it
        if (window.selectPresetButton && typeof window.selectPresetButton === 'function') {
            // Call the main script's select function (with presetId 1-6)
            window.selectPresetButton(presetId, modelId);
            
            // Update the UI to reflect the change
            updateSelectedModelNames();
            
            // Update the active button in the numbered row
            updateMobileActiveButton(presetId);
            
            // Show a confirmation notification - but only if this isn't the first initialization
            if (!isFirstInit && window.availableModels) {
                const model = window.availableModels.find(m => m.id === modelId);
                if (model) {
                    showModelNotification(presetId, model.name || model.id);
                }
            }
        } else {
            console.error('Mobile: selectPresetButton function not available');
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
        
        // Set notification content
        notification.textContent = `Selected "${modelName}" for preset ${presetId}`;
        
        // Show notification
        notification.classList.add('visible');
        
        // Hide after a delay (3 seconds)
        setTimeout(() => {
            notification.classList.remove('visible');
        }, 3000);
    }
    
    // Update selected model names in the panel - adapted from desktop implementation
    function updateSelectedModelNames() {
        console.log('Mobile: Updating selected model names in panel');
        
        // Handle case where preferences aren't loaded yet
        if (!window.userPreferences) {
            console.log('Mobile: Cannot update model names - userPreferences not loaded');
            return;
        }
        
        // Log the current state to help with debugging
        console.log('Mobile: Current userPreferences:', JSON.stringify(window.userPreferences));
        console.log('Mobile: defaultModelDisplayNames available:', window.defaultModelDisplayNames ? 'yes' : 'no');
        
        for (const presetId in window.userPreferences) {
            const modelId = window.userPreferences[presetId];
            console.log(`Mobile: Processing preset ${presetId} with model ${modelId}`);
            
            // Update mobile panel model name (in the sliding panel)
            const displayElement = document.getElementById(`mobile-selected-model-${presetId}`);
            if (displayElement) {
                // Get the formatted model name using the same function as desktop
                let displayName = 'Not set';
                
                if (modelId) {
                    // Use the same formatting logic as desktop
                    if (window.formatModelName && typeof window.formatModelName === 'function') {
                        // Special handling for preset 6 (Free)
                        if (presetId === '6') {
                            displayName = window.formatModelName(modelId, true);
                        } else {
                            displayName = window.formatModelName(modelId);
                        }
                    } else {
                        // Fallback if formatModelName is not available
                        displayName = modelId.split('/').pop().replace(/-/g, ' ');
                    }
                }
                
                console.log(`Mobile: Setting display name for preset ${presetId} to "${displayName}"`);
                displayElement.textContent = displayName;
                
                // Also update the parent button's data-model-id attribute
                const parentButton = displayElement.closest('.mobile-panel-preset-btn');
                if (parentButton && modelId) {
                    parentButton.setAttribute('data-model-id', modelId);
                }
            } else {
                console.error(`Mobile: Display element not found for preset ${presetId}`);
            }
        }
        
        console.log('Mobile: Model names updated');
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
        // First filter out free models for all presets except 6
        const nonFreeModels = presetId === '6' ? allModels : allModels.filter(model => !model.is_free && !model.id.includes(':free'));
        
        // Then apply specific filters based on preset
        const filteredModels = presetId === '4' ? nonFreeModels.filter(model => model.is_multimodal) :
                              presetId === '5' ? nonFreeModels.filter(model => model.id.includes('perplexity')) :
                              presetId === '6' ? allModels.filter(model => model.is_free === true || model.id.includes(':free')) :
                              nonFreeModels; // For presets 1-5, we already filtered out free models above
                              
        console.log(`Mobile: Filtered to ${filteredModels.length} models for preset ${presetId} (excluding free models for presets 1-5)`);
        
        // Get current selected model for this preset
        const currentModel = window.userPreferences?.[presetId] || window.defaultModels?.[presetId];
        
        // Display empty state message if no models are available after filtering
        if (filteredModels.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'empty-models-message';
            emptyMessage.textContent = 'No models available for this category. Please try another preset.';
            
            if (mobileModelList) {
                mobileModelList.appendChild(emptyMessage);
            } else {
                console.error('Mobile: mobileModelList is null, cannot append empty state message');
            }
            return;
        }
        
        // Create list items
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
            } else if (model.input_cost_per_token > 0.000020 || model.output_cost_per_token > 0.000100) {
                costBandClass = 'cost-band-4-danger';
                costBandIndicator.textContent = '$$$$';
            } else if (model.input_cost_per_token > 0.000010 || model.output_cost_per_token > 0.000050) {
                costBandClass = 'cost-band-3-warn';
                costBandIndicator.textContent = '$$$';
            } else if (model.input_cost_per_token > 0.000005 || model.output_cost_per_token > 0.000020) {
                costBandClass = 'cost-band-2';
                costBandIndicator.textContent = '$$';
            } else {
                costBandClass = 'cost-band-1';
                costBandIndicator.textContent = '$';
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
            
            // Add the list item to the model list if it exists
            if (mobileModelList) {
                mobileModelList.appendChild(li);
            } else {
                console.error('Mobile: mobileModelList is null, cannot append model item');
            }
        });
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
    function resetCurrentPresetToDefault() {
        if (!currentPresetId || !window.defaultModels) return;
        
        const defaultModel = window.defaultModels[currentPresetId];
        if (defaultModel) {
            console.log(`Mobile: Resetting preset ${currentPresetId} to default model ${defaultModel}`);
            
            // Mark as not first init since this is a user-triggered action
            isFirstInit = false;
            
            // Update the model selection - this already handles the notification
            selectModelForPreset(currentPresetId, defaultModel);
            
            // No need for additional notification as selectModelForPreset will handle it
        }
    }
    
    // Set up event listeners
    
    // Mobile preset buttons (1-6)
    mobilePresetBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const presetId = this.getAttribute('data-preset-id');
            handlePresetButtonClick(presetId);
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
    document.addEventListener('model-selected', function(e) {
        updateSelectedModelNames();
    });
    
    // Reset All to Default button in model panel
    const mobileResetAllToDefault = document.getElementById('mobile-reset-all-to-default');
    if (mobileResetAllToDefault) {
        mobileResetAllToDefault.addEventListener('click', function() {
            resetAllPresetsToDefault();
        });
    }
    
    /**
     * Reset all presets to their default models
     */
    function resetAllPresetsToDefault() {
        if (window.defaultModels) {
            console.log('Mobile: Resetting all presets to default models');
            
            // Confirm with the user before resetting
            if (confirm('Reset all presets to their default models?')) {
                // Reset to default models
                for (let i = 1; i <= 6; i++) {
                    const presetId = i.toString();
                    const defaultModel = window.defaultModels[presetId];
                    
                    if (defaultModel) {
                        // Update user preferences
                        if (!window.userPreferences) {
                            window.userPreferences = {};
                        }
                        window.userPreferences[presetId] = defaultModel;
                        
                        // Update the displayed model name
                        const modelNameElement = document.getElementById(`mobile-selected-model-${presetId}`);
                        if (modelNameElement) {
                            modelNameElement.textContent = defaultModel.name || defaultModel.id;
                        }
                    }
                }
                
                // Save preferences to server
                if (window.saveUserPreferences && typeof window.saveUserPreferences === 'function') {
                    window.saveUserPreferences();
                }
                
                // Hide the panel
                hideMobileModelPanel();
            }
        } else {
            console.error('Mobile: Default models not available for reset');
        }
    }
});