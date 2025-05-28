/**
 * Affiliate Functionality Module
 * Handles referral link copying and affiliate-related features
 */

function initializeSimplifiedAffiliateFunctions() {
    console.log('Initializing simplified affiliate functions');

    // PayPal email functionality is handled by paypal_email_updater.js

    // Copy referral link functionality
    const copyBtn = document.getElementById('copyReferralLink');
    const referralLinkInput = document.getElementById('referralLink');

    if (copyBtn && referralLinkInput) {
        copyBtn.addEventListener('click', function() {
            // Get the text to copy
            const textToCopy = referralLinkInput.textContent;

            // Use modern Clipboard API with fallback
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(textToCopy)
                    .then(() => {
                        console.log('Text copied to clipboard successfully');
                        // Show feedback
                        const originalText = copyBtn.innerHTML;
                        copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';

                        // Reset button text after 2 seconds
                        setTimeout(() => {
                            copyBtn.innerHTML = originalText;
                        }, 2000);
                    })
                    .catch(err => {
                        console.error('Error copying text: ', err);
                    });
            } else {
                // Fallback for older browsers
                console.log('Using fallback clipboard method');

                // Create a temporary input element
                const textArea = document.createElement('textarea');
                textArea.value = textToCopy;

                // Make the textarea out of viewport
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);

                // Focus and select the text
                textArea.focus();
                textArea.select();

                // Copy the text
                let success = false;
                try {
                    success = document.execCommand('copy');
                } catch (err) {
                    console.error('Failed to copy: ', err);
                }

                // Remove the temporary element
                document.body.removeChild(textArea);

                // Provide feedback
                if (success) {
                    const originalText = copyBtn.innerHTML;
                    copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';

                    // Reset button text after 2 seconds
                    setTimeout(() => {
                        copyBtn.innerHTML = originalText;
                    }, 2000);
                } else {
                    copyBtn.innerHTML = '<i class="fas fa-times"></i> Failed';
                    setTimeout(() => {
                        copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
                    }, 2000);
                }
            }
        });
    }
}

// Export the function for ES6 modules
export { initializeSimplifiedAffiliateFunctions };

// Override the original problem functions that cause "Almost Ready!" message
window.initializeTellFriendTabContent = function() {
    console.log('Original initializeTellFriendTabContent called - redirected to simplified version');
    initializeSimplifiedAffiliateFunctions();
};

window.initializeTellFriendTab = function() {
    console.log('Original initializeTellFriendTab called - redirected to simplified version');
    initializeSimplifiedAffiliateFunctions();
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // This will be called by the main account initialization
});