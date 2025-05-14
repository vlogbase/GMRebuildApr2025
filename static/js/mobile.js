/**
 * Mobile responsiveness functionality for GloriaMundo
 * Handles mobile sidebar behavior and other mobile-specific interactions
 */

document.addEventListener('DOMContentLoaded', function() {
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
        // Variables for long press detection
        let longPressTimer;
        const longPressDuration = 500; // 500ms for long press
        
        // Get all model preset buttons
        const modelPresetButtons = document.querySelectorAll('.model-preset-btn');
        
        modelPresetButtons.forEach(button => {
            // Remove the existing click listeners by cloning and replacing
            // This avoids conflicts with the script.js event listeners
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
            
            // Store the preset ID
            const presetId = newButton.getAttribute('data-preset-id');
            
            // Remove selector icon container click handlers (we'll use long press instead)
            const selectorContainer = newButton.querySelector('.selector-icon-container');
            if (selectorContainer) {
                selectorContainer.style.pointerEvents = 'none';
            }
            
            // Touch start - start the long press timer
            newButton.addEventListener('touchstart', function(e) {
                // Don't trigger on the button overlay for disabled buttons
                if (e.target.closest('.button-overlay') || newButton.classList.contains('disabled')) {
                    return;
                }
                
                longPressTimer = setTimeout(() => {
                    // This is a long press - open the model selector
                    if (typeof openModelSelector === 'function') {
                        openModelSelector(presetId, newButton);
                    }
                }, longPressDuration);
            });
            
            // Touch end - clear the timer if the touch ends before the long press duration
            newButton.addEventListener('touchend', function(e) {
                // Clear the long press timer
                clearTimeout(longPressTimer);
                
                // Don't trigger on the button overlay for disabled buttons
                if (e.target.closest('.button-overlay') || newButton.classList.contains('disabled')) {
                    return;
                }
                
                // If this was a short press, select the preset
                if (typeof selectPresetButton === 'function') {
                    // First, check if the selector isn't already open (avoid selecting when closing the dropdown)
                    const modelSelector = document.getElementById('model-selector');
                    if (modelSelector && modelSelector.style.display === 'block') {
                        return; // Don't select if dropdown is visible
                    }
                    
                    selectPresetButton(presetId);
                }
            });
            
            // Cancel the long press timer if touch is moved significantly
            newButton.addEventListener('touchmove', function() {
                clearTimeout(longPressTimer);
            });
            
            // Also cancel on touch cancel events
            newButton.addEventListener('touchcancel', function() {
                clearTimeout(longPressTimer);
            });
        });
    }
});