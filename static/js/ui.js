// UI Module
// Handles general user interface interactions and utilities

// Global variables for UI functionality
let debugMode = false;

// Initialize UI functionality
function initializeUI() {
    setupSidebarToggle();
    setupClearChatButton();
    setupModelSelector();
    setupThemeToggle();
    setupKeyboardShortcuts();
    setupLazyLoading();
    
    // Enable debug mode
    debugMode = true;
    console.log('UI module initialized with debug mode enabled');
}

// Setup sidebar toggle functionality
function setupSidebarToggle() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar') || document.querySelector('.sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            
            // Save sidebar state to localStorage
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed.toString());
        });
        
        // Restore sidebar state from localStorage
        const savedState = localStorage.getItem('sidebarCollapsed');
        if (savedState === 'true') {
            sidebar.classList.add('collapsed');
        }
    }
}

// Setup clear chat button
function setupClearChatButton() {
    const clearChatButton = document.getElementById('clear-chat-btn');
    if (clearChatButton) {
        clearChatButton.addEventListener('click', function() {
            if (confirm('Are you sure you want to clear this conversation?')) {
                clearChat();
            }
        });
    }
}

// Clear chat functionality
function clearChat() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        chatMessages.innerHTML = '';
    }
    
    // Clear any uploaded files
    if (window.upload) {
        window.upload.removeImagePreview();
        window.upload.removePdfPreview();
    }
    
    // Create new conversation if chat module is available
    if (window.chat) {
        window.chat.createNewConversation();
    }
    
    if (window.utils) {
        window.utils.showToast('Chat cleared', 'info');
    }
}

// Setup model selector
function setupModelSelector() {
    const modelSelector = document.getElementById('model-selector');
    if (modelSelector) {
        modelSelector.addEventListener('change', function() {
            const selectedModel = this.value;
            
            // Save selected model to localStorage
            localStorage.setItem('selectedModel', selectedModel);
            
            if (window.utils) {
                window.utils.showToast(`Switched to ${selectedModel}`, 'info');
            }
            
            console.log('Model changed to:', selectedModel);
        });
        
        // Restore selected model from localStorage
        const savedModel = localStorage.getItem('selectedModel');
        if (savedModel && modelSelector.querySelector(`option[value="${savedModel}"]`)) {
            modelSelector.value = savedModel;
        }
    }
}

// Setup theme toggle
function setupThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            
            // Save theme preference
            const isDarkTheme = document.body.classList.contains('dark-theme');
            localStorage.setItem('darkTheme', isDarkTheme.toString());
            
            // Update button text
            this.textContent = isDarkTheme ? '☀️' : '🌙';
        });
        
        // Restore theme from localStorage
        const savedTheme = localStorage.getItem('darkTheme');
        if (savedTheme === 'true') {
            document.body.classList.add('dark-theme');
            themeToggle.textContent = '☀️';
        }
    }
}

// Setup keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to send message
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            if (window.chat) {
                window.chat.sendMessage();
            }
        }
        
        // Ctrl/Cmd + K to focus search/input
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const messageInput = document.getElementById('user-input');
            if (messageInput) {
                messageInput.focus();
            }
        }
        
        // Ctrl/Cmd + N for new chat
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            if (window.chat) {
                window.chat.createNewConversation();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });
}

// Close all open modals
function closeAllModals() {
    const modals = document.querySelectorAll('.modal, .modal-overlay');
    modals.forEach(modal => {
        if (modal.style.display !== 'none') {
            modal.style.display = 'none';
        }
    });
}

// Setup lazy loading for images
function setupLazyLoading() {
    if (window.utils) {
        window.utils.setupLazyLoading();
    }
}

// Smooth scroll to element
function smoothScrollTo(element) {
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Copy text to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        if (window.utils) {
            window.utils.showToast('Copied to clipboard', 'success');
        }
        return true;
    } catch (err) {
        console.error('Failed to copy to clipboard:', err);
        if (window.utils) {
            window.utils.showToast('Failed to copy to clipboard', 'error');
        }
        return false;
    }
}

// Add copy buttons to code blocks
function addCopyButtonsToCodeBlocks() {
    const codeBlocks = document.querySelectorAll('pre code, .code-block');
    
    codeBlocks.forEach(codeBlock => {
        // Skip if copy button already exists
        if (codeBlock.parentElement.querySelector('.copy-button')) {
            return;
        }
        
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.textContent = 'Copy';
        copyButton.title = 'Copy code to clipboard';
        
        copyButton.addEventListener('click', async function() {
            const code = codeBlock.textContent || codeBlock.innerText;
            const success = await copyToClipboard(code);
            
            if (success) {
                this.textContent = 'Copied!';
                setTimeout(() => {
                    this.textContent = 'Copy';
                }, 2000);
            }
        });
        
        // Add button to code block container
        const container = codeBlock.parentElement;
        container.style.position = 'relative';
        container.appendChild(copyButton);
    });
}

// Initialize tooltips
function initializeTooltips() {
    const elementsWithTooltips = document.querySelectorAll('[title], [data-tooltip]');
    
    elementsWithTooltips.forEach(element => {
        const tooltipText = element.getAttribute('title') || element.getAttribute('data-tooltip');
        if (!tooltipText) return;
        
        // Remove default title to prevent browser tooltip
        element.removeAttribute('title');
        
        let tooltip = null;
        
        element.addEventListener('mouseenter', function() {
            tooltip = document.createElement('div');
            tooltip.className = 'custom-tooltip';
            tooltip.textContent = tooltipText;
            tooltip.style.cssText = `
                position: absolute;
                background: #333;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                white-space: nowrap;
                z-index: 1000;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.2s;
            `;
            
            document.body.appendChild(tooltip);
            
            // Position tooltip
            const rect = element.getBoundingClientRect();
            tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
            
            // Show tooltip
            setTimeout(() => {
                tooltip.style.opacity = '1';
            }, 100);
        });
        
        element.addEventListener('mouseleave', function() {
            if (tooltip) {
                tooltip.style.opacity = '0';
                setTimeout(() => {
                    if (tooltip && tooltip.parentNode) {
                        tooltip.parentNode.removeChild(tooltip);
                    }
                }, 200);
            }
        });
    });
}

// Handle responsive design adjustments
function handleResponsiveAdjustments() {
    const mobileBreakpoint = 768;
    
    function adjustForMobile() {
        const isMobile = window.innerWidth < mobileBreakpoint;
        document.body.classList.toggle('mobile-view', isMobile);
        
        // Adjust sidebar behavior for mobile
        const sidebar = document.getElementById('sidebar') || document.querySelector('.sidebar');
        if (sidebar && isMobile) {
            sidebar.classList.add('mobile-sidebar');
        } else if (sidebar) {
            sidebar.classList.remove('mobile-sidebar');
        }
    }
    
    // Initial check
    adjustForMobile();
    
    // Listen for resize events
    window.addEventListener('resize', window.utils ? window.utils.debounce(adjustForMobile, 250) : adjustForMobile);
}

// Export UI functions
window.ui = {
    initializeUI,
    clearChat,
    smoothScrollTo,
    copyToClipboard,
    addCopyButtonsToCodeBlocks,
    initializeTooltips,
    closeAllModals
};

// Initialize UI when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeUI();
    
    // Initialize other UI features after a short delay
    setTimeout(() => {
        addCopyButtonsToCodeBlocks();
        initializeTooltips();
        handleResponsiveAdjustments();
    }, 500);
});