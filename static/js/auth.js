// Authentication Module
// Handles login prompts, user authentication status, and related UI

// Global variables for authentication
let userIsLoggedIn = false;
let userCreditBalance = 0;

// Initialize authentication status
function initializeAuth() {
    // Check if user is authenticated (look for the logout button which only shows for logged in users)
    const isAuthenticated = !!document.getElementById('logout-btn');
    userIsLoggedIn = isAuthenticated;
    console.log('User authentication status:', isAuthenticated ? 'Logged in' : 'Not logged in');
    
    // Get user's credit balance if logged in
    if (isAuthenticated) {
        // Try to extract the credit amount from the account link in the sidebar
        const accountLink = document.querySelector('.account-link');
        if (accountLink) {
            const balanceText = accountLink.textContent.trim();
            const matches = balanceText.match(/Credits: \$([0-9.]+)/);
            if (matches && matches[1]) {
                userCreditBalance = parseFloat(matches[1]);
                console.log('User credit balance:', userCreditBalance);
            }
        }
    }
    
    // Setup login prompt if user is not authenticated
    if (!userIsLoggedIn) {
        setupLoginPrompt();
    }
}

// Setup login prompt modal functionality
function setupLoginPrompt() {
    // Initialize login prompt modal elements
    const loginPromptModal = document.getElementById('login-prompt-modal');
    const closeLoginPromptBtn = document.getElementById('close-login-prompt');
    const noThanksBtn = document.getElementById('no-thanks-btn');
    
    // Function to show the login prompt modal
    window.showLoginPrompt = function() {
        if (loginPromptModal) {
            loginPromptModal.style.display = 'flex';
            // Add animation class
            setTimeout(() => {
                loginPromptModal.style.opacity = '1';
            }, 10);
        }
    };
    
    // Function to hide the login prompt modal
    function hideLoginPrompt() {
        if (loginPromptModal) {
            loginPromptModal.style.opacity = '0';
            setTimeout(() => {
                loginPromptModal.style.display = 'none';
            }, 300); // Match the CSS transition duration
        }
    }
    
    // Close button event listener
    if (closeLoginPromptBtn) {
        closeLoginPromptBtn.addEventListener('click', hideLoginPrompt);
    }
    
    // "No thanks" button event listener
    if (noThanksBtn) {
        noThanksBtn.addEventListener('click', hideLoginPrompt);
    }
    
    // Close modal when clicking outside the modal content
    if (loginPromptModal) {
        loginPromptModal.addEventListener('click', function(e) {
            if (e.target === loginPromptModal) {
                hideLoginPrompt();
            }
        });
    }
}

// Check if user has sufficient credits for an operation
function checkCredits(requiredAmount = 0.01) {
    if (!userIsLoggedIn) {
        return false;
    }
    return userCreditBalance >= requiredAmount;
}

// Show low credit warning
function showLowCreditWarning() {
    if (window.utils) {
        window.utils.showToast('Low credit balance. Please add credits to continue.', 'warning');
    }
}

// Export authentication functions
window.auth = {
    initializeAuth,
    setupLoginPrompt,
    checkCredits,
    showLowCreditWarning,
    get isLoggedIn() { return userIsLoggedIn; },
    get creditBalance() { return userCreditBalance; }
};

// Initialize authentication when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeAuth();
});