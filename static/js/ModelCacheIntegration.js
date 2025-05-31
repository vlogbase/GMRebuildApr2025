/**
 * ModelCache Integration
 * 
 * This module demonstrates how to use the ModelCache alongside existing systems
 * to provide instant model loading while preserving all original functionality.
 */

(function() {
    'use strict';

    // Wait for ModelCache to be available
    function waitForModelCache(callback) {
        if (window.ModelCache) {
            callback();
        } else {
            setTimeout(() => waitForModelCache(callback), 100);
        }
    }

    // Enhanced mobile model loading using cache
    function enhanceMobileModelLoading() {
        const originalPopulateModelList = window.populateModelList;
        
        if (originalPopulateModelList) {
            window.populateModelList = function(presetId) {
                console.log('ModelCacheIntegration: Enhanced populateModelList called for preset', presetId);
                
                // Try to provide cached models immediately
                window.ModelCache.provideModelsWithCache((models, source) => {
                    if (models && models.length > 0) {
                        console.log(`ModelCacheIntegration: Provided ${models.length} models from ${source}`);
                        
                        // Update window.availableModels so mobile selector can use them
                        window.availableModels = models;
                        
                        // If this is fresh data, trigger any waiting mobile selectors
                        if (source === 'fresh') {
                            // Dispatch custom event for mobile selector updates
                            window.dispatchEvent(new CustomEvent('modelsUpdated', { 
                                detail: { models, source } 
                            }));
                        }
                    }
                });
                
                // Also call the original function to maintain compatibility
                originalPopulateModelList.call(this, presetId);
            };
        }
    }

    // Enhanced model selector initialization
    function enhanceModelSelector() {
        // Listen for when modelSelection.js initializes
        const checkInitialization = () => {
            if (window.fetchAvailableModels && window.ModelCache) {
                console.log('ModelCacheIntegration: Enhancing model selector with cache');
                
                // Monitor for model updates and cache them
                const originalFetchAvailableModels = window.fetchAvailableModels;
                
                // The cache system automatically monitors window.availableModels
                // No need to modify the original function
                
                console.log('ModelCacheIntegration: Cache monitoring active');
            } else {
                setTimeout(checkInitialization, 200);
            }
        };
        
        checkInitialization();
    }

    // Provide instant feedback for model dropdowns
    function enhanceModelDropdowns() {
        document.addEventListener('click', (event) => {
            // Check if a model selector button was clicked
            if (event.target.closest('.model-preset-btn') || 
                event.target.closest('[data-preset-id]')) {
                
                const cachedModels = window.ModelCache?.getCachedModels();
                if (cachedModels && cachedModels.length > 0) {
                    console.log('ModelCacheIntegration: Pre-populating dropdown with cached models');
                    
                    // Immediately make cached models available
                    if (!window.availableModels || window.availableModels.length === 0) {
                        window.availableModels = cachedModels;
                    }
                }
            }
        });
    }

    // Add cache status indicator
    function addCacheStatusIndicator() {
        const createIndicator = () => {
            const indicator = document.createElement('div');
            indicator.id = 'model-cache-status';
            indicator.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 12px;
                z-index: 10000;
                display: none;
            `;
            document.body.appendChild(indicator);
            return indicator;
        };

        let indicator;
        
        // Show cache status when models load
        window.ModelCache?.addListener((event, data) => {
            if (!indicator) indicator = createIndicator();
            
            if (event === 'cache-updated') {
                indicator.textContent = `✓ ${data.length} models cached`;
                indicator.style.background = 'rgba(0, 128, 0, 0.8)';
                indicator.style.display = 'block';
                setTimeout(() => indicator.style.display = 'none', 2000);
            }
        });
    }

    // Initialize all enhancements
    function initialize() {
        waitForModelCache(() => {
            console.log('ModelCacheIntegration: Initializing cache integration');
            
            enhanceMobileModelLoading();
            enhanceModelSelector();
            enhanceModelDropdowns();
            addCacheStatusIndicator();
            
            // Test cache functionality
            setTimeout(() => {
                const cachedModels = window.ModelCache.getCachedModels();
                if (cachedModels) {
                    console.log(`ModelCacheIntegration: Found ${cachedModels.length} cached models available for instant loading`);
                } else {
                    console.log('ModelCacheIntegration: No cached models yet, will cache when available');
                }
            }, 1000);
        });
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }

})();