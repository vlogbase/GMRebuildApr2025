/**
 * document-manager.js - Handles document interaction for conversations
 * 
 * This script provides functionality for:
 * 1. Displaying documents in the document preview area
 * 2. Removing documents from conversations
 * 3. Opening documents for viewing
 */

// Document removal function - called when clicking the remove button on a document
function removeDocument(documentId, element) {
    if (!documentId) {
        console.error('No document ID provided for removal');
        return;
    }
    
    // Send a request to remove the document
    fetch(`/document/${documentId}/remove`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Successfully removed the document from the database
            console.log('Document removed successfully:', data);
            
            // Remove the document element from the UI
            const docElement = element.closest('.document-preview');
            if (docElement) {
                docElement.remove();
                
                // Check if there are no more documents and hide the container if empty
                const docContainer = document.querySelector('.document-preview-container');
                if (docContainer && docContainer.querySelectorAll('.document-preview').length === 0) {
                    docContainer.style.display = 'none';
                }
            }
        } else {
            console.error('Error removing document:', data.error);
        }
    })
    .catch(error => {
        console.error('Error removing document:', error);
    });
}

// Function to open a document in a viewer
function openDocumentViewer(url, type) {
    if (!url) {
        console.error('No URL provided for document viewer');
        return;
    }
    
    if (type === 'pdf') {
        // Open PDF in a new tab
        window.open(url, '_blank');
    } else if (type === 'image') {
        // Display image in a modal or lightbox
        const modal = document.createElement('div');
        modal.className = 'document-modal';
        modal.innerHTML = `
            <div class="document-modal-content">
                <span class="document-modal-close">&times;</span>
                <img src="${url}" alt="Document Preview" class="document-modal-image">
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Add event listener to close button
        const closeButton = modal.querySelector('.document-modal-close');
        closeButton.addEventListener('click', () => {
            modal.remove();
        });
        
        // Also close on click outside the image
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                modal.remove();
            }
        });
    }
}

// Helper function to get CSRF token
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Display documents for the current conversation
function loadConversationDocuments(conversationId) {
    if (!conversationId) {
        console.error('No conversation ID provided for loading documents');
        return;
    }
    
    fetch(`/conversation/${conversationId}/documents`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.documents && data.documents.length > 0) {
                const docContainer = document.querySelector('.document-preview-container');
                if (docContainer) {
                    // Clear existing documents
                    docContainer.innerHTML = '';
                    
                    // Create elements for each document
                    data.documents.forEach(doc => {
                        const docElement = document.createElement('div');
                        docElement.className = 'document-preview';
                        docElement.dataset.documentId = doc.id;
                        
                        const iconClass = doc.document_type === 'pdf' ? 'fa-file-pdf' : 'fa-file-image';
                        const docColor = doc.document_type === 'pdf' ? 'document-pdf' : 'document-image';
                        
                        docElement.innerHTML = `
                            <div class="document-preview-header ${docColor}">
                                <i class="fas ${iconClass}"></i>
                                <span class="document-name">${doc.document_name || 'Document'}</span>
                                <button class="document-remove-btn" onclick="removeDocument(${doc.id}, this)" title="Remove document">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                            <div class="document-preview-body" onclick="openDocumentViewer('${doc.document_url}', '${doc.document_type}')">
                                ${doc.document_type === 'image' ? 
                                    `<img src="${doc.document_url}" alt="${doc.document_name || 'Image'}" class="document-thumbnail">` : 
                                    `<div class="pdf-placeholder">PDF Document</div>`
                                }
                            </div>
                        `;
                        
                        docContainer.appendChild(docElement);
                    });
                    
                    // Make the container visible
                    docContainer.style.display = 'flex';
                }
            }
        })
        .catch(error => {
            console.error('Error loading conversation documents:', error);
        });
}