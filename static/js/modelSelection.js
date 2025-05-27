/**
 * Model Selection Module
 * Handles all model selection functionality including presets, filters, and user preferences
 */

import { debounce, getCSRFToken, forceRepaint } from './utils.js';
import { fetchUserPreferencesAPI, fetchAvailableModelsAPI, saveModelPreferenceAPI, resetModelPreferenceAPI } from './apiService.js';

// Model selection state variables
export let allModels = []; // All models from OpenRouter
export let userPreferences = {}; // User preferences for preset buttons
export let currentModel = null; // Model ID of the currently selected preset
export let currentPresetId = '1'; // Default to first preset
export let currentlyEditingPresetId = null;

// Expose globally for mobile scripts
window.availableModels = allModels;
window.userPreferences = userPreferences;

// Filter configurations for each preset
export const presetFilters = {
    '1': (model) => !model.is_free, // All non-free models
    '2': (model) => !model.is_free, // All non-free models
    '3': (model) => {
        // All image-capable models (non-free)
        return !model.is_free && model.supports_vision;
    },
    '4': (model) => {
        // All document-capable models (non-free) 
        return !model.is_free && model.supports_pdf;
    },
    '5': (model) => model.is_free, // Free models only
    '6': (model) => {
        // Free image-capable models
        return model.is_free && model.supports_vision;
    },
    '7': (model) => {
        // Free document-capable models
        return model.is_free && model.supports_pdf;
    },
    '8': (model) => {
        // Reasoning models
        return model.id.includes('reasoning') || model.id.includes('o1') || model.id.includes('o3');
    }
};

// Default models for each preset
export const defaultModels = {
    '1': 'anthropic/claude-3-5-sonnet-20241022',
    '2': 'openai/gpt-4o-2024-11-20',
    '3': 'anthropic/claude-3-5-sonnet-20241022', // Image-capable
    '4': 'anthropic/claude-3-5-sonnet-20241022', // Document-capable
    '5': 'meta-llama/llama-3.1-8b-instruct:free',
    '6': 'meta-llama/llama-3.2-11b-vision-instruct:free', // Free image-capable
    '7': 'meta-llama/llama-3.1-8b-instruct:free', // Free document-capable (fallback)
    '8': 'openai/o1-preview' // Reasoning
};

// Expose defaultModels globally for mobile scripts
window.defaultModels = defaultModels;

// Display names for default models
export const defaultModelDisplayNames = {
    'anthropic/claude-3-5-sonnet-20241022': 'Claude 3.5 Sonnet',
    'openai/gpt-4o-2024-11-20': 'GPT-4o',
    'meta-llama/llama-3.1-8b-instruct:free': 'Llama 3.1 8B',
    'meta-llama/llama-3.2-11b-vision-instruct:free': 'Llama 3.2 11B Vision',
    'openai/o1-preview': 'o1-preview'
};

// Free model fallbacks for different capabilities
export const freeModelFallbacks = [
    'meta-llama/llama-3.1-8b-instruct:free',
    'microsoft/wizardlm-2-8x22b:free',
    'google/gemma-2-9b-it:free',
    'qwen/qwen-2.5-7b-instruct:free',
    'mistralai/mistral-7b-instruct:free'
];

// Initialize model selection functionality
export function initializeModelSelectionLogic() {
    console.log('🎯 Initializing model selection logic...');
    
    // Set up event listeners for model preset buttons
    setupPresetButtonListeners();
    
    // Set up model selector event listeners
    setupModelSelectorListeners();
    
    // Fetch initial data
    fetchUserPreferences();
    fetchAvailableModels();
}

// Set up event listeners for preset buttons
function setupPresetButtonListeners() {
    const presetButtons = document.querySelectorAll('.preset-button');
    presetButtons.forEach(button => {
        button.addEventListener('click', () => {
            const presetId = button.dataset.preset;
            selectPresetButton(presetId);
        });
    });
}

// Set up event listeners for model selector
function setupModelSelectorListeners() {
    const modelSelector = document.getElementById('model-selector');
    const modelSearchInput = document.getElementById('model-search');
    const closeButton = document.querySelector('.close-model-selector');
    
    if (closeButton) {
        closeButton.addEventListener('click', closeModelSelector);
    }
    
    if (modelSelector) {
        // Close selector when clicking outside
        modelSelector.addEventListener('click', (e) => {
            if (e.target === modelSelector) {
                closeModelSelector();
            }
        });
    }
    
    if (modelSearchInput) {
        // Debounced search
        const debouncedFilter = debounce((searchTerm) => {
            filterModelList(searchTerm);
        }, 300);
        
        modelSearchInput.addEventListener('input', (e) => {
            debouncedFilter(e.target.value);
        });
    }
}

// Function to update preset button labels
export function updatePresetButtonLabels() {
    console.log('🏷️ Updating preset button labels...');
    
    Object.keys(defaultModels).forEach(presetId => {
        const button = document.querySelector(`[data-preset="${presetId}"]`);
        if (button) {
            let modelId = userPreferences[presetId] || defaultModels[presetId];
            let displayName = defaultModelDisplayNames[modelId] || formatModelName(modelId);
            
            // Find the model in our allModels array for better display name
            if (allModels.length > 0) {
                const modelInfo = allModels.find(m => m.id === modelId);
                if (modelInfo) {
                    displayName = modelInfo.name || formatModelName(modelId);
                } else {
                    console.warn(`Model ${modelId} not found in allModels array`);
                }
            }
            
            // Update button text
            const nameSpan = button.querySelector('.preset-name');
            if (nameSpan) {
                nameSpan.textContent = displayName;
            }
        }
    });
}

// Function to format model names for display
export function formatModelName(modelId) {
    if (!modelId) return 'Unknown Model';
    
    // Remove provider prefix and format nicely
    let name = modelId.split('/').pop() || modelId;
    
    // Replace hyphens and underscores with spaces
    name = name.replace(/[-_]/g, ' ');
    
    // Capitalize words
    name = name.split(' ').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    ).join(' ');
    
    return name;
}

// Function to fetch user preferences
export async function fetchUserPreferences() {
    try {
        console.log('👤 Fetching user preferences...');
        const data = await fetchUserPreferencesAPI();
        
        if (data.success) {
            userPreferences = data.preferences || {};
            window.userPreferences = userPreferences;
            console.log('✅ User preferences loaded:', userPreferences);
            updatePresetButtonLabels();
        } else {
            console.warn('⚠️ Failed to fetch user preferences:', data.error);
        }
    } catch (error) {
        console.error('❌ Error fetching user preferences:', error);
    }
}

// Function to fetch available models
export async function fetchAvailableModels() {
    try {
        console.log('🤖 Fetching available models...');
        const data = await fetchAvailableModelsAPI();
        
        if (data.success && data.models) {
            allModels = data.models;
            window.availableModels = allModels;
            console.log(`✅ Loaded ${allModels.length} models`);
            updatePresetButtonLabels();
        } else {
            console.error('❌ Failed to fetch models:', data.error);
        }
    } catch (error) {
        console.error('❌ Error fetching models:', error);
    }
}

// Function to close model selector
export function closeModelSelector() {
    const modelSelector = document.getElementById('model-selector');
    if (modelSelector) {
        modelSelector.style.display = 'none';
        document.body.classList.remove('modal-open');
    }
    currentlyEditingPresetId = null;
}

// Function to filter model list
export function filterModelList(searchTerm) {
    const modelItems = document.querySelectorAll('.model-item');
    const lowerSearchTerm = searchTerm.toLowerCase();
    
    modelItems.forEach(item => {
        const modelName = item.querySelector('.model-name')?.textContent.toLowerCase() || '';
        const modelId = item.dataset.modelId?.toLowerCase() || '';
        
        const matches = modelName.includes(lowerSearchTerm) || modelId.includes(lowerSearchTerm);
        item.style.display = matches ? 'flex' : 'none';
    });
}

// Function to select a preset button
export function selectPresetButton(presetId) {
    console.log(`🎯 Selecting preset ${presetId}`);
    
    // Update active preset
    currentPresetId = presetId;
    
    // Update UI
    const presetButtons = document.querySelectorAll('.preset-button');
    presetButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.preset === presetId) {
            btn.classList.add('active');
        }
    });
    
    // Get the model for this preset
    const modelId = userPreferences[presetId] || defaultModels[presetId];
    currentModel = modelId;
    
    console.log(`📱 Selected model: ${modelId} for preset ${presetId}`);
    
    // Update UI elements that depend on model selection
    updateSelectedModelCostIndicator(modelId);
    updateMultimodalControls(modelId);
}

// Function to update cost indicator for selected model
export function updateSelectedModelCostIndicator(modelId) {
    if (!modelId || !allModels.length) return;
    
    const modelInfo = allModels.find(m => m.id === modelId);
    if (!modelInfo) return;
    
    // Update cost indicator in the UI
    const costIndicator = document.querySelector('.cost-indicator');
    if (costIndicator) {
        const costBand = calculateCostBand(modelInfo);
        costIndicator.className = `cost-indicator cost-${costBand}`;
        costIndicator.textContent = modelInfo.is_free ? 'FREE' : `$${costBand}`;
    }
}

// Function to calculate cost band (moved from main script)
function calculateCostBand(modelData) {
    if (modelData.is_free) return 'free';
    
    const inputCost = parseFloat(modelData.pricing?.prompt) || 0;
    const outputCost = parseFloat(modelData.pricing?.completion) || 0;
    const avgCost = (inputCost + outputCost) / 2;
    
    if (avgCost <= 0.001) return 'low';
    if (avgCost <= 0.01) return 'medium';
    if (avgCost <= 0.05) return 'high';
    return 'premium';
}

// Function to update multimodal controls based on model
export function updateMultimodalControls(modelId) {
    if (!modelId || !allModels.length) return;
    
    const modelInfo = allModels.find(m => m.id === modelId);
    if (!modelInfo) return;
    
    // Update image upload button visibility
    const imageUploadButton = document.getElementById('image-upload-button');
    if (imageUploadButton) {
        if (modelInfo.supports_vision) {
            imageUploadButton.style.display = 'flex';
            imageUploadButton.disabled = false;
        } else {
            imageUploadButton.style.display = 'none';
        }
    }
    
    // Update PDF upload button visibility  
    const pdfUploadButton = document.getElementById('pdf-upload-button');
    if (pdfUploadButton) {
        if (modelInfo.supports_pdf) {
            pdfUploadButton.style.display = 'flex';
            pdfUploadButton.disabled = false;
        } else {
            pdfUploadButton.style.display = 'none';
        }
    }
}

// Function to save model preference
export async function saveModelPreference(presetId, modelId) {
    try {
        console.log(`💾 Saving preference: Preset ${presetId} -> ${modelId}`);
        
        const data = await saveModelPreferenceAPI(presetId, modelId);
        
        if (data.success) {
            userPreferences[presetId] = modelId;
            window.userPreferences = userPreferences;
            updatePresetButtonLabels();
            console.log('✅ Model preference saved successfully');
            return true;
        } else {
            console.error('❌ Failed to save model preference:', data.error);
            return false;
        }
    } catch (error) {
        console.error('❌ Error saving model preference:', error);
        return false;
    }
}

// Function to reset to default model
export async function resetToDefault(presetId) {
    try {
        console.log(`🔄 Resetting preset ${presetId} to default`);
        
        const data = await resetModelPreferenceAPI(presetId);
        
        if (data.success) {
            delete userPreferences[presetId];
            window.userPreferences = userPreferences;
            updatePresetButtonLabels();
            console.log('✅ Preset reset to default successfully');
            return true;
        } else {
            console.error('❌ Failed to reset preset:', data.error);
            return false;
        }
    } catch (error) {
        console.error('❌ Error resetting preset:', error);
        return false;
    }
}