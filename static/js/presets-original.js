// Preset Button Functions - Extracted from original working script.js

// Function to select a preset button and update the current model
// Expose this function globally for mobile.js
window.selectPresetButton = function(presetId) {
    // Check if this is a premium preset (all except preset 6)
    if (presetId !== '6') {
        // Check premium access before allowing selection of premium model
        if (!checkPremiumAccess('premium_model')) {
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
    
    // Get model preset buttons
    const modelPresetButtons = document.querySelectorAll('.model-preset-btn');
    
    // Remove active class from all buttons
    modelPresetButtons.forEach(btn => btn.classList.remove('active'));
    
    // Add active class to selected button
    const activeButton = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
    if (activeButton) {
        // Add loading state
        activeButton.classList.add('loading');
        
        // Add active class
        activeButton.classList.add('active');
        window.activePresetButton = activeButton;
        window.currentPresetId = presetId;
        
        // Get the model ID for this preset
        const userPreferences = window.userPreferences || {};
        const defaultModels = window.defaultModels || {};
        window.currentModel = userPreferences[presetId] || defaultModels[presetId];
        console.log(`Selected preset ${presetId} with model: ${window.currentModel}`);
        
        // Update multimodal controls based on the selected model
        updateMultimodalControls(window.currentModel);
        
        // Update the cost indicator for the selected model
        updateSelectedModelCostIndicator(window.currentModel);
        
        // Save preference - passing the button element to handle loading state
        saveModelPreference(presetId, window.currentModel, activeButton);
    }
}

// Function to update the selected model's cost indicator in the UI
// Expose this function globally for mobile UI
window.updateSelectedModelCostIndicator = function(modelId) {
    if (!modelId) return;
    
    // Find the model in allModels to get its cost band
    const model = window.allModels?.find(m => m.id === modelId);
    if (!model || !model.cost_band) return;
    
    // Find the active model button
    const activeButton = document.querySelector('.model-preset-btn.active');
    if (!activeButton) return;
    
    // Check if this is the free preset
    const isFreeBand = activeButton.getAttribute('data-preset-id') === '6';
    if (isFreeBand) return; // Don't show cost band on free preset
    
    // Update cost indicator in the active button
    const nameSpan = activeButton.querySelector('.model-name');
    if (!nameSpan) return;
    
    // Remove any existing cost band indicators
    const existingCostBand = nameSpan.querySelector('.cost-band-indicator');
    if (existingCostBand) {
        existingCostBand.remove();
    }
    
    // Create the cost indicator
    const costSpan = document.createElement('span');
    costSpan.textContent = model.cost_band;
    costSpan.className = 'cost-band-indicator';
    
    // Add the specific band class based on the band value
    if (model.cost_band === '$$$$') {
        costSpan.classList.add('cost-band-4-danger');
    } else if (model.cost_band === '$$$') {
        costSpan.classList.add('cost-band-3-warn');
    } else if (model.cost_band === '$$') {
        costSpan.classList.add('cost-band-2');
    } else if (model.cost_band === '$') {
        costSpan.classList.add('cost-band-1');
    } else {
        costSpan.classList.add('cost-band-free');
    }
    
    nameSpan.appendChild(costSpan);
}

// Function to update multimodal controls (image upload, camera) based on model capability
// Expose this function globally for mobile UI
window.updateMultimodalControls = function(modelId) {
    // Store the current model ID globally for capability checks
    window.currentModel = modelId;
    
    // Find the model in allModels
    const model = window.allModels ? window.allModels.find(m => m.id === modelId) : null;
    if (!model) {
        console.warn(`Model ${modelId} not found in allModels array`);
        return;
    }
    
    // Get model capabilities
    const isMultimodalModel = model.is_multimodal === true;
    const supportsPDF = model.supports_pdf === true;
    
    console.log(`🖼️ Model capabilities for ${modelId}: 
        - Multimodal/images: ${isMultimodalModel ? 'Yes' : 'No'}
        - PDF documents: ${supportsPDF ? 'Yes' : 'No'}`);
    
    // Get UI elements
    const imageUploadButton = document.getElementById('image-upload-button');
    const cameraButton = document.getElementById('camera-button');
    const uploadDocumentsBtn = document.getElementById('upload-documents-btn');
    
    // Show/hide image upload and camera buttons based on multimodal capability
    if (imageUploadButton) {
        imageUploadButton.style.display = isMultimodalModel ? 'inline-flex' : 'none';
    }
    
    // Only show camera button if browser supports it and model supports images
    const hasCamera = !!navigator.mediaDevices?.getUserMedia;
    if (cameraButton) {
        cameraButton.style.display = isMultimodalModel && hasCamera ? 'inline-flex' : 'none';
    }
    
    // Show/hide document upload button based on PDF capability
    if (uploadDocumentsBtn) {
        uploadDocumentsBtn.style.display = supportsPDF ? 'inline-flex' : 'none';
    }
    
    // If switching to a non-multimodal model, clear any attached image
    if (!isMultimodalModel && window.clearAttachedImage) {
        window.clearAttachedImage();
    }
    
    // If switching to a model that doesn't support PDFs, clear any attached PDF
    if (!supportsPDF && window.clearAttachedPdf) {
        window.clearAttachedPdf();
    }
    
    return isMultimodalModel; // Return for testing purposes
}

// Function to save model preference
function saveModelPreference(presetId, modelId, buttonElement) {
    if (!presetId || !modelId) return;
    
    fetch('/save_preference', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            preset_id: presetId,
            model_id: modelId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`Preference saved: Preset ${presetId} -> ${modelId}`);
        } else {
            console.error('Failed to save preference:', data.error);
        }
    })
    .catch(error => {
        console.error('Error saving preference:', error);
    })
    .finally(() => {
        // Remove loading state from button
        if (buttonElement) {
            buttonElement.classList.remove('loading');
        }
    });
}