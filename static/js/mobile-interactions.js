/**
 * Mobile Interactions for GloriaMundo
 * 
 * Provides mobile-specific interactions:
 * - Long-press detection for model preset buttons
 * - Bottom sheet for model selection
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add a class to body for CSS targeting
    if (deviceDetection && deviceDetection.isMobileDevice) {
        document.body.classList.add('mobile-device');
    } else {
        return; // Only continue for mobile devices
    }
    
    // DOM elements
    const modelPresetButtons = document.querySelectorAll('.model-preset-btn');
    const bottomSheet = document.getElementById('model-bottom-sheet');
    const bottomSheetBackdrop = document.getElementById('model-bottom-sheet-backdrop');
    const closeBottomSheetBtn = document.getElementById('close-bottom-sheet');
    const bottomSheetModelList = document.getElementById('bottom-sheet-model-list');
    const bottomSheetSearchInput = document.getElementById('bottom-sheet-search-input');
    const bottomSheetResetBtn = document.getElementById('bottom-sheet-reset');
    
    // Variables for tracking current state
    let currentPresetId = null;
    let longPressTimer = null;
    const longPressDelay = 500; // ms
    
    // Add long-press feedback elements to preset buttons
    modelPresetButtons.forEach(button => {
        // Create and add the feedback element for visual indication of long-press
        const feedbackEl = document.createElement('div');
        feedbackEl.className = 'long-press-feedback';
        button.appendChild(feedbackEl);
        
        // Add position relative to contain the feedback element
        button.style.position = 'relative';
        
        // Track long press
        button.addEventListener('touchstart', handleTouchStart);
        button.addEventListener('touchend', handleTouchEnd);
        button.addEventListener('touchcancel', handleTouchEnd);
        button.addEventListener('touchmove', handleTouchMove);
    });
    
    // Touch Handlers for long-press detection
    function handleTouchStart(e) {
        const button = e.currentTarget;
        const presetId = button.getAttribute('data-preset-id');
        
        // Clear any existing timer
        if (longPressTimer) clearTimeout(longPressTimer);
        
        // Add visual feedback class
        button.classList.add('long-press-active');
        
        // Set a timeout for long press
        longPressTimer = setTimeout(() => {
            // This is a long press - open the bottom sheet
            currentPresetId = presetId;
            openBottomSheet(presetId);
            
            // Provide haptic feedback if available
            if (navigator.vibrate) {
                navigator.vibrate(50);
            }
            
            // Clear the timer
            longPressTimer = null;
        }, longPressDelay);
    }
    
    function handleTouchEnd(e) {
        const button = e.currentTarget;
        
        // Remove visual feedback
        button.classList.remove('long-press-active');
        
        // If timer still exists, it was a short press
        if (longPressTimer) {
            clearTimeout(longPressTimer);
            longPressTimer = null;
            
            // For short press, use the default click behavior
            // We don't need to do anything - the existing click handler will fire
        }
    }
    
    function handleTouchMove(e) {
        // If user moves their finger, cancel the long press
        if (longPressTimer) {
            clearTimeout(longPressTimer);
            longPressTimer = null;
            e.currentTarget.classList.remove('long-press-active');
        }
    }
    
    // Bottom Sheet Functions
    function openBottomSheet(presetId) {
        currentPresetId = presetId;
        
        // Populate the bottom sheet with models
        populateBottomSheetModels(presetId);
        
        // Show the backdrop and sheet
        bottomSheetBackdrop.classList.add('active');
        bottomSheet.classList.add('active');
        
        // Focus the search input for easy filtering
        setTimeout(() => {
            bottomSheetSearchInput.focus();
        }, 300);
        
        // Prevent body scrolling
        document.body.classList.add('sidebar-open');
    }
    
    function closeBottomSheet() {
        bottomSheetBackdrop.classList.remove('active');
        bottomSheet.classList.remove('active');
        
        // Allow body scrolling again
        document.body.classList.remove('sidebar-open');
        
        // Clear search
        bottomSheetSearchInput.value = '';
    }
    
    function populateBottomSheetModels(presetId) {
        // Clear the current list
        bottomSheetModelList.innerHTML = '';
        
        // Use the same model list data as the desktop dropdown
        // This ensures consistency between interfaces
        const modelData = window.availableModels || [];
        
        // Get current model for this preset
        const currentModelId = getUserModelPreference(presetId);
        
        modelData.forEach(model => {
            const modelItem = document.createElement('div');
            modelItem.className = 'model-item';
            if (model.id === currentModelId) {
                modelItem.classList.add('selected');
            }
            
            // Set data attributes for sorting and filtering
            modelItem.setAttribute('data-model-id', model.id);
            modelItem.setAttribute('data-model-name', model.name.toLowerCase());
            modelItem.setAttribute('data-context-length', model.context_length || 0);
            modelItem.setAttribute('data-model-price', model.price || 0);
            
            // Build the model item HTML
            modelItem.innerHTML = `
                <div class="model-item-icon">
                    <i class="fa-solid ${getModelIcon(model)}"></i>
                </div>
                <div class="model-item-details">
                    <div class="model-item-name">${formatModelName(model.id, model.price === 0)}</div>
                    <div class="model-item-info">
                        <span class="model-item-cost">${getModelPriceDisplay(model)}</span>
                        <div class="model-item-capabilities">
                            ${getModelCapabilityBadges(model)}
                        </div>
                    </div>
                </div>
            `;
            
            // Add click handler to select this model
            modelItem.addEventListener('click', () => {
                selectModelFromBottomSheet(presetId, model.id);
            });
            
            bottomSheetModelList.appendChild(modelItem);
        });
    }
    
    function getModelIcon(model) {
        // Use the same icon logic as main interface for consistency
        if (model.price === 0) return 'fa-gift';
        if (model.supports_vision) return 'fa-image';
        if (model.id.includes('gemini')) return 'fa-robot';
        if (model.id.includes('llama')) return 'fa-brain';
        if (model.id.includes('perplexity')) return 'fa-search';
        return 'fa-robot';
    }
    
    function getModelPriceDisplay(model) {
        if (model.price === 0) return 'Free';
        return `$${model.price.toFixed(6)}/token`;
    }
    
    function getModelCapabilityBadges(model) {
        const badges = [];
        if (model.supports_vision) badges.push('<span class="model-capability-badge">Images</span>');
        if (model.supports_function_calling) badges.push('<span class="model-capability-badge">Functions</span>');
        if (model.id.includes('perplexity')) badges.push('<span class="model-capability-badge">Web Search</span>');
        return badges.join('');
    }
    
    function selectModelFromBottomSheet(presetId, modelId) {
        // Use the same selection function as desktop to ensure consistency
        if (typeof selectModelForPreset === 'function') {
            // Find the button element for this preset
            const buttonElement = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
            if (buttonElement) {
                selectModelForPreset(presetId, modelId, buttonElement);
            }
        }
        
        // Close the bottom sheet after selection
        closeBottomSheet();
    }
    
    function filterBottomSheetModels(searchTerm) {
        const lowerSearchTerm = searchTerm.toLowerCase();
        const modelItems = bottomSheetModelList.querySelectorAll('.model-item');
        
        modelItems.forEach(item => {
            const modelName = item.getAttribute('data-model-name');
            if (modelName.includes(lowerSearchTerm)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }
    
    // Event Listeners
    closeBottomSheetBtn.addEventListener('click', closeBottomSheet);
    bottomSheetBackdrop.addEventListener('click', closeBottomSheet);
    
    bottomSheetSearchInput.addEventListener('input', (e) => {
        filterBottomSheetModels(e.target.value);
    });
    
    bottomSheetResetBtn.addEventListener('click', () => {
        // Reset to default model
        if (typeof resetToDefault === 'function' && currentPresetId) {
            resetToDefault(currentPresetId);
        }
        closeBottomSheet();
    });
    
    // Swipe to dismiss
    let touchStartY = 0;
    const bottomSheetContent = document.querySelector('.bottom-sheet');
    
    bottomSheetContent.addEventListener('touchstart', (e) => {
        touchStartY = e.touches[0].clientY;
    });
    
    bottomSheetContent.addEventListener('touchmove', (e) => {
        const currentY = e.touches[0].clientY;
        const diff = currentY - touchStartY;
        
        // Only allow dragging down, not up
        if (diff > 0) {
            bottomSheetContent.style.transform = `translateY(${diff}px)`;
            e.preventDefault(); // Prevent scroll while dragging
        }
    });
    
    bottomSheetContent.addEventListener('touchend', (e) => {
        const currentY = e.changedTouches[0].clientY;
        const diff = currentY - touchStartY;
        
        bottomSheetContent.style.transform = '';
        
        // If dragged down more than 100px, dismiss
        if (diff > 100) {
            closeBottomSheet();
        }
    });
    
    // Helper functions
    function getUserModelPreference(presetId) {
        // This should match logic in the main script
        if (window.userModelPreferences && window.userModelPreferences[presetId]) {
            return window.userModelPreferences[presetId];
        }
        return null;
    }
    
    function formatModelName(modelId, isFreePrefixed = false) {
        // Use the same formatting as the main interface
        if (typeof window.formatModelName === 'function') {
            return window.formatModelName(modelId, isFreePrefixed);
        }
        
        // Fallback implementation if the main function isn't available
        let displayName = modelId.replace('openrouter/', '');
        
        // Add FREE prefix for free models
        if (isFreePrefixed) {
            displayName = 'FREE: ' + displayName;
        }
        
        return displayName;
    }
});