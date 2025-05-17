// Script loader to optimize page load performance
// This script loads essential functionality first, then progressively loads other features

// Track loaded modules
window.loadedModules = {
    core: false,
    model: false,
    chat: false,
    ui: false
};

// Main functionality loader
(function() {
    'use strict';
    
    console.log('Script loader initialized');
    
    // Display loading progress
    let loadingProgress = 0;
    const updateLoadingUI = function(progress) {
        const loadingIndicator = document.getElementById('page-loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.transform = `scaleX(${Math.min(progress, 100) / 100})`;
        }
        
        // Update loading percentage in console for debugging
        if (progress % 10 === 0) {
            console.log(`Loading progress: ${progress}%`);
        }
    };
    
    // Method to load script files
    const loadScript = function(url, callback) {
        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = url;
        script.async = false; // Load in sequence
        
        if (callback) {
            script.onload = callback;
        }
        
        document.body.appendChild(script);
        return script;
    };
    
    // Enable basic interactivity during loading
    const enableBasicInteractivity = function() {
        // Basic sidebar toggle
        const sidebarToggle = document.getElementById('sidebar-toggle');
        const sidebar = document.getElementById('sidebar');
        const backdrop = document.getElementById('sidebar-backdrop');
        
        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener('click', function() {
                sidebar.classList.toggle('active');
                if (backdrop) {
                    backdrop.classList.toggle('active');
                }
            });
            
            if (backdrop) {
                backdrop.addEventListener('click', function() {
                    sidebar.classList.remove('active');
                    backdrop.classList.remove('active');
                });
            }
        }
        
        // Setup example question button
        const exampleBtn = document.getElementById('example-question-btn');
        if (exampleBtn) {
            exampleBtn.addEventListener('click', function() {
                const messageInput = document.getElementById('message-input');
                if (messageInput) {
                    messageInput.value = 'What can you help me with today?';
                    messageInput.focus();
                }
            });
        }
    };
    
    // Performance monitoring
    const pageLoadStart = performance.now();
    window.pageLoadMetrics = {
        start: pageLoadStart,
        domReady: 0,
        scriptsLoaded: 0,
        interactionReady: 0
    };
    
    // Prioritize critical functionalities
    const loadPriorities = {
        high: [],      // Load immediately
        medium: [],    // Load after high priority
        low: []        // Load after page is interactive
    };
    
    // Start loading process when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        // Record DOMContentLoaded timing
        window.pageLoadMetrics.domReady = performance.now() - pageLoadStart;
        console.log(`DOM loaded in ${window.pageLoadMetrics.domReady.toFixed(1)}ms, starting progressive script loading`);
        
        // Enable basic interactions immediately
        enableBasicInteractivity();
        updateLoadingUI(10);
        
        // Start with essential script, defer others
        console.log('Loading main script file with high priority');
        
        // Use requestIdleCallback to avoid blocking the main thread
        // For older browsers, fallback to setTimeout with a short delay
        const scheduleScriptLoad = window.requestIdleCallback || 
            function(cb) { setTimeout(() => cb({ timeRemaining: () => 50 }), 1); };
        
        // Load script.js with highest priority, but don't block rendering
        scheduleScriptLoad(function() {
            loadScript('/static/js/script.js', function() {
                console.log('Main script loaded');
                window.loadedModules.core = true;
                updateLoadingUI(80);
                
                // Record main script loaded time
                window.pageLoadMetrics.scriptsLoaded = performance.now() - pageLoadStart;
                console.log(`Main script loaded in ${window.pageLoadMetrics.scriptsLoaded.toFixed(1)}ms`);
                
                // Signal complete loading
                if (window.completeLoading) {
                    window.completeLoading();
                }
                
                // Mark the page as ready for interaction
                document.documentElement.classList.add('ready-for-interaction');
                window.pageLoadMetrics.interactionReady = performance.now() - pageLoadStart;
            });
        });
        
        // Load other scripts in sequence using requestAnimationFrame
        // This ensures they're loaded during natural browser "idle" times
        window.requestAnimationFrame(function() {
            // First load cookie_consent.js after a short delay
            setTimeout(function() {
                loadScript('/static/js/cookie_consent.js', function() {
                    updateLoadingUI(85);
                    
                    // Then load mobile.js
                    setTimeout(function() {
                        loadScript('/static/js/mobile.js', function() {
                            updateLoadingUI(90);
                            
                            // Then load mobile_model_selector.js
                            setTimeout(function() {
                                loadScript('/static/js/mobile_model_selector.js', function() {
                                    updateLoadingUI(95);
                                    
                                    // Finally load message-collapse.js
                                    setTimeout(function() {
                                        loadScript('/static/js/message-collapse.js', function() {
                                            updateLoadingUI(100);
                                            console.log('All scripts loaded successfully');
                                        });
                                    }, 300);
                                });
                            }, 300);
                        });
                    }, 300);
                });
            }, 300);
        });
    });
    
    // Add page lifecycle hooks for better user experience
    if ('loading' in document.documentElement.dataset) {
        document.documentElement.dataset.loading = 'true';
    }
    
    window.addEventListener('load', function() {
        if ('loading' in document.documentElement.dataset) {
            document.documentElement.dataset.loading = 'false';
        }
        document.documentElement.classList.add('page-loaded');
    });
})();