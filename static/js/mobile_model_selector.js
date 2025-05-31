/**
 * Mobile Model Selector for GloriaMundo Chat (Cache-First Version)
 * 
 * This file handles the mobile-specific UI for model selection with cache-first loading:
 * - Numbered buttons (1-6)
 * - Bottom sheet panel with preset details
 * - Model selection interface with localStorage caching
 */

document.addEventListener('DOMContentLoaded', function() {
    // Only run on mobile devices
    if (window.innerWidth > 576) return;
    
    console.log('Mobile: Initializing mobile model selector with cache-first approach');
    
    // Core Elements
    const mobileModelButtons = document.getElementById('mobile-model-buttons');
    const mobilePresetBtns = document.querySelectorAll('.mobile-preset-btn');
    const mobilePanelToggle = document.getElementById('mobile-model-panel-toggle');
    
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
    const mobileBackdrop = document.getElementById('mobile-panel-backdrop');
    
    // Init variables
    let currentPresetId = null;
    
    // Function to update mobile panel with current model assignments
    function updateMobilePanelLabels() {
        console.log('Mobile: Updating panel labels with current model assignments');
        
        // Get current model assignments from desktop preset buttons
        for (let i = 1; i <= 6; i++) {
            const desktopButton = document.querySelector(`.model-preset-btn[data-preset-id="${i}"]`);
            const mobileLabel = document.getElementById(`mobile-selected-model-${i}`);
            
            if (desktopButton && mobileLabel) {
                const currentModelSpan = desktopButton.querySelector('.current-model');
                if (currentModelSpan) {
                    const currentModel = currentModelSpan.textContent.trim();
                    mobileLabel.textContent = currentModel;
                    console.log(`Mobile: Updated preset ${i} label to: ${currentModel}`);
                } else {
                    // Fallback to default labels
                    const defaultLabels = {
                        '1': 'General Model',
                        '2': 'Alternative Model', 
                        '3': 'Reasoning Model',
                        '4': 'Vision Model',
                        '5': 'Search Model',
                        '6': 'Free Model'
                    };
                    mobileLabel.textContent = defaultLabels[i] || 'Model';
                }
            }
        }
    }
    
    // Helper function to check if cache is near expiry
    function isNearExpiry() {
        const timestampKey = 'gloriamundo_model_cache_timestamp';
        const maxAge = 15 * 60 * 1000; // 15 minutes
        const nearExpiryThreshold = 2 * 60 * 1000; // 2 minutes
        
        const cachedTimestamp = localStorage.getItem(timestampKey);
        if (!cachedTimestamp) return true;
        
        const cacheAge = Date.now() - parseInt(cachedTimestamp);
        return cacheAge > (maxAge - nearExpiryThreshold);
    }
    
    // Filter models based on preset criteria
    function filterModelsByPreset(models, presetId) {
        if (!models || !Array.isArray(models)) return models;
        
        const preset = parseInt(presetId);
        let filteredModels = [...models];
        
        switch (preset) {
            case 3: // Reasoning models
                filteredModels = models.filter(model => model.is_reasoning);
                break;
            case 4: // Multimodal models
                filteredModels = models.filter(model => model.is_multimodal || model.supports_vision);
                break;
            case 5: // Search models (Perplexity)
                filteredModels = models.filter(model => model.id && model.id.includes('perplexity'));
                break;
            case 6: // Free models
                filteredModels = models.filter(model => model.cost_band === 'Free' || (model.input_price === 0 && model.output_price === 0));
                break;
            default: // All models for presets 1 and 2
                filteredModels = models;
        }
        
        console.log(`Mobile: Filtered ${models.length} models to ${filteredModels.length} for preset ${presetId}`);
        return filteredModels;
    }

    // Helper function to populate model list from data
    function populateModelListFromData(models, presetId) {
        if (!models || !Array.isArray(models)) {
            console.warn('Mobile: Invalid models data provided');
            return;
        }
        
        console.log(`Mobile: Populating model list with ${models.length} models for preset ${presetId}`);
        
        // Filter models based on preset
        const filteredModels = filterModelsByPreset(models, presetId);
        
        // Make models available globally
        window.availableModels = filteredModels;
        
        // Hide loading indicator
        const loadingElement = document.getElementById('mobile-models-loading');
        if (loadingElement) {
            loadingElement.classList.add('hidden');
        }
        
        // Clear the current list
        if (mobileModelList) {
            mobileModelList.innerHTML = '';
        }
        
        // Always use manual population for mobile to ensure consistency
        populateModelListManually(filteredModels, presetId);
    }
    
    // Manual model list population with improved styling
    function populateModelListManually(models, presetId) {
        if (!mobileModelList) return;
        
        // Filter models based on preset if needed
        let filteredModels = models;
        
        if (filteredModels.length === 0) {
            mobileModelList.innerHTML = '<li class="mobile-model-item no-models">No models available for this preset</li>';
            return;
        }
        
        // Create model items with desktop-style formatting
        mobileModelList.innerHTML = filteredModels.map(model => {
            const isSelected = isModelSelected(model.id, presetId);
            const costBandClass = model.cost_band ? model.cost_band.replace(/\$/g, 'dollar') : 'unknown';
            const contextLength = model.context_length ? `${(model.context_length / 1000).toFixed(0)}k` : '';
            
            // Create description preview (first 100 chars)
            const description = model.description ? 
                (model.description.length > 100 ? 
                    model.description.substring(0, 100) + '...' : 
                    model.description) : '';
            
            return `
                <li class="mobile-model-item ${isSelected ? 'selected' : ''}" data-model-id="${model.id}">
                    <div class="model-header">
                        <div class="model-name">${model.model_name}</div>
                        <div class="model-badges">
                            <span class="cost-band cost-${costBandClass}">${model.cost_band || '?'}</span>
                            ${contextLength ? `<span class="context-length">${contextLength}</span>` : ''}
                            ${model.is_free ? '<span class="free-badge">FREE</span>' : ''}
                            ${model.supports_vision ? '<span class="vision-badge">👁</span>' : ''}
                            ${model.supports_pdf ? '<span class="pdf-badge">📄</span>' : ''}
                        </div>
                    </div>
                    ${description ? `<div class="model-description">${description}</div>` : ''}
                    <div class="model-pricing">
                        ${model.input_price ? `Input: $${(model.input_price * 1000).toFixed(3)}/1k` : ''}
                        ${model.output_price ? ` • Output: $${(model.output_price * 1000).toFixed(3)}/1k` : ''}
                    </div>
                    ${isSelected ? '<i class="fa-solid fa-check selected-icon"></i>' : ''}
                </li>
            `;
        }).join('');
        
        // Add click handlers for model selection
        const modelItems = mobileModelList.querySelectorAll('.mobile-model-item');
        modelItems.forEach(item => {
            item.addEventListener('click', function() {
                const modelId = this.getAttribute('data-model-id');
                selectMobileModel(modelId, presetId);
            });
        });
        
        console.log(`Mobile: Populated ${filteredModels.length} models for preset ${presetId}`);
    }
    
    // Continue with original forEach implementation for compatibility
    function populateModelListManuallyLegacy(models, presetId) {
        if (!mobileModelList) return;
        let filteredModels = models;
        
        // Create model items
        filteredModels.forEach(model => {
            const modelItem = document.createElement('li');
            modelItem.className = 'mobile-model-item';
            modelItem.dataset.modelId = model.id;
            
            modelItem.innerHTML = `
                <div class="model-info">
                    <span class="model-name">${model.name || model.id}</span>
                    <span class="model-pricing">${model.pricing || ''}</span>
                </div>
            `;
            
            modelItem.addEventListener('click', () => {
                selectModelForPreset(presetId, model.id);
            });
            
            mobileModelList.appendChild(modelItem);
        });
    }
    
    // Helper function to fetch fresh models in background
    function fetchFreshModelsInBackground(presetId) {
        console.log('Mobile: Fetching fresh models in background');
        
        // Call the original API-based loading without showing loading indicator
        if (window.populateModelList && typeof window.populateModelList === 'function') {
            try {
                window.populateModelList(presetId, null, true); // true flag for background fetch
            } catch (error) {
                console.warn('Mobile: Error fetching fresh models in background:', error);
            }
        }
    }
    
    // Helper function for original loading behavior
    function showLoadingAndFetchModels(presetId) {
        // Get reference to the loading element
        const loadingElement = document.getElementById('mobile-models-loading');
        
        // Show the loading indicator
        if (loadingElement) {
            loadingElement.classList.remove('hidden');
        }
        
        // Call original loading function
        if (window.populateModelList && typeof window.populateModelList === 'function') {
            window.populateModelList(presetId);
        }
    }
    
    // Direct database fallback function
    function fetchModelsFromDatabase(presetId) {
        console.log('Mobile: Fetching models directly from database');
        
        const loadingElement = document.getElementById('mobile-models-loading');
        if (loadingElement) {
            loadingElement.classList.remove('hidden');
        }
        
        // Direct API call to get models
        fetch('/api/get_model_prices')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Mobile: Received models from database API:', data);
                
                if (data && data.prices) {
                    // Convert prices object to array format
                    const models = Object.keys(data.prices).map(modelId => {
                        const modelData = data.prices[modelId];
                        return {
                            id: modelId,
                            name: modelData.model_name || modelId,
                            pricing: `$${(modelData.input_price || 0).toFixed(6)}/M tokens`,
                            cost_band: modelData.cost_band || '',
                            is_multimodal: modelData.is_multimodal || false,
                            supports_pdf: modelData.supports_pdf || false,
                            is_reasoning: modelData.is_reasoning || false
                        };
                    });
                    
                    console.log(`Mobile: Converted ${models.length} models for mobile display`);
                    populateModelListFromData(models, presetId);
                } else {
                    console.error('Mobile: No model data received from API');
                    showErrorMessage('No models available');
                }
            })
            .catch(error => {
                console.error('Mobile: Error fetching models from database:', error);
                showErrorMessage('Failed to load models');
            })
            .finally(() => {
                if (loadingElement) {
                    loadingElement.classList.add('hidden');
                }
            });
    }
    
    // Show error message in model list
    function showErrorMessage(message) {
        if (mobileModelList) {
            mobileModelList.innerHTML = `
                <li class="mobile-model-error">
                    <div class="error-message">
                        <i class="fa-solid fa-exclamation-triangle"></i>
                        <span>${message}</span>
                    </div>
                </li>
            `;
        }
    }

    // Main function - cache-first approach with robust database fallback
    function populateMobileModelList(presetId) {
        console.log(`Mobile: Loading models for preset ${presetId} with cache-first approach`);
        
        // Try cache first for instant loading
        if (window.ModelCache) {
            const cachedModels = window.ModelCache.getCachedModels();
            if (cachedModels && cachedModels.length > 0) {
                console.log('Mobile: Using cached models for instant loading');
                populateModelListFromData(cachedModels, presetId);
                
                // Still fetch fresh data in background if cache is getting old
                if (!window.ModelCache.hasCachedModels() || isNearExpiry()) {
                    fetchFreshModelsInBackground(presetId);
                }
                return;
            }
        }
        
        // Try original desktop function if available
        if (window.populateModelList && typeof window.populateModelList === 'function') {
            console.log('Mobile: Trying original desktop loading method');
            try {
                showLoadingAndFetchModels(presetId);
                
                // Set a timeout to fallback to database if desktop method doesn't work
                setTimeout(() => {
                    const loadingElement = document.getElementById('mobile-models-loading');
                    if (loadingElement && !loadingElement.classList.contains('hidden')) {
                        console.log('Mobile: Desktop method taking too long, falling back to database');
                        fetchModelsFromDatabase(presetId);
                    }
                }, 3000); // 3 second timeout
                
                return;
            } catch (error) {
                console.warn('Mobile: Desktop loading method failed:', error);
            }
        }
        
        // Final fallback - always fetch directly from database
        console.log('Mobile: Using database fallback method');
        fetchModelsFromDatabase(presetId);
    }
    
    // Rest of the mobile selector functions would go here...
    // For now, let's add the essential event handlers
    
    // Panel preset buttons
    if (mobilePanelPresetBtns) {
        mobilePanelPresetBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const presetId = this.getAttribute('data-preset-id');
                currentPresetId = presetId;
                showMobileModelSelection();
                populateMobileModelList(presetId);
            });
        });
    }
    
    // Show mobile model selection
    function showMobileModelSelection() {
        if (mobileModelSelection) {
            mobileModelSelection.classList.add('visible');
        }
        if (mobileModelPanel) {
            mobileModelPanel.classList.remove('visible');
        }
        if (mobileBackdrop) {
            mobileBackdrop.classList.add('visible');
        }
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
    
    // Show mobile model panel
    function showMobileModelPanel() {
        if (mobileModelPanel) {
            mobileModelPanel.classList.add('visible');
        }
        if (mobileBackdrop) {
            mobileBackdrop.classList.add('visible');
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
    
    // Event handlers
    if (mobilePanelToggle) {
        mobilePanelToggle.addEventListener('click', function() {
            updateMobilePanelLabels(); // Update labels before showing panel
            showMobileModelPanel();
        });
    }
    
    if (mobilePanelClose) {
        mobilePanelClose.addEventListener('click', hideMobileModelPanel);
    }
    
    if (mobileSelectionBack) {
        mobileSelectionBack.addEventListener('click', function() {
            hideMobileModelSelection();
            showMobileModelPanel();
        });
    }
    
    if (mobileSelectionClose) {
        mobileSelectionClose.addEventListener('click', function() {
            hideMobileModelSelection();
            hideMobileModelPanel();
        });
    }
    
    if (mobileBackdrop) {
        mobileBackdrop.addEventListener('click', function() {
            hideMobileModelSelection();
            hideMobileModelPanel();
        });
    }
    
    // Model selection function
    function selectModelForPreset(presetId, modelId) {
        console.log(`Mobile: Selected model ${modelId} for preset ${presetId}`);
        
        // Update the preset button with selected model
        updatePresetButtonWithModel(presetId, modelId);
        
        // Use existing model selection logic if available
        if (window.selectPresetButton && typeof window.selectPresetButton === 'function') {
            try {
                window.selectPresetButton(presetId, modelId);
            } catch (error) {
                console.warn('Mobile: Error calling selectPresetButton:', error);
                // Fallback to direct model selection
                directModelSelection(presetId, modelId);
            }
        } else {
            // Direct model selection fallback
            directModelSelection(presetId, modelId);
        }
        
        // Hide panels
        hideMobileModelSelection();
        hideMobileModelPanel();
        
        // Show notification
        showModelSelectionNotification(presetId, modelId);
    }
    
    // Direct model selection when desktop functions aren't available
    function directModelSelection(presetId, modelId) {
        console.log(`Mobile: Direct model selection for preset ${presetId}, model ${modelId}`);
        
        // Store the selection in localStorage for persistence
        const selections = JSON.parse(localStorage.getItem('model_selections') || '{}');
        selections[presetId] = modelId;
        localStorage.setItem('model_selections', JSON.stringify(selections));
        
        // Update global variables if they exist
        if (window.selectedModels) {
            window.selectedModels[presetId] = modelId;
        }
        
        // Trigger any existing update functions
        if (window.updateModelDisplay && typeof window.updateModelDisplay === 'function') {
            window.updateModelDisplay(presetId, modelId);
        }
    }
    
    // Update preset button to show selected model
    function updatePresetButtonWithModel(presetId, modelId) {
        const selectedModelSpan = document.getElementById(`mobile-selected-model-${presetId}`);
        if (selectedModelSpan) {
            // Find the model name from available models
            const model = window.availableModels?.find(m => m.id === modelId);
            const modelName = model ? (model.name || modelId) : modelId;
            
            // Truncate long model names for mobile display
            const displayName = modelName.length > 20 ? modelName.substring(0, 17) + '...' : modelName;
            selectedModelSpan.textContent = displayName;
        }
    }
    
    // Show selection notification
    function showModelSelectionNotification(presetId, modelId) {
        const notification = document.getElementById('mobile-model-notification');
        const notificationText = document.getElementById('notification-text');
        
        if (notification && notificationText) {
            const model = window.availableModels?.find(m => m.id === modelId);
            const modelName = model ? (model.name || modelId) : modelId;
            
            notificationText.textContent = `Selected ${modelName} for preset ${presetId}`;
            notification.classList.add('show');
            
            // Hide notification after 3 seconds
            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        }
    }
    
    console.log('Mobile: Cache-first mobile model selector initialized');
});