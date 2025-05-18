// Conversation rename functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get modal elements
    const renameModal = document.getElementById('rename-conversation-modal');
    const conversationTitleInput = document.getElementById('conversation-title-input');
    const conversationIdToRename = document.getElementById('conversation-id-to-rename');
    const cancelRenameBtn = document.getElementById('cancel-rename-btn');
    const confirmRenameBtn = document.getElementById('confirm-rename-btn');
    
    // Add event listeners for the rename modal buttons
    if (cancelRenameBtn) {
        cancelRenameBtn.addEventListener('click', closeRenameModal);
    }
    
    if (confirmRenameBtn) {
        confirmRenameBtn.addEventListener('click', submitRename);
    }
    
    // Close modal when clicking outside it
    window.addEventListener('click', function(event) {
        if (event.target === renameModal) {
            closeRenameModal();
        }
    });

    // Function to open the rename modal
    window.openRenameModal = function(conversationId, currentTitle) {
        // Set the conversation ID and current title
        conversationIdToRename.value = conversationId;
        conversationTitleInput.value = currentTitle;
        
        // Show the modal
        renameModal.classList.add('show');
        
        // Focus the input
        setTimeout(() => {
            conversationTitleInput.focus();
            conversationTitleInput.select();
        }, 100);
        
        // Add event listener for Enter key
        conversationTitleInput.addEventListener('keydown', handleRenameKeydown);
    };
    
    // Handle Enter key in the rename input
    function handleRenameKeydown(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            submitRename();
        } else if (e.key === 'Escape') {
            closeRenameModal();
        }
    }
    
    // Function to close the rename modal
    function closeRenameModal() {
        renameModal.classList.remove('show');
        // Remove event listener
        conversationTitleInput.removeEventListener('keydown', handleRenameKeydown);
    }
    
    // Function to get CSRF token
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    }
    
    // Function to submit the rename request
    function submitRename() {
        const conversationId = conversationIdToRename.value;
        const newTitle = conversationTitleInput.value.trim();
        
        if (!newTitle) {
            alert('Please enter a title for the conversation.');
            return;
        }
        
        // Show loading state
        confirmRenameBtn.disabled = true;
        confirmRenameBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Renaming...';
        
        // Send request to rename the conversation
        fetch(`/api/rename-conversation/${conversationId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ title: newTitle })
        })
        .then(response => response.json())
        .then(data => {
            // Reset button state
            confirmRenameBtn.disabled = false;
            confirmRenameBtn.textContent = 'Rename';
            
            if (data.success) {
                // Close the modal
                closeRenameModal();
                
                // Update the conversation title in the UI
                const conversationItem = document.querySelector(`.conversation-item[data-id="${conversationId}"]`);
                if (conversationItem) {
                    const titleDiv = conversationItem.querySelector('.conversation-title');
                    if (titleDiv) {
                        titleDiv.textContent = newTitle;
                    }
                }
                
                console.log(`Successfully renamed conversation ${conversationId} to "${newTitle}"`);
            } else {
                alert(data.error || 'Failed to rename conversation. Please try again.');
            }
        })
        .catch(error => {
            // Reset button state
            confirmRenameBtn.disabled = false;
            confirmRenameBtn.textContent = 'Rename';
            
            console.error('Error renaming conversation:', error);
            alert('Failed to rename conversation. Please try again.');
        });
    }
});