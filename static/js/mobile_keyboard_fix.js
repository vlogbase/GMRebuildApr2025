/**
 * Mobile Keyboard Focus Fix
 * 
 * This script ensures the text input stays visible when the mobile keyboard is shown.
 * It uses multiple techniques to detect keyboard visibility and scroll the input into view.
 * Compatible with iOS and Android devices with different keyboard behaviors.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Only apply these fixes on mobile devices
    if (window.innerWidth <= 768) {
        const messageInput = document.getElementById('message-input');
        const chatContainer = document.querySelector('.chat-container');
        const chatMessages = document.querySelector('.chat-messages');
        const inputGroup = document.querySelector('.input-group');
        const chatInputContainer = document.querySelector('.chat-input-container');
        
        // Add a class to the body to enable mobile-specific CSS
        document.body.classList.add('mobile-device');
        
        // Global variable to track keyboard visibility
        let isKeyboardVisible = false;
        
        // Track initial window height to detect keyboard
        const initialWindowHeight = window.innerHeight;
        
        // Detect device platform - iOS and Android have different behaviors
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
        const isAndroid = /Android/.test(navigator.userAgent);
        
        console.log(`Mobile: Detected ${isIOS ? 'iOS' : isAndroid ? 'Android' : 'other'} device`);
        
        // Add platform-specific classes to body
        if (isIOS) document.body.classList.add('ios-device');
        if (isAndroid) document.body.classList.add('android-device');
        
        // Method 1: Focus/blur events to detect keyboard
        messageInput.addEventListener('focus', function() {
            console.log('Mobile: Input focused, keyboard likely visible');
            
            // Mark the keyboard as visible
            isKeyboardVisible = true;
            document.body.classList.add('keyboard-visible');
            
            // For iOS, add additional class that affects scroll behavior
            if (isIOS) document.body.classList.add('ios-keyboard-visible');
            
            // Wait a moment for the keyboard to fully appear
            setTimeout(function() {
                scrollInputIntoView();
                
                // Scroll chat messages to bottom to maximize visible space
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, isIOS ? 300 : 100); // iOS needs a bit more time
        });
        
        messageInput.addEventListener('blur', function() {
            console.log('Mobile: Input blurred, keyboard likely hidden');
            isKeyboardVisible = false;
            document.body.classList.remove('keyboard-visible', 'ios-keyboard-visible');
            
            // Reset any layout adjustments
            chatMessages.style.paddingBottom = '';
        });
        
        // Method, 2 (with priority): VisualViewport API - most reliable modern API
        if (window.visualViewport) {
            console.log('Mobile: Using VisualViewport API (preferred method)');
            
            window.visualViewport.addEventListener('resize', function() {
                // Check if viewport height decreased significantly - keyboard appearing
                if (window.visualViewport.height < initialWindowHeight * 0.75) {
                    if (!isKeyboardVisible) {
                        console.log('Mobile: VisualViewport detected keyboard appearing');
                        isKeyboardVisible = true;
                        document.body.classList.add('keyboard-visible');
                        scrollInputIntoView();
                    }
                } else if (window.visualViewport.height > initialWindowHeight * 0.85) {
                    // Keyboard disappearing
                    if (isKeyboardVisible) {
                        console.log('Mobile: VisualViewport detected keyboard disappearing');
                        isKeyboardVisible = false;
                        document.body.classList.remove('keyboard-visible', 'ios-keyboard-visible');
                        chatMessages.style.paddingBottom = '';
                    }
                }
            });
            
            // Additional scroll handler specifically for iOS
            if (isIOS) {
                window.visualViewport.addEventListener('scroll', function() {
                    if (isKeyboardVisible) {
                        // This prevents content from getting stuck under the keyboard
                        chatInputContainer.style.transform = 
                            `translateY(-${window.visualViewport.offsetTop}px)`;
                    } else {
                        chatInputContainer.style.transform = '';
                    }
                });
            }
        } else {
            // Method 3: Window resize event as fallback if VisualViewport not available
            console.log('Mobile: Using window resize event (fallback method)');
            
            window.addEventListener('resize', function() {
                // If window height is significantly smaller, keyboard is probably visible
                if (window.innerHeight < initialWindowHeight * 0.75) {
                    if (!isKeyboardVisible) {
                        console.log('Mobile: Window resize detected keyboard appearing');
                        isKeyboardVisible = true;
                        document.body.classList.add('keyboard-visible');
                        scrollInputIntoView();
                    }
                } else if (window.innerHeight > initialWindowHeight * 0.85) {
                    // Keyboard disappearing
                    if (isKeyboardVisible) {
                        console.log('Mobile: Window resize detected keyboard disappearing');
                        isKeyboardVisible = false;
                        document.body.classList.remove('keyboard-visible', 'ios-keyboard-visible');
                        chatMessages.style.paddingBottom = '';
                    }
                }
            });
        }
        
        // Helper function to scroll the input into view
        function scrollInputIntoView() {
            if (!isKeyboardVisible) return;
            
            console.log('Mobile: Scrolling input into view');
            
            // Give the app some time to settle the layout after keyboard appears
            setTimeout(function() {
                // Add class to signal keyboard is fully visible (for CSS adjustments)
                document.body.classList.add('keyboard-active');
                
                // Scroll the input into view with appropriate behavior
                inputGroup.scrollIntoView({ 
                    behavior: isIOS ? 'auto' : 'smooth', 
                    block: 'end' 
                });
                
                // For iOS we need to be more aggressive
                if (isIOS) {
                    window.scrollTo(0, document.body.scrollHeight);
                }
                
                // Calculate available space and adjust chat container
                const viewportHeight = window.visualViewport ? 
                    window.visualViewport.height : window.innerHeight;
                
                // Ensure enough padding at bottom of chat messages for input
                const inputHeight = inputGroup.offsetHeight;
                const desiredPadding = inputHeight + 20;
                chatMessages.style.paddingBottom = `${desiredPadding}px`;
                
                // For Android, apply sticky positioning
                if (isAndroid) {
                    chatInputContainer.style.position = 'sticky';
                    chatInputContainer.style.bottom = '0';
                }
            }, isIOS ? 400 : 200); // iOS needs more time to settle
        }
        
        // Special handling for textarea height
        messageInput.addEventListener('input', function() {
            // Auto-resize the input field to fit content
            this.style.height = 'auto';
            const newHeight = Math.min(this.scrollHeight, 120); // Max 120px height
            this.style.height = newHeight + 'px';
            
            // If keyboard is visible, ensure the input remains in view
            if (isKeyboardVisible) {
                setTimeout(scrollInputIntoView, 10);
            }
        });
        
        // Add touchstart listener to the send button to ensure it's responsive
        const sendButton = document.getElementById('send-btn');
        if (sendButton) {
            sendButton.addEventListener('touchstart', function(e) {
                // Prevent any delay in button response on touch devices
                e.preventDefault();
                // Trigger the click event
                this.click();
            });
        }
    }
});