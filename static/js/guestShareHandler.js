/**
 * Guest Share Handler Module
 * 
 * Handles interaction blocking for guest users viewing shared conversations.
 * Shows modal overlay when guests try to interact, prompting them to log in.
 */

let guestModal = null;
let isGuestMode = false;

/**
 * Initialize guest share handling
 * @param {boolean} guestMode - Whether the current user is a guest viewing a shared conversation
 */
export function initializeGuestShareHandler(guestMode = false) {
    isGuestMode = guestMode;
    
    if (!isGuestMode) {
        return; // Not in guest mode, nothing to do
    }
    
    console.log('Initializing guest share handler');
    
    // Create the modal overlay
    createGuestModal();
    
    // Block all interactive elements
    blockInteractions();
    
    // Add visual indicators
    addReadOnlyIndicators();
}

/**
 * Create the modal overlay for guest login prompt
 */
function createGuestModal() {
    const modalHTML = `
        <div id="guest-login-modal" class="modal-overlay" style="display: none;">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Join the conversation!</h3>
                    <button class="modal-close" onclick="closeGuestModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <p>Sign in to continue this conversation and access all features.</p>
                    <div class="modal-buttons">
                        <a href="/google_login" class="btn primary-btn">
                            <i class="fa-brands fa-google"></i>
                            Sign in with Google
                        </a>
                    </div>
                    <p class="modal-note">
                        After signing in, you'll get your own copy of this conversation to continue.
                    </p>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    guestModal = document.getElementById('guest-login-modal');
    
    // Add modal styles
    const modalStyles = `
        <style>
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            backdrop-filter: blur(4px);
        }
        
        .modal-content {
            background: var(--background-color);
            border-radius: 12px;
            padding: 0;
            max-width: 400px;
            width: 90%;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.5rem 1.5rem 0 1.5rem;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 1.5rem;
        }
        
        .modal-header h3 {
            margin: 0;
            color: var(--accent-color);
            font-size: 1.3rem;
        }
        
        .modal-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            color: var(--text-muted);
            cursor: pointer;
            padding: 0;
            line-height: 1;
        }
        
        .modal-close:hover {
            color: var(--text-color);
        }
        
        .modal-body {
            padding: 0 1.5rem 1.5rem 1.5rem;
        }
        
        .modal-body p {
            color: var(--text-color);
            margin-bottom: 1.5rem;
            line-height: 1.5;
        }
        
        .modal-buttons {
            margin-bottom: 1rem;
        }
        
        .modal-buttons .btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            width: 100%;
            padding: 0.75rem 1rem;
            font-size: 1rem;
            text-decoration: none;
        }
        
        .modal-note {
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-bottom: 0 !important;
            text-align: center;
        }
        
        .read-only-indicator {
            position: fixed;
            top: 1rem;
            right: 1rem;
            background: var(--accent-color);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .input-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            cursor: pointer;
            z-index: 10;
        }
        
        .input-overlay-text {
            background: var(--background-color);
            color: var(--text-muted);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            border: 1px solid var(--border-color);
        }
        </style>
    `;
    
    document.head.insertAdjacentHTML('beforeend', modalStyles);
    
    // Make close function global for onclick handler
    window.closeGuestModal = function() {
        if (guestModal) {
            guestModal.style.display = 'none';
        }
    };
}

/**
 * Block interactions for guest users
 */
function blockInteractions() {
    // Block message input area
    const messageInputContainer = document.querySelector('.message-input-container');
    if (messageInputContainer) {
        messageInputContainer.style.position = 'relative';
        
        const overlay = document.createElement('div');
        overlay.className = 'input-overlay';
        overlay.innerHTML = '<div class="input-overlay-text">Sign in to continue this conversation</div>';
        overlay.addEventListener('click', showGuestModal);
        
        messageInputContainer.appendChild(overlay);
    }
    
    // Block model selection buttons
    const modelButtons = document.querySelectorAll('.model-btn, .preset-btn');
    modelButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            showGuestModal();
        });
    });
    
    // Block file upload buttons
    const uploadButtons = document.querySelectorAll('[data-file-type], .upload-btn');
    uploadButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            showGuestModal();
        });
    });
    
    // Block any form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            showGuestModal();
        });
    });
    
    // Block sidebar interactions (new chat, conversation selection)
    const sidebarInteractions = document.querySelectorAll('.new-chat-btn, .conversation-item');
    sidebarInteractions.forEach(element => {
        element.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            showGuestModal();
        });
    });
}

/**
 * Add visual indicators for read-only mode
 */
function addReadOnlyIndicators() {
    // Add read-only badge
    const badge = document.createElement('div');
    badge.className = 'read-only-indicator';
    badge.innerHTML = '<i class="fa-solid fa-share-nodes"></i> Shared Conversation';
    document.body.appendChild(badge);
    
    // Add visual styling to indicate read-only state
    document.body.classList.add('guest-read-only');
}

/**
 * Show the guest login modal
 */
function showGuestModal() {
    if (guestModal) {
        guestModal.style.display = 'flex';
    }
}

/**
 * Check if current session is in guest mode
 */
export function isGuestShareMode() {
    return isGuestMode;
}