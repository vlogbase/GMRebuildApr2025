// Preset Button Functionality
// This file contains the preset button system that was separated during the JavaScript split

// Global variables for preset system
let currentlyEditingPresetId = null;
let modelPresetButtons = [];
let modelSelector = null;

// Initialize preset system
function initializePresets() {
    modelPresetButtons = document.querySelectorAll('.model-preset-btn');
    modelSelector = document.getElementById('model-selector');
    
    if (modelPresetButtons.length > 0) {
        console.log('Initializing preset buttons:', modelPresetButtons.length);
        setupPresetEventListeners();
    }
    
    // Make functions globally available
    window.openModelSelector = openModelSelector;
    window.selectPresetButton = selectPresetButton;
    window.selectModelForPreset = selectModelForPreset;
}

// Set up event listeners for preset buttons
function setupPresetEventListeners() {
    modelPresetButtons.forEach(button => {
        const presetId = button.getAttribute('data-preset-id');
        
        // Desktop click handler
        button.addEventListener('click', function(e) {
            // Prevent default if clicking on selector icon
            if (e.target.closest('.selector-icon-container')) {
                e.preventDefault();
                openModelSelector(presetId, button);
            } else {
                // Regular click - select the preset
                selectPresetButton(presetId);
            }
        });
    });
}

// Select a preset button
window.selectPresetButton = function(presetId) {
    // Check if this is a premium preset (all except preset 6)
    if (presetId !== '6') {
        // Check premium access before allowing selection of premium model
        if (typeof checkPremiumAccess === 'function' && !checkPremiumAccess('premium_model')) {
            // If access check failed, select the free model instead
            console.log('Premium access denied, selecting free model instead');
            selectPresetButton('6');
            return;
        }
    }
    
    // Dispatch event for the mobile UI
    document.dispatchEvent(new CustomEvent('preset-button-selected', {
        detail: { presetId }
    }));
    
    // Remove active class from all buttons
    modelPresetButtons.forEach(btn => btn.classList.remove('active'));
    
    // Add active class to selected button
    const selectedButton = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
    
    // Update current model and preferences
    if (typeof updateCurrentModel === 'function') {
        updateCurrentModel(presetId);
    }
    
    console.log(`Selected preset button: ${presetId}`);
};

// Open model selector for a preset
window.openModelSelector = function(presetId, buttonElement) {
    // Set current editing preset
    currentlyEditingPresetId = presetId;
    
    // For mobile: add a class to body when selector is active
    if (window.innerWidth <= 576) {
        document.body.classList.add('model-selector-active');
    }
    
    // Position the selector relative to the button
    const button = buttonElement || document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
    if (button && modelSelector) {
        const rect = button.getBoundingClientRect();
        const selectorRect = modelSelector.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Calculate position with a gap
        const gap = 10; // Gap in pixels
        
        // Position the selector
        let left = rect.left;
        let top = rect.bottom + gap;
        
        // Adjust for viewport boundaries
        if (left + 300 > viewportWidth) {
            left = viewportWidth - 320;
        }
        if (left < 10) {
            left = 10;
        }
        
        if (top + 200 > viewportHeight) {
            top = rect.top - 210;
        }
        
        modelSelector.style.left = `${left}px`;
        modelSelector.style.top = `${top}px`;
        modelSelector.style.display = 'block';
        
        // Populate the selector with available models for this preset
        if (typeof populateModelSelector === 'function') {
            populateModelSelector(presetId);
        }
    }
    
    console.log(`Opened model selector for preset: ${presetId}`);
};

// Select a model for a specific preset
window.selectModelForPreset = function(presetId, modelId, skipActivation = false) {
    console.log(`Selecting model ${modelId} for preset ${presetId}`);
    
    // Update user preferences
    if (window.userPreferences) {
        window.userPreferences[presetId] = modelId;
    }
    
    // Update the preset button display
    updatePresetButtonModel(presetId, modelId);
    
    // Save preferences to server
    if (window.models && window.models.saveUserPreferences) {
        window.models.saveUserPreferences();
    }
    
    // Activate the preset unless specifically skipped
    if (!skipActivation) {
        selectPresetButton(presetId);
    }
    
    // Close the model selector
    if (modelSelector) {
        modelSelector.style.display = 'none';
        document.body.classList.remove('model-selector-active');
    }
};

// Update preset button to show selected model
function updatePresetButtonModel(presetId, modelId) {
    const button = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
    if (button && window.availableModels) {
        const model = window.availableModels.find(m => m.id === modelId);
        if (model) {
            const modelNameSpan = button.querySelector('.model-name');
            if (modelNameSpan) {
                modelNameSpan.textContent = model.name || model.id;
            }
        }
    }
}

// Close model selector when clicking outside
document.addEventListener('click', function(e) {
    if (modelSelector && !modelSelector.contains(e.target) && !e.target.closest('.model-preset-btn')) {
        modelSelector.style.display = 'none';
        document.body.classList.remove('model-selector-active');
    }
});

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializePresets();
});

// Export functions for use by other modules
window.presets = {
    initializePresets,
    selectPresetButton,
    openModelSelector,
    selectModelForPreset
};