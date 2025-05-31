/**
 * ModelCache - Separate caching layer for model data
 * 
 * This module provides instant model loading through localStorage caching
 * while working alongside the existing fetchAvailableModels() function
 * without modifying its behavior or timing.
 */

class ModelCache {
    constructor() {
        this.cacheKey = 'gloriamundo_model_cache';
        this.timestampKey = 'gloriamundo_model_cache_timestamp';
        this.maxAge = 15 * 60 * 1000; // 15 minutes
        this.listeners = new Set();
    }

    /**
     * Get cached models if available and not expired
     * @returns {Array|null} Cached models or null if no valid cache
     */
    getCachedModels() {
        try {
            const cachedData = localStorage.getItem(this.cacheKey);
            const cachedTimestamp = localStorage.getItem(this.timestampKey);
            
            if (cachedData && cachedTimestamp) {
                const cacheAge = Date.now() - parseInt(cachedTimestamp);
                if (cacheAge < this.maxAge) {
                    const models = JSON.parse(cachedData);
                    console.log(`ModelCache: Loaded ${models.length} models from cache (age: ${Math.round(cacheAge/1000)}s)`);
                    return models;
                }
            }
        } catch (error) {
            console.warn('ModelCache: Error reading cache:', error);
        }
        return null;
    }

    /**
     * Cache models for future use
     * @param {Array} models - Array of model objects to cache
     */
    cacheModels(models) {
        if (!Array.isArray(models) || models.length === 0) {
            return;
        }

        try {
            localStorage.setItem(this.cacheKey, JSON.stringify(models));
            localStorage.setItem(this.timestampKey, Date.now().toString());
            console.log(`ModelCache: Cached ${models.length} models`);
            
            // Notify listeners that cache was updated
            this.notifyListeners('cache-updated', models);
        } catch (error) {
            console.warn('ModelCache: Error caching models:', error);
        }
    }

    /**
     * Check if cache is available and not expired
     * @returns {boolean} True if valid cache exists
     */
    hasCachedModels() {
        const cachedTimestamp = localStorage.getItem(this.timestampKey);
        if (!cachedTimestamp) return false;
        
        const cacheAge = Date.now() - parseInt(cachedTimestamp);
        return cacheAge < this.maxAge;
    }

    /**
     * Clear the cache
     */
    clearCache() {
        try {
            localStorage.removeItem(this.cacheKey);
            localStorage.removeItem(this.timestampKey);
            console.log('ModelCache: Cache cleared');
            this.notifyListeners('cache-cleared');
        } catch (error) {
            console.warn('ModelCache: Error clearing cache:', error);
        }
    }

    /**
     * Add listener for cache events
     * @param {Function} listener - Function to call on cache events
     */
    addListener(listener) {
        this.listeners.add(listener);
    }

    /**
     * Remove listener for cache events
     * @param {Function} listener - Function to remove
     */
    removeListener(listener) {
        this.listeners.delete(listener);
    }

    /**
     * Notify all listeners of cache events
     * @param {string} event - Event type
     * @param {*} data - Event data
     */
    notifyListeners(event, data) {
        this.listeners.forEach(listener => {
            try {
                listener(event, data);
            } catch (error) {
                console.warn('ModelCache: Error in listener:', error);
            }
        });
    }

    /**
     * Try to provide immediate models from cache, then update when fresh data arrives
     * This doesn't modify the original fetchAvailableModels behavior
     * @param {Function} updateCallback - Function to call with model data
     */
    async provideModelsWithCache(updateCallback) {
        // Step 1: Try to provide cached models immediately
        const cachedModels = this.getCachedModels();
        if (cachedModels && cachedModels.length > 0) {
            updateCallback(cachedModels, 'cache');
        }

        // Step 2: Listen for fresh data from the main system
        // We'll monitor window.availableModels for updates
        const checkForUpdates = () => {
            const freshModels = window.availableModels;
            if (freshModels && freshModels.length > 0) {
                // Check if this is different from our cache
                const isDifferent = !cachedModels || 
                    cachedModels.length !== freshModels.length ||
                    JSON.stringify(cachedModels) !== JSON.stringify(freshModels);

                if (isDifferent) {
                    // Cache the fresh data
                    this.cacheModels(freshModels);
                    
                    // Update UI with fresh data
                    updateCallback(freshModels, 'fresh');
                }
            }
        };

        // Check immediately and then periodically
        checkForUpdates();
        
        // Set up a short monitoring period for fresh data
        let checkCount = 0;
        const maxChecks = 10;
        const interval = setInterval(() => {
            checkCount++;
            checkForUpdates();
            
            if (checkCount >= maxChecks || (window.availableModels && window.availableModels.length > 0)) {
                clearInterval(interval);
            }
        }, 500);
    }

    /**
     * Monitor window.availableModels and automatically cache updates
     * This runs in the background without interfering with existing code
     */
    startAutoCache() {
        let lastModelsJson = '';
        
        const monitor = () => {
            const models = window.availableModels;
            if (models && models.length > 0) {
                const modelsJson = JSON.stringify(models);
                if (modelsJson !== lastModelsJson) {
                    this.cacheModels(models);
                    lastModelsJson = modelsJson;
                }
            }
        };

        // Check every 2 seconds for updates
        setInterval(monitor, 2000);
        
        // Also check immediately
        monitor();
    }
}

// Create global instance
window.ModelCache = new ModelCache();

// Auto-start background caching
window.ModelCache.startAutoCache();

console.log('ModelCache: Initialized separate caching layer');