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
    '1': (model) => {
        // All non-free models - check for :free suffix and cost_band
        const isFree = model.id.includes(':free') || model.cost_band === 'free';
        return !isFree;
    },
    '2': (model) => {
        // All non-free models
        const isFree = model.id.includes(':free') || model.cost_band === 'free';
        return !isFree;
    },
    '3': (model) => {
        // Reasoning models - check for o1, o3, reasoning keywords
        return model.id.includes('reasoning') || model.id.includes('o1') || model.id.includes('o3');
    },
    '4': (model) => {
        // Multimodal/image-capable models (non-free)
        const isFree = model.id.includes(':free') || model.cost_band === 'free';
        const isMultimodal = model.is_multimodal || model.supports_vision || 
                            model.id.includes('vision') || model.id.includes('gpt-4o');
        return !isFree && isMultimodal;
    },
    '5': (model) => {
        // Search/Perplexity models - placeholder filter for now
        return model.id.includes('perplexity') || model.id.includes('search');
    },
    '6': (model) => {
        // Free models only
        return model.id.includes(':free') || model.cost_band === 'free';
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
    console.log('🔧 Setting up preset button listeners...');
    
    // Use the correct selector for the actual HTML structure
    const presetButtons = document.querySelectorAll('.model-preset-btn');
    console.log(`Found ${presetButtons.length} preset buttons`);
    
    presetButtons.forEach(button => {
        const presetId = button.getAttribute('data-preset-id');
        console.log(`Setting up listener for preset ${presetId}`);
        
        button.addEventListener('click', (e) => {
            // Check if click was on the dropdown selector
            if (e.target.closest('.selector-icon-container')) {
                e.preventDefault();
                e.stopPropagation();
                openModelSelector(presetId, button);
            } else {
                // Regular button click - select the preset
                selectPresetButton(presetId);
            }
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
        // Use the correct selector for the actual HTML structure
        const button = document.querySelector(`[data-preset-id="${presetId}"]`);
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
            
            // Update button text using the correct class name
            const nameSpan = button.querySelector('.model-name');
            if (nameSpan) {
                nameSpan.textContent = displayName;
                console.log(`Updated preset ${presetId} label to: ${displayName}`);
            } else {
                console.warn(`Could not find .model-name span in preset button ${presetId}`);
            }
        } else {
            console.warn(`Could not find preset button with data-preset-id="${presetId}"`);
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
        
        console.log('🔍 Complete API response structure:', data);
        
        // Check if the API call was successful and returned prices (not models)
        if (data.success && data.prices) {
            console.log('✅ API returned prices data, processing models...');
            
            // Create model data array directly from pricing data (matching original logic)
            const modelDataArray = [];
            for (const modelId in data.prices) {
                const modelData = data.prices[modelId];
                
                // Format the model name if it doesn't exist in the pricing data
                const formatModelName = (id) => {
                    return id.split('/').pop().replace(/-/g, ' ').replace(/(^\w|\s\w)/g, m => m.toUpperCase());
                };
                
                modelDataArray.push({
                    id: modelId,
                    name: modelData.name || formatModelName(modelId),
                    cost_band: modelData.cost_band,
                    pricing: modelData.pricing,
                    is_multimodal: modelData.is_multimodal || false,
                    supports_pdf: modelData.supports_pdf || false,
                    context_length: modelData.context_length,
                    description: modelData.description
                });
            }
            
            allModels = modelDataArray;
            window.availableModels = allModels;
            console.log(`✅ Loaded ${allModels.length} models from prices data`);
            updatePresetButtonLabels();
        } else {
            const errorMsg = data.error || 'API response missing success=true or prices data';
            console.error('❌ Failed to fetch models - API response structure issue:', {
                hasSuccess: !!data.success,
                hasPrices: !!data.prices,
                hasModels: !!data.models,
                fullResponse: data,
                errorFromAPI: errorMsg
            });
        }
    } catch (error) {
        console.error('❌ Error fetching models in modelSelection.js:', {
            errorMessage: error.message || error.toString(),
            errorName: error.name,
            fullError: error
        });
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

// Function to open model selector for a preset
export function openModelSelector(presetId, buttonElement) {
    console.log(`🔧 Opening model selector for preset ${presetId}`);
    
    currentlyEditingPresetId = presetId;
    
    const modelSelector = document.getElementById('model-selector');
    if (!modelSelector) {
        console.error('Model selector element not found');
        return;
    }
    
    // Show the modal
    modelSelector.style.display = 'flex';
    document.body.classList.add('modal-open');
    
    // Clear and populate the model list
    populateModelList(presetId);
    
    // Clear search input
    const searchInput = document.getElementById('model-search');
    if (searchInput) {
        searchInput.value = '';
    }
}

// Function to populate model list based on preset filter
function populateModelList(presetId) {
    const modelList = document.querySelector('.model-list');
    if (!modelList) {
        console.error('Model list container not found');
        return;
    }
    
    // Clear existing models
    modelList.innerHTML = '';
    
    // Get filter for this preset
    const filter = presetFilters[presetId] || (() => true);
    
    // Filter and display models
    const filteredModels = allModels.filter(filter);
    
    filteredModels.forEach(model => {
        const modelItem = document.createElement('div');
        modelItem.className = 'model-item';
        modelItem.dataset.modelId = model.id;
        
        // Check if this model is currently selected for this preset
        const currentModelId = userPreferences[presetId] || defaultModels[presetId];
        const isSelected = model.id === currentModelId;
        
        modelItem.innerHTML = `
            <div class="model-info">
                <div class="model-name">${model.name}</div>
                <div class="model-id">${model.id}</div>
            </div>
            <div class="model-meta">
                <span class="cost-band cost-${model.cost_band || 'unknown'}">${model.cost_band || 'Unknown'}</span>
                ${isSelected ? '<span class="selected-indicator">✓</span>' : ''}
            </div>
        `;
        
        // Add click handler to select this model
        modelItem.addEventListener('click', () => {
            selectModelForPreset(presetId, model.id);
            closeModelSelector();
        });
        
        modelList.appendChild(modelItem);
    });
}

// Function to select a model for a specific preset
async function selectModelForPreset(presetId, modelId) {
    console.log(`📝 Selecting model ${modelId} for preset ${presetId}`);
    
    const success = await saveModelPreference(presetId, modelId);
    if (success) {
        // Update current model if this is the active preset
        if (presetId === currentPresetId) {
            currentModel = modelId;
            updateSelectedModelCostIndicator(modelId);
            updateMultimodalControls(modelId);
        }
    }
}

// Function to select a preset button
export function selectPresetButton(presetId) {
    console.log(`🎯 Selecting preset ${presetId}`);
    
    // Update active preset
    currentPresetId = presetId;
    
    // Update UI using correct selectors
    const presetButtons = document.querySelectorAll('.model-preset-btn');
    presetButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-preset-id') === presetId) {
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

// Expose functions globally for cross-module compatibility
window.openModelSelector = openModelSelector;
window.selectPresetButton = selectPresetButton;
window.closeModelSelector = closeModelSelector;
window.updatePresetButtonLabels = updatePresetButtonLabels;
window.fetchAvailableModels = fetchAvailableModels;
window.fetchUserPreferences = fetchUserPreferences;