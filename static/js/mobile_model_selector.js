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
    
    // Helper function to populate model list from data
    function populateModelListFromData(models, presetId) {
        if (!models || !Array.isArray(models)) {
            console.warn('Mobile: Invalid models data provided');
            return;
        }
        
        console.log(`Mobile: Populating model list with ${models.length} models for preset ${presetId}`);
        
        // Make models available globally
        window.availableModels = models;
        
        // Hide loading indicator
        const loadingElement = document.getElementById('mobile-models-loading');
        if (loadingElement) {
            loadingElement.classList.add('hidden');
        }
        
        // Clear the current list
        if (mobileModelList) {
            mobileModelList.innerHTML = '';
        }
        
        // Use existing logic to populate the list
        if (window.populateModelList && typeof window.populateModelList === 'function') {
            // Call the original function which will use window.availableModels
            try {
                window.populateModelList(presetId, models);
            } catch (error) {
                console.warn('Mobile: Error calling populateModelList:', error);
                // Fallback to manual population if needed
                populateModelListManually(models, presetId);
            }
        } else {
            populateModelListManually(models, presetId);
        }
    }
    
    // Manual model list population as fallback
    function populateModelListManually(models, presetId) {
        if (!mobileModelList) return;
        
        // Filter models based on preset if needed
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
    
    // Main function - cache-first approach for mobile model list population
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
        
        // Fallback to original behavior if no cache available
        console.log('Mobile: No cache available, using original loading method');
        showLoadingAndFetchModels(presetId);
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
        mobilePanelToggle.addEventListener('click', showMobileModelPanel);
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
        
        // Use existing model selection logic
        if (window.selectPresetButton && typeof window.selectPresetButton === 'function') {
            window.selectPresetButton(presetId, modelId);
        }
        
        // Hide panels
        hideMobileModelSelection();
        hideMobileModelPanel();
    }
    
    console.log('Mobile: Cache-first mobile model selector initialized');
});