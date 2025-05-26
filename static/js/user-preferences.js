// User Preferences Management
// This file handles loading, saving, and managing user preferences

// Fetch user preferences from server
window.fetchUserPreferences = function() {
    return fetch('/get_preferences')
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                console.warn('Failed to fetch user preferences, using defaults');
                return { preferences: {} };
            }
        })
        .then(data => {
            const preferences = data.preferences || {};
            
            // Store globally
            window.userPreferences = preferences;
            
            console.log('Loaded user preferences:', preferences);
            
            // Update UI with loaded preferences
            updateUIWithPreferences(preferences);
            
            return preferences;
        })
        .catch(error => {
            console.error('Error fetching user preferences:', error);
            window.userPreferences = {};
            return {};
        });
};

// Save a specific model preference
window.saveModelPreference = function(presetId, modelId, buttonElement) {
    // Update local preferences
    if (!window.userPreferences) {
        window.userPreferences = {};
    }
    window.userPreferences[presetId] = modelId;
    
    // Save to server
    return fetch('/api/user-preferences', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            preferences: window.userPreferences
        })
    })
    .then(response => {
        if (response.ok) {
            console.log(`Saved preference: preset ${presetId} -> model ${modelId}`);
            
            // Update button display if provided
            if (buttonElement && window.availableModels) {
                const model = window.availableModels.find(m => m.id === modelId);
                if (model) {
                    const modelNameSpan = buttonElement.querySelector('.model-name');
                    if (modelNameSpan) {
                        modelNameSpan.textContent = model.name || model.id;
                    }
                }
            }
            
            return true;
        } else {
            console.error('Failed to save user preferences');
            return false;
        }
    })
    .catch(error => {
        console.error('Error saving user preferences:', error);
        return false;
    });
};

// Reset a preset to its default model
window.resetToDefault = function(presetId) {
    const defaultModels = {
        '1': 'google/gemini-2.5-pro-preview-03-25',
        '2': 'meta/llama-4-maverick',
        '3': 'openai/o4-Mini-High',
        '4': 'openai/gpt-4o',
        '5': 'perplexity/sonar-pro',
        '6': 'google/gemini-2.0-flash-exp:free'
    };
    
    const defaultModel = defaultModels[presetId];
    if (!defaultModel) {
        console.error(`No default model found for preset ${presetId}`);
        return;
    }
    
    // Update preferences
    if (!window.userPreferences) {
        window.userPreferences = {};
    }
    window.userPreferences[presetId] = defaultModel;
    
    // Update button display
    const button = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
    if (button && window.availableModels) {
        const model = window.availableModels.find(m => m.id === defaultModel);
        if (model) {
            const modelNameSpan = button.querySelector('.model-name');
            if (modelNameSpan) {
                modelNameSpan.textContent = model.name || model.id;
            }
        }
    }
    
    // Save to server
    saveModelPreference(presetId, defaultModel, button);
    
    console.log(`Reset preset ${presetId} to default model: ${defaultModel}`);
};

// Update UI elements with loaded preferences
function updateUIWithPreferences(preferences) {
    if (!preferences || !window.availableModels) return;
    
    // Update each preset button with user's selected model
    Object.keys(preferences).forEach(presetId => {
        const modelId = preferences[presetId];
        const button = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
        
        if (button) {
            const model = window.availableModels.find(m => m.id === modelId);
            if (model) {
                const modelNameSpan = button.querySelector('.model-name');
                if (modelNameSpan) {
                    modelNameSpan.textContent = model.name || model.id;
                }
            }
        }
    });
}

// Save all preferences to server
function saveAllPreferences() {
    if (!window.userPreferences) return Promise.resolve(false);
    
    return fetch('/api/user-preferences', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            preferences: window.userPreferences
        })
    })
    .then(response => {
        if (response.ok) {
            console.log('All preferences saved successfully');
            return true;
        } else {
            console.error('Failed to save preferences');
            return false;
        }
    })
    .catch(error => {
        console.error('Error saving preferences:', error);
        return false;
    });
}

// Initialize preferences system
function initializePreferences() {
    // Initialize empty preferences if not exists
    if (!window.userPreferences) {
        window.userPreferences = {};
    }
    
    // Load preferences from server if user is logged in
    if (window.userIsLoggedIn) {
        fetchUserPreferences();
    }
    
    console.log('User preferences system initialized');
}

// Listen for models loaded event to update UI
document.addEventListener('modelsLoaded', function(event) {
    if (window.userPreferences && Object.keys(window.userPreferences).length > 0) {
        updateUIWithPreferences(window.userPreferences);
    }
});

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializePreferences();
});

// Export for use by other modules
window.userPreferencesManager = {
    fetchUserPreferences,
    saveModelPreference,
    resetToDefault,
    saveAllPreferences
};