/**
 * Model Selection Module
 * Handles all model selection functionality including presets, filters, and user preferences
 */

import { debounce } from './utils.js';
import { fetchUserPreferencesAPI, fetchAvailableModelsAPI, saveModelPreferenceAPI, resetPreferencesAPI } from './apiService.js';

// Model selection state variables
export let allModels = []; // All models from OpenRouter
export let userPreferences = {}; // User preferences for preset buttons
export let userFallbackEnabled = true; // User's fallback preference setting
export let currentModel = null; // Model ID of the currently selected preset
export let currentPresetId = '1'; // Default to first preset
export let currentlyEditingPresetId = null;

// Expose globally for mobile scripts
window.availableModels = allModels;
window.userPreferences = userPreferences;

// Filter configurations for each preset
export const presetFilters = {
    '1': (model) => {
        // All non-free models - include auto model specifically
        if (model.id === 'openrouter/auto') return true;
        const isFree = model.id.includes(':free') || model.cost_band === 'free' || model.is_free === true;
        return !isFree;
    },
    '2': (model) => {
        // All non-free models - include auto model specifically
        if (model.id === 'openrouter/auto') return true;
        const isFree = model.id.includes(':free') || model.cost_band === 'free' || model.is_free === true;
        return !isFree;
    },
    '3': (model) => {
        // Reasoning models (non-free) - check for is_reasoning flag first, then fallback to ID patterns
        const isFree = model.id.includes(':free') || model.cost_band === 'free' || model.is_free === true;
        if (isFree) {
            return false; // Exclude free models
        }
        
        if (model.is_reasoning === true) {
            return true;
        }
        // Fallback to ID-based detection for o1, o3, reasoning keywords
        return model.id.includes('reasoning') || model.id.includes('o1') || model.id.includes('o3');
    },
    '4': (model) => {
        // Multimodal/image-capable models (non-free)
        const isFree = model.id.includes(':free') || model.cost_band === 'free' || model.is_free === true;
        const isMultimodal = model.is_multimodal || model.supports_vision || 
                            model.id.includes('vision') || model.id.includes('gpt-4o');
        return !isFree && isMultimodal;
    },
    '5': (model) => {
        // Search/Perplexity models - only Perplexity models, exclude free models
        const isFree = model.id.includes(':free') || model.cost_band === 'free' || model.is_free === true;
        const isPerplexity = model.id.includes('perplexity');
        return isPerplexity && !isFree;
    },
    '6': (model) => {
        // Free models only - exclude auto model specifically
        if (model.id === 'openrouter/auto') return false;
        return model.id.includes(':free') || model.cost_band === 'free' || model.is_free === true;
    }
};

// Default models for each preset
export const defaultModels = {
    '1': 'google/gemini-2.5-pro-preview', // Current Gemini 2.5 Pro
    '2': 'x-ai/grok-3-beta',
    '3': 'anthropic/claude-sonnet-4', // Reasoning
    '4': 'openai/gpt-4o-2024-11-20', // Multimodal
    '5': 'perplexity/sonar-pro', // Search/Perplexity
    '6': 'google/gemini-2.0-flash-exp:free' // Free
};

// Preset fallback chains - ordered by preference for each preset category
export const presetFallbackChains = {
    '1': [ // Multimodal Gemini preset
        'google/gemini-2.5-pro-preview',
        'google/gemini-2.5-flash-preview-05-20', 
        'openai/o4-mini-high',
        'openai/o4-mini',
        'meta-llama/llama-4-maverick'
    ],
    '2': [ // Reasoning/Advanced preset  
        'x-ai/grok-3-beta',
        'meta-llama/llama-4-maverick',
        'anthropic/claude-3.7-sonnet:thinking',
        'openai/o4-mini-high',
        'anthropic/claude-3-sonnet-20240229'
    ],
    '3': [ // Reasoning preset
        'anthropic/claude-sonnet-4',
        'anthropic/claude-3.7-sonnet:thinking',
        'deepseek/deepseek-r1-0528',
        'openai/o4-mini-high',
        'openai/o4',
        'anthropic/claude-opus-4'
    ],
    '4': [ // Premium multimodal preset
        'openai/gpt-4o-2024-11-20',
        'openai/gpt-4o-2024-05-13',
        'openai/gpt-4.1',
        'openai/gpt-4o-mini',
        'google/gemini-2.0-flash-001'
    ],
    '5': [ // Search/Web preset
        'perplexity/sonar-pro',
        'perplexity/sonar-reasoning-pro',
        'perplexity/sonar',
        'perplexity/llama-3.1-sonar-large-128k-online'
    ],
    '6': [ // Free preset
        'google/gemini-2.0-flash-exp:free',
        'meta-llama/llama-4-scout:free',
        'microsoft/phi-4-reasoning-plus:free',
        'deepseek/deepseek-r1-0528:free'
    ]
};

// Display names for default models (shown on buttons - concise for limited space)
export const defaultModelDisplayNames = {
    'google/gemini-2.5-pro-preview': 'Gemini 2.5 Pro',
    'x-ai/grok-3-beta': 'Grok 3',
    'anthropic/claude-sonnet-4': 'Claude Sonnet 4',
    'openai/gpt-4o-2024-11-20': 'GPT 4o',
    'perplexity/sonar-pro': 'Perplexity Pro',
    'google/gemini-2.0-flash-exp:free': 'Gemini 2'
};

// Full technical names for dropdown display (users see exact model names when selecting)
export const fullModelDisplayNames = {
    'google/gemini-2.0-flash-exp': 'Gemini 2.0 Flash Experimental',
    'x-ai/grok-3-beta': 'Grok 3 Beta',
    'anthropic/claude-sonnet-4': 'Claude Sonnet 4',
    'openai/gpt-4o-2024-11-20': 'GPT-4o (2024-11-20)',
    'perplexity/sonar-pro': 'Perplexity Sonar Pro',
    'google/gemini-2.0-flash-exp:free': 'Gemini 2.0 Flash Experimental (Free)'
};

// Expose defaultModels and fullModelDisplayNames globally for mobile scripts
window.defaultModels = defaultModels;
window.fullModelDisplayNames = fullModelDisplayNames;

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
    const modelSearchInput = document.getElementById('model-search');
    const closeButton = document.getElementById('close-selector');
    
    if (closeButton) {
        closeButton.addEventListener('click', closeModelSelector);
    }
    
    // Note: Click outside handling is now managed in eventOrchestration.js
    
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
            
            // Keep using our predefined concise display names for buttons
            // Don't override with full technical names from allModels
            
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
            
            // Set user's fallback preference
            userFallbackEnabled = data.enable_model_fallback !== undefined ? data.enable_model_fallback : true;
            console.log('✅ User preferences loaded:', userPreferences);
            console.log('📋 User fallback enabled:', userFallbackEnabled);
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
                
                // Determine capabilities with fallbacks for known multimodal models
                const isKnownVisionModel = modelId.includes('claude') || modelId.includes('gpt-4') || 
                                         modelId.includes('gemini') || modelId.includes('vision');
                const hasVisionSupport = modelData.supports_vision || modelData.is_multimodal || isKnownVisionModel;
                const hasPdfSupport = modelData.supports_pdf || isKnownVisionModel;
                
                console.log(`📝 Processing model ${modelId}:`, {
                    originalData: { 
                        is_multimodal: modelData.is_multimodal, 
                        supports_vision: modelData.supports_vision, 
                        supports_pdf: modelData.supports_pdf 
                    },
                    computed: { hasVisionSupport, hasPdfSupport, isKnownVisionModel }
                });
                
                modelDataArray.push({
                    id: modelId,
                    name: modelData.name || formatModelName(modelId),
                    cost_band: modelData.cost_band,
                    pricing: modelData.pricing,
                    is_multimodal: modelData.is_multimodal || isKnownVisionModel,
                    supports_vision: hasVisionSupport,
                    supports_pdf: hasPdfSupport,
                    context_length: modelData.context_length,
                    description: modelData.description,
                    is_reasoning: modelData.is_reasoning || false,
                    is_free: modelData.is_free || false,
                    elo_score: modelData.elo_score || null
                });
            }
            
            allModels = modelDataArray;
            window.availableModels = allModels;
            console.log(`✅ Loaded ${allModels.length} models from prices data`);
            updatePresetButtonLabels();
            
            // Initialize upload controls for the default preset
            if (currentPresetId) {
                console.log(`🔧 Initializing upload controls for default preset: ${currentPresetId}`);
                selectPresetButton(currentPresetId);
            }
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

// Function to sort models based on preset requirements
function sortModelsByPreset(models, presetId) {
    const modelsCopy = [...models]; // Create a copy to avoid mutating original array
    
    if (presetId === '2') {
        // Preset 2: Sort by context length (highest first)
        return modelsCopy.sort((a, b) => {
            const contextA = parseInt(a.context_length) || 0;
            const contextB = parseInt(b.context_length) || 0;
            return contextB - contextA;
        });
    } else {
        // All other presets: Sort by ELO score (highest first)
        return modelsCopy.sort((a, b) => {
            const eloA = parseFloat(a.elo_score) || 0;
            const eloB = parseFloat(b.elo_score) || 0;
            return eloB - eloA;
        });
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
    
    // Apply the filter
    const filteredModels = allModels.filter(filterFn);
    
    // Sort the filtered models based on preset requirements
    const sortedModels = sortModelsByPreset(filteredModels, presetId);
    
    console.log(`[Debug] Found ${filteredModels.length} models for preset ${presetId}`);
    console.log(`[Debug] After sorting: ${sortedModels.length} models for preset ${presetId}`);
    
    // Log: After filtering and sorting
    if (sortedModels.length === 0 && allModels && allModels.length > 0) {
        console.warn(`[Debug] Filtering for preset ${presetId} resulted in 0 models. Check filter logic and model properties.`);
        // Log the filter function itself if possible
        console.log('[Debug] Filter function:', filterFn.toString());
        // Log the first few models from allModels again for comparison
        console.log('[Debug] First few models in allModels before filtering:', JSON.stringify(allModels.slice(0, 3), null, 2));
    }
    
    // Use DocumentFragment for batch DOM updates
    const fragment = document.createDocumentFragment();
    
    // Add each model to the fragment
    sortedModels.forEach(model => {
        // Log: Inside rendering loop
        console.log(`[Debug] Rendering list item for model: ${model.id}, Band: ${model.cost_band}`);
        
        const li = document.createElement('li');
        li.dataset.modelId = model.id;
        
        // Create model name element
        const nameSpan = document.createElement('span');
        nameSpan.className = 'model-name';
        // Use full technical names for dropdown display
        if (fullModelDisplayNames[model.id]) {
            nameSpan.textContent = fullModelDisplayNames[model.id];
        } else {
            nameSpan.textContent = model.name;
        }
        
        // Add cost band indicator if available - gracefully handle missing cost_band
        if (model.cost_band !== undefined && model.cost_band !== null) {
            const costSpan = document.createElement('span');
            costSpan.textContent = model.cost_band || ''; // Handle empty string cost_band for free models
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
                // For empty band (free models) or any other value
                costSpan.classList.add('cost-band-free');
            }
            
            nameSpan.appendChild(costSpan);
        }
        // If cost_band is missing entirely, simply don't add a cost indicator - no error thrown
        
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
        // Handle missing cost_band gracefully - check if cost_band exists and is valid
        if (modelInfo.cost_band && ['$$$$', '$$$', '$$', '$', ''].includes(modelInfo.cost_band)) {
            const costBand = modelInfo.cost_band;
            costIndicator.className = `cost-indicator cost-${costBand}`;
            costIndicator.textContent = modelInfo.is_free ? 'FREE' : (costBand || 'N/A');
        } else {
            // Fallback when cost_band is missing - don't show cost indicator
            costIndicator.className = 'cost-indicator';
            costIndicator.textContent = modelInfo.is_free ? 'FREE' : '';
        }
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

// Function to update upload controls based on model capabilities
export function updateUploadControls(modelId) {
    const modelInfo = allModels.find(m => m.id === modelId);
    const fileBtn = document.getElementById('file-upload-button');
    const camBtn = document.getElementById('camera-button');
    const fileInput = document.getElementById('file-upload-input');
    
    console.log(`🔧 updateUploadControls called for model: ${modelId}`);
    console.log(`📊 Model info:`, modelInfo);
    console.log(`🔍 Button elements found:`, { fileBtn: !!fileBtn, camBtn: !!camBtn, fileInput: !!fileInput });
    
    if (!modelInfo || !fileBtn) {
        console.log(`❌ Early return: modelInfo=${!!modelInfo}, fileBtn=${!!fileBtn}`);
        return;
    }
    
    // Only enable if model supports vision or PDF
    const canImage = modelInfo.supports_vision || modelInfo.is_multimodal;
    const canPdf = !!modelInfo.supports_pdf;
    
    console.log(`🎯 Capabilities: canImage=${canImage} (supports_vision=${modelInfo.supports_vision}, is_multimodal=${modelInfo.is_multimodal}), canPdf=${canPdf}`);
    
    if (canImage || canPdf) {
        console.log(`✅ Showing upload button - model supports uploads`);
        fileBtn.style.display = 'flex';
        fileBtn.disabled = false;
    } else {
        console.log(`❌ Hiding upload button - model doesn't support uploads`);
        fileBtn.style.display = 'none';
        fileBtn.disabled = true;
    }
    
    // Adjust camera: only if vision supported
    if (camBtn) {
        if (canImage) {
            console.log(`📷 Showing camera button`);
            camBtn.style.display = 'flex';
            camBtn.disabled = false;
        } else {
            console.log(`📷 Hiding camera button`);
            camBtn.style.display = 'none';
            camBtn.disabled = true;
        }
    }
    
    // Adjust file input accept types
    if (fileInput) {
        let acceptTypes = [];
        if (canImage) acceptTypes.push('image/*');
        if (canPdf) acceptTypes.push('.pdf');
        fileInput.accept = acceptTypes.join(',');
        console.log(`📎 File input accept types: ${fileInput.accept}`);
    }
}

// Cache for UI state to enable instant updates
const uiStateCache = {
    uploadControls: new Map(), // modelId -> {canImage, canPdf}
    lastKnownCapabilities: new Map() // presetId -> {canImage, canPdf}
};

// Function to get cached UI capabilities or reasonable defaults
function getCachedCapabilities(modelId, presetId) {
    // First try the exact model ID
    if (uiStateCache.uploadControls.has(modelId)) {
        return uiStateCache.uploadControls.get(modelId);
    }
    
    // Then try the preset's last known capabilities
    if (uiStateCache.lastKnownCapabilities.has(presetId)) {
        return uiStateCache.lastKnownCapabilities.get(presetId);
    }
    
    // Default fallback based on known model patterns
    const isGemini = modelId.includes('gemini');
    const isGPT = modelId.includes('gpt-4');
    const isClaude = modelId.includes('claude-3');
    const isMultimodal = isGemini || isGPT || isClaude;
    
    return { canImage: isMultimodal, canPdf: isMultimodal };
}

// Function to apply UI updates immediately
function applyUploadControlsUI(capabilities, modelId) {
    const fileBtn = document.getElementById('file-upload-button');
    const camBtn = document.getElementById('camera-button');
    const fileInput = document.getElementById('file-upload-input');
    
    if (!fileBtn) return;
    
    const { canImage, canPdf } = capabilities;
    
    // Apply changes immediately
    if (canImage || canPdf) {
        fileBtn.style.display = 'flex';
        fileBtn.disabled = false;
    } else {
        fileBtn.style.display = 'none';
        fileBtn.disabled = true;
    }
    
    if (camBtn) {
        if (canImage) {
            camBtn.style.display = 'flex';
            camBtn.disabled = false;
        } else {
            camBtn.style.display = 'none';
            camBtn.disabled = true;
        }
    }
    
    if (fileInput) {
        let acceptTypes = [];
        if (canImage) acceptTypes.push('image/*');
        if (canPdf) acceptTypes.push('.pdf');
        fileInput.accept = acceptTypes.join(',');
    }
    
    console.log(`⚡ Applied cached UI for ${modelId}: canImage=${canImage}, canPdf=${canPdf}`);
}

// Function to update multimodal controls based on model
export function updateMultimodalControls(modelId) {
    console.log(`🔄 updateMultimodalControls called with modelId: ${modelId}`);
    
    if (!modelId) {
        console.log(`❌ No modelId provided to updateMultimodalControls`);
        return;
    }
    
    // Get current preset for caching
    const presetId = currentPresetId;
    
    // STEP 1: Apply cached/predicted UI immediately for fast response
    const cachedCapabilities = getCachedCapabilities(modelId, presetId);
    applyUploadControlsUI(cachedCapabilities, modelId);
    
    // STEP 2: Verify with actual model data in background
    if (!allModels.length) {
        console.log(`📡 Models not loaded, fetching in background`);
        fetchAvailableModels().then(() => {
            updateMultimodalControlsBackground(modelId, presetId);
        });
        return;
    }
    
    updateMultimodalControlsBackground(modelId, presetId);
}

// Function to find the best available model from a fallback chain
function findBestAvailableModel(modelId, presetId) {
    console.log(`🔍 Finding best available model for ${modelId} (preset ${presetId})`);
    
    // First check if the requested model is available
    const requestedModel = allModels.find(m => m.id === modelId);
    if (requestedModel) {
        console.log(`✅ Requested model ${modelId} is available`);
        return { modelId, modelInfo: requestedModel, fallbackUsed: false };
    }
    
    // Check if user has fallback enabled before trying alternatives
    if (!userFallbackEnabled) {
        console.log(`❌ Model ${modelId} not available and user has disabled fallbacks`);
        return null;
    }
    
    // Try fuzzy matching for the requested model
    const fuzzyMatch = allModels.find(m => 
        m.id.toLowerCase().includes(modelId.toLowerCase().split('/').pop()) ||
        modelId.toLowerCase().includes(m.id.toLowerCase().split('/').pop())
    );
    
    if (fuzzyMatch) {
        console.log(`🎯 Found fuzzy match: ${fuzzyMatch.id} for ${modelId}`);
        return { modelId: fuzzyMatch.id, modelInfo: fuzzyMatch, fallbackUsed: true };
    }
    
    // Use preset fallback chain
    const fallbackChain = presetFallbackChains[presetId] || [];
    console.log(`📋 Trying fallback chain for preset ${presetId}:`, fallbackChain);
    
    for (const fallbackModelId of fallbackChain) {
        const fallbackModel = allModels.find(m => m.id === fallbackModelId);
        if (fallbackModel) {
            console.log(`✅ Found working fallback: ${fallbackModelId}`);
            return { modelId: fallbackModelId, modelInfo: fallbackModel, fallbackUsed: true };
        }
    }
    
    console.log(`⚠️ No fallbacks available for preset ${presetId}`);
    return null;
}

// Background function to verify and update cache
function updateMultimodalControlsBackground(modelId, presetId) {
    const result = findBestAvailableModel(modelId, presetId);
    
    if (!result) {
        console.log(`❌ No working model found for ${modelId}`);
        return;
    }
    
    const { modelId: workingModelId, modelInfo, fallbackUsed } = result;
    
    if (fallbackUsed && workingModelId !== modelId) {
        console.log(`🔄 Switching to fallback model: ${workingModelId}`);
        // Update the preset to use the working model
        currentModel = workingModelId;
        updatePresetButtonLabel(presetId, workingModelId);
    }
    
    // Calculate actual capabilities
    const actualCapabilities = {
        canImage: modelInfo.supports_vision || modelInfo.is_multimodal,
        canPdf: !!modelInfo.supports_pdf
    };
    
    // Update cache for both original and working model IDs
    uiStateCache.uploadControls.set(modelId, actualCapabilities);
    uiStateCache.uploadControls.set(workingModelId, actualCapabilities);
    uiStateCache.lastKnownCapabilities.set(presetId, actualCapabilities);
    
    // Check if UI needs updating (capabilities changed)
    const currentCached = getCachedCapabilities(modelId, presetId);
    if (currentCached.canImage !== actualCapabilities.canImage || 
        currentCached.canPdf !== actualCapabilities.canPdf) {
        console.log(`🔄 Capabilities changed, updating UI`);
        applyUploadControlsUI(actualCapabilities, workingModelId);
    }
    
    console.log(`✅ Background verification complete for ${workingModelId}`);
}

// Function to update a preset button label when fallback is used
function updatePresetButtonLabel(presetId, modelId) {
    const button = document.querySelector(`[data-preset-id="${presetId}"]`);
    if (!button) return;
    
    const nameElement = button.querySelector('.model-name');
    if (!nameElement) return;
    
    // Get display name for the model
    const displayName = defaultModelDisplayNames[modelId] || 
                       fullModelDisplayNames[modelId] || 
                       modelId.split('/').pop();
    
    nameElement.textContent = displayName;
    console.log(`🏷️ Updated preset ${presetId} label to: ${displayName}`);
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