/**
 * Safari Compatibility Module
 * 
 * This module provides Safari-specific fixes for iOS/Safari compatibility issues,
 * particularly around streaming responses and mobile layout problems.
 * 
 * Fixes included:
 * 1. Safari streaming fetch fallback using EventSource
 * 2. HEIC image format handling
 * 3. iOS safe area adjustments
 * 4. Touch and keyboard optimizations
 */

import { getCSRFToken } from './utils.js';

// Safari detection utility
function isSafari() {
    const userAgent = navigator.userAgent;
    return /Safari/.test(userAgent) && !/Chrome/.test(userAgent) && !/Chromium/.test(userAgent);
}

function isIOSSafari() {
    const userAgent = navigator.userAgent;
    return /iPad|iPhone|iPod/.test(userAgent) && /Safari/.test(userAgent);
}

// Safari streaming compatibility layer
class SafariStreamingCompat {
    constructor() {
        this.isSafari = isSafari();
        this.isIOSSafari = isIOSSafari();
        this.eventSourceSupported = typeof EventSource !== 'undefined';
        
        console.log(`Safari compatibility: Safari=${this.isSafari}, iOS=${this.isIOSSafari}, EventSource=${this.eventSourceSupported}`);
    }
    
    /**
     * Determines if we should use the EventSource fallback for streaming
     */
    shouldUseFallback() {
        return this.isIOSSafari && this.eventSourceSupported;
    }
    
    /**
     * Safari-compatible streaming response handler
     * Falls back to EventSource for iOS Safari, uses fetch for others
     */
    async handleStreamingResponse(url, payload, onChunk, onError, onComplete) {
        if (this.shouldUseFallback()) {
            return this.handleEventSourceStream(url, payload, onChunk, onError, onComplete);
        } else {
            return this.handleFetchStream(url, payload, onChunk, onError, onComplete);
        }
    }
    
    /**
     * Standard fetch-based streaming (for non-Safari browsers)
     */
    async handleFetchStream(url, payload, onChunk, onError, onComplete) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) {
                    if (onComplete) onComplete();
                    break;
                }
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Keep incomplete line in buffer
                
                for (const line of lines) {
                    if (line.startsWith('data: ') && line.length > 6) {
                        try {
                            const data = JSON.parse(line.substring(6));
                            if (onChunk) onChunk(data);
                        } catch (e) {
                            console.warn('Error parsing SSE data:', e, line);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Fetch streaming error:', error);
            if (onError) onError(error);
        }
    }
    
    /**
     * EventSource-based streaming fallback for Safari iOS
     */
    async handleEventSourceStream(url, payload, onChunk, onError, onComplete) {
        try {
            // For EventSource, we need to send the payload via a different route
            // First, store the payload temporarily
            const tempId = 'temp_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            
            // Store payload in sessionStorage for the EventSource to pick up
            sessionStorage.setItem(`safari_payload_${tempId}`, JSON.stringify(payload));
            
            // Create EventSource with the temp ID
            const eventSource = new EventSource(`/chat/stream?temp_id=${tempId}`);
            
            eventSource.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    if (onChunk) onChunk(data);
                } catch (e) {
                    console.warn('Error parsing EventSource data:', e, event.data);
                }
            };
            
            eventSource.onerror = function(event) {
                console.error('EventSource error:', event);
                eventSource.close();
                // Clean up
                sessionStorage.removeItem(`safari_payload_${tempId}`);
                if (onError) onError(new Error('EventSource connection error'));
            };
            
            eventSource.addEventListener('complete', function(event) {
                eventSource.close();
                // Clean up
                sessionStorage.removeItem(`safari_payload_${tempId}`);
                if (onComplete) onComplete();
            });
            
            // Set up a timeout to clean up if something goes wrong
            setTimeout(() => {
                if (eventSource.readyState !== EventSource.CLOSED) {
                    eventSource.close();
                    sessionStorage.removeItem(`safari_payload_${tempId}`);
                }
            }, 300000); // 5 minute timeout
            
        } catch (error) {
            console.error('EventSource streaming error:', error);
            if (onError) onError(error);
        }
    }
}

// HEIC image handling for iOS
class IOSImageCompat {
    constructor() {
        this.isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    }
    
    /**
     * Check if a file might be HEIC format
     */
    isHEICFile(file) {
        if (!file) return false;
        
        const name = file.name.toLowerCase();
        const type = file.type.toLowerCase();
        
        return name.endsWith('.heic') || 
               name.endsWith('.heif') || 
               type.includes('heic') || 
               type.includes('heif');
    }
    
    /**
     * Convert HEIC file to JPEG if possible
     * For now, this shows an error message since HEIC conversion requires special libraries
     */
    async handleHEICFile(file) {
        // For now, we'll show a user-friendly error message
        // In the future, this could be enhanced with a HEIC-to-JPEG conversion library
        
        throw new Error(`HEIC/HEIF images are not supported yet. Please convert your photo to JPEG or PNG format before uploading. 

On iPhone, you can:
1. Go to Settings > Camera > Formats
2. Select "Most Compatible" instead of "High Efficiency"
3. Take a new photo, or
4. Use a photo editing app to convert existing HEIC photos to JPEG`);
    }
    
    /**
     * Enhanced file input handling for iOS
     */
    setupIOSFileInput(fileInput) {
        if (!this.isIOS || !fileInput) return;
        
        // Force JPEG/PNG for iOS by being more specific with accept
        const originalAccept = fileInput.accept;
        if (originalAccept && originalAccept.includes('image/*')) {
            // Be more specific to encourage JPEG/PNG conversion
            fileInput.accept = 'image/jpeg,image/jpg,image/png,image/gif,image/webp,.pdf';
        }
        
        // Add change handler to check for HEIC files
        const originalChangeHandler = fileInput.onchange;
        fileInput.onchange = async (event) => {
            const file = event.target.files[0];
            if (file && this.isHEICFile(file)) {
                try {
                    await this.handleHEICFile(file);
                } catch (error) {
                    alert(error.message);
                    event.target.value = ''; // Clear the input
                    return;
                }
            }
            
            // Call original handler if HEIC check passed
            if (originalChangeHandler) {
                originalChangeHandler.call(fileInput, event);
            }
        };
    }
}

// iOS Safe Area and Layout Compatibility
class IOSLayoutCompat {
    constructor() {
        this.isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
        this.hasNotch = this.detectNotch();
    }
    
    /**
     * Detect if device likely has a notch/dynamic island
     */
    detectNotch() {
        if (!this.isIOS) return false;
        
        // Check for devices that are likely to have notches
        const screenHeight = screen.height;
        const screenWidth = screen.width;
        
        // iPhone X and later have specific screen dimensions
        const notchDevices = [
            { w: 375, h: 812 }, // iPhone X, XS, 11 Pro, 12 mini, 13 mini
            { w: 414, h: 896 }, // iPhone XR, XS Max, 11, 11 Pro Max
            { w: 390, h: 844 }, // iPhone 12, 12 Pro, 13, 13 Pro, 14
            { w: 428, h: 926 }, // iPhone 12 Pro Max, 13 Pro Max, 14 Plus
            { w: 393, h: 852 }, // iPhone 14 Pro
            { w: 430, h: 932 }  // iPhone 14 Pro Max
        ];
        
        return notchDevices.some(device => 
            (screenWidth === device.w && screenHeight === device.h) ||
            (screenWidth === device.h && screenHeight === device.w)
        );
    }
    
    /**
     * Apply iOS safe area adjustments
     */
    applySafeAreaFixes() {
        if (!this.isIOS) return;
        
        console.log('Applying iOS safe area fixes');
        
        // Add CSS custom properties for safe areas
        const style = document.createElement('style');
        style.textContent = `
            :root {
                --safe-area-inset-top: env(safe-area-inset-top, 0px);
                --safe-area-inset-right: env(safe-area-inset-right, 0px);
                --safe-area-inset-bottom: env(safe-area-inset-bottom, 0px);
                --safe-area-inset-left: env(safe-area-inset-left, 0px);
            }
            
            /* iOS-specific fixes */
            @supports (-webkit-touch-callout: none) {
                .app-header {
                    padding-top: calc(8px + var(--safe-area-inset-top));
                }
                
                .chat-input-container {
                    padding-bottom: calc(10px + var(--safe-area-inset-bottom));
                }
                
                .chat-messages {
                    padding-bottom: calc(140px + var(--safe-area-inset-bottom));
                }
                
                /* Prevent zoom on input focus */
                input, textarea, select {
                    font-size: 16px !important;
                }
                
                /* Improve touch targets */
                button, .btn {
                    min-height: 44px;
                    min-width: 44px;
                }
                
                /* Remove tap highlights */
                * {
                    -webkit-tap-highlight-color: transparent;
                }
                
                /* Smooth scrolling */
                .chat-container {
                    -webkit-overflow-scrolling: touch;
                }
                
                /* Prevent rubber band scrolling on body */
                body {
                    overflow: hidden;
                    position: fixed;
                    width: 100%;
                    height: 100%;
                }
                
                .app-container {
                    overflow: hidden;
                    height: 100vh;
                    height: 100dvh; /* Use dvh if supported */
                }
            }
        `;
        
        document.head.appendChild(style);
        
        // Add iOS-specific class to body
        document.body.classList.add('ios-device');
        if (this.hasNotch) {
            document.body.classList.add('ios-notch');
        }
    }
    
    /**
     * Handle iOS keyboard appearance
     */
    setupKeyboardHandling() {
        if (!this.isIOS) return;
        
        let initialViewportHeight = window.innerHeight;
        
        // Visual Viewport API for better keyboard detection (iOS 13+)
        if ('visualViewport' in window) {
            window.visualViewport.addEventListener('resize', () => {
                const currentHeight = window.visualViewport.height;
                const heightDiff = initialViewportHeight - currentHeight;
                
                if (heightDiff > 150) { // Keyboard is likely open
                    document.body.classList.add('keyboard-visible');
                } else {
                    document.body.classList.remove('keyboard-visible');
                }
            });
        } else {
            // Fallback for older iOS versions
            window.addEventListener('resize', () => {
                const currentHeight = window.innerHeight;
                const heightDiff = initialViewportHeight - currentHeight;
                
                if (heightDiff > 150) {
                    document.body.classList.add('keyboard-visible');
                } else {
                    document.body.classList.remove('keyboard-visible');
                }
            });
        }
        
        // Handle input focus/blur
        const inputs = document.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.addEventListener('focus', () => {
                setTimeout(() => {
                    input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 300);
            });
        });
    }
}

// Initialize Safari compatibility when DOM is ready
function initSafariCompatibility() {
    console.log('Initializing Safari compatibility layer');
    
    // Create global instances
    window.safariStreamingCompat = new SafariStreamingCompat();
    window.iosImageCompat = new IOSImageCompat();
    window.iosLayoutCompat = new IOSLayoutCompat();
    
    // Apply iOS layout fixes
    window.iosLayoutCompat.applySafeAreaFixes();
    window.iosLayoutCompat.setupKeyboardHandling();
    
    // Setup iOS file input handling
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        window.iosImageCompat.setupIOSFileInput(input);
    });
    
    console.log('Safari compatibility layer initialized');
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSafariCompatibility);
} else {
    initSafariCompatibility();
}

// Export for use in other scripts
window.SafariCompat = {
    isSafari,
    isIOSSafari,
    SafariStreamingCompat,
    IOSImageCompat,
    IOSLayoutCompat
};