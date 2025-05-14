/**
 * Mobile Interactions for GloriaMundo
 * 
 * Provides mobile-specific interactions:
 * - Long-press detection for model preset buttons
 * - Bottom sheet for model selection
 * - Sidebar toggle for mobile navigation
 * 
 * @version 1.1.0
 */

// Define a debug logger that works in all browsers
const mobileLogger = {
    log: function(msg) {
        if (window.console && window.console.log) {
            console.log('[Mobile] ' + msg);
        }
    },
    error: function(msg, err) {
        if (window.console && window.console.error) {
            console.error('[Mobile Error] ' + msg, err || '');
        }
    }
};

// Execute when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    try {
        mobileLogger.log('Mobile interactions script started');
        initializeMobileInterface();
    } catch (err) {
        mobileLogger.error('Fatal error initializing mobile interactions', err);
    }
});

/**
 * Main initialization function
 */
function initializeMobileInterface() {
    // Detect if we're on a mobile device
    const isMobile = detectMobileDevice();
    
    // Add mobile class to body for CSS targeting
    if (isMobile) {
        document.body.classList.add('mobile-device');
        mobileLogger.log('Added mobile-device class to body');
    }
    
    // Get all required elements
    const elements = getMobileElements();
    
    // Log missing elements with clear errors
    validateElements(elements);
    
    // Ensure bottom sheet is hidden by default
    setupBottomSheetInitialState(elements, isMobile);
    
    // Exit early for non-mobile devices
    if (!isMobile) {
        mobileLogger.log('Not a mobile device, exiting mobile interactions setup');
        return;
    }
    
    mobileLogger.log('Setting up mobile interactions for mobile device');
    
    // Initialize core mobile functionality
    setupLongPressDetection(elements);
    setupBottomSheetInteractions(elements);
    setupSidebarToggle(elements);
    
    // Log successful initialization
    mobileLogger.log('Mobile interactions initialized successfully');
}

/**
 * Detect if the current device is mobile
 */
function detectMobileDevice() {
    try {
        // Method 1: Use our deviceDetection object if available
        if (typeof window.deviceDetection !== 'undefined' && window.deviceDetection.isMobileDevice === true) {
            mobileLogger.log('Detected mobile device via deviceDetection');
            return true;
        }
        
        // Method 2: Check for touch capabilities (most reliable)
        if (window.matchMedia && window.matchMedia('(pointer: coarse)').matches) {
            mobileLogger.log('Detected mobile device via pointer:coarse');
            return true;
        }
        
        // Method 3: Check common mobile user agent patterns
        const userAgent = navigator.userAgent || navigator.vendor || window.opera;
        if (/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino/i.test(userAgent) || 
            /1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(userAgent.substr(0,4))) {
            mobileLogger.log('Detected mobile device via user agent');
            return true;
        }
        
        // Method 4: Check screen size
        if (window.innerWidth <= 768) {
            mobileLogger.log('Detected mobile device via screen size');
            return true;
        }
        
        mobileLogger.log('Not a mobile device');
        return false;
    } catch (err) {
        mobileLogger.error('Error detecting mobile device', err);
        // Default to false if detection fails
        return false;
    }
}

/**
 * Gather all DOM elements needed for mobile interactions
 */
function getMobileElements() {
    return {
        bottomSheet: document.getElementById('model-bottom-sheet'),
        bottomSheetBackdrop: document.getElementById('model-bottom-sheet-backdrop'),
        bottomSheetContent: document.getElementById('model-bottom-sheet-content'),
        bottomSheetClose: document.getElementById('model-bottom-sheet-close'),
        bottomSheetSearch: document.getElementById('model-bottom-sheet-search'),
        modelPresetButtons: document.querySelectorAll('.model-preset-btn'),
        sidebar: document.getElementById('sidebar'),
        sidebarToggle: document.getElementById('sidebar-toggle'),
        sidebarOverlay: document.getElementById('sidebar-overlay'),
        sidebarCloseBtn: document.getElementById('sidebar-close-btn')
    };
}

/**
 * Validate that all required elements exist
 */
function validateElements(elements) {
    if (!elements.bottomSheet) mobileLogger.error('Bottom sheet element not found (id="model-bottom-sheet")');
    if (!elements.bottomSheetBackdrop) mobileLogger.error('Bottom sheet backdrop element not found (id="model-bottom-sheet-backdrop")');
    if (!elements.bottomSheetContent) mobileLogger.error('Bottom sheet content element not found (id="model-bottom-sheet-content")');
    if (!elements.bottomSheetClose) mobileLogger.error('Bottom sheet close button not found (id="model-bottom-sheet-close")');
    if (!elements.modelPresetButtons.length) mobileLogger.error('No model preset buttons found (class="model-preset-btn")');
    if (!elements.sidebar) mobileLogger.error('Sidebar element not found (id="sidebar")');
    if (!elements.sidebarToggle) mobileLogger.error('Sidebar toggle button not found (id="sidebar-toggle")');
    if (!elements.sidebarOverlay) mobileLogger.error('Sidebar overlay element not found (id="sidebar-overlay")');
    if (!elements.sidebarCloseBtn) mobileLogger.error('Sidebar close button not found (id="sidebar-close-btn")');
}

/**
 * Setup initial state of bottom sheet
 */
function setupBottomSheetInitialState(elements, isMobile) {
    if (elements.bottomSheet && elements.bottomSheetBackdrop) {
        // Apply display style directly to override CSS
        elements.bottomSheet.style.display = isMobile ? 'block' : 'none';
        elements.bottomSheetBackdrop.style.display = isMobile ? 'block' : 'none';
        
        // Remove active class to ensure it's hidden
        elements.bottomSheet.classList.remove('active');
        elements.bottomSheetBackdrop.classList.remove('active');
        
        mobileLogger.log('Bottom sheet display set to: ' + (isMobile ? 'block (hidden until triggered)' : 'none'));
    }
}

/**
 * Setup long press detection for model preset buttons
 */
function setupLongPressDetection(elements) {
    // Variables for long-press detection
    let longPressTimer = null;
    const longPressDuration = 500; // ms
    let activePresetButton = null;
    
    // Set up long press for each model preset button
    elements.modelPresetButtons.forEach(button => {
        // Check if button has preset ID
        if (!button.dataset.presetId) {
            mobileLogger.error('Model preset button missing data-preset-id attribute');
            return;
        }
        
        mobileLogger.log(`Setting up long-press for preset: ${button.dataset.presetId}`);
        
        // Touch start - begin potential long press
        button.addEventListener('touchstart', function(e) {
            // Store button reference
            activePresetButton = this;
            
            // Add visual feedback
            this.classList.add('long-press-active');
            
            // Start timer for long press detection
            longPressTimer = setTimeout(() => {
                mobileLogger.log('Long press detected on preset button');
                openBottomSheet(elements, this.dataset.presetId);
            }, longPressDuration);
            
            // Prevent normal click to allow for potential long press
            e.preventDefault();
        });
        
        // Touch end - handle as click if not a long press
        button.addEventListener('touchend', function() {
            // Clear long press timer
            if (longPressTimer) {
                clearTimeout(longPressTimer);
                longPressTimer = null;
            }
            
            // Remove visual feedback
            this.classList.remove('long-press-active');
            
            // If this was just a normal click, continue with default action
            if (activePresetButton === this) {
                // Simulate click on desktop version button for normal tap
                mobileLogger.log('Normal tap on preset button (not long press)');
                // The default action will proceed
            }
            
            // Reset active button
            activePresetButton = null;
        });
        
        // Touch cancel - clean up
        button.addEventListener('touchcancel', function() {
            // Clear long press timer
            if (longPressTimer) {
                clearTimeout(longPressTimer);
                longPressTimer = null;
            }
            
            // Remove visual feedback
            this.classList.remove('long-press-active');
            
            // Reset active button
            activePresetButton = null;
        });
    });
}

/**
 * Setup bottom sheet interactions
 */
function setupBottomSheetInteractions(elements) {
    if (!elements.bottomSheet || !elements.bottomSheetBackdrop || !elements.bottomSheetClose) {
        mobileLogger.error('Cannot setup bottom sheet interactions - elements not found');
        return;
    }
    
    mobileLogger.log('Setting up bottom sheet interactions');
    
    // Close button
    elements.bottomSheetClose.addEventListener('click', function() {
        closeBottomSheet(elements);
    });
    
    // Backdrop click to close
    elements.bottomSheetBackdrop.addEventListener('click', function() {
        closeBottomSheet(elements);
    });
    
    // Search functionality for bottom sheet
    if (elements.bottomSheetSearch) {
        elements.bottomSheetSearch.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            filterBottomSheetModels(elements, searchTerm);
        });
    }
    
    // Delegate click events for model items (added dynamically)
    if (elements.bottomSheetContent) {
        elements.bottomSheetContent.addEventListener('click', function(e) {
            // Find closest model item if it exists
            const modelItem = e.target.closest('.bottom-sheet-item');
            if (modelItem && modelItem.dataset.modelId) {
                selectModel(elements, modelItem.dataset.modelId);
            }
        });
    }
}

/**
 * Setup sidebar toggle functionality
 */
function setupSidebarToggle(elements) {
    if (!elements.sidebarToggle || !elements.sidebar) {
        mobileLogger.error('Cannot setup sidebar toggle - elements not found');
        return;
    }
    
    mobileLogger.log('Setting up sidebar toggle');
    
    // Toggle button click
    elements.sidebarToggle.addEventListener('click', function() {
        mobileLogger.log('Sidebar toggle clicked');
        
        // Toggle sidebar active class
        elements.sidebar.classList.toggle('active');
        
        // Toggle overlay visibility
        if (elements.sidebarOverlay) {
            elements.sidebarOverlay.classList.toggle('active');
        }
        
        // Toggle body class to prevent scrolling
        document.body.classList.toggle('sidebar-open');
    });
    
    // Close button click
    if (elements.sidebarCloseBtn) {
        elements.sidebarCloseBtn.addEventListener('click', function() {
            mobileLogger.log('Sidebar close button clicked');
            
            // Remove active classes
            elements.sidebar.classList.remove('active');
            if (elements.sidebarOverlay) {
                elements.sidebarOverlay.classList.remove('active');
            }
            
            // Allow body scrolling again
            document.body.classList.remove('sidebar-open');
        });
    }
    
    // Overlay click to close
    if (elements.sidebarOverlay) {
        elements.sidebarOverlay.addEventListener('click', function() {
            mobileLogger.log('Sidebar overlay clicked');
            
            // Remove active classes
            elements.sidebar.classList.remove('active');
            elements.sidebarOverlay.classList.remove('active');
            
            // Allow body scrolling again
            document.body.classList.remove('sidebar-open');
        });
    }
}

/**
 * Open the bottom sheet to select a model
 */
function openBottomSheet(elements, presetId) {
    try {
        mobileLogger.log(`Opening bottom sheet for preset ${presetId}`);
        
        if (!elements.bottomSheet || !elements.bottomSheetBackdrop) {
            mobileLogger.error('Cannot open bottom sheet - elements not found');
            return;
        }
        
        // Store the preset ID on the bottom sheet
        elements.bottomSheet.dataset.activePresetId = presetId;
        
        // Populate models
        populateBottomSheetModels(elements, presetId);
        
        // Show the bottom sheet with animation
        elements.bottomSheetBackdrop.classList.add('active');
        elements.bottomSheet.classList.add('active');
        
        // Focus search input after animation
        if (elements.bottomSheetSearch) {
            setTimeout(() => {
                elements.bottomSheetSearch.focus();
            }, 300);
        }
    } catch (err) {
        mobileLogger.error('Error opening bottom sheet', err);
    }
}

/**
 * Close the bottom sheet
 */
function closeBottomSheet(elements) {
    try {
        mobileLogger.log('Closing bottom sheet');
        
        if (!elements.bottomSheet || !elements.bottomSheetBackdrop) {
            mobileLogger.error('Cannot close bottom sheet - elements not found');
            return;
        }
        
        // Hide with animation
        elements.bottomSheetBackdrop.classList.remove('active');
        elements.bottomSheet.classList.remove('active');
        
        // Clear search
        if (elements.bottomSheetSearch) {
            elements.bottomSheetSearch.value = '';
        }
    } catch (err) {
        mobileLogger.error('Error closing bottom sheet', err);
    }
}

/**
 * Populate the bottom sheet with available models
 */
function populateBottomSheetModels(elements, presetId) {
    try {
        mobileLogger.log(`Populating models for preset ${presetId}`);
        
        if (!elements.bottomSheetContent) {
            mobileLogger.error('Cannot populate models - content element not found');
            return;
        }
        
        if (!window.modelData) {
            mobileLogger.error('Model data not available');
            elements.bottomSheetContent.innerHTML = '<div class="bottom-sheet-error">Model data not available</div>';
            return;
        }
        
        // Get models for the selected preset
        const models = window.modelData[presetId] || [];
        
        if (!models.length) {
            mobileLogger.error(`No models found for preset ${presetId}`);
            elements.bottomSheetContent.innerHTML = '<div class="bottom-sheet-error">No models available for this preset</div>';
            return;
        }
        
        mobileLogger.log(`Found ${models.length} models for preset ${presetId}`);
        
        // Get user's saved preference
        const preferredModel = getUserModelPreference(presetId);
        
        // Clear current content
        elements.bottomSheetContent.innerHTML = '';
        
        // Add each model to the sheet
        models.forEach(model => {
            const isSelected = preferredModel === model.id;
            
            const modelElement = document.createElement('div');
            modelElement.className = 'bottom-sheet-item';
            if (isSelected) modelElement.classList.add('selected');
            modelElement.dataset.modelId = model.id;
            
            modelElement.innerHTML = `
                <div class="bottom-sheet-item-icon">${getModelIcon(model)}</div>
                <div class="bottom-sheet-item-details">
                    <div class="bottom-sheet-item-name">${formatModelName(model.id, true)}</div>
                    <div class="bottom-sheet-item-description">${model.description || 'No description available'}</div>
                    <div class="bottom-sheet-item-price">${getModelPriceDisplay(model)}</div>
                    <div class="bottom-sheet-item-capabilities">${getModelCapabilityBadges(model)}</div>
                </div>
            `;
            
            elements.bottomSheetContent.appendChild(modelElement);
        });
    } catch (err) {
        mobileLogger.error('Error populating bottom sheet models', err);
        elements.bottomSheetContent.innerHTML = '<div class="bottom-sheet-error">Error loading models</div>';
    }
}

/**
 * Filter models in the bottom sheet based on search term
 */
function filterBottomSheetModels(elements, searchTerm) {
    try {
        if (!elements.bottomSheetContent) {
            mobileLogger.error('Cannot filter models - content element not found');
            return;
        }
        
        const modelItems = elements.bottomSheetContent.querySelectorAll('.bottom-sheet-item');
        
        if (!modelItems.length) {
            mobileLogger.log('No model items to filter');
            return;
        }
        
        mobileLogger.log(`Filtering ${modelItems.length} models with term: ${searchTerm}`);
        
        let visibleCount = 0;
        
        modelItems.forEach(item => {
            const modelName = item.querySelector('.bottom-sheet-item-name').textContent.toLowerCase();
            const modelDesc = item.querySelector('.bottom-sheet-item-description').textContent.toLowerCase();
            
            // Check if model name or description contains the search term
            const isMatch = modelName.includes(searchTerm) || modelDesc.includes(searchTerm);
            
            // Show or hide based on match
            item.style.display = isMatch ? 'flex' : 'none';
            
            if (isMatch) visibleCount++;
        });
        
        mobileLogger.log(`Filter results: ${visibleCount} models visible`);
        
        // Show message if no results
        let noResultsEl = elements.bottomSheetContent.querySelector('.no-results-message');
        
        if (visibleCount === 0) {
            // Add "no results" message if it doesn't exist
            if (!noResultsEl) {
                noResultsEl = document.createElement('div');
                noResultsEl.className = 'no-results-message';
                noResultsEl.textContent = 'No models match your search';
                elements.bottomSheetContent.appendChild(noResultsEl);
            }
        } else {
            // Remove "no results" message if it exists
            if (noResultsEl) {
                noResultsEl.remove();
            }
        }
    } catch (err) {
        mobileLogger.error('Error filtering bottom sheet models', err);
    }
}

/**
 * Select a model from the bottom sheet
 */
function selectModel(elements, modelId) {
    try {
        mobileLogger.log(`Selecting model: ${modelId}`);
        
        if (!elements.bottomSheet || !elements.bottomSheet.dataset.activePresetId) {
            mobileLogger.error('Cannot select model - active preset ID not found');
            return;
        }
        
        const presetId = elements.bottomSheet.dataset.activePresetId;
        
        // Close the bottom sheet
        closeBottomSheet(elements);
        
        // Find the preset button for this preset
        const presetButton = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
        
        if (!presetButton) {
            mobileLogger.error(`Cannot find preset button for preset ID: ${presetId}`);
            return;
        }
        
        mobileLogger.log(`Setting model ${modelId} for preset ${presetId}`);
        
        // Update the button's model ID
        presetButton.dataset.selectedModelId = modelId;
        
        // Save the selection by calling the save preference function
        if (window.saveModelPreference) {
            window.saveModelPreference(presetId, modelId);
        } else {
            mobileLogger.error('saveModelPreference function not available');
        }
        
        // Update button display
        updatePresetButtonDisplay(presetButton, modelId);
    } catch (err) {
        mobileLogger.error('Error selecting model', err);
    }
}

/**
 * Update the display of a preset button after model selection
 */
function updatePresetButtonDisplay(button, modelId) {
    try {
        // Get model display name
        const displayName = formatModelName(modelId);
        
        // Find the model name element inside the button
        const nameElement = button.querySelector('.model-name');
        
        if (nameElement) {
            nameElement.textContent = displayName;
        } else {
            mobileLogger.error('Cannot find model name element in preset button');
        }
    } catch (err) {
        mobileLogger.error('Error updating preset button display', err);
    }
}

/**
 * Format a model name for display
 */
function formatModelName(modelId, isFreePrefixed = false) {
    try {
        // Remove vendor prefix if present
        let displayName = modelId.replace(/^[^\/]+\//, '');
        
        // Check if model is free (has 'free' in userModelPrices)
        const isFree = window.userModelPrices && 
                      window.userModelPrices[modelId] && 
                      window.userModelPrices[modelId].isFree;
        
        // Add FREE prefix if requested and model is free
        if (isFreePrefixed && isFree) {
            displayName = `FREE: ${displayName}`;
        }
        
        return displayName;
    } catch (err) {
        mobileLogger.error('Error formatting model name', err);
        return modelId; // Return original as fallback
    }
}

/**
 * Get an icon for a model based on provider
 */
function getModelIcon(model) {
    try {
        const modelId = model.id.toLowerCase();
        
        if (modelId.includes('anthropic') || modelId.includes('claude')) {
            return '<i class="fa-solid fa-spa"></i>';
        } else if (modelId.includes('openai') || modelId.includes('gpt')) {
            return '<i class="fa-solid fa-robot"></i>';
        } else if (modelId.includes('google') || modelId.includes('gemini')) {
            return '<i class="fa-brands fa-google"></i>';
        } else if (modelId.includes('meta') || modelId.includes('llama')) {
            return '<i class="fa-brands fa-facebook"></i>';
        } else if (modelId.includes('mistral')) {
            return '<i class="fa-solid fa-wind"></i>';
        } else {
            return '<i class="fa-solid fa-microchip"></i>';
        }
    } catch (err) {
        mobileLogger.error('Error getting model icon', err);
        return '<i class="fa-solid fa-microchip"></i>'; // Default icon
    }
}

/**
 * Get price display for a model
 */
function getModelPriceDisplay(model) {
    try {
        // Check if we have price data for this model
        if (!window.userModelPrices || !window.userModelPrices[model.id]) {
            return '<span class="price-unknown">Price unknown</span>';
        }
        
        const priceData = window.userModelPrices[model.id];
        
        if (priceData.isFree) {
            return '<span class="price-free">FREE</span>';
        } else {
            return `<span class="price-prompt">$${priceData.promptPrice}/1K tkns</span> | <span class="price-completion">$${priceData.completionPrice}/1K tkns</span>`;
        }
    } catch (err) {
        mobileLogger.error('Error getting model price display', err);
        return '<span class="price-unknown">Price unknown</span>';
    }
}

/**
 * Get capability badges for a model
 */
function getModelCapabilityBadges(model) {
    try {
        const badges = [];
        
        if (model.multimodal) {
            badges.push('<span class="capability-badge multimodal"><i class="fa-solid fa-image"></i> Images</span>');
        }
        
        if (model.vision) {
            badges.push('<span class="capability-badge vision"><i class="fa-solid fa-eye"></i> Vision</span>');
        }
        
        if (model.documentProcessing) {
            badges.push('<span class="capability-badge document"><i class="fa-solid fa-file-pdf"></i> Documents</span>');
        }
        
        return badges.join('');
    } catch (err) {
        mobileLogger.error('Error getting model capability badges', err);
        return '';
    }
}

/**
 * Get user's model preference for a preset
 */
function getUserModelPreference(presetId) {
    try {
        // Check if window.userModelPreferences exists and has this preset
        if (window.userModelPreferences && window.userModelPreferences[presetId]) {
            return window.userModelPreferences[presetId];
        }
        return null;
    } catch (err) {
        mobileLogger.error('Error getting user model preference', err);
        return null;
    }
}