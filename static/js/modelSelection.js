/**
 * Model Selection Module
 * Handles all model selection functionality including presets, filters, and user preferences
 */

import { debounce } from './utils.js';
import { fetchUserPreferencesAPI, fetchAvailableModelsAPI, saveModelPreferenceAPI, resetPreferencesAPI } from './apiService.js';

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
    '3': 'openai/o1-preview', // Reasoning
    '4': 'anthropic/claude-3-5-sonnet-20241022', // Multimodal
    '5': 'meta-llama/llama-3.1-8b-instruct:free', // Search/Perplexity
    '6': 'meta-llama/llama-3.2-11b-vision-instruct:free' // Free
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
                    console.debug(`Model ${modelId} not found in allModels array, using fallback name`);
                }
            }
            
            // Update button text using the correct class name
            const nameSpan = button.querySelector('.model-name');
            if (nameSpan) {
                nameSpan.textContent = displayName;
                console.log(`Updated preset ${presetId} label to: ${displayName}`);
            } else {
                console.debug(`Could not find .model-name span in preset button ${presetId}`);
            }
        } else {
            // Only log debug message instead of warning since some presets may not exist in HTML
            console.debug(`Preset button ${presetId} not found in HTML - this is normal if not all presets are implemented`);
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
        
        console.log('Received preferences data:', data);
        
        if (data && data.preferences) {
            userPreferences = data.preferences || {};
            window.userPreferences = userPreferences;
            console.log('✅ User preferences loaded:', userPreferences);
            updatePresetButtonLabels();
        } else {
            const errorMsg = data ? (data.error || 'No preferences data in response') : 'No data received';
            console.warn('⚠️ Failed to fetch user preferences:', errorMsg);
            console.warn('Full response data:', data);
        }
    } catch (error) {
        console.error('❌ Complete error fetching user preferences:');
        console.error('Error object:', error);
        console.error('Error type:', typeof error);
        console.error('Error constructor:', error.constructor.name);
        console.error('Error message:', error.message || 'No message available');
        console.error('Error stack:', error.stack || 'No stack available');
        
        // If error is undefined or has no message, provide more context
        if (!error || error.message === undefined) {
            console.error('Error appears to be undefined or malformed');
            console.error('This might indicate a network issue or CORS problem');
        }
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
        currentlyEditingPresetId = null;
        
        // Remove the selector active class from body (for mobile view)
        document.body.classList.remove('model-selector-active');
    }
}

// Update UI based on model capabilities (original behavior)
export function updateUIForModelCapabilities() {
    if (!currentModel || !allModels.length) {
        return;
    }
    
    // Find the current model in the available models
    const model = allModels.find(m => m.id === currentModel);
    if (!model) {
        return;
    }
    
    console.log(`🔧 Updating UI for model capabilities: ${model.name}`);
    
    // Update image upload button visibility
    const imageUploadButton = document.getElementById('image-upload-button');
    if (imageUploadButton) {
        if (model.is_multimodal || model.supports_vision) {
            imageUploadButton.style.display = 'block';
            imageUploadButton.disabled = false;
        } else {
            imageUploadButton.style.display = 'none';
            imageUploadButton.disabled = true;
        }
    }
    
    // Update PDF upload button visibility
    const pdfUploadButton = document.getElementById('pdf-upload-button');
    if (pdfUploadButton) {
        if (model.supports_pdf) {
            pdfUploadButton.style.display = 'block';
            pdfUploadButton.disabled = false;
        } else {
            pdfUploadButton.style.display = 'none';
            pdfUploadButton.disabled = true;
        }
    }
    
    // Update general file upload input
    const imageUploadInput = document.getElementById('image-upload');
    if (imageUploadInput) {
        if (model.is_multimodal || model.supports_pdf) {
            const acceptTypes = [];
            if (model.is_multimodal) acceptTypes.push('image/*');
            if (model.supports_pdf) acceptTypes.push('application/pdf');
            imageUploadInput.accept = acceptTypes.join(',');
        } else {
            imageUploadInput.accept = '';
            imageUploadInput.disabled = true;
        }
    }
}

// Function to filter model list
export function filterModelList(searchTerm) {
    const modelList = document.getElementById('model-list');
    if (!modelList) return;
    
    const items = modelList.querySelectorAll('li');
    const lowerSearchTerm = searchTerm.toLowerCase();
    
    items.forEach(item => {
        const modelName = item.querySelector('.model-name')?.textContent.toLowerCase() || '';
        const modelProvider = item.querySelector('.model-provider')?.textContent.toLowerCase() || '';
        
        if (modelName.includes(lowerSearchTerm) || modelProvider.includes(lowerSearchTerm)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

// Function to open model selector for a preset
export function openModelSelector(presetId, buttonElement) {
    // Set current editing preset
    currentlyEditingPresetId = presetId;
    
    const modelSelector = document.getElementById('model-selector');
    if (!modelSelector) {
        console.error('Model selector element not found');
        return;
    }
    
    // For mobile: add a class to body when selector is active
    if (window.innerWidth <= 576) {
        document.body.classList.add('model-selector-active');
    }
    
    // Position the selector relative to the button
    const button = buttonElement || document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
    if (button) {
        const rect = button.getBoundingClientRect();
        const selectorRect = modelSelector.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Calculate position with a gap
        const gap = 10; // Gap in pixels
        
        // Set default dimensions for selector
        const selectorWidth = 300; // Width of the selector
        const selectorHeight = selectorRect.height || 300; // Default if not visible yet
        
        // Mobile-specific positioning (centered in viewport)
        if (window.innerWidth <= 576) {
            // Center horizontally on the screen
            const leftPosition = Math.max(10, Math.floor((viewportWidth - selectorWidth) / 2));
            
            // Position vertically in the middle of the viewport
            const topPosition = Math.floor((viewportHeight - selectorHeight) / 2);
            
            // Apply centered position
            modelSelector.style.top = `${topPosition}px`;
            modelSelector.style.left = `${leftPosition}px`;
        } else {
            // Desktop positioning (relative to button)
            // Try to position above the button first
            let topPosition = rect.top - selectorHeight - gap;
            
            // Check if there's enough space above
            if (topPosition < 0) {
                // Not enough space above, position below the button
                topPosition = rect.bottom + gap;
            }
            
            // Center horizontally relative to the button
            let leftPosition = rect.left + (rect.width / 2) - (selectorWidth / 2);
            
            // Ensure the selector doesn't go off-screen
            if (leftPosition < 10) leftPosition = 10;
            if (leftPosition + selectorWidth > viewportWidth - 10) {
                leftPosition = viewportWidth - selectorWidth - 10;
            }
            
            // Apply the position
            modelSelector.style.top = `${topPosition}px`;
            modelSelector.style.left = `${leftPosition}px`;
        }
        
        // Make visible
        modelSelector.style.display = 'block';
        
        // Clear search input
        const modelSearch = document.getElementById('model-search');
        if (modelSearch) {
            modelSearch.value = '';
        }
        
        // Populate model list for this preset
        populateModelList(presetId);
    }
}

// Function to populate model list based on preset filter
function populateModelList(presetId) {
    // Log: At function start
    console.log(`[Debug] populateModelList called for presetId: ${presetId}`);
    console.log(`[Debug] Current global allModels count: ${allModels ? allModels.length : 'undefined'}`);
    
    const modelList = document.getElementById('model-list');
    if (!modelList) {
        console.error('Model list container not found');
        return;
    }
    
    // Clear existing items
    modelList.innerHTML = '';
    
    // For FREE models (preset 6), ensure there's always at least the default free models available
    // This is especially important for non-logged in users where the API might not return models
    if (presetId === '6' && (!allModels || allModels.length === 0 || !allModels.some(m => m.is_free === true || m.id.includes(':free')))) {
        console.log('[Debug] No free models found in allModels, using fallback models for preset 6');
        
        // Create fallback list of free models
        const fallbackFreeModels = [
            {
                id: 'google/gemini-2.0-flash-exp:free',
                name: 'Gemini 2.0 Flash',
                is_free: true,
                is_multimodal: false,
                pricing: { prompt: 0, completion: 0 },
                cost_band: ''
            },
            {
                id: 'qwen/qwq-32b:free',
                name: 'Qwen 32B',
                is_free: true,
                is_multimodal: false,
                pricing: { prompt: 0, completion: 0 },
                cost_band: ''
            },
            {
                id: 'deepseek/deepseek-r1-distill-qwen-32b:free',
                name: 'Deepseek R1 Qwen 32B',
                is_free: true,
                is_multimodal: false,
                pricing: { prompt: 0, completion: 0 },
                cost_band: ''
            }
        ];
        
        // Use DocumentFragment for batch DOM updates
        const fragment = document.createDocumentFragment();
        
        // Add these fallback models to the fragment
        fallbackFreeModels.forEach(model => {
            const li = document.createElement('li');
            li.dataset.modelId = model.id;
            
            // Create free tag
            const freeTag = document.createElement('span');
            freeTag.className = 'free-tag';
            freeTag.textContent = 'FREE';
            
            // Create model name element
            const nameSpan = document.createElement('span');
            nameSpan.className = 'model-name';
            nameSpan.textContent = model.name;
            
            // Create provider span
            const providerSpan = document.createElement('span');
            providerSpan.className = 'model-provider';
            providerSpan.textContent = model.id.split('/')[0];
            
            // Assemble the elements
            li.appendChild(freeTag);
            li.appendChild(nameSpan);
            li.appendChild(providerSpan);
            
            // Add click handler to select this model
            li.addEventListener('click', function() {
                selectModelForPreset(presetId, model.id);
            });
            
            // Add to the fragment instead of directly to DOM
            fragment.appendChild(li);
        });
        
        // Add the fragment to the DOM in one operation
        modelList.appendChild(fragment);
        
        // Exit early as we've already populated the list with fallback models
        return;
    }
    
    // Standard case - API returned models properly
    if (!allModels || allModels.length === 0) {
        const placeholder = document.createElement('li');
        placeholder.textContent = 'Loading models...';
        modelList.appendChild(placeholder);
        return;
    }
    
    // Get filter function for this preset
    const filterFn = presetFilters[presetId] || (() => true);
    
    // Filter and sort models
    const filteredModels = allModels
        .filter(filterFn)
        .sort((a, b) => {
            // Preset 2 ONLY: Sort by context length first (for context-focused models)
            if (presetId === '2') {
                // Primary sort: Context Length (descending)
                const aContext = parseInt(a.context_length) || 0;
                const bContext = parseInt(b.context_length) || 0;
                if (aContext !== bContext) {
                    return bContext - aContext;
                }
                
                // Secondary sort: Input Price (ascending)
                const aPrice = a.pricing?.prompt || 0;
                const bPrice = b.pricing?.prompt || 0;
                if (aPrice !== bPrice) {
                    return aPrice - bPrice;
                }
                
                // Tertiary sort: Model Name (alphabetical)
                return a.name.localeCompare(b.name);
            }
            
            // For other presets: ELO-based sorting
            
            // Primary sort: ELO Score (descending, higher is better)
            const aElo = a.elo_score || 0;
            const bElo = b.elo_score || 0;
            
            // Models with ELO scores come before models without ELO scores
            if (aElo > 0 && bElo === 0) return -1;
            if (aElo === 0 && bElo > 0) return 1;
            
            // Both have ELO scores - sort by ELO (descending)
            if (aElo !== bElo) {
                return bElo - aElo;
            }
            
            // Secondary sort: Context Length (descending)
            const aContext = parseInt(a.context_length) || 0;
            const bContext = parseInt(b.context_length) || 0;
            if (aContext !== bContext) {
                return bContext - aContext;
            }
            
            // Tertiary sort: Input Price (ascending)
            const aPrice = a.pricing?.prompt || 0;
            const bPrice = b.pricing?.prompt || 0;
            if (aPrice !== bPrice) {
                return aPrice - bPrice;
            }
            
            // Quaternary sort: Model Name (alphabetical)
            return a.name.localeCompare(b.name);
        });
    
    // Log: After filtering
    console.log(`[Debug] Filtered models count for preset ${presetId}: ${filteredModels.length}`);
    if (filteredModels.length === 0 && allModels && allModels.length > 0) {
        console.warn(`[Debug] Filtering for preset ${presetId} resulted in 0 models. Check filter logic and model properties.`);
        // Log the filter function itself if possible
        console.log('[Debug] Filter function:', filterFn.toString());
        // Log the first few models from allModels again for comparison
        console.log('[Debug] First few models in allModels before filtering:', JSON.stringify(allModels.slice(0, 3), null, 2));
    }
    
    // Use DocumentFragment for batch DOM updates
    const fragment = document.createDocumentFragment();
    
    // Add each model to the fragment
    filteredModels.forEach(model => {
        // Log: Inside rendering loop
        console.log(`[Debug] Rendering list item for model: ${model.id}, Band: ${model.cost_band}`);
        
        const li = document.createElement('li');
        li.dataset.modelId = model.id;
        
        // Create model name element
        const nameSpan = document.createElement('span');
        nameSpan.className = 'model-name';
        // Use our display name mapping if available
        if (defaultModelDisplayNames[model.id]) {
            nameSpan.textContent = defaultModelDisplayNames[model.id];
        } else {
            nameSpan.textContent = model.name;
        }
        
        // Add cost band indicator if available
        if (model.cost_band) {
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
                // For empty band (free models)
                costSpan.classList.add('cost-band-free');
            }
            
            nameSpan.appendChild(costSpan);
        }
        
        // Create provider badge
        const providerSpan = document.createElement('span');
        providerSpan.className = 'model-provider';
        providerSpan.textContent = model.id.split('/')[0];
        
        // Add badge for free models
        if (model.is_free === true || model.id.includes(':free')) {
            const freeTag = document.createElement('span');
            freeTag.className = 'free-tag';
            freeTag.textContent = 'FREE';
            li.appendChild(freeTag);
        }
        
        li.appendChild(nameSpan);
        li.appendChild(providerSpan);
        
        // Add click handler to select this model
        li.addEventListener('click', function() {
            selectModelForPreset(currentlyEditingPresetId, model.id);
        });
        
        // Add to fragment instead of directly to DOM
        fragment.appendChild(li);
    });
    
    // Add the fragment to the DOM in one operation
    modelList.appendChild(fragment);
    
    // If no models match the filter
    if (filteredModels.length === 0) {
        const noResults = document.createElement('li');
        noResults.textContent = 'No models found';
        modelList.appendChild(noResults);
    }
}

// Function to select a model for a specific preset
async function selectModelForPreset(presetId, modelId, skipActivation) {
    // Check if trying to assign a free model to a non-free preset
    const isFreeModel = modelId.includes(':free') || allModels.some(m => m.id === modelId && m.is_free === true);
    if (presetId !== '6' && isFreeModel) {
        alert('Free models can only be selected for Preset 6');
        return;
    }
    
    // Update the UI
    const button = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
    if (button) {
        const nameSpan = button.querySelector('.model-name');
        if (nameSpan) {
            // Special handling for preset 6 (Free Model)
            if (presetId === '6') {
                if (defaultModelDisplayNames[modelId]) {
                    nameSpan.textContent = 'FREE - ' + defaultModelDisplayNames[modelId];
                } else {
                    nameSpan.textContent = 'FREE - ' + formatModelName(modelId, true);
                }
            } else {
                if (defaultModelDisplayNames[modelId]) {
                    nameSpan.textContent = defaultModelDisplayNames[modelId];
                } else {
                    nameSpan.textContent = formatModelName(modelId);
                }
            }
        }
    }
    
    // Update local state
    userPreferences[presetId] = modelId;
    
    // If this is the active preset, update the current model
    if (presetId === currentPresetId) {
        currentModel = modelId;
        
        // Update multimodal controls based on the selected model
        updateMultimodalControls(modelId);
    }
    
    // Save preference to server
    await saveModelPreference(presetId, modelId);
    
    // Close the selector
    closeModelSelector();
    
    // For the desktop flow, automatically activate the preset we just updated
    // For mobile, we'll handle this separately to avoid duplicate calls
    if (!skipActivation && presetId !== currentPresetId) {
        // Log for debugging
        console.log(`Auto-activating preset ${presetId} after model selection`);
        
        // Select the preset button to actually use this model
        selectPresetButton(presetId);
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
        
        const data = await resetPreferencesAPI(presetId);
        
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
window.populateModelList = populateModelList;
window.selectModelForPreset = selectModelForPreset;