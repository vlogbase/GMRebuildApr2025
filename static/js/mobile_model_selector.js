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
    
    // Update the selected model names in the panel
    function updateSelectedModelNames() {
        // For each preset, get the selected model from userPreferences or defaultModels
        for (let i = 1; i <= 6; i++) {
            const presetId = i.toString();
            const modelId = window.userPreferences?.[presetId] || window.defaultModels?.[presetId];
            
            if (modelId) {
                // Format the model name
                let modelName = modelId;
                
                // Try to get a more friendly name from the list of models
                if (window.formatModelName && typeof window.formatModelName === 'function') {
                    modelName = window.formatModelName(modelId);
                }
                
                // Update the display
                const modelNameElement = document.getElementById(`mobile-selected-model-${presetId}`);
                if (modelNameElement) {
                    modelNameElement.textContent = modelName;
                }
            }
        }
    }
    
    // Show mobile model panel
    function showMobileModelPanel() {
        mobileModelPanel.classList.add('visible');
        mobileBackdrop.classList.add('visible');
        
        // Update selected model names
        updateSelectedModelNames();
    }
    
    // Hide mobile model panel
    function hideMobileModelPanel() {
        mobileModelPanel.classList.remove('visible');
        mobileBackdrop.classList.remove('visible');
    }
    
    // Show mobile model selection for a specific preset
    function showMobileModelSelection(presetId) {
        currentPresetId = presetId;
        
        // Hide the model panel
        mobileModelPanel.classList.remove('visible');
        
        // Show the selection panel
        mobileModelSelection.classList.add('visible');
        
        // Populate the model list
        populateMobileModelList(presetId);
        
        // Clear search input
        if (mobileModelSearch) {
            mobileModelSearch.value = '';
        }
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
            const filteredModels = presetId === '4' ? allModels.filter(model => model.multimodal) :
                                  presetId === '5' ? allModels.filter(model => model.id.includes('perplexity')) :
                                  presetId === '6' ? allModels.filter(model => model.free) :
                                  allModels;
            
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
                
                // Model cost
                const modelCost = document.createElement('div');
                modelCost.className = 'model-cost';
                
                if (model.price_input) {
                    modelCost.textContent = `$${model.price_input.toFixed(4)}/1K in`;
                } else if (model.free) {
                    modelCost.textContent = 'Free';
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
            window.selectModelForPreset(presetId, modelId);
            
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
});