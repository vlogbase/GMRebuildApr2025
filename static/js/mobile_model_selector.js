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
    
    // Debug panel elements
    console.log('Mobile: Found model panel:', mobileModelPanel ? 'yes' : 'no');
    console.log('Mobile: Found panel close:', mobilePanelClose ? 'yes' : 'no');
    console.log('Mobile: Found panel preset buttons:', mobilePanelPresetBtns.length);
    
    // Selection Elements
    const mobileModelSelection = document.getElementById('mobile-model-selection');
    const mobileSelectionBack = document.getElementById('mobile-selection-back');
    const mobileSelectionClose = document.getElementById('mobile-selection-close');
    const mobileModelSearch = document.getElementById('mobile-model-search');
    const mobileModelList = document.getElementById('mobile-model-list');
    const mobileResetToDefault = document.getElementById('mobile-reset-to-default');
    
    // Backdrop
    const mobileBackdrop = document.getElementById('mobile-panel-backdrop');
    
    // Current state
    let currentPresetId = null;
    
    // Initialize the state - set the active button based on the current model
    function initializeMobileModelUI() {
        // Get the currently active preset ID from the desktop UI
        const activeDesktopBtn = document.querySelector('.model-preset-btn.active');
        if (activeDesktopBtn) {
            const presetId = activeDesktopBtn.getAttribute('data-preset-id');
            updateMobileActiveButton(presetId);
            
            // Update the selected model names in the panel
            updateSelectedModelNames();
        }
    }
    
    // Update mobile active button
    function updateMobileActiveButton(presetId) {
        // Clear active state from all buttons
        mobilePresetBtns.forEach(btn => btn.classList.remove('active'));
        
        // Set the active button
        const activeBtn = document.querySelector(`.mobile-preset-btn[data-preset-id="${presetId}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
    }
    
    // Update the selected model names in the panel with cost band indicators
    function updateSelectedModelNames() {
        // Force a fresh look at the global userPreferences object
        console.log('Mobile: Refreshing model names from preferences', window.userPreferences);
        
        // For each preset, get the selected model from userPreferences or defaultModels
        for (let i = 1; i <= 6; i++) {
            const presetId = i.toString();
            // Make sure we're getting the most up-to-date values 
            const modelId = window.userPreferences?.[presetId] || window.defaultModels?.[presetId];
            
            console.log(`Mobile: For preset ${presetId}, using model: ${modelId}`);
            
            if (modelId) {
                // Get the model name
                let modelName = modelId;
                
                // Try to get a more friendly name from the list of models
                if (window.formatModelName && typeof window.formatModelName === 'function') {
                    const formattedName = window.formatModelName(modelId);
                    console.log(`Mobile: Formatting model ${modelId} -> "${formattedName}"`);
                    modelName = formattedName;
                } else {
                    console.warn(`Mobile: formatModelName function not available for ${modelId}`);
                }
                
                // Update the display
                const modelNameElement = document.getElementById(`mobile-selected-model-${presetId}`);
                if (modelNameElement) {
                    console.log(`Mobile: Updating display for preset ${presetId} to ${modelName}`);
                    // Clear any existing content
                    modelNameElement.innerHTML = '';
                    
                    // Create and add the model name span
                    const nameSpan = document.createElement('span');
                    nameSpan.textContent = modelName;
                    nameSpan.className = 'selected-model-name-text';
                    modelNameElement.appendChild(nameSpan);
                    
                    // Find the model in the global list to get its properties
                    // Use the correct global array: window.availableModels
                    const model = window.availableModels?.find(m => m.id === modelId);
                    
                    // Log for debugging
                    if (!model) {
                        console.warn(`Mobile: Model ${modelId} not found in availableModels (${window.availableModels?.length || 0} models available)`);
                    }
                    
                    if (model) {
                        // Add cost band indicator if available
                        if (model.cost_band) {
                            const costBandSpan = document.createElement('span');
                            costBandSpan.textContent = model.cost_band;
                            costBandSpan.className = 'preset-cost-band';
                            
                            // Add appropriate color class based on band value
                            if (model.cost_band === '$$$$') {
                                costBandSpan.classList.add('cost-band-4-danger');
                            } else if (model.cost_band === '$$$') {
                                costBandSpan.classList.add('cost-band-3-warn');
                            } else if (model.cost_band === '$$') {
                                costBandSpan.classList.add('cost-band-2');
                            } else if (model.cost_band === '$') {
                                costBandSpan.classList.add('cost-band-1');
                            }
                            
                            modelNameElement.appendChild(costBandSpan);
                        }
                        // Add free indicator if it's a free model
                        else if (model.is_free === true || modelId.includes(':free')) {
                            const freeSpan = document.createElement('span');
                            freeSpan.textContent = 'Free';
                            freeSpan.className = 'preset-free-indicator';
                            modelNameElement.appendChild(freeSpan);
                        }
                    }
                }
            }
        }
    }
    
    // Show mobile model panel
    function showMobileModelPanel() {
        mobileModelPanel.classList.add('visible');
        mobileBackdrop.classList.add('visible');
        
        // Refresh preferences from server first if main script has the function
        if (window.fetchUserPreferences && typeof window.fetchUserPreferences === 'function') {
            console.log('Mobile: Refreshing user preferences before showing panel');
            
            // This will update the global userPreferences object
            window.fetchUserPreferences().then(() => {
                console.log('Mobile: Successfully refreshed preferences from server:', window.userPreferences);
                
                // Then update the UI after preferences are fetched
                updateSelectedModelNames();
            }).catch(err => {
                console.error('Mobile: Error refreshing preferences:', err);
                // Still try to update with what we have
                updateSelectedModelNames();
            });
        } else {
            console.log('Mobile: fetchUserPreferences not available, using current values');
            // Fallback to just updating from current values
            updateSelectedModelNames();
        }
    }
    
    // Hide mobile model panel
    function hideMobileModelPanel() {
        mobileModelPanel.classList.remove('visible');
        mobileBackdrop.classList.remove('visible');
    }
    
    // Show mobile model selection for a specific preset
    function showMobileModelSelection(presetId) {
        console.log(`Mobile: Opening model selection for preset ${presetId}`);
        currentPresetId = presetId;
        
        // Hide the model panel
        mobileModelPanel.classList.remove('visible');
        
        // Show the selection panel and backdrop
        mobileModelSelection.classList.add('visible');
        mobileBackdrop.classList.add('visible');
        
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
        mobileModelSelection.classList.remove('visible');
        mobileBackdrop.classList.remove('visible');
    }
    
    // Back from selection to panel
    function backToModelPanel() {
        mobileModelSelection.classList.remove('visible');
        mobileModelPanel.classList.add('visible');
        currentPresetId = null;
    }
    
    // Populate the mobile model list for a specific preset
    function populateMobileModelList(presetId) {
        // Clear the current list
        if (mobileModelList) {
            mobileModelList.innerHTML = '';
        }
        
        // If the main script's populateModelList function exists, use it to get the models
        if (window.populateModelList && typeof window.populateModelList === 'function') {
            // We'll use our own list, but let the main script load the data first
            window.populateModelList(presetId);
            
            // Now create our own list items with mobile-specific styling
            const allModels = window.availableModels || [];
            
            // Log available models for debugging
            console.log(`Mobile: Found ${allModels.length} models from window.availableModels`);
            
            // Use the same property names as in the main script
            const filteredModels = presetId === '4' ? allModels.filter(model => model.is_multimodal) :
                                  presetId === '5' ? allModels.filter(model => model.id.includes('perplexity')) :
                                  presetId === '6' ? allModels.filter(model => model.is_free === true || model.id.includes(':free')) :
                                  allModels.filter(model => !model.is_free); // Filter out free models for presets 1-3
                                  
            console.log(`Mobile: Filtered to ${filteredModels.length} models for preset ${presetId} (excluding free models for presets 1-3)`);
            
            // Get current selected model for this preset
            const currentModel = window.userPreferences?.[presetId] || window.defaultModels?.[presetId];
            
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
                
                li.appendChild(modelInfo);
                
                // Model cost with proper cost band styling
                const modelCost = document.createElement('div');
                modelCost.className = 'model-cost';
                
                // Free model case
                if (model.is_free === true || model.id.includes(':free')) {
                    modelCost.textContent = 'Free';
                    modelCost.classList.add('free-model');
                } 
                // Model with cost band
                else if (model.cost_band) {
                    // Create styled cost band span (similar to desktop UI)
                    const costBandSpan = document.createElement('span');
                    costBandSpan.textContent = model.cost_band;
                    costBandSpan.className = 'cost-band-indicator';
                    
                    // Add appropriate color class based on band value
                    if (model.cost_band === '$$$$') {
                        costBandSpan.classList.add('cost-band-4-danger');
                    } else if (model.cost_band === '$$$') {
                        costBandSpan.classList.add('cost-band-3-warn');
                    } else if (model.cost_band === '$$') {
                        costBandSpan.classList.add('cost-band-2');
                    } else if (model.cost_band === '$') {
                        costBandSpan.classList.add('cost-band-1');
                    } else {
                        costBandSpan.classList.add('cost-band-free');
                    }
                    
                    modelCost.appendChild(costBandSpan);
                }
                // Fallback for models with pricing but no cost band
                else if (model.pricing && model.pricing.prompt) {
                    const promptPrice = model.pricing.prompt;
                    modelCost.textContent = `$${promptPrice.toFixed(4)}/1K in`;
                }
                
                li.appendChild(modelCost);
                
                // Add click handler
                li.addEventListener('click', function() {
                    selectModelForPreset(presetId, model.id);
                });
                
                mobileModelList.appendChild(li);
            });
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
            
            if (modelText.includes(searchTerm) || modelId.includes(searchTerm)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }
    
    // Select a model for a preset
    function selectModelForPreset(presetId, modelId) {
        // If the main script's selectModelForPreset function exists, use it
        if (window.selectModelForPreset && typeof window.selectModelForPreset === 'function') {
            // Call with true for skipActivation since we'll handle that ourselves
            window.selectModelForPreset(presetId, modelId, true);
            
            // After selecting the model, activate the preset button to use this model
            if (window.selectPresetButton && typeof window.selectPresetButton === 'function') {
                // This is the key fix - actually activate the preset after selecting a model
                window.selectPresetButton(presetId);
                
                // Log for debugging
                console.log(`Mobile: Activated preset ${presetId} with model: ${modelId}`);
            }
            
            // Close the mobile selection
            hideMobileModelSelection();
            hideMobileModelPanel();
            
            // Update the mobile button state
            updateMobileActiveButton(presetId);
            
            // Update the mobile panel selected model names
            updateSelectedModelNames();
        }
    }
    
    // Handle numbered button click (1-6)
    function handlePresetButtonClick(presetId) {
        // If the main script's selectPresetButton function exists, use it
        if (window.selectPresetButton && typeof window.selectPresetButton === 'function') {
            window.selectPresetButton(presetId);
            
            // Update the mobile button state
            updateMobileActiveButton(presetId);
        }
    }
    
    // Reset to default model for current preset
    function resetToDefault(presetId) {
        // If the main script's resetToDefault function exists, use it
        if (window.resetToDefault && typeof window.resetToDefault === 'function') {
            window.resetToDefault(presetId);
            
            // Update the list to show the new active model
            populateMobileModelList(presetId);
            
            // Update the mobile panel selected model names
            updateSelectedModelNames();
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
    
    // Panel close button
    if (mobilePanelClose) {
        mobilePanelClose.addEventListener('click', function() {
            hideMobileModelPanel();
        });
    }
    
    // Panel preset buttons
    mobilePanelPresetBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const presetId = this.getAttribute('data-preset-id');
            showMobileModelSelection(presetId);
        });
    });
    
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
    
    // Model search input
    if (mobileModelSearch) {
        mobileModelSearch.addEventListener('input', function() {
            filterMobileModelList(this.value.toLowerCase());
        });
    }
    
    // Reset to default button
    if (mobileResetToDefault) {
        mobileResetToDefault.addEventListener('click', function() {
            if (currentPresetId) {
                resetToDefault(currentPresetId);
            }
        });
    }
    
    // Backdrop click
    if (mobileBackdrop) {
        mobileBackdrop.addEventListener('click', function() {
            hideMobileModelPanel();
            hideMobileModelSelection();
        });
    }
    
    // Initialize the UI when window loads
    window.addEventListener('load', function() {
        initializeMobileModelUI();
    });
    
    // Listen for changes to the active preset button from the main script
    document.addEventListener('preset-button-selected', function(e) {
        if (e.detail && e.detail.presetId) {
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
});

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
            
            // Display confirmation
            alert('All presets have been reset to default models');
            
            // Hide the panel
            hideMobileModelPanel();
        }
    } else {
        console.error('Mobile: Default models not available for reset');
    }
}