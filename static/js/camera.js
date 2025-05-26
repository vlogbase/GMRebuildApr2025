// Camera and Media Management
// This file handles camera operations, device switching, and media stream management

// Global variables for camera management
let currentStream = null;
let availableCameras = [];
let currentCameraIndex = 0;

// Stop the current camera stream
function stopCameraStream() {
    if (currentStream) {
        currentStream.getTracks().forEach(track => {
            track.stop();
        });
        currentStream = null;
        console.log('Camera stream stopped');
    }
    
    // Clear video element if it exists
    const videoElement = document.getElementById('camera-video');
    if (videoElement) {
        videoElement.srcObject = null;
    }
}

// Switch to the next available camera
async function switchCamera() {
    if (availableCameras.length <= 1) {
        console.log('No other cameras available to switch to');
        return;
    }
    
    // Stop current stream
    stopCameraStream();
    
    // Move to next camera
    currentCameraIndex = (currentCameraIndex + 1) % availableCameras.length;
    const nextCamera = availableCameras[currentCameraIndex];
    
    try {
        // Start new stream with next camera
        const constraints = {
            video: {
                deviceId: { exact: nextCamera.deviceId }
            }
        };
        
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        currentStream = stream;
        
        // Update video element
        const videoElement = document.getElementById('camera-video');
        if (videoElement) {
            videoElement.srcObject = stream;
        }
        
        console.log(`Switched to camera: ${nextCamera.label}`);
        
        // Update UI to show current camera
        updateCameraUI(nextCamera);
        
    } catch (error) {
        console.error('Error switching camera:', error);
        showNotification('Failed to switch camera', 'error');
    }
}

// Load available camera devices
async function loadCameraDevices() {
    try {
        // Request permission first
        await navigator.mediaDevices.getUserMedia({ video: true });
        
        // Get all video input devices
        const devices = await navigator.mediaDevices.enumerateDevices();
        availableCameras = devices.filter(device => device.kind === 'videoinput');
        
        console.log(`Found ${availableCameras.length} camera(s):`, availableCameras);
        
        // Update camera selection UI if it exists
        updateCameraSelection();
        
        return availableCameras;
        
    } catch (error) {
        console.error('Error loading camera devices:', error);
        showNotification('Camera access denied or not available', 'error');
        return [];
    }
}

// Update camera selection UI
function updateCameraSelection() {
    const cameraSelect = document.getElementById('camera-select');
    if (!cameraSelect) return;
    
    cameraSelect.innerHTML = '';
    
    availableCameras.forEach((camera, index) => {
        const option = document.createElement('option');
        option.value = index;
        option.textContent = camera.label || `Camera ${index + 1}`;
        cameraSelect.appendChild(option);
    });
    
    // Set current selection
    cameraSelect.value = currentCameraIndex;
}

// Update camera UI elements
function updateCameraUI(camera) {
    const cameraLabel = document.getElementById('current-camera-label');
    if (cameraLabel) {
        cameraLabel.textContent = camera.label || 'Camera';
    }
    
    const switchButton = document.getElementById('switch-camera-btn');
    if (switchButton) {
        switchButton.style.display = availableCameras.length > 1 ? 'block' : 'none';
    }
}

// Start camera with specific device
async function startCamera(deviceId = null) {
    try {
        const constraints = {
            video: deviceId ? { deviceId: { exact: deviceId } } : true
        };
        
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        currentStream = stream;
        
        // Update video element
        const videoElement = document.getElementById('camera-video');
        if (videoElement) {
            videoElement.srcObject = stream;
        }
        
        // Load available cameras if not already loaded
        if (availableCameras.length === 0) {
            await loadCameraDevices();
        }
        
        console.log('Camera started successfully');
        return stream;
        
    } catch (error) {
        console.error('Error starting camera:', error);
        showNotification('Failed to start camera', 'error');
        throw error;
    }
}

// Take a photo from the current camera stream
function takePhoto() {
    const videoElement = document.getElementById('camera-video');
    if (!videoElement || !currentStream) {
        console.error('No active camera stream');
        return null;
    }
    
    // Create canvas to capture frame
    const canvas = document.createElement('canvas');
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    
    const context = canvas.getContext('2d');
    context.drawImage(videoElement, 0, 0);
    
    // Convert to blob
    return new Promise(resolve => {
        canvas.toBlob(blob => {
            resolve(blob);
        }, 'image/jpeg', 0.9);
    });
}

// Check if camera is supported
function isCameraSupported() {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
}

// Show camera not supported message
function showCameraNotSupported() {
    showNotification('Camera is not supported in this browser', 'warning');
}

// Initialize camera system
function initializeCamera() {
    if (!isCameraSupported()) {
        console.warn('Camera not supported');
        return;
    }
    
    // Set up camera UI event listeners
    const switchButton = document.getElementById('switch-camera-btn');
    if (switchButton) {
        switchButton.addEventListener('click', switchCamera);
    }
    
    const captureButton = document.getElementById('capture-photo-btn');
    if (captureButton) {
        captureButton.addEventListener('click', async () => {
            const photo = await takePhoto();
            if (photo && window.documentManager) {
                const photoUrl = URL.createObjectURL(photo);
                window.documentManager.addImageToAttachments(photoUrl, 'camera-photo.jpg', photo.size);
            }
        });
    }
    
    const cameraSelect = document.getElementById('camera-select');
    if (cameraSelect) {
        cameraSelect.addEventListener('change', (e) => {
            const selectedIndex = parseInt(e.target.value);
            if (availableCameras[selectedIndex]) {
                currentCameraIndex = selectedIndex;
                startCamera(availableCameras[selectedIndex].deviceId);
            }
        });
    }
    
    console.log('Camera system initialized');
}

// Show notification (fallback if not available from other modules)
function showNotification(message, type = 'info') {
    if (window.messageActions && window.messageActions.showNotification) {
        window.messageActions.showNotification(message, type);
        return;
    }
    
    // Fallback notification
    console.log(`${type.toUpperCase()}: ${message}`);
    alert(message);
}

// Make functions globally available
window.stopCameraStream = stopCameraStream;
window.switchCamera = switchCamera;
window.loadCameraDevices = loadCameraDevices;
window.startCamera = startCamera;
window.takePhoto = takePhoto;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeCamera();
});

// Export for use by other modules
window.camera = {
    stopCameraStream,
    switchCamera,
    loadCameraDevices,
    startCamera,
    takePhoto,
    isCameraSupported
};