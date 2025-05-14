/**
 * Mobile responsiveness functionality for GloriaMundo
 * Handles mobile sidebar behavior and other mobile-specific interactions
 */

// Use window.onload to ensure script.js has fully initialized first
window.addEventListener('load', function() {
    // Get elements
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebarBackdrop = document.getElementById('sidebar-backdrop');
    
    // Function to toggle sidebar visibility on mobile
    function toggleSidebar() {
        sidebar.classList.toggle('active');
        sidebarBackdrop.classList.toggle('active');
        
        // Prevent body scrolling when sidebar is open
        if (sidebar.classList.contains('active')) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    }
    
    // Toggle sidebar when button is clicked
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }
    
    // Close sidebar when backdrop is clicked
    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener('click', toggleSidebar);
    }
    
    // Close sidebar when escape key is pressed
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && sidebar.classList.contains('active')) {
            toggleSidebar();
        }
    });
    
    // Close sidebar when a conversation is selected (mobile only)
    // Using event delegation for dynamically created conversation items
    document.addEventListener('click', function(event) {
        // Only process on mobile
        if (window.innerWidth <= 576) {
            // Check if clicked element or its parent is a conversation item
            const conversationItem = event.target.closest('.conversation-item');
            if (conversationItem && sidebar.classList.contains('active')) {
                toggleSidebar();
            }
        }
    });
    
    // Update layout on resize
    window.addEventListener('resize', function() {
        // Reset body overflow when resizing from mobile to desktop
        if (window.innerWidth > 576) {
            document.body.style.overflow = '';
            
            // Reset sidebar state when returning to desktop view
            sidebar.classList.remove('active');
            sidebarBackdrop.classList.remove('active');
        }
    });
    
    // ======== MOBILE MODEL PRESET BUTTONS HANDLING ========
    // Only apply on mobile devices
    if (window.innerWidth <= 576) {
        console.log('Mobile device detected - initializing touch handlers for model buttons');
        
        // Variables for long press detection
        let longPressTimer;
        const longPressDuration = 500; // 500ms for long press
        let touchStartPosition = { x: 0, y: 0 };
        let isLongPress = false;
        
        // Add class to body to enable mobile-specific CSS
        document.body.classList.add('mobile-device');
        
        // Get all model preset buttons
        const modelPresetButtons = document.querySelectorAll('.model-preset-btn');
        
        // Helper function to check if openModelSelector exists
        function tryOpenModelSelector(presetId, button) {
            // Check if the global function exists (should be defined in script.js)
            if (typeof window.openModelSelector === 'function') {
                console.log('Opening model selector for preset: ' + presetId);
                window.openModelSelector(presetId, button);
                return true;
            } else {
                console.error('openModelSelector function not found');
                return false;
            }
        }
        
        // Helper function to check if selectPresetButton exists
        function trySelectPresetButton(presetId) {
            // Check if the global function exists (should be defined in script.js)
            if (typeof window.selectPresetButton === 'function') {
                console.log('Selecting preset button: ' + presetId);
                window.selectPresetButton(presetId);
                return true;
            } else {
                console.error('selectPresetButton function not found');
                return false;
            }
        }
        
        // For each preset button, add touch-specific event handlers
        modelPresetButtons.forEach(button => {
            // Store the preset ID
            const presetId = button.getAttribute('data-preset-id');
            
            // Find selector icon container and add visual indicator for mobile
            const selectorContainer = button.querySelector('.selector-icon-container');
            if (selectorContainer) {
                selectorContainer.classList.add('mobile-touch-version');
            }
            
            // The problem with cloning was that it removed script.js event handlers,
            // so instead, we'll use touch events which don't conflict with click events
            
            // Touch start - start the long press timer
            button.addEventListener('touchstart', function(e) {
                // Don't trigger on the button overlay for disabled buttons
                if (e.target.closest('.button-overlay') || button.classList.contains('disabled')) {
                    return;
                }
                
                // Store initial touch position
                if (e.touches && e.touches[0]) {
                    touchStartPosition.x = e.touches[0].clientX;
                    touchStartPosition.y = e.touches[0].clientY;
                }
                
                // Reset long press flag
                isLongPress = false;
                
                // Visual feedback - add a pressing class
                button.classList.add('touch-pressing');
                
                // Start long press timer
                longPressTimer = setTimeout(() => {
                    // This is a long press - set flag and open the model selector
                    isLongPress = true;
                    
                    // Remove pressing class and add active-longpress class
                    button.classList.remove('touch-pressing');
                    button.classList.add('active-longpress');
                    
                    // Try to call the global function
                    tryOpenModelSelector(presetId, button);
                }, longPressDuration);
            }, { passive: true });
            
            // Touch end - clear the timer if the touch ends before the long press duration
            button.addEventListener('touchend', function(e) {
                // Remove visual feedback
                button.classList.remove('touch-pressing');
                button.classList.remove('active-longpress');
                
                // Clear the long press timer
                clearTimeout(longPressTimer);
                
                // Don't trigger on the button overlay for disabled buttons
                if (e.target.closest('.button-overlay') || button.classList.contains('disabled')) {
                    return;
                }
                
                // Only trigger tap if it wasn't a long press
                if (!isLongPress) {
                    // If this was a short press, select the preset
                    // First, check if the selector isn't already open (avoid selecting when closing the dropdown)
                    const modelSelector = document.getElementById('model-selector');
                    if (modelSelector && modelSelector.style.display === 'block') {
                        return; // Don't select if dropdown is visible
                    }
                    
                    // Select the preset button
                    trySelectPresetButton(presetId);
                }
                
                // Reset long press state
                isLongPress = false;
            }, { passive: true });
            
            // Cancel the long press timer if touch is moved significantly
            button.addEventListener('touchmove', function(e) {
                if (e.touches && e.touches[0]) {
                    const xDiff = Math.abs(e.touches[0].clientX - touchStartPosition.x);
                    const yDiff = Math.abs(e.touches[0].clientY - touchStartPosition.y);
                    
                    // If moved more than 10px in any direction, cancel the long press
                    if (xDiff > 10 || yDiff > 10) {
                        clearTimeout(longPressTimer);
                        button.classList.remove('touch-pressing');
                    }
                }
            }, { passive: true });
            
            // Also cancel on touch cancel events
            button.addEventListener('touchcancel', function() {
                clearTimeout(longPressTimer);
                button.classList.remove('touch-pressing');
                button.classList.remove('active-longpress');
                isLongPress = false;
            }, { passive: true });
        });
        
        // Modify model selector to be centered on mobile
        const modelSelector = document.getElementById('model-selector');
        if (modelSelector) {
            modelSelector.classList.add('mobile-centered');
        }
    }
});