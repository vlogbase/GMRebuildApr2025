// Document and Image Management
// This file handles document previews, image management, and file operations

// Global variables for document management
let attachedDocuments = [];
let attachedImages = [];

// Update document previews in the UI
function updateDocumentPreviews() {
    const documentPreviewContainer = document.getElementById('document-preview-container');
    if (!documentPreviewContainer) return;
    
    documentPreviewContainer.innerHTML = '';
    
    attachedDocuments.forEach((doc, index) => {
        const previewElement = document.createElement('div');
        previewElement.className = 'document-preview';
        previewElement.innerHTML = `
            <div class="document-info">
                <i class="fas fa-file-pdf"></i>
                <span class="document-name">${doc.name}</span>
                <span class="document-size">${formatFileSize(doc.size)}</span>
            </div>
            <div class="document-actions">
                <button onclick="openDocumentViewer(${index})" class="view-btn" title="View document">
                    <i class="fas fa-eye"></i>
                </button>
                <button onclick="removeDocument(${index})" class="remove-btn" title="Remove document">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        documentPreviewContainer.appendChild(previewElement);
    });
    
    // Update global reference
    window.attachedDocuments = attachedDocuments;
}

// Remove an image by index
function removeImage(index) {
    if (index >= 0 && index < attachedImages.length) {
        attachedImages.splice(index, 1);
        updateImagePreviews();
        console.log(`Removed image at index ${index}`);
    }
}

// Show image preview in a modal
function showImagePreview(imageUrl) {
    const modal = document.createElement('div');
    modal.className = 'image-preview-modal';
    modal.innerHTML = `
        <div class="modal-backdrop" onclick="closeImagePreview()"></div>
        <div class="modal-content">
            <img src="${imageUrl}" alt="Image preview" class="preview-image">
            <button onclick="closeImagePreview()" class="close-btn">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Prevent body scrolling
    document.body.style.overflow = 'hidden';
}

// Close image preview modal
function closeImagePreview() {
    const modal = document.querySelector('.image-preview-modal');
    if (modal) {
        document.body.removeChild(modal);
        document.body.style.overflow = '';
    }
}

// Clear all attached images
function clearAttachedImages() {
    attachedImages = [];
    updateImagePreviews();
    console.log('Cleared all attached images');
}

// Clear single attached image (for single image mode)
function clearAttachedImage() {
    if (attachedImages.length > 0) {
        attachedImages = [];
        updateImagePreviews();
        console.log('Cleared attached image');
    }
}

// Clear attached PDF
function clearAttachedPdf() {
    attachedDocuments = [];
    updateDocumentPreviews();
    console.log('Cleared attached PDF');
}

// Remove a document by index
function removeDocument(index) {
    if (index >= 0 && index < attachedDocuments.length) {
        const removedDoc = attachedDocuments.splice(index, 1)[0];
        updateDocumentPreviews();
        console.log(`Removed document: ${removedDoc.name}`);
    }
}

// Open document viewer
function openDocumentViewer(index) {
    if (index < 0 || index >= attachedDocuments.length) {
        console.error('Invalid document index');
        return;
    }
    
    const document = attachedDocuments[index];
    
    // Create document viewer modal
    const modal = document.createElement('div');
    modal.className = 'document-viewer-modal';
    modal.innerHTML = `
        <div class="modal-backdrop" onclick="closeDocumentViewer()"></div>
        <div class="modal-content document-viewer">
            <div class="document-viewer-header">
                <h3>${document.name}</h3>
                <button onclick="closeDocumentViewer()" class="close-btn">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="document-viewer-body">
                <iframe src="${document.url}" frameborder="0" class="document-frame"></iframe>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';
}

// Close document viewer
function closeDocumentViewer() {
    const modal = document.querySelector('.document-viewer-modal');
    if (modal) {
        document.body.removeChild(modal);
        document.body.style.overflow = '';
    }
}

// Update image previews in the UI
function updateImagePreviews() {
    const imagePreviewContainer = document.getElementById('image-preview-container');
    if (!imagePreviewContainer) return;
    
    imagePreviewContainer.innerHTML = '';
    
    attachedImages.forEach((image, index) => {
        const previewElement = document.createElement('div');
        previewElement.className = 'image-preview';
        previewElement.innerHTML = `
            <img src="${image.url}" alt="Preview" class="preview-thumbnail" onclick="showImagePreview('${image.url}')">
            <button onclick="removeImage(${index})" class="remove-btn" title="Remove image">
                <i class="fas fa-times"></i>
            </button>
        `;
        imagePreviewContainer.appendChild(previewElement);
    });
}

// Format file size for display
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Add image to attachments
function addImageToAttachments(imageUrl, imageName, imageSize) {
    const imageObj = {
        url: imageUrl,
        name: imageName || 'image',
        size: imageSize || 0
    };
    
    attachedImages.push(imageObj);
    updateImagePreviews();
    console.log('Added image to attachments:', imageName);
}

// Add document to attachments
function addDocumentToAttachments(documentUrl, documentName, documentSize) {
    const docObj = {
        url: documentUrl,
        name: documentName || 'document',
        size: documentSize || 0
    };
    
    attachedDocuments.push(docObj);
    updateDocumentPreviews();
    console.log('Added document to attachments:', documentName);
}

// Get current attachments summary
function getAttachmentsSummary() {
    return {
        images: attachedImages.length,
        documents: attachedDocuments.length,
        totalImages: attachedImages,
        totalDocuments: attachedDocuments
    };
}

// Initialize document manager
function initializeDocumentManager() {
    // Initialize attachment arrays
    attachedDocuments = [];
    attachedImages = [];
    
    // Expose globally for other scripts
    window.attachedDocuments = attachedDocuments;
    window.attachedImages = attachedImages;
    
    console.log('Document manager initialized');
}

// Make functions globally available
window.updateDocumentPreviews = updateDocumentPreviews;
window.removeImage = removeImage;
window.showImagePreview = showImagePreview;
window.clearAttachedImages = clearAttachedImages;
window.clearAttachedImage = clearAttachedImage;
window.clearAttachedPdf = clearAttachedPdf;
window.removeDocument = removeDocument;
window.openDocumentViewer = openDocumentViewer;
window.closeImagePreview = closeImagePreview;
window.closeDocumentViewer = closeDocumentViewer;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeDocumentManager();
});

// Export for use by other modules
window.documentManager = {
    updateDocumentPreviews,
    removeImage,
    showImagePreview,
    clearAttachedImages,
    clearAttachedPdf,
    removeDocument,
    openDocumentViewer,
    addImageToAttachments,
    addDocumentToAttachments,
    getAttachmentsSummary
};