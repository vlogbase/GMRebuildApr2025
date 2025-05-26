// Model Management and Premium Access Functions for GloriaMundo Chat

// The free model preset ID
const FREE_PRESET_ID = '6';

// Helper function to check premium access and fallback to free model if needed
function checkPremiumAccess(featureName) {
    // Check if user is authenticated (look for the logout button which only shows for logged in users)
    const isAuthenticated = !!document.getElementById('logout-btn');
    
    // Get user's credit balance if logged in
    let userCreditBalance = 0;
    if (isAuthenticated) {
        // Try to extract the credit amount from the account link in the sidebar
        const accountLink = document.querySelector('.account-link');
        if (accountLink) {
            const balanceText = accountLink.textContent.trim();
            const matches = balanceText.match(/Credits: \$([0-9.]+)/);
            if (matches && matches[1]) {
                userCreditBalance = parseFloat(matches[1]);
            }
        }
    }
    
    if (!isAuthenticated) {
        console.log(`Access denied: Not logged in, redirecting to login for ${featureName}`);
        window.location.href = '/login?redirect=chat&feature=' + featureName;
        return false;
    }
    
    if (userCreditBalance <= 0) {
        console.log(`Access denied: Insufficient credits, switching to free model in-place for ${featureName}`);
        if (featureName === 'premium_model') {
            // Use in-place fallback instead of redirecting
            console.warn("No credits – switching to free model in-place.");
            if (typeof selectPresetButton === 'function') {
                selectPresetButton(FREE_PRESET_ID);
            }
        }
        return false;
    }
    
    return true;
}

// Function to check if current model supports specific capabilities
function checkModelCapabilities(capabilityType) {
    // Get current model ID
    const activeModel = document.querySelector('.model-btn.active, .model-preset-btn.active');
    if (!activeModel) {
        console.warn('No active model found when checking capabilities');
        return false;
    }
    
    const modelId = activeModel.getAttribute('data-model-id');
    if (!modelId) {
        console.warn('Active model has no model ID attribute');
        return false;
    }
    
    console.log(`Checking ${capabilityType} capability for model: ${modelId}`);
    
    // Find the model in our allModels array
    if (typeof allModels === 'undefined') {
        console.warn('allModels array not found');
        return false;
    }
    
    const modelInfo = allModels.find(m => m.id === modelId);
    if (!modelInfo) {
        console.warn(`Model ${modelId} not found in allModels array`);
        return false;
    }
    
    // Check for the requested capability
    switch (capabilityType) {
        case 'image':
        case 'is_multimodal':
            return modelInfo.is_multimodal === true;
        case 'pdf':
        case 'supports_pdf':
            return modelInfo.supports_pdf === true;
        default:
            console.warn(`Unknown capability type: ${capabilityType}`);
            return false;
    }
}

// Function to update UI based on current model capabilities
function updateUIForModelCapabilities() {
    const supportsImages = checkModelCapabilities('image');
    const supportsPDFs = checkModelCapabilities('pdf');
    
    console.log(`Current model capabilities - Images: ${supportsImages}, PDFs: ${supportsPDFs}`);
    
    // Get UI elements
    const imageUploadButton = document.getElementById('image-upload-btn');
    const fileUploadInput = document.getElementById('file-upload');
    const uploadDocumentsBtn = document.getElementById('upload-documents-btn');
    
    // Update upload buttons visibility/state based on capabilities
    if (imageUploadButton) {
        if (supportsImages) {
            imageUploadButton.style.display = 'inline-flex';
            imageUploadButton.classList.remove('disabled');
            
            // Update button title based on supported file types
            if (supportsPDFs) {
                imageUploadButton.title = 'Upload an image or PDF';
                
                // Update file input accept attribute to include PDFs
                if (fileUploadInput) {
                    fileUploadInput.accept = "image/*,.pdf";
                }
            } else {
                imageUploadButton.title = 'Upload an image';
                
                // Update file input accept attribute to only accept images
                if (fileUploadInput) {
                    fileUploadInput.accept = "image/*";
                }
            }
        } else {
            imageUploadButton.style.display = 'none';
        }
    }
    
    // Update file upload interface for PDFs if we have a document upload button
    if (uploadDocumentsBtn) {
        if (supportsPDFs) {
            uploadDocumentsBtn.style.display = 'inline-flex';
            uploadDocumentsBtn.classList.remove('disabled');
            uploadDocumentsBtn.title = 'Upload documents to enhance responses';
        } else {
            uploadDocumentsBtn.style.display = 'none';
        }
    }
}

// Make functions globally available
window.checkPremiumAccess = checkPremiumAccess;
window.checkModelCapabilities = checkModelCapabilities;
window.updateUIForModelCapabilities = updateUIForModelCapabilities;
window.FREE_PRESET_ID = FREE_PRESET_ID;