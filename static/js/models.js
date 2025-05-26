// Model Data Loading and Management
// This file handles loading model data and connecting it to the preset system

// Global variables for model system
let allModels = [];
let userPreferences = {};
let modelList = null;
let modelSearch = null;

// Initialize model system
function initializeModels() {
    // Find DOM elements
    modelList = document.getElementById('model-list');
    modelSearch = document.getElementById('model-search');
    
    // Expose globally for other scripts
    window.availableModels = allModels;
    window.userPreferences = userPreferences;
    window.populateModelList = populateModelList;
    window.populateModelSelector = populateModelSelector;
    
    // Load models from server
    loadModelsFromServer();
    
    console.log('Model system initialized');
}

// Load models from server
async function loadModelsFromServer() {
    try {
        const response = await fetch('/api/models');
        if (response.ok) {
            const data = await response.json();
            allModels = data.models || [];
            window.availableModels = allModels;
            
            console.log(`Loaded ${allModels.length} models from server`);
            
            // Dispatch event to notify other scripts
            const modelsEvent = new CustomEvent('modelsLoaded', {
                detail: { 
                    models: allModels,
                    count: allModels.length,
                    success: true
                }
            });
            
            window.dispatchEvent(modelsEvent);
            document.dispatchEvent(modelsEvent);
            
            // Update preset button labels with current selections
            updatePresetButtonLabels();
            
        } else {
            console.error('Failed to load models:', response.status);
        }
    } catch (error) {
        console.error('Error loading models:', error);
    }
}

// Filter configurations for each preset
const presetFilters = {
    '1': (model) => !model.is_free, // All non-free models
    '2': (model) => !model.is_free, // All non-free models  
    '3': (model) => model.is_reasoning === true && !model.is_free, // Reasoning models
    '4': (model) => model.is_multimodal === true && !model.is_free, // Multimodal models
    '5': (model) => model.id.includes('perplexity') && !model.is_free, // Perplexity models
    '6': (model) => model.is_free === true || model.id.includes(':free') // Free models
};

// Default models for each preset
const defaultPresetModels = {
    '1': 'google/gemini-2.5-pro-preview-03-25',
    '2': 'meta/llama-4-maverick', 
    '3': 'openai/o4-Mini-High',
    '4': 'openai/gpt-4o',
    '5': 'perplexity/sonar-pro',
    '6': 'google/gemini-2.0-flash-exp:free'
};

// Populate model list for a specific preset
window.populateModelList = function(presetId) {
    console.log(`Populating model list for preset: ${presetId}`);
    
    if (!modelList) {
        modelList = document.getElementById('model-list');
        if (!modelList) {
            console.error('Model list element not found');
            return;
        }
    }
    
    // Clear existing items
    modelList.innerHTML = '';
    
    // Get filter function for this preset
    const filterFn = presetFilters[presetId];
    if (!filterFn) {
        console.error('No filter found for preset:', presetId);
        return;
    }
    
    // Filter models for this preset
    const filteredModels = allModels.filter(filterFn);
    console.log(`Found ${filteredModels.length} models for preset ${presetId}`);
    
    if (filteredModels.length === 0) {
        modelList.innerHTML = '<li class="no-models">No models available for this preset</li>';
        return;
    }
    
    // Create list items for each model
    filteredModels.forEach(model => {
        const listItem = document.createElement('li');
        listItem.className = 'model-item';
        listItem.setAttribute('data-model-id', model.id);
        
        listItem.innerHTML = `
            <span class="model-name">${model.name || model.id}</span>
            <span class="model-cost">${model.cost_band || ''}</span>
        `;
        
        // Add click handler to select this model
        listItem.addEventListener('click', function() {
            selectModelForPreset(presetId, model.id);
        });
        
        modelList.appendChild(listItem);
    });
};

// Populate model selector (alias for consistency)
window.populateModelSelector = function(presetId) {
    populateModelList(presetId);
};

// Update preset button labels with selected models
function updatePresetButtonLabels() {
    Object.keys(defaultPresetModels).forEach(presetId => {
        const selectedModelId = userPreferences[presetId] || defaultPresetModels[presetId];
        const model = allModels.find(m => m.id === selectedModelId);
        
        if (model) {
            updatePresetButtonModel(presetId, model.id, model.name);
        }
    });
}

// Update a specific preset button's model display
function updatePresetButtonModel(presetId, modelId, modelName) {
    const button = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
    if (button) {
        const modelNameSpan = button.querySelector('.model-name');
        if (modelNameSpan) {
            const model = allModels.find(m => m.id === modelId);
            modelNameSpan.textContent = modelName || (model && model.name) || modelId;
        }
    }
}

// Load user preferences from server
async function loadUserPreferences() {
    try {
        const response = await fetch('/api/user-preferences');
        if (response.ok) {
            const data = await response.json();
            userPreferences = data.preferences || {};
            window.userPreferences = userPreferences;
            console.log('Loaded user preferences:', userPreferences);
        }
    } catch (error) {
        console.error('Error loading user preferences:', error);
    }
}

// Save user preferences to server
async function saveUserPreferences() {
    try {
        const response = await fetch('/api/user-preferences', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ preferences: userPreferences })
        });
        
        if (response.ok) {
            console.log('User preferences saved successfully');
        }
    } catch (error) {
        console.error('Error saving user preferences:', error);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeModels();
    loadUserPreferences();
});

// Export functions for use by other modules
window.models = {
    initializeModels,
    loadModelsFromServer,
    populateModelList,
    updatePresetButtonLabels,
    saveUserPreferences: saveUserPreferences
};