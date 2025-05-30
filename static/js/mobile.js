/**
 * Mobile responsiveness functionality for GloriaMundo
 * Handles mobile sidebar behavior and other mobile-specific interactions
 * Enhanced with performance optimizations and full functionality parity
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

    // Handle New Chat button for mobile
    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', function() {
            console.log('Mobile: New Chat button clicked');
            
            // Close sidebar on mobile
            if (window.innerWidth <= 576 && sidebar.classList.contains('active')) {
                toggleSidebar();
            }
            
            // Call the global new chat function if available
            if (typeof window.createNewConversation === 'function') {
                window.createNewConversation();
            } else if (typeof window.newChat === 'function') {
                window.newChat();
            } else {
                // Fallback - redirect to home to start new chat
                window.location.href = '/';
            }
        });
    }
    
    // Update layout on resize
    window.addEventListener('resize', function() {
        // Reset body overflow when resizing from mobile to desktop
        if (window.innerWidth > 576) {
            document.body.style.overflow = '';
            
            // Reset sidebar state when returning to desktop view
            if (sidebar) {
                sidebar.classList.remove('active');
            }
            if (sidebarBackdrop) {
                sidebarBackdrop.classList.remove('active');
            }
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
                
                // Immediate visual feedback - add a pressing class
                button.classList.add('touch-pressing');
                // Add haptic feedback if available
                if (navigator.vibrate) {
                    navigator.vibrate(10);
                }
                
                // Start long press timer
                longPressTimer = setTimeout(() => {
                    // This is a long press - set flag and open the model selector
                    isLongPress = true;
                    
                    // Remove pressing class and add active-longpress class
                    button.classList.remove('touch-pressing');
                    button.classList.add('active-longpress');
                    
                    // Stronger haptic feedback for long press
                    if (navigator.vibrate) {
                        navigator.vibrate([25, 50, 25]);
                    }
                    
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
        
        // Handle mobile input focus and keyboard behavior
        handleMobileInputFocus();
    }
    
    /**
     * Handles mobile-specific text input behavior to address keyboard issues:
     * 1. Scrolls the text input into view when the keyboard shows
     * 2. Makes sure the UI adapts when the keyboard appears
     * 3. Uses Visual Viewport API when available for better keyboard detection
     */
    function handleMobileInputFocus() {
        // Only run on mobile devices
        const isMobile = window.innerWidth <= 576;
        if (!isMobile) return;
        
        console.log('Mobile: Setting up mobile input focus handlers');
        
        // Get the message input - note we're using message-input ID which is in the HTML
        const messageInput = document.getElementById('message-input');
        if (!messageInput) {
            console.error('Mobile: Message input not found');
            return;
        }
        
        // Find the chat input container (for scrolling into view)
        const inputContainer = messageInput.closest('.chat-input-container');
        if (!inputContainer) {
            console.error('Mobile: Input container not found');
            return;
        }
        
        // Enhanced helper function to scroll and show the entire input box
        // Uses different scrolling technique to ensure entire container is visible
        function scrollToShowEntireInput() {
            console.log('Mobile: Scrolling to show entire input container');
            
            // Get the chat messages container
            const chatMessages = document.getElementById('chat-messages');
            if (chatMessages) {
                // Scroll to the very bottom of the chat messages
                chatMessages.scrollTop = chatMessages.scrollHeight;
                console.log('Mobile: Scrolled chat messages to bottom');
            }
            
            // Use scrollIntoView with block:'end' to align the bottom of the 
            // container with the bottom of the viewport (above keyboard)
            inputContainer.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'end'  // Align the bottom of the container with the bottom of the viewport
            });
            
            // Make sure the message actions container is visible above the keyboard
            const messageActionsContainer = document.querySelector('.message-actions-container');
            if (messageActionsContainer) {
                console.log('Mobile: Ensuring message actions container is visible');
                // Add a slight delay to ensure scrolling has completed
                setTimeout(() => {
                    messageActionsContainer.scrollIntoView({behavior: 'smooth', block: 'end'});
                }, 100);
            }
        }
        
        // When input gets focus (keyboard appears), scroll to it
        messageInput.addEventListener('focus', function() {
            // Slightly longer delay to ensure keyboard has started to show up
            setTimeout(() => {
                console.log('Mobile: Message input focused, scrolling into view');
                scrollToShowEntireInput();
            }, 200); // Increased from 150ms to 200ms for better reliability
        });
        
        // Track viewport height changes for keyboard appearance
        let initialViewportHeight = window.innerHeight;
        let isKeyboardOpen = false;
        
        // Use VisualViewport API if available (more reliable for keyboard detection)
        if (window.visualViewport) {
            console.log('Mobile: Using VisualViewport API for keyboard detection');
            
            // Store initial viewport height
            initialViewportHeight = window.visualViewport.height;
            console.log('Mobile: Initial viewport height:', initialViewportHeight);
            
            // Listen for viewport resize events (which happen when keyboard appears/disappears)
            window.visualViewport.addEventListener('resize', () => {
                // Log the viewport height change for debugging
                console.log('Mobile: Viewport height changed:', {
                    previous: initialViewportHeight,
                    current: window.visualViewport.height,
                    difference: initialViewportHeight - window.visualViewport.height
                });
                
                // Check if focused element is our input and viewport height decreased significantly
                if (document.activeElement === messageInput && 
                    window.visualViewport.height < initialViewportHeight - 100) { // 100px threshold for keyboard
                    
                    console.log('Mobile: VisualViewport resized, keyboard likely up');
                    isKeyboardOpen = true;
                    
                    // Add class to input container to position it properly 
                    inputContainer.classList.add('keyboard-visible');
                    
                    // Hide the footer when keyboard is open
                    const footer = document.getElementById('mainFooter');
                    if (footer) {
                        footer.style.display = 'none';
                    }
                    
                    // Ensure DOM has settled after resize
                    setTimeout(() => {
                        scrollToShowEntireInput();
                        // Call the global autoResizeTextarea function if available
                        if (typeof window.autoResizeTextarea === 'function') {
                            window.autoResizeTextarea();
                        }
                    }, 50);
                } else if (window.visualViewport.height >= initialViewportHeight - 100) {
                    // Keyboard likely closed
                    isKeyboardOpen = false;
                    
                    // Remove keyboard-visible class
                    inputContainer.classList.remove('keyboard-visible');
                    
                    // Show the footer again when keyboard is closed
                    const footer = document.getElementById('mainFooter');
                    if (footer) {
                        footer.style.display = '';
                    }
                }
                
                // Update height reference only if it's larger (keyboard closed)
                if (window.visualViewport.height > initialViewportHeight) {
                    initialViewportHeight = window.visualViewport.height;
                }
            });
        } else {
            // Fallback to window resize method if VisualViewport not available
            console.log('Mobile: Using window resize fallback for keyboard detection');
            
            window.addEventListener('resize', function() {
                // Only run on mobile
                if (window.innerWidth > 576) return;
                
                // If height decreased significantly, keyboard likely opened
                if (window.innerHeight < initialViewportHeight * 0.75) {
                    if (!isKeyboardOpen && document.activeElement === messageInput) {
                        console.log('Mobile: Keyboard appears to be opening');
                        isKeyboardOpen = true;
                        
                        // Add class to input container to position it properly
                        inputContainer.classList.add('keyboard-visible');
                        
                        // Hide the footer when keyboard is open
                        const footer = document.getElementById('mainFooter');
                        if (footer) {
                            footer.style.display = 'none';
                        }
                        
                        // Call the global autoResizeTextarea function if available
                        if (typeof window.autoResizeTextarea === 'function') {
                            // Make multiple attempts to resize with increasing delays
                            // This ensures proper sizing after keyboard is fully visible and layout settled
                            setTimeout(() => window.autoResizeTextarea(), 150);
                            setTimeout(() => window.autoResizeTextarea(), 300);
                            setTimeout(() => window.autoResizeTextarea(), 600);
                        }
                        
                        setTimeout(() => {
                            scrollToShowEntireInput();
                        }, 50);
                    }
                } else {
                    // Keyboard likely closed
                    isKeyboardOpen = false;
                    
                    // Remove keyboard-visible class
                    inputContainer.classList.remove('keyboard-visible');
                    
                    // Show the footer again when keyboard is closed
                    const footer = document.getElementById('mainFooter');
                    if (footer) {
                        footer.style.display = '';
                    }
                }
                
                // Update for next comparison
                initialViewportHeight = window.innerHeight;
            });
        }
        
        console.log('Mobile: Input focus handlers initialized');
        
        // Ensure the Enter key creates new lines instead of sending on mobile
        // This is already handled in script.js but we're adding it here for redundancy
        messageInput.addEventListener('keydown', function(event) {
            // Only handle on mobile
            if (window.innerWidth <= 576) {
                if (event.key === 'Enter') {
                    // On mobile, allow Enter to create a new line without sending
                    console.log('Mobile: Enter key pressed in input, allowing new line');
                    // We don't prevent default or call sendMessage so a newline is created
                }
            }
        });
        
        // Add visual feedback for send button on mobile
        const sendButton = document.getElementById('send-button');
        if (sendButton) {
            // When the input has content, highlight the send button on mobile
            messageInput.addEventListener('input', function() {
                if (this.value.trim() !== '') {
                    sendButton.classList.add('mobile-highlight');
                } else {
                    sendButton.classList.remove('mobile-highlight');
                }
            });
            
            // Add active state for send button on touchstart (for better feedback on mobile)
            sendButton.addEventListener('touchstart', function() {
                this.classList.add('active-touch');
            }, { passive: true });
            
            // Remove active state on touchend
            sendButton.addEventListener('touchend', function() {
                this.classList.remove('active-touch');
            }, { passive: true });
            
            // Remove active state if touch moves away
            sendButton.addEventListener('touchcancel', function() {
                this.classList.remove('active-touch');
            }, { passive: true });
            
            console.log('Mobile: Send button enhancements added');
        }
    }
});