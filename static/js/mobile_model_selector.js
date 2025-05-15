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
            // Deep clone to prevent reference issues
            window.userPreferences = JSON.parse(JSON.stringify(event.detail.preferences));
            
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
            // Deep clone to prevent reference issues
            window.availableModels = JSON.parse(JSON.stringify(event.detail.models));
            
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
            
            // Show a confirmation notification
            if (window.availableModels) {
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
            
            // Update the model selection
            selectModelForPreset(currentPresetId, defaultModel);
            
            // Additional notification since we're closing the panel
            const friendlyModelName = window.availableModels?.find(m => m.id === defaultModel)?.name || defaultModel;
            showModelNotification(currentPresetId, `Default (${friendlyModelName})`);
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
     * 
     * This function now uses the server's canonical defaults by calling
     * the same resetToDefault function used by the desktop interface
     * without specifying a preset_id, which resets all presets.
     */
    function resetAllPresetsToDefault() {
        console.log('Mobile: Resetting all presets to canonical server defaults');
        
        // Check if the main reset function exists
        if (window.resetToDefault && typeof window.resetToDefault === 'function') {
            // Show loading state in the UI
            const resetBtn = document.getElementById('mobile-reset-all-presets');
            if (resetBtn) {
                resetBtn.textContent = 'Resetting...';
                resetBtn.disabled = true;
            }
            
            try {
                // Call the main script's reset function without a preset ID
                // This makes a POST to /reset_preferences with an empty body,
                // which signals the server to reset all preferences
                window.resetToDefault();
                
                // The desktop function already handles:
                // - Server communication
                // - Re-fetching preferences
                // - Showing confirmation messages
                // - Updating the UI
                
                // Hide the mobile panel after reset is complete
                setTimeout(() => {
                    hideMobileModelPanel();
                    
                    // Reset the button state
                    if (resetBtn) {
                        resetBtn.textContent = 'Reset All Models to Defaults';
                        resetBtn.disabled = false;
                    }
                }, 500);
            } catch (error) {
                console.error('Mobile: Error while resetting all presets:', error);
                alert('Error resetting model preferences. Please try again.');
                
                // Reset the button state
                if (resetBtn) {
                    resetBtn.textContent = 'Reset All Models to Defaults';
                    resetBtn.disabled = false;
                }
            }
        } else {
            // Fallback if the main reset function isn't available
            console.error('Mobile: window.resetToDefault function not available');
            alert('Cannot reset models at this time. Please try again later.');
        }
    }
});