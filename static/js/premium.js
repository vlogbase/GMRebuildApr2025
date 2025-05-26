// Premium Access and Feature Control
// This file handles premium feature access, model capabilities, and UI restrictions

// Check if user has premium access for a specific feature
function checkPremiumAccess(featureName) {
    // Check if user is logged in
    if (!window.userIsLoggedIn) {
        console.log(`Premium access check failed: User not logged in for feature: ${featureName}`);
        return false;
    }
    
    // For now, assume logged-in users with credits have premium access
    // You can modify this logic based on your actual premium system
    const hasCredits = window.userCredits && window.userCredits > 0;
    const isPremiumUser = window.userHasPremium || hasCredits;
    
    // Check specific premium features
    switch (featureName) {
        case 'premium_model':
            // Allow premium models if user has credits or premium status
            return isPremiumUser;
            
        case 'file_upload':
            // File upload available for premium users
            return isPremiumUser;
            
        case 'advanced_features':
            // Advanced features require premium
            return isPremiumUser;
            
        default:
            console.warn(`Unknown premium feature: ${featureName}`);
            return isPremiumUser;
    }
}

// Check if a model has specific capabilities
function checkModelCapabilities(capabilityType) {
    const currentModel = getCurrentSelectedModel();
    if (!currentModel || !window.availableModels) {
        return false;
    }
    
    const model = window.availableModels.find(m => m.id === currentModel);
    if (!model) return false;
    
    switch (capabilityType) {
        case 'multimodal':
        case 'vision':
            return model.is_multimodal === true;
            
        case 'reasoning':
            return model.is_reasoning === true;
            
        case 'free':
            return model.is_free === true;
            
        default:
            return false;
    }
}

// Update UI based on model capabilities
function updateUIForModelCapabilities() {
    const currentModel = getCurrentSelectedModel();
    if (!currentModel) return;
    
    // Update multimodal controls
    updateMultimodalControls(currentModel);
    
    // Update cost indicator
    if (window.updateSelectedModelCostIndicator) {
        window.updateSelectedModelCostIndicator(currentModel);
    }
    
    // Update any capability-specific UI elements
    const isMultimodal = checkModelCapabilities('multimodal');
    const isReasoning = checkModelCapabilities('reasoning');
    
    // Show/hide upload button based on capabilities
    const uploadButton = document.getElementById('upload-file-btn');
    if (uploadButton) {
        uploadButton.style.display = isMultimodal ? 'block' : 'none';
    }
    
    console.log(`Updated UI for model capabilities: multimodal=${isMultimodal}, reasoning=${isReasoning}`);
}

// Update multimodal controls based on selected model
window.updateMultimodalControls = function(modelId) {
    if (!modelId || !window.availableModels) return;
    
    const model = window.availableModels.find(m => m.id === modelId);
    const isMultimodal = model ? model.is_multimodal === true : false;
    
    // Update file upload button visibility
    const uploadButton = document.getElementById('upload-file-btn');
    if (uploadButton) {
        uploadButton.style.display = isMultimodal ? 'flex' : 'none';
    }
    
    // Update camera button if it exists
    const cameraButton = document.getElementById('camera-btn');
    if (cameraButton) {
        cameraButton.style.display = isMultimodal ? 'flex' : 'none';
    }
    
    // Update any multimodal indicators
    const multimodalIndicator = document.querySelector('.multimodal-indicator');
    if (multimodalIndicator) {
        multimodalIndicator.style.display = isMultimodal ? 'block' : 'none';
    }
    
    console.log(`Updated multimodal controls for model ${modelId}: multimodal=${isMultimodal}`);
};

// Lock premium features for non-premium users
function lockPremiumFeatures() {
    if (checkPremiumAccess('premium_model')) {
        // User has premium, remove any existing locks
        unlockPremiumFeatures();
        return;
    }
    
    // Add disabled class to premium preset buttons (1-5, not 6)
    const premiumPresets = document.querySelectorAll('.model-preset-btn:not([data-preset-id="6"])');
    premiumPresets.forEach(button => {
        button.classList.add('premium-locked');
        
        // Only add overlay if it doesn't already exist
        if (!button.querySelector('.premium-overlay')) {
            const overlay = document.createElement('div');
            overlay.className = 'premium-overlay';
            overlay.innerHTML = '<i class="fas fa-lock"></i>';
            button.appendChild(overlay);
        }
    });
    
    // Show premium upgrade prompts where needed
    showPremiumPrompts();
}

// Unlock premium features for premium users
function unlockPremiumFeatures() {
    // Remove premium-locked class from all buttons
    const allPresets = document.querySelectorAll('.model-preset-btn');
    allPresets.forEach(button => {
        button.classList.remove('premium-locked');
        
        // Remove any existing premium overlays
        const overlay = button.querySelector('.premium-overlay');
        if (overlay) {
            overlay.remove();
        }
    });
    
    // Hide premium prompts
    hidePremiumPrompts();
}

// Show premium upgrade prompts
function showPremiumPrompts() {
    const premiumPrompts = document.querySelectorAll('.premium-prompt');
    premiumPrompts.forEach(prompt => {
        prompt.style.display = 'block';
    });
}

// Hide premium upgrade prompts
function hidePremiumPrompts() {
    const premiumPrompts = document.querySelectorAll('.premium-prompt');
    premiumPrompts.forEach(prompt => {
        prompt.style.display = 'none';
    });
}

// Get currently selected model
function getCurrentSelectedModel() {
    // Find the active preset button
    const activePreset = document.querySelector('.model-preset-btn.active');
    if (!activePreset) return null;
    
    const presetId = activePreset.getAttribute('data-preset-id');
    
    // Get the selected model for this preset
    if (window.userPreferences && window.userPreferences[presetId]) {
        return window.userPreferences[presetId];
    }
    
    // Fall back to default model for this preset
    const defaultModels = {
        '1': 'google/gemini-2.5-pro-preview-03-25',
        '2': 'meta/llama-4-maverick',
        '3': 'openai/o4-Mini-High',
        '4': 'openai/gpt-4o',
        '5': 'perplexity/sonar-pro',
        '6': 'google/gemini-2.0-flash-exp:free'
    };
    
    return defaultModels[presetId] || null;
}

// Update cost indicator for selected model
window.updateSelectedModelCostIndicator = function(modelId) {
    if (!modelId || !window.availableModels) return;
    
    const model = window.availableModels.find(m => m.id === modelId);
    const costIndicator = document.querySelector('.cost-indicator');
    
    if (costIndicator && model) {
        const costBand = model.cost_band || '';
        costIndicator.textContent = costBand;
        costIndicator.className = `cost-indicator ${costBand.toLowerCase().replace(/\s+/g, '-')}`;
    }
};

// Initialize premium system
function initializePremium() {
    // Don't lock features immediately - wait for user data to load
    console.log('Premium system initialized - waiting for user data');
    
    // Set up a delayed check after other systems have loaded
    setTimeout(() => {
        if (!checkPremiumAccess('premium_model')) {
            console.log('No premium access detected, but not locking features yet');
            // Don't lock features automatically - let user try to use them
        }
    }, 2000);
}

// Make functions globally available
window.checkPremiumAccess = checkPremiumAccess;
window.checkModelCapabilities = checkModelCapabilities;
window.updateUIForModelCapabilities = updateUIForModelCapabilities;
window.lockPremiumFeatures = lockPremiumFeatures;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializePremium();
});

// Export for use by other modules
window.premium = {
    checkPremiumAccess,
    checkModelCapabilities,
    updateUIForModelCapabilities,
    lockPremiumFeatures
};