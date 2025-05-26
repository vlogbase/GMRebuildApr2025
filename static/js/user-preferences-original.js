// User Preferences - Extracted from original working script.js

// Function to fetch user preferences for model presets
// Expose this globally for the mobile UI
window.fetchUserPreferences = function() {
    return fetch('/get_preferences')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Check if user is authenticated (look for the logout button which only shows for logged in users)
            const isAuthenticated = !!document.getElementById('logout-btn');
            const defaultModels = window.defaultModels || {};
            let userPreferences = {};

            if (data.preferences) {
                // Validate preferences to ensure presets 1-5 don't have free models
                const validatedPreferences = {};
                
                for (const presetId in data.preferences) {
                    const modelId = data.preferences[presetId];
                    const isFreeModel = modelId.includes(':free');
                    
                    // If it's preset 1-5 and has a free model, use the default non-free model
                    if (presetId !== '6' && isFreeModel) {
                        console.warn(`Preset ${presetId} has a free model (${modelId}), reverting to default`);
                        validatedPreferences[presetId] = defaultModels[presetId];
                        
                        // Note: Preset 4 is our vision model (openai/gpt-4o) for multimodal capabilities
                        if (presetId === '4') {
                            console.log(`Ensuring preset 4 uses vision-capable model: ${defaultModels['4']}`);
                        }
                    } else {
                        validatedPreferences[presetId] = modelId;
                    }
                }
                
                userPreferences = validatedPreferences;
                console.log('Loaded user preferences:', userPreferences);
                
                // Make sure the global window.userPreferences is set before dispatching event
                window.userPreferences = userPreferences;
                
                // Update button text to reflect preferences
                updatePresetButtonLabels();
                
                // Select default preset - use preset 6 (free) for non-authenticated users
                selectPresetButton(isAuthenticated ? '1' : '6');
                
                // Dispatch an event to notify other scripts that preferences are loaded
                // This helps mobile scripts synchronize their initialization
                console.log('Script.js: User preferences successfully loaded, dispatching event');
                // Dispatch to both window (legacy) and document (standard approach)
                const userPrefsEvent = new CustomEvent('userPreferencesLoaded', {
                    detail: { 
                        preferences: userPreferences,
                        success: true 
                    }
                });
                
                // Dispatch on window for backward compatibility
                window.dispatchEvent(userPrefsEvent);
                
                // Dispatch on document (recommended approach)
                document.dispatchEvent(userPrefsEvent);
            } else {
                // Handle case where data.preferences is empty
                console.warn('Script.js: data.preferences is empty, using defaults');
                
                // Use defaults
                userPreferences = {};
                for (const presetId in defaultModels) {
                    userPreferences[presetId] = defaultModels[presetId];
                }
                window.userPreferences = userPreferences;
                
                // Update UI
                updatePresetButtonLabels();
                selectPresetButton(isAuthenticated ? '1' : '6');
                
                // Dispatch with defaults
                // Create event for both window and document
                const userPrefsEvent = new CustomEvent('userPreferencesLoaded', {
                    detail: { 
                        preferences: userPreferences,
                        success: false,
                        defaultsUsed: true
                    }
                });
                
                // Dispatch to both targets
                window.dispatchEvent(userPrefsEvent);
                document.dispatchEvent(userPrefsEvent);
            }
            
            // After loading preferences, fetch available models
            // Return this promise to maintain the chain
            return fetchAvailableModels().then(models => {
                // Return a combined result
                return {
                    preferences: userPreferences,
                    models: models,
                    preferencesSuccess: !!data.preferences
                };
            });
        })
        .catch(error => {
            console.error('Error fetching preferences:', error);
            
            // Check if user is authenticated
            const isAuthenticated = !!document.getElementById('logout-btn');
            const defaultModels = window.defaultModels || {};
            
            // Use defaults for user preferences
            let userPreferences = {};
            for (const presetId in defaultModels) {
                userPreferences[presetId] = defaultModels[presetId];
            }
            window.userPreferences = userPreferences;
            
            // Dispatch event to notify that preferences are ready (with defaults)
            console.log('Script.js: User preferences set to defaults due to error, dispatching event');
            // Create event for user preferences error case
            const userPrefsErrorEvent = new CustomEvent('userPreferencesLoaded', {
                detail: { 
                    preferences: userPreferences, 
                    error: true,
                    defaultsUsed: true
                }
            });
            
            // Dispatch to both targets
            window.dispatchEvent(userPrefsErrorEvent);
            document.dispatchEvent(userPrefsErrorEvent);
            
            // Select the appropriate preset - free for non-authenticated users
            selectPresetButton(isAuthenticated ? '1' : '6');
            
            // Important: Return the fetchAvailableModels promise to maintain the chain
            return fetchAvailableModels().then(models => {
                // After models are loaded, return a combined result
                return {
                    preferences: userPreferences,
                    models: models,
                    preferencesError: true
                };
            });
        });
}

// Function to update the model preset button labels
function updatePresetButtonLabels() {
    const userPreferences = window.userPreferences || {};
    
    for (const presetId in userPreferences) {
        const modelId = userPreferences[presetId];
        const button = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
        
        if (button && window.allModels) {
            const model = window.allModels.find(m => m.id === modelId);
            if (model) {
                const nameElement = button.querySelector('.model-name');
                if (nameElement) {
                    // Update button text with model name
                    nameElement.textContent = model.name || modelId;
                    
                    // Update data-model-id attribute
                    button.setAttribute('data-model-id', modelId);
                }
            }
        }
    }
}

// Make functions globally available
window.updatePresetButtonLabels = updatePresetButtonLabels;