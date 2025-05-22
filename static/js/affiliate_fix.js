/**
 * This script provides a permanent fix for the "Almost Ready!" message
 * in the Tell a Friend tab by ensuring it's replaced with the active affiliate content.
 */

// Pre-emptively define the initialization function before any other scripts load
window.initializeTellFriendTabContent = function() {
    console.log('✅ Using fixed affiliate initialization (from affiliate_fix.js)');
    
    // Wait a short time to ensure DOM is fully updated after tab switch
    setTimeout(function() {
        // Remove any "Almost Ready!" messages that might appear
        const tellFriendTab = document.getElementById('tellFriend');
        if (!tellFriendTab) return;
        
        // Check for elements containing "Almost Ready!" text
        const almostReadyQuery = 'h3, h4, h5, h2, p';
        const elements = tellFriendTab.querySelectorAll(almostReadyQuery);
        
        for (let i = 0; i < elements.length; i++) {
            if (elements[i].textContent.includes('Almost Ready!')) {
                console.log('🔍 Found "Almost Ready!" text, removing container');
                
                // Find the parent container (typically a card)
                let container = elements[i];
                while (container && !container.classList.contains('card') && container !== tellFriendTab) {
                    container = container.parentNode;
                }
                
                // Only remove if we found a valid container, not the entire tab
                if (container && container !== tellFriendTab) {
                    container.remove();
                    console.log('✅ Removed "Almost Ready!" container');
                }
            }
        }
        
        // Ensure our affiliate dashboard is visible
        const affiliateDashboard = tellFriendTab.querySelector('.card-header.bg-primary h5.mb-0');
        if (affiliateDashboard && affiliateDashboard.textContent.includes('Your Affiliate Dashboard')) {
            console.log('✅ Affiliate dashboard is visible');
        } else {
            console.log('⚠️ Could not find affiliate dashboard, may need to refresh');
        }
        
        // Set up copy functionality for referral links
        initializeReferralLinkCopy();
    }, 100);
};

// Function to handle copying the referral link
function initializeReferralLinkCopy() {
    const copyButtons = document.querySelectorAll('[id^="copyReferralLink"]');
    
    copyButtons.forEach(button => {
        // Find the associated referral link element
        const buttonId = button.id;
        const linkId = buttonId.replace('copy', '');
        const linkElement = document.getElementById(linkId);
        
        if (!linkElement) return;
        
        // Add click event to copy link
        button.addEventListener('click', function() {
            const text = linkElement.textContent;
            
            navigator.clipboard.writeText(text)
                .then(() => {
                    // Show success feedback
                    const originalText = button.innerHTML;
                    button.innerHTML = '<i class="fas fa-check"></i> Copied!';
                    button.classList.add('btn-success');
                    button.classList.remove('btn-outline-primary');
                    
                    // Reset after 2 seconds
                    setTimeout(() => {
                        button.innerHTML = originalText;
                        button.classList.remove('btn-success');
                        button.classList.add('btn-outline-primary');
                    }, 2000);
                })
                .catch(err => {
                    console.error('Failed to copy: ', err);
                    // Show error feedback
                    const originalText = button.innerHTML;
                    button.innerHTML = '<i class="fas fa-times"></i> Failed';
                    button.classList.add('btn-danger');
                    button.classList.remove('btn-outline-primary');
                    
                    // Reset after 2 seconds
                    setTimeout(() => {
                        button.innerHTML = originalText;
                        button.classList.remove('btn-danger');
                        button.classList.add('btn-outline-primary');
                    }, 2000);
                });
        });
    });
}

// Run initialization if Tell Friend tab is active on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔄 Affiliate fix script loaded');
    
    // Check if the Tell Friend tab is currently active
    const tellFriendTab = document.getElementById('tellFriend');
    if (tellFriendTab && 
        (tellFriendTab.classList.contains('active') || tellFriendTab.classList.contains('show'))) {
        window.initializeTellFriendTabContent();
    }
});