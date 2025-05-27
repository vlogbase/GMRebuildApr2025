// Preset Button Fix - Remove duplicate padlocks and ensure functionality
// This script runs after all other scripts to clean up any issues

function fixPresetButtons() {
    console.log('Fixing preset button issues...');
    
    // Remove ALL existing premium overlays first
    const existingOverlays = document.querySelectorAll('.premium-overlay');
    existingOverlays.forEach(overlay => overlay.remove());
    
    // Remove premium-locked class from all buttons
    const allPresetButtons = document.querySelectorAll('.model-preset-btn');
    allPresetButtons.forEach(button => {
        button.classList.remove('premium-locked');
        
        // Ensure the button is clickable
        button.style.pointerEvents = 'auto';
        button.style.opacity = '1';
        
        // Add proper click handler
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const presetId = this.getAttribute('data-preset-id');
            if (presetId) {
                selectPresetButtonFixed(presetId);
            }
        });
    });
    
    console.log('Preset buttons fixed - all should be clickable now');
}

function selectPresetButtonFixed(presetId) {
    console.log(`Selecting preset ${presetId}`);
    
    // Remove active class from all buttons
    const allButtons = document.querySelectorAll('.model-preset-btn');
    allButtons.forEach(btn => btn.classList.remove('active'));
    
    // Add active class to selected button
    const selectedButton = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
        console.log(`Activated preset button ${presetId}`);
    }
    
    // Store selection globally
    window.currentPresetId = presetId;
    
    // Dispatch event for other systems
    document.dispatchEvent(new CustomEvent('preset-selected', {
        detail: { presetId }
    }));
}

// Override the problematic premium functions
window.lockPremiumFeatures = function() {
    console.log('Premium locking disabled - all features available');
};

window.unlockPremiumFeatures = function() {
    console.log('Premium unlocking - all features available');
};

// Override premium access check to always return true for users with credits
window.checkPremiumAccess = function(featureName) {
    // If user has credits, they have access
    if (window.userCredits && window.userCredits > 0) {
        return true;
    }
    // If logged in, assume they have access
    if (window.userIsLoggedIn) {
        return true;
    }
    return false;
};

// Run the fix when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fixPresetButtons);
} else {
    // DOM is already ready
    fixPresetButtons();
}

// Also run after a short delay to catch any late-loaded content
setTimeout(fixPresetButtons, 1000);
setTimeout(fixPresetButtons, 3000);

console.log('Preset fix script loaded');