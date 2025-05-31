// Import required modules
import { uploadFileAPI } from './apiService.js';
import { attachedImageUrls, currentConversationId, setAttachedPdfUrl, setAttachedPdfName } from './chatLogic.js';

// File upload state management
export let isUploadingFile = false;
export let uploadingImageCount = 0;

// Main file upload handler (unified for both images and PDFs)
export async function handleFileUpload(file, type = null) {
    console.log(`🔄 Starting unified file upload for: ${file.name}, type: ${type || 'auto-detect'}`);
    
    if (isUploadingFile) {
        console.log('⚠️ Upload already in progress, ignoring new upload');
        return { success: false, error: 'Upload already in progress' };
    }
    
    isUploadingFile = true;
    
    try {
        // Auto-detect file type if not provided
        const detectedType = type || (file.type.startsWith('image/') ? 'image' : 'pdf');
        console.log(`📁 File type: ${detectedType} for ${file.name}`);
        
        // Call the unified API endpoint
        const response = await uploadFileAPI(file, currentConversationId);
        
        if (response.success) {
            console.log(`✅ File uploaded successfully:`, response);
            
            if (detectedType === 'image' && response.image_url) {
                // Store the image URL for sending with the message
                attachedImageUrls.push(response.image_url);
                console.log(`📸 Image URL stored: ${response.image_url}`);
                
                // Show image preview
                showImagePreview(response.image_url);
                
                return {
                    success: true,
                    type: 'image',
                    url: response.image_url,
                    filename: file.name
                };
            } else if (detectedType === 'pdf' && response.document_url) {
                // Store PDF data using the setter functions from chatLogic
                setAttachedPdfUrl(response.document_url);
                setAttachedPdfName(response.document_name || file.name);
                console.log(`📄 PDF attached: ${response.document_name || file.name}`);
                
                // Show PDF preview/indicator
                showPdfPreview(response.document_name || file.name);
                
                return {
                    success: true,
                    type: 'pdf',
                    url: response.document_url,
                    filename: window.attachedPdfName,
                    document_name: response.document_name
                };
            }
        }
        
        return { success: false, error: response.error || 'Upload failed' };
        
    } catch (error) {
        console.error('❌ File upload error:', error);
        return { success: false, error: error.message || 'Upload failed' };
    } finally {
        isUploadingFile = false;
    }
}

// Specific handlers for backward compatibility
export async function handleImageFile(fileOrBlob) {
    console.log("✅ handleImageFile() - delegating to handleFileUpload");
    if (!fileOrBlob) return;
    
    // Use the unified file upload handler with type 'image'
    return handleFileUpload(fileOrBlob, 'image');
}

export async function handlePdfFile(file) {
    console.log("📄 handlePdfFile() - delegating to handleFileUpload");
    
    // Show upload indicator specifically for PDF
    const uploadIndicator = document.getElementById('upload-indicator') || createUploadIndicator();
    uploadIndicator.style.display = 'block';
    uploadIndicator.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing PDF document...';
    uploadIndicator.className = 'upload-indicator pdf-upload';
    
    const result = await handleFileUpload(file, 'pdf');
    
    // Update indicator based on result
    if (result && result.success) {
        uploadIndicator.innerHTML = '<i class="fas fa-check-circle"></i> PDF ready for chat!';
        uploadIndicator.className = 'upload-indicator pdf-upload success';
        
        // If we have a document name from the response, display it
        if (result.document_name) {
            // Update the displayed name
            uploadIndicator.innerHTML = '<i class="fas fa-check-circle"></i> PDF ready: ' + result.document_name;
        }
        
        // Show success message for 3 seconds then fade out
        setTimeout(() => {
            uploadIndicator.style.opacity = '0';
            setTimeout(() => {
                uploadIndicator.style.display = 'none';
                uploadIndicator.style.opacity = '1';
                uploadIndicator.className = 'upload-indicator';
            }, 500); // Fade out transition duration
        }, 3000);
    } else {
        uploadIndicator.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error processing PDF: ' + (result?.error || 'Unknown error');
        uploadIndicator.className = 'upload-indicator pdf-upload error';
        
        // Show error for 5 seconds then fade out
        setTimeout(() => {
            uploadIndicator.style.opacity = '0';
            setTimeout(() => {
                uploadIndicator.style.display = 'none';
                uploadIndicator.style.opacity = '1';
                uploadIndicator.className = 'upload-indicator';
            }, 500); // Fade out transition duration
        }, 5000);
    }
    
    return result;
}

// UI helper functions
export function showImagePreview(imageUrl) {
    console.log(`📸 Showing image preview for: ${imageUrl}`);
    const previewArea = document.getElementById('document-preview-area');
    if (!previewArea) return;
    previewArea.style.display = 'block';
    const preview = document.createElement('div');
    preview.className = 'image-preview';
    preview.innerHTML = `
        <img src="${imageUrl}" alt="Preview" class="preview-image"
             style="max-width:100%; height:auto;"/>
        <button class="remove-image" onclick="this.parentElement.remove()">×</button>
    `;
    previewArea.appendChild(preview);
}

export function showPdfPreview(filename) {
    console.log(`📄 Showing PDF preview for: ${filename}`);
    const previewArea = document.getElementById('document-preview-area');
    if (!previewArea) return;
    previewArea.style.display = 'block';
    const preview = document.createElement('div');
    preview.className = 'pdf-preview';
    preview.innerHTML = `
        <div class="pdf-icon">📄</div>
        <span class="pdf-name">${filename}</span>
        <button class="remove-pdf" onclick="this.parentElement.remove()">×</button>
    `;
    previewArea.appendChild(preview);
}

export function createUploadIndicator() {
    // Check if it already exists
    let indicator = document.getElementById('upload-indicator');
    if (indicator) return indicator;
    
    // Create new indicator with the appropriate styling
    indicator = document.createElement('div');
    indicator.id = 'upload-indicator';
    indicator.className = 'upload-indicator';
    indicator.style.display = 'none';
    
    // Insert it near the message input area
    const messageForm = document.querySelector('.message-input-container') || document.querySelector('.input-container');
    if (messageForm) {
        messageForm.appendChild(indicator);
    }
    
    return indicator;
}

// Camera-related variables and functions
let cameras = [];
let currentCameraIndex = 0;

export function stopCameraStream() {
    const cameraStream = document.getElementById('camera-stream');
    if (cameraStream && cameraStream.srcObject) {
        const tracks = cameraStream.srcObject.getTracks();
        tracks.forEach(track => track.stop());
        cameraStream.srcObject = null;
    }
}

export async function switchCamera() {
    const cameraStream = document.getElementById('camera-stream');
    
    // Only allow switching if there are multiple cameras
    if (cameras.length <= 1) {
        console.warn('📷 Cannot switch camera - only one camera available');
        return;
    }
    
    if (!cameraStream) {
        console.error('📷 Camera stream element not found');
        return;
    }
    
    try {
        stopCameraStream();
        currentCameraIndex = (currentCameraIndex + 1) % cameras.length;
        
        console.log(`📷 Switching to camera ${currentCameraIndex + 1} of ${cameras.length}`);
        
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { deviceId: { exact: cameras[currentCameraIndex].deviceId } }
        });
        
        cameraStream.srcObject = stream;
        
    } catch (err) {
        console.error('Error switching camera:', err);
        
        // Try to fall back to the default camera
        try {
            console.log('📷 Falling back to default camera');
            const fallbackStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' }
            });
            cameraStream.srcObject = fallbackStream;
        } catch (fallbackErr) {
            console.error('Error with fallback camera:', fallbackErr);
            alert('Failed to switch camera. Please close and reopen the camera.');
        }
    }
}

export async function loadCameraDevices() {
    if (!navigator.mediaDevices?.enumerateDevices) {
        console.warn('enumerateDevices() not supported');
        // Hide switch button if device enumeration is not supported
        const switchCameraButton = document.getElementById('switch-camera-button');
        if (switchCameraButton) {
            switchCameraButton.style.display = 'none';
        }
        return;
    }
    
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        cameras = devices.filter(device => device.kind === 'videoinput');
        
        console.log(`📷 Found ${cameras.length} camera(s):`, cameras.map(c => c.label || 'Camera'));
        
        // Enable/disable switch camera button based on available cameras
        const switchCameraButton = document.getElementById('switch-camera-button');
        if (switchCameraButton) {
            if (cameras.length > 1) {
                switchCameraButton.style.display = 'block';
                switchCameraButton.disabled = false;
                console.log('📷 Multiple cameras available - switch button enabled');
            } else {
                switchCameraButton.style.display = 'none';
                switchCameraButton.disabled = true;
                console.log('📷 Single camera detected - switch button hidden');
            }
        }
    } catch (err) {
        console.error('Error enumerating devices:', err);
        // Hide switch button on error
        const switchCameraButton = document.getElementById('switch-camera-button');
        if (switchCameraButton) {
            switchCameraButton.style.display = 'none';
        }
    }
}