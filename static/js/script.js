document.addEventListener('DOMContentLoaded', function() {
    // Create authentication and credit variables at the top level scope
    let isAuthenticated = false;
    let userCreditBalance = 0;
    let authCheckComplete = false;
    
    // Helper function to check premium access and redirect if needed
    // This will only work after authentication check is complete
    function checkPremiumAccess(featureName) {
        // If auth check isn't complete, assume we can proceed but log a warning
        if (!authCheckComplete) {
            console.warn(`Premium access check called before authentication check completed for ${featureName}`);
            return true;
        }
        
        if (!isAuthenticated) {
            console.log(`Access denied: Not logged in, redirecting to login for ${featureName}`);
            window.location.href = '/login?redirect=chat&feature=' + featureName;
            return false;
        }
        
        if (userCreditBalance <= 0) {
            console.log(`Access denied: Insufficient credits, redirecting to account page for ${featureName}`);
            window.location.href = '/billing/account?source=chat&feature=' + featureName;
            return false;
        }
        
        return true;
    }
    
    // Delay authentication check slightly to ensure DOM is fully loaded
    setTimeout(() => {
        // Check if user is authenticated (look for the logout button which only shows for logged in users)
        isAuthenticated = !!document.getElementById('logout-btn');
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
        
        // Mark authentication check as complete
        authCheckComplete = true;
        
        // Initialize features that depend on authentication status
        if (isAuthenticated) {
            fetchConversations();
        } else {
            // For non-authenticated users, lock premium features
            lockPremiumFeatures();
        }
    }, 100); // 100ms delay to ensure DOM is fully loaded
    
    // Setup clipboard paste event listener for the entire document
    document.addEventListener('paste', handlePaste);
    
    // Paste handler function
    function handlePaste(e) {
        // Only handle paste if the chat input area is focused
        const activeElement = document.activeElement;
        const chatInput = document.getElementById('user-input');
        
        if (activeElement !== chatInput && !activeElement.closest('.chat-input-container')) {
            return; // Not focused on chat input, ignore paste event
        }
        
        // Check if clipboard contains images
        const items = e.clipboardData.items;
        for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf('image') !== -1) {
                console.log('Image found in clipboard');
                
                // Check premium access before handling the pasted image
                if (!checkPremiumAccess('image_upload')) {
                    // Prevent default paste behavior
                    e.preventDefault();
                    return;
                }
                
                // Get the image as a file
                const file = items[i].getAsFile();
                if (!file) continue;
                
                // Prevent the default paste behavior
                e.preventDefault();
                
                // Set upload flag to true and disable send button
                isUploadingImage = true;
                updateSendButtonState();
                
                // Show upload indicator
                const uploadIndicator = document.getElementById('upload-indicator') || createUploadIndicator();
                uploadIndicator.style.display = 'block';
                uploadIndicator.textContent = 'Uploading image from clipboard...';
                
                // Create FormData and upload the image
                const formData = new FormData();
                formData.append('file', file, 'clipboard-image.png');
                
                // Get the currently selected model
                const activeModel = document.querySelector('.model-btn.active');
                const modelId = activeModel ? activeModel.dataset.modelId : null;
                
                // Add model parameter if available
                let uploadUrl = '/upload_image';
                if (modelId) {
                    uploadUrl += `?model=${encodeURIComponent(modelId)}`;
                }
                
                fetch(uploadUrl, {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    // Set upload flag to false and re-enable send button
                    isUploadingImage = false;
                    updateSendButtonState();
                    
                    if (data.success && data.image_url) {
                        // Set the current image URL for sending with the message
                        currentImageUrl = data.image_url;
                        attachedImageUrl = data.image_url;
                        
                        // Show the image preview
                        showImagePreview(data.image_url);
                        
                        // Update upload indicator
                        uploadIndicator.textContent = 'Image ready to send!';
                        setTimeout(() => {
                            uploadIndicator.style.display = 'none';
                        }, 1500);
                    } else {
                        uploadIndicator.textContent = 'Error uploading image: ' + (data.error || 'Unknown error');
                        uploadIndicator.style.color = 'red';
                        setTimeout(() => {
                            uploadIndicator.style.display = 'none';
                            uploadIndicator.style.color = '';
                        }, 3000);
                    }
                })
                .catch(error => {
                    console.error('Error uploading image:', error);
                    
                    // Set upload flag to false and re-enable send button
                    isUploadingImage = false;
                    updateSendButtonState();
                    
                    uploadIndicator.textContent = 'Error uploading image';
                    uploadIndicator.style.color = 'red';
                    setTimeout(() => {
                        uploadIndicator.style.display = 'none';
                        uploadIndicator.style.color = '';
                    }, 3000);
                });
                
                // Only process the first image
                break;
            }
        }
    }
    
    // Create upload indicator if it doesn't exist
    function createUploadIndicator() {
        // Check if it already exists
        let indicator = document.getElementById('upload-indicator');
        if (indicator) return indicator;
        
        // Create new indicator with the appropriate styling
        indicator = document.createElement('div');
        indicator.id = 'upload-indicator';
        indicator.style.display = 'none';
        
        // Add it before the chat input
        const chatInputContainer = document.querySelector('.chat-input-container');
        if (chatInputContainer) {
            chatInputContainer.insertBefore(indicator, chatInputContainer.firstChild);
        } else {
            // Fallback - add to body
            document.body.appendChild(indicator);
            console.warn('Chat input container not found, added upload indicator to body');
        }
        
        return indicator;
    }
    // DOM Elements
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const modelPresetButtons = document.querySelectorAll('.model-preset-btn');
    const newChatButton = document.getElementById('new-chat-btn');
    const clearConversationsButton = document.getElementById('clear-conversations-btn');
    const exampleQuestionButton = document.getElementById('example-question-btn');
    const conversationsList = document.getElementById('conversations-list');
    const modelSelector = document.getElementById('model-selector');
    const modelList = document.getElementById('model-list');
    const modelSearch = document.getElementById('model-search');
    const closeSelector = document.getElementById('close-selector');
    
    // Document upload elements
    const uploadDocumentsBtn = document.getElementById('upload-documents-btn');
    const documentUploadModal = document.getElementById('document-upload-modal');
    const closeUploadModal = document.getElementById('close-upload-modal');
    const uploadDropzone = document.getElementById('upload-dropzone');
    const fileUploadInput = document.getElementById('file-upload-input');
    const uploadFileList = document.getElementById('upload-file-list');
    const uploadFilesBtn = document.getElementById('upload-files-btn');
    const uploadStatus = document.getElementById('upload-status');
    
    // Image upload and camera elements
    const imageUploadInput = document.getElementById('image-upload-input');
    const imageUploadButton = document.getElementById('image-upload-button');
    const cameraButton = document.getElementById('camera-button');
    const cameraModal = document.getElementById('camera-modal');
    const cameraStream = document.getElementById('camera-stream');
    const imageCanvas = document.getElementById('image-canvas');
    const captureButton = document.getElementById('capture-button');
    const switchCameraButton = document.getElementById('switch-camera-button');
    const closeCameraButton = document.getElementById('close-camera-button');
    const imagePreviewArea = document.getElementById('image-preview-area');
    const imagePreview = document.getElementById('image-preview');
    const removeImageButton = document.getElementById('remove-image-button');
    
    // App state
    let activePresetButton = null; // Currently selected preset button
    let currentModel = null; // Model ID of the currently selected preset
    let currentPresetId = '1'; // Default to first preset
    let currentConversationId = null;
    let messageHistory = [];
    
    // Image upload state
    let attachedImageBlob = null;
    let attachedImageUrls = []; // Array to hold multiple image URLs
    let isUploadingImage = false; // Track if an image is currently being uploaded
    let uploadingImageCount = 0; // Track number of images currently uploading
    let cameras = [];
    let currentCameraIndex = 0;
    
    // Model data
    let allModels = []; // All models from OpenRouter
    let userPreferences = {}; // User preferences for preset buttons
    
    // Filter configurations for each preset
    const presetFilters = {
        '1': (model) => !model.is_free, // All non-free models
        '2': (model) => !model.is_free, // All non-free models
        '3': (model) => model.is_reasoning === true && !model.is_free,
        '4': (model) => {
            // For preset 4, prioritize true vision models
            // OpenAI GPT-4o is the primary choice for this preset
            return model.is_multimodal === true && !model.is_free;
        },
        '5': (model) => model.is_perplexity === true && !model.is_free,
        '6': (model) => model.is_free === true // Only free models
    };
    
    // Default model IDs for each preset button
    const defaultModels = {
        '1': 'google/gemini-2.5-pro-preview-03-25',
        '2': 'anthropic/claude-3.7-sonnet',
        '3': 'openai/o4-Mini-High',
        '4': 'openai/gpt-4o', // Vision model for multimodal capabilities
        '5': 'perplexity/sonar-pro',
        '6': 'google/gemini-2.0-flash-exp:free'
    };
    
    // Free model fallbacks (in order of preference)
    const freeModelFallbacks = [
        'google/gemini-2.0-flash-exp:free',
        'qwen/qwq-32b:free',
        'deepseek/deepseek-r1-distill-qwen-32b:free',
        'deepseek/deepseek-r1-distill-llama-70b:free',
        'openrouter/optimus-alpha'
    ];
    
    // Open selector variable - tracks which preset is being configured
    let currentlyEditingPresetId = null;
    
    // NOTE: Authentication-based fetching is now handled in the setTimeout block above.
    
    // Function to lock premium features for non-authenticated users or those with zero balance
    function lockPremiumFeatures() {
        // Lock premium model presets (1-5)
        document.querySelectorAll('.model-preset-btn').forEach(btn => {
            const presetId = btn.getAttribute('data-preset-id');
            if (presetId !== '6') { // All except the free model
                btn.classList.add('premium-locked');
                // Add tooltip
                const tooltip = document.createElement('span');
                tooltip.className = 'locked-tooltip';
                tooltip.textContent = 'Premium feature - Sign in to unlock';
                btn.appendChild(tooltip);
                
                // Change button behavior to redirect to login
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    window.location.href = '/google_login';
                });
            }
        });
        
        // Lock document upload button
        if (uploadDocumentsBtn) {
            uploadDocumentsBtn.classList.add('premium-locked');
            // Change button behavior to redirect to login
            uploadDocumentsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                window.location.href = '/google_login';
            });
            
            const tooltip = document.createElement('span');
            tooltip.className = 'locked-tooltip';
            tooltip.textContent = 'Premium feature - Sign in to unlock';
            uploadDocumentsBtn.appendChild(tooltip);
        }
        
        // Lock image upload and camera buttons
        if (imageUploadButton) {
            imageUploadButton.classList.add('premium-locked');
            imageUploadButton.style.display = 'none'; // Initially hidden, so hide it
        }
        
        if (cameraButton) {
            cameraButton.classList.add('premium-locked');
            cameraButton.style.display = 'none'; // Initially hidden, so hide it
        }
        
        // Update conversations list with login message
        const conversationsList = document.getElementById('conversations-list');
        if (conversationsList) {
            conversationsList.innerHTML = `
                <div class="login-prompt">
                    <p>Sign in to save your chat history and access premium features</p>
                    <button class="auth-btn google-auth-btn" onclick="window.location.href='/google_login'">
                        <i class="fa-brands fa-google"></i> Sign in with Google
                    </button>
                </div>
            `;
        }
    }
    
    // Image upload and camera event listeners with premium access checks
    if (imageUploadButton) {
        imageUploadButton.addEventListener('click', () => {
            // Check premium access before allowing image upload
            if (!checkPremiumAccess('image_upload')) {
                return; // Stop if access check failed
            }
            imageUploadInput.click();
        });
    }
    
    if (imageUploadInput) {
        imageUploadInput.addEventListener('change', event => {
            const file = event.target.files[0];
            if (file && file.type.startsWith('image/')) {
                // Check premium access before processing the image
                if (!checkPremiumAccess('image_upload')) {
                    return; // Stop if access check failed
                }
                handleImageFile(file);
            }
            // Reset the input so the same file can be selected again
            event.target.value = null;
        });
    }
    
    if (cameraButton) {
        cameraButton.addEventListener('click', async () => {
            // Check premium access before allowing camera use
            if (!checkPremiumAccess('camera')) {
                return; // Stop if access check failed
            }
            
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                cameraStream.srcObject = stream;
                cameraModal.style.display = 'block';
                loadCameraDevices();
            } catch (err) {
                console.error('Camera access error:', err);
                alert('Camera access denied or not available');
            }
        });
    }
    
    if (captureButton) {
        captureButton.addEventListener('click', () => {
            // Set canvas dimensions to match video
            const width = cameraStream.videoWidth;
            const height = cameraStream.videoHeight;
            imageCanvas.width = width;
            imageCanvas.height = height;
            
            // Draw video frame to canvas
            const ctx = imageCanvas.getContext('2d');
            ctx.drawImage(cameraStream, 0, 0, width, height);
            
            // Convert canvas to blob
            imageCanvas.toBlob(blob => {
                handleImageFile(blob);
                
                // Stop camera stream and close modal
                stopCameraStream();
                cameraModal.style.display = 'none';
            }, 'image/jpeg', 0.85);
        });
    }
    
    if (switchCameraButton) {
        switchCameraButton.addEventListener('click', switchCamera);
    }
    
    if (closeCameraButton) {
        closeCameraButton.addEventListener('click', () => {
            stopCameraStream();
            cameraModal.style.display = 'none';
        });
    }
    
    if (removeImageButton) {
        removeImageButton.addEventListener('click', clearAttachedImage);
    }
    
    // Image handling functions
    async function handleImageFile(fileOrBlob) {
        console.log("✅ handleImageFile()", fileOrBlob);
        if (!fileOrBlob) return;

        try {
            // Increment upload counter
            uploadingImageCount++;
            
            // Set upload flag to true - this will disable the send button
            isUploadingImage = true;
            
            // Update send button state
            updateSendButtonState();
            
            // Show loading state
            imageUploadButton.classList.add('loading');
            
            // Create FormData and append file
            const formData = new FormData();
            formData.append('file', fileOrBlob, fileOrBlob.name || 'photo.jpg');
            
            console.log("📤 Uploading image to server...");
            
            // Upload to server
            const response = await fetch('/upload_image', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.status}`);
            }
            
            const data = await response.json();
            console.log("↩️ upload response:", data);
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Store the image URL in the array
            attachedImageUrls.push(data.image_url);
            
            // Show previews
            updateImagePreviews();
            
            console.log(`Image uploaded successfully (${attachedImageUrls.length} total):`, data.image_url);
        } catch (error) {
            console.error('Error uploading image:', error);
            alert(`Upload failed: ${error.message}`);
        } finally {
            // Decrement upload counter
            uploadingImageCount--;
            
            // Only disable uploading flag if all uploads are complete
            if (uploadingImageCount === 0) {
                isUploadingImage = false;
                
                // Update send button state
                updateSendButtonState();
                
                // Hide loading state
                imageUploadButton.classList.remove('loading');
            }
        }
    }
    // Add a new function to update all image previews based on the attached URLs
    function updateImagePreviews() {
        // Clear existing previews
        imagePreviewArea.innerHTML = '';
        
        // If no images, hide the preview area
        if (attachedImageUrls.length === 0) {
            imagePreviewArea.style.display = 'none';
            return;
        }
        
        // Show the preview area
        imagePreviewArea.style.display = 'flex';
        imagePreviewArea.classList.add('multi-image');
        
        // Create a counter to show total images
        const counter = document.createElement('div');
        counter.className = 'image-counter';
        counter.textContent = `${attachedImageUrls.length} image${attachedImageUrls.length > 1 ? 's' : ''}`;
        imagePreviewArea.appendChild(counter);
        
        // Add previews for each image (limit display to first 4 images)
        const displayLimit = Math.min(attachedImageUrls.length, 4);
        
        for (let i = 0; i < displayLimit; i++) {
            const imageUrl = attachedImageUrls[i];
            
            // Create a container for each preview
            const previewContainer = document.createElement('div');
            previewContainer.className = 'image-preview-container';
            
            // Create the image element
            const img = document.createElement('img');
            img.className = 'image-preview-thumbnail';
            img.src = imageUrl;
            img.alt = `Image ${i+1}`;
            
            // Add a remove button for each image
            const removeBtn = document.createElement('button');
            removeBtn.className = 'remove-image-btn';
            removeBtn.innerHTML = '×';
            removeBtn.setAttribute('data-index', i);
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                // Remove this specific image
                removeImage(i);
            });
            
            // Add elements to container
            previewContainer.appendChild(img);
            previewContainer.appendChild(removeBtn);
            imagePreviewArea.appendChild(previewContainer);
        }
        
        // If there are more images than we're showing, add a count indicator
        if (attachedImageUrls.length > displayLimit) {
            const moreIndicator = document.createElement('div');
            moreIndicator.className = 'more-images-indicator';
            moreIndicator.textContent = `+${attachedImageUrls.length - displayLimit} more`;
            imagePreviewArea.appendChild(moreIndicator);
        }
        
        // Add a "clear all" button
        const clearAllBtn = document.createElement('button');
        clearAllBtn.className = 'clear-all-images-btn';
        clearAllBtn.textContent = 'Clear All';
        clearAllBtn.addEventListener('click', clearAttachedImages);
        imagePreviewArea.appendChild(clearAllBtn);
        
        console.log(`🖼️ Updated image previews: ${attachedImageUrls.length} images`);
    }
    
    // Function to remove a specific image by index
    function removeImage(index) {
        // Remove the image from the array
        if (index >= 0 && index < attachedImageUrls.length) {
            attachedImageUrls.splice(index, 1);
            updateImagePreviews();
        }
    }
    
    // Legacy function for single image - redirect to new function
    function showImagePreview(imageUrl) {
        // Add the URL to our array if it's not already there
        if (imageUrl && !attachedImageUrls.includes(imageUrl)) {
            attachedImageUrls.push(imageUrl);
        }
        
        // Update all previews
        updateImagePreviews();
    }
    
    // Clear all attached images
    function clearAttachedImages() {
        attachedImageBlob = null;
        attachedImageUrls = [];
        updateImagePreviews();
    }
    
    // Legacy function for backward compatibility
    function clearAttachedImage() {
        clearAttachedImages();
    }
    
    // Function to update send button state based on image upload status
    function updateSendButtonState() {
        const uploadIndicator = document.getElementById('upload-indicator') || createUploadIndicator();
        
        if (isUploadingImage) {
            // Disable send button while image is uploading
            sendButton.disabled = true;
            sendButton.classList.add('disabled');
            sendButton.title = 'Please wait for image to finish uploading';
            
            // Show upload indicator with spinner icon
            uploadIndicator.style.display = 'flex';
            uploadIndicator.innerHTML = '<i class="fa-solid fa-spinner"></i> Uploading image...';
            
            // Also disable the image upload button during upload
            if (imageUploadButton) {
                imageUploadButton.disabled = true;
                imageUploadButton.classList.add('disabled');
            }
            
            // Disable camera button during upload
            if (cameraButton) {
                cameraButton.disabled = true;
                cameraButton.classList.add('disabled');
            }
        } else {
            // Enable send button when image upload is complete
            sendButton.disabled = false;
            sendButton.classList.remove('disabled');
            sendButton.title = '';
            
            // Hide the upload indicator
            uploadIndicator.style.display = 'none';
            
            // Re-enable image upload button
            if (imageUploadButton) {
                imageUploadButton.disabled = false;
                imageUploadButton.classList.remove('disabled');
            }
            
            // Re-enable camera button
            if (cameraButton) {
                cameraButton.disabled = false;
                cameraButton.classList.remove('disabled');
            }
        }
    }
    
    function stopCameraStream() {
        if (cameraStream.srcObject) {
            const tracks = cameraStream.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            cameraStream.srcObject = null;
        }
    }
    
    async function switchCamera() {
        if (cameras.length > 1) {
            stopCameraStream();
            currentCameraIndex = (currentCameraIndex + 1) % cameras.length;
            
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { deviceId: { exact: cameras[currentCameraIndex].deviceId } }
                });
                cameraStream.srcObject = stream;
            } catch (err) {
                console.error('Error switching camera:', err);
                alert('Failed to switch camera');
            }
        }
    }
    
    async function loadCameraDevices() {
        if (!navigator.mediaDevices?.enumerateDevices) {
            console.warn('enumerateDevices() not supported');
            return;
        }
        
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            cameras = devices.filter(device => device.kind === 'videoinput');
            
            // Enable/disable switch camera button based on available cameras
            switchCameraButton.style.display = cameras.length > 1 ? 'block' : 'none';
        } catch (err) {
            console.error('Error enumerating devices:', err);
        }
    }
    
    // Event Listeners - with null checks
    if (messageInput) {
        messageInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
            
            // Auto-resize textarea
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }
    
    // Add clipboard paste event listener to the message input
    document.addEventListener('paste', function(event) {
        // Check if messageInput exists first
        if (!messageInput) {
            return; // Skip this handler if no message input exists on this page
        }
        
        // Only process if we're focused on the message input or inside the chat container
        if (document.activeElement === messageInput || 
            document.activeElement.closest('.chat-input-container')) {
            
            // Get clipboard data
            const clipboardData = event.clipboardData || window.clipboardData;
            const items = clipboardData.items;
            
            // Check for images in clipboard data
            for (let i = 0; i < items.length; i++) {
                if (items[i].type.indexOf('image') !== -1) {
                    console.log('📎 Image found in clipboard');
                    
                    // Convert image data to a blob
                    const blob = items[i].getAsFile();
                    if (blob) {
                        // Prevent default paste behavior for images
                        event.preventDefault();
                        
                        // Process the image
                        handleImageFile(blob);
                        return;
                    }
                }
            }
        }
    });
    
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    // Initialize model data
    fetchUserPreferences();
    
    // Only initialize model selector related code if the model selector exists on this page
    if (modelSelector) {
        console.log('Model selector found, initializing selector functionality');
        
        // Model preset button click handlers
        if (modelPresetButtons && modelPresetButtons.length > 0) {
            modelPresetButtons.forEach(button => {
                // Find selector icon within this button
                const selectorIcon = button.querySelector('.selector-icon');
                
                // Add click event to the model button
                button.addEventListener('click', function(e) {
                    const presetId = this.getAttribute('data-preset-id');
                    
                    // If shift key or right-click, open model selector
                    if (e.shiftKey || e.button === 2) {
                        e.preventDefault();
                        openModelSelector(presetId, this);
                        return;
                    }
                    
                    // Otherwise, select this preset
                    selectPresetButton(presetId);
                });
                
                // Add context menu to open selector
                button.addEventListener('contextmenu', function(e) {
                    e.preventDefault();
                    const presetId = this.getAttribute('data-preset-id');
                    openModelSelector(presetId, this);
                });
                
                // Add click event to the selector icon
                if (selectorIcon) {
                    selectorIcon.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation(); // Prevent button click from firing
                        
                        const presetId = button.getAttribute('data-preset-id');
                        openModelSelector(presetId, button);
                    });
                }
            });
        }
        
        // Close model selector on button click (only if close button exists)
        if (closeSelector) {
            closeSelector.addEventListener('click', function() {
                closeModelSelector();
            });
        }
        
        // Close model selector when clicking outside
        document.addEventListener('click', function(e) {
            if (modelSelector.style.display === 'block' && 
                !modelSelector.contains(e.target) && 
                !e.target.matches('.model-preset-btn') && 
                !e.target.closest('.model-preset-btn')) {
                closeModelSelector();
            }
        });
        
        // Search functionality for model selector (only if search input exists)
        if (modelSearch) {
            modelSearch.addEventListener('input', function() {
                filterModelList(this.value.toLowerCase());
            });
        }
    } else {
        console.log('Model selector not found on this page, skipping selector initialization');
    }
    
    // Function to select a preset button and update the current model
    function selectPresetButton(presetId) {
        // Check if this is a premium preset (all except preset 6)
        if (presetId !== '6') {
            // Check premium access before allowing selection of premium model
            if (!checkPremiumAccess('premium_model')) {
                // If access check failed, select the free model instead
                console.log('Premium access denied, selecting free model instead');
                selectPresetButton('6');
                return;
            }
        }
        
        // Remove active class from all buttons
        modelPresetButtons.forEach(btn => btn.classList.remove('active'));
        
        // Add active class to selected button
        const activeButton = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
        if (activeButton) {
            activeButton.classList.add('active');
            activePresetButton = activeButton;
            currentPresetId = presetId;
            
            // Get the model ID for this preset
            currentModel = userPreferences[presetId] || defaultModels[presetId];
            console.log(`Selected preset ${presetId} with model: ${currentModel}`);
            
            // Update multimodal controls based on the selected model
            updateMultimodalControls(currentModel);
        }
    }
    
    // Function to update multimodal controls (image upload, camera) based on model capability
    function updateMultimodalControls(modelId) {
        // Find the model in allModels
        const model = allModels.find(m => m.id === modelId);
        
        // Check if model is multimodal - preset 4 (GPT-4o) is always treated as multimodal
        const isPreset4 = modelId === defaultModels['4']; // GPT-4o is preset 4
        const isMultimodalModel = (model && model.is_multimodal === true) || isPreset4;
        
        console.log(`🖼️ Multimodal UI check for ${modelId}: isMultimodalModel=${isMultimodalModel}, isPreset4=${isPreset4}`);
        
        // Show/hide upload and camera buttons (if they exist on this page)
        if (imageUploadButton) {
            imageUploadButton.style.display = isMultimodalModel ? 'inline-flex' : 'none';
        }
        
        // Only show camera button if browser supports it and it exists on this page
        const hasCamera = !!navigator.mediaDevices?.getUserMedia;
        if (cameraButton) {
            cameraButton.style.display = isMultimodalModel && hasCamera ? 'inline-flex' : 'none';
        }
        
        // If switching to a non-multimodal model, clear any attached image (if we're on a page with image functionality)
        if (!isMultimodalModel && typeof clearAttachedImage === 'function') {
            clearAttachedImage();
        }
        
        return isMultimodalModel; // Return for testing purposes
    }
    
    // Function to fetch user preferences for model presets
    function fetchUserPreferences() {
        fetch('/get_preferences')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.preferences) {
                    // Validate preferences to ensure presets 1-5 don't have free models
                    const validatedPreferences = {};
                    
                    for (const presetId in data.preferences) {
                        const modelId = data.preferences[presetId];
                        const isFreeModel = modelId.includes(':free');
                        
                        // If it's preset 1-5 and has a free model, use the default non-free model
                        if (presetId !== '6' && isFreeModel) {
                            console.warn(`Preset ${presetId} has a free model (${modelId}), reverting to default`);
                            validatedPreferences[presetId] = defaultModels[presetId];
                            
                            // Note: Preset 4 is our vision model (openai/gpt-4o) for multimodal capabilities
                            if (presetId === '4') {
                                console.log(`Ensuring preset 4 uses vision-capable model: ${defaultModels['4']}`);
                            }
                        } else {
                            validatedPreferences[presetId] = modelId;
                        }
                    }
                    
                    userPreferences = validatedPreferences;
                    console.log('Loaded user preferences:', userPreferences);
                    
                    // Update button text to reflect preferences
                    updatePresetButtonLabels();
                    
                    // Select the first preset by default
                    selectPresetButton('1');
                }
                
                // After loading preferences, fetch available models
                fetchAvailableModels();
            })
            .catch(error => {
                console.error('Error fetching preferences:', error);
                // Still try to fetch models if preferences fail
                fetchAvailableModels();
                
                // Use defaults and select first preset
                selectPresetButton('1');
            });
    }
    
    // Function to update the model preset button labels
    function updatePresetButtonLabels() {
        for (const presetId in userPreferences) {
            const modelId = userPreferences[presetId];
            const button = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
            if (button) {
                const nameSpan = button.querySelector('.model-name');
                if (nameSpan) {
                    // Special handling for preset 6 (Free Model)
                    if (presetId === '6') {
                        nameSpan.textContent = 'FREE - ' + formatModelName(modelId, true);
                    } else {
                        nameSpan.textContent = formatModelName(modelId);
                    }
                }
            }
        }
    }
    
    // Function to format model ID into a display name
    function formatModelName(modelId, isFreePrefixed = false) {
        if (!modelId) return 'Unknown';
        
        // Handle special cases for free models
        if (modelId.includes(':free') && !isFreePrefixed) {
            return 'Free Model';
        }
        
        // Split by / and get the last part
        const parts = modelId.split('/');
        let name = parts[parts.length - 1];
        
        // Remove the :free suffix if present
        name = name.replace(':free', '');
        
        // Replace dashes with spaces and capitalize
        name = name.replace(/-/g, ' ');
        
        // Shorten common prefixes
        name = name
            .replace('claude ', 'Claude ')
            .replace('gemini ', 'Gemini ')
            .replace('gpt ', 'GPT ')
            .replace('mistral ', 'Mistral ')
            .replace('llama ', 'Llama ');
        
        // Truncate if too long - different lengths depending on context
        // Increase max length to avoid excessive truncation
        const maxLength = isFreePrefixed ? 12 : 20;
        if (name.length > maxLength) {
            name = name.substring(0, maxLength - 3) + '...';
        }
        
        return name;
    }
    
    // Function to fetch available models from OpenRouter
    function fetchAvailableModels() {
        fetch('/models')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.data && Array.isArray(data.data)) {
                    allModels = data.data;
                    console.log(`Loaded ${allModels.length} models from OpenRouter`);
                    
                    // Update multimodal controls for the current model
                    if (currentModel) {
                        updateMultimodalControls(currentModel);
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching models:', error);
            });
    }
    
    // Function to open the model selector for a specific preset
    function openModelSelector(presetId, buttonElement) {
        // Set current editing preset
        currentlyEditingPresetId = presetId;
        
        // Position the selector relative to the button
        const button = buttonElement || document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
        if (button) {
            const rect = button.getBoundingClientRect();
            const selectorRect = modelSelector.getBoundingClientRect();
            
            // Calculate position
            // First try to position above the button with a gap
            const gap = 10; // Gap in pixels between button and selector
            
            // Get dimensions
            const selectorHeight = selectorRect.height || 300; // Default if not visible yet
            let topPosition = rect.top - selectorHeight - gap;
            
            // Check if there's enough space above
            if (topPosition < 0) {
                // Not enough space above, position below the button
                topPosition = rect.bottom + gap;
            }
            
            // Center horizontally relative to the button
            const leftPosition = rect.left + (rect.width / 2) - 150; // 150 = half of selector width
            
            // Apply the position
            modelSelector.style.top = `${topPosition}px`;
            modelSelector.style.left = `${leftPosition}px`;
            
            // Make visible
            modelSelector.style.display = 'block';
            
            // Clear search input
            modelSearch.value = '';
            
            // Populate model list for this preset
            populateModelList(presetId);
        }
    }
    
    // Function to close the model selector
    function closeModelSelector() {
        modelSelector.style.display = 'none';
        currentlyEditingPresetId = null;
    }
    
    // Function to populate the model list based on preset filters
    function populateModelList(presetId) {
        // Clear existing items
        modelList.innerHTML = '';
        
        if (!allModels || allModels.length === 0) {
            const placeholder = document.createElement('li');
            placeholder.textContent = 'Loading models...';
            modelList.appendChild(placeholder);
            return;
        }
        
        // Get filter function for this preset
        const filterFn = presetFilters[presetId] || (() => true);
        
        // Filter and sort models
        const filteredModels = allModels
            .filter(filterFn)
            .sort((a, b) => {
                // Special handling for preset 4 (vision models)
                if (presetId === '4') {
                    // Always put GPT-4o at the top
                    if (a.id === 'openai/gpt-4o') return -1;
                    if (b.id === 'openai/gpt-4o') return 1;
                    
                    // Put Claude vision models next
                    const aIsClaudeVision = a.id.includes('claude') && a.is_multimodal;
                    const bIsClaudeVision = b.id.includes('claude') && b.is_multimodal;
                    
                    if (aIsClaudeVision && !bIsClaudeVision) return -1;
                    if (!aIsClaudeVision && bIsClaudeVision) return 1;
                    
                    // Put Gemini vision models next
                    const aIsGeminiVision = a.id.includes('gemini') && a.is_multimodal;
                    const bIsGeminiVision = b.id.includes('gemini') && b.is_multimodal;
                    
                    if (aIsGeminiVision && !bIsGeminiVision) return -1;
                    if (!aIsGeminiVision && bIsGeminiVision) return 1;
                }
                
                // Free models at the bottom
                if (a.is_free && !b.is_free) return 1;
                if (!a.is_free && b.is_free) return -1;
                
                // Sort by pricing (cheapest first)
                const aPrice = a.pricing?.prompt || 0;
                const bPrice = b.pricing?.prompt || 0;
                return aPrice - bPrice;
            });
        
        // Add each model to the list
        filteredModels.forEach(model => {
            const li = document.createElement('li');
            li.dataset.modelId = model.id;
            
            // Create model name element
            const nameSpan = document.createElement('span');
            nameSpan.className = 'model-name';
            nameSpan.textContent = model.name;
            
            // Create provider badge
            const providerSpan = document.createElement('span');
            providerSpan.className = 'model-provider';
            providerSpan.textContent = model.id.split('/')[0];
            
            // Add badge for free models
            if (model.is_free) {
                const freeTag = document.createElement('span');
                freeTag.className = 'free-tag';
                freeTag.textContent = 'FREE';
                li.appendChild(freeTag);
            }
            
            li.appendChild(nameSpan);
            li.appendChild(providerSpan);
            
            // Add click handler to select this model
            li.addEventListener('click', function() {
                selectModelForPreset(currentlyEditingPresetId, model.id);
            });
            
            modelList.appendChild(li);
        });
        
        // If no models match the filter
        if (filteredModels.length === 0) {
            const noResults = document.createElement('li');
            noResults.textContent = 'No models found';
            modelList.appendChild(noResults);
        }
    }
    
    // Function to filter the model list by search term
    function filterModelList(searchTerm) {
        const items = modelList.querySelectorAll('li');
        
        items.forEach(item => {
            const modelName = item.querySelector('.model-name')?.textContent.toLowerCase() || '';
            const modelProvider = item.querySelector('.model-provider')?.textContent.toLowerCase() || '';
            
            if (modelName.includes(searchTerm) || modelProvider.includes(searchTerm)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }
    
    // Function to select a model for a preset and save the preference
    function selectModelForPreset(presetId, modelId) {
        // Check if trying to assign a free model to a non-free preset
        const isFreeModel = modelId.includes(':free');
        if (presetId !== '6' && isFreeModel) {
            alert('Free models can only be selected for Preset 6');
            return;
        }
        
        // Update the UI
        const button = document.querySelector(`.model-preset-btn[data-preset-id="${presetId}"]`);
        if (button) {
            const nameSpan = button.querySelector('.model-name');
            if (nameSpan) {
                // Special handling for preset 6 (Free Model)
                if (presetId === '6') {
                    nameSpan.textContent = 'FREE - ' + formatModelName(modelId, true);
                } else {
                    nameSpan.textContent = formatModelName(modelId);
                }
            }
        }
        
        // Update local state
        userPreferences[presetId] = modelId;
        
        // If this is the active preset, update the current model
        if (presetId === currentPresetId) {
            currentModel = modelId;
            
            // Update multimodal controls based on the selected model
            updateMultimodalControls(modelId);
        }
        
        // Save preference to server
        saveModelPreference(presetId, modelId);
        
        // Close the selector
        closeModelSelector();
    }
    
    // Function to save model preference to the server
    function saveModelPreference(presetId, modelId) {
        fetch('/save_preference', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                preset_id: presetId,
                model_id: modelId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Preference saved:', data);
        })
        .catch(error => {
            console.error('Error saving preference:', error);
        });
    }
    
    // New chat button - with null check
    if (newChatButton) {
        newChatButton.addEventListener('click', function() {
            // Clear chat messages except the welcome message
            clearChat();
        });
    }
    
    // Clear conversations button - with null check
    if (clearConversationsButton) {
        clearConversationsButton.addEventListener('click', function() {
            // Clear chat and reset conversation items in sidebar
            clearChat();
            // In a real app, you would also clear the storage/backend
        });
    }
    
    // Example question button - with null check
    if (exampleQuestionButton && messageInput) {
        exampleQuestionButton.addEventListener('click', function() {
            const exampleQuestions = [
                "What are the major differences between renewable and fossil fuel energy sources?",
                "Can you explain how artificial intelligence works in simple terms?",
                "What are some effective strategies for reducing carbon emissions?",
                "How does quantum computing differ from classical computing?",
                "What are the potential implications of gene editing technologies?"
            ];
            
            // Select a random example question
            const randomQuestion = exampleQuestions[Math.floor(Math.random() * exampleQuestions.length)];
            
            // Set the input value and trigger sending
            messageInput.value = randomQuestion;
            sendMessage();
        });
    }
    
    // Function to send message
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message && attachedImageUrls.length === 0) return;
        
        // Clear input
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        // First time? Clear welcome message
        if (document.querySelector('.welcome-container')) {
            chatMessages.innerHTML = '';
        }
        
        // Check if we're sending a multimodal message with images
        if (attachedImageUrls.length > 0) {
            // Create a standardized content array for user messages with images
            const userContent = [
                { type: 'text', text: message || 'Image:' }
            ];
            
            // Add all image URLs to the content array
            for (const imageUrl of attachedImageUrls) {
                userContent.push({
                    type: 'image_url',
                    image_url: { url: imageUrl }
                });
            }
            
            // Add user message with images to chat
            addMessage(userContent, 'user');
        } else {
            // Add text-only user message to chat
            addMessage(message, 'user');
        }
        
        // Show typing indicator
        const typingIndicator = addTypingIndicator();
        
        // Send message to backend
        sendMessageToBackend(message, currentModel, typingIndicator);
    }
    
    // Function to add message to chat
    function addMessage(content, sender, isTyping = false, metadata = null) {
        // Create the main message container
        const messageElement = document.createElement('div');
        messageElement.className = `message message-${sender}`;
        messageElement.dataset.messageId = metadata ? metadata.id : Date.now(); // Use actual message ID if available
        
        // Create avatar
        const avatar = document.createElement('div');
        avatar.className = `message-avatar ${sender}`;
        
        if (sender === 'user') {
            avatar.textContent = 'U';
        } else {
            avatar.textContent = 'A';
        }
        
        // Create wrapper for content, actions, and metadata
        const messageWrapper = document.createElement('div');
        messageWrapper.className = 'message-wrapper';
        
        // Create content container
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (isTyping) {
            messageContent.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        } else {
            // Handle both standardized content array format and plain text
            if (typeof content === 'object' && Array.isArray(content)) {
                console.log('📦 Message content is in array format:', content);
                
                // First collect all content items by type
                let textItems = [];
                let imageItems = [];
                
                content.forEach(item => {
                    if (item.type === 'text') {
                        textItems.push(item);
                    } else if (item.type === 'image_url' && item.image_url?.url) {
                        imageItems.push(item);
                    }
                });
                
                // Add all text content first
                textItems.forEach(item => {
                    const textDiv = document.createElement('div');
                    textDiv.innerHTML = formatMessage(item.text);
                    messageContent.appendChild(textDiv);
                });
                
                // Then add images
                if (imageItems.length > 0) {
                    console.log(`📸 Message has ${imageItems.length} images`);
                    
                    // Create a container for all images
                    const imageContainer = document.createElement('div');
                    
                    // Use different layouts depending on number of images
                    if (imageItems.length === 1) {
                        // Single image - standard layout
                        imageContainer.className = 'message-image-container';
                        
                        const messageImage = document.createElement('img');
                        messageImage.className = 'message-image';
                        messageImage.src = imageItems[0].image_url.url;
                        messageImage.alt = 'Attached image';
                        messageImage.addEventListener('click', () => {
                            window.open(imageItems[0].image_url.url, '_blank');
                        });
                        
                        imageContainer.appendChild(messageImage);
                    } else {
                        // Multiple images - use grid layout
                        imageContainer.className = 'message-multi-image';
                        
                        // Add each image as a thumbnail
                        imageItems.forEach((item, index) => {
                            const wrapper = document.createElement('div');
                            wrapper.className = 'message-image-wrapper';
                            
                            const thumbnail = document.createElement('img');
                            thumbnail.className = 'message-thumbnail';
                            thumbnail.src = item.image_url.url;
                            thumbnail.alt = `Image ${index + 1}`;
                            thumbnail.addEventListener('click', () => {
                                window.open(item.image_url.url, '_blank');
                            });
                            
                            wrapper.appendChild(thumbnail);
                            imageContainer.appendChild(wrapper);
                        });
                    }
                    
                    messageContent.appendChild(imageContainer);
                }
                
            } else {
                // Legacy format - just text content
                messageContent.innerHTML = formatMessage(content);
                
                // Check if this message has an image (from metadata)
                if (metadata && metadata.image_url) {
                    console.log('📸 Message has image URL from metadata:', metadata.image_url);
                    
                    // Create image container
                    const imageContainer = document.createElement('div');
                    imageContainer.className = 'message-image-container';
                    
                    // Create and add the image
                    const messageImage = document.createElement('img');
                    messageImage.className = 'message-image';
                    messageImage.src = metadata.image_url;
                    messageImage.alt = 'Attached image';
                    messageImage.addEventListener('click', () => {
                        // Open image in full-screen or new tab on click
                        window.open(metadata.image_url, '_blank');
                    });
                    
                    imageContainer.appendChild(messageImage);
                    messageContent.appendChild(imageContainer);
                }
            }
        }
        
        // Add message content to wrapper
        messageWrapper.appendChild(messageContent);
        
        // Only add action buttons and metadata if not a typing indicator
        if (!isTyping) {
            // Create action buttons container
            const actionsContainer = document.createElement('div');
            actionsContainer.className = 'message-actions';
            
            // Add copy button for all messages
            const copyButton = document.createElement('button');
            copyButton.className = 'copy-btn';
            copyButton.title = 'Copy text';
            copyButton.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
            copyButton.addEventListener('click', function() {
                copyMessageText(messageElement);
            });
            actionsContainer.appendChild(copyButton);
            
            // For assistant messages only, add additional buttons
            if (sender === 'assistant') {
                // Share button (using conversation share ID)
                const shareButton = document.createElement('button');
                shareButton.className = 'share-btn';
                shareButton.title = 'Copy share link';
                shareButton.innerHTML = '<i class="fa-solid fa-share-nodes"></i> Share';
                shareButton.addEventListener('click', function() {
                    shareConversation(messageElement);
                });
                actionsContainer.appendChild(shareButton);
                
                // Upvote button
                const upvoteButton = document.createElement('button');
                upvoteButton.className = 'upvote-btn';
                upvoteButton.title = 'Upvote';
                upvoteButton.innerHTML = '<i class="fa-regular fa-thumbs-up"></i>';
                // If there's a rating of 1, add the 'voted' class
                if (metadata && metadata.rating === 1) {
                    upvoteButton.classList.add('voted');
                }
                upvoteButton.addEventListener('click', function() {
                    rateMessage(messageElement, 1);
                });
                actionsContainer.appendChild(upvoteButton);
                
                // Downvote button
                const downvoteButton = document.createElement('button');
                downvoteButton.className = 'downvote-btn';
                downvoteButton.title = 'Downvote';
                downvoteButton.innerHTML = '<i class="fa-regular fa-thumbs-down"></i>';
                // If there's a rating of -1, add the 'voted' class
                if (metadata && metadata.rating === -1) {
                    downvoteButton.classList.add('voted');
                }
                downvoteButton.addEventListener('click', function() {
                    rateMessage(messageElement, -1);
                });
                actionsContainer.appendChild(downvoteButton);
                
                // Add metadata display for assistant messages
                if (metadata) {
                    const metadataContainer = document.createElement('div');
                    metadataContainer.className = 'message-metadata';
                    
                    // If we have model and token information, display it
                    let metadataText = '';
                    
                    if (metadata.model_id_used) {
                        // Format and shorten the model name
                        const shortModelName = formatModelName(metadata.model_id_used);
                        metadataText += `Model: ${shortModelName}`;
                    } else if (metadata.model) {
                        const shortModelName = formatModelName(metadata.model);
                        metadataText += `Model: ${shortModelName}`;
                    }
                    
                    if (metadata.prompt_tokens && metadata.completion_tokens) {
                        if (metadataText) metadataText += ' · ';
                        metadataText += `Tokens: ${metadata.prompt_tokens} prompt + ${metadata.completion_tokens} completion`;
                    }
                    
                    metadataContainer.textContent = metadataText;
                    if (metadataText) {
                        messageWrapper.appendChild(metadataContainer);
                    }
                }
            }
            
            // Add actions container to wrapper
            messageWrapper.appendChild(actionsContainer);
        }
        
        // Assemble the message element
        messageElement.appendChild(avatar);
        messageElement.appendChild(messageWrapper);
        
        // Add to chat container
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageElement;
    }
    
    // Function to add typing indicator
    function addTypingIndicator() {
        return addMessage('', 'assistant', true);
    }
    
    // Function to fetch conversations from the backend
    function fetchConversations(bustCache = false) {
        // ALWAYS use cache busting to ensure we get the latest titles
        const url = `/conversations?_=${Date.now()}`;
        
        console.log("Fetching conversations list with cache busting");
        
        // Show loading indicator if conversations list element exists
        if (conversationsList) {
            // Check if loading indicator already exists
            let loadingIndicator = conversationsList.querySelector('.loading-indicator');
            if (!loadingIndicator) {
                // Create loading indicator if it doesn't exist
                loadingIndicator = document.createElement('div');
                loadingIndicator.className = 'loading-indicator';
                loadingIndicator.innerHTML = `
                    <div class="loading-spinner"></div>
                    <div class="loading-text">Loading conversations...</div>
                `;
                conversationsList.innerHTML = '';
                conversationsList.appendChild(loadingIndicator);
            }
        }
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("Got conversations data:", data);
                if (data.conversations && data.conversations.length > 0) {
                    // Clear existing conversations
                    if (conversationsList) {
                        console.log("Clearing and rebuilding conversation list...");
                        conversationsList.innerHTML = '';
                        
                        // Add each conversation to the sidebar
                        data.conversations.forEach(conversation => {
                            console.log(`Adding conversation to UI: ID=${conversation.id}, Title='${conversation.title}'`);
                            const conversationItem = document.createElement('div');
                            conversationItem.className = 'conversation-item';
                            conversationItem.dataset.id = conversation.id;
                            
                            // Create title and date elements to match the HTML structure
                            const titleDiv = document.createElement('div');
                            titleDiv.className = 'conversation-title';
                            titleDiv.textContent = conversation.title;
                            
                            const dateDiv = document.createElement('div');
                            dateDiv.className = 'conversation-date';
                            
                            // Format the date (using relative time if possible)
                            const createdDate = new Date(conversation.created_at);
                            const now = new Date();
                            const diffDays = Math.floor((now - createdDate) / (1000 * 60 * 60 * 24));
                            
                            if (diffDays < 1) {
                                dateDiv.textContent = 'Today';
                            } else if (diffDays === 1) {
                                dateDiv.textContent = 'Yesterday';
                            } else if (diffDays < 7) {
                                dateDiv.textContent = `${diffDays} days ago`;
                            } else {
                                dateDiv.textContent = createdDate.toLocaleDateString();
                            }
                            
                            // Append title and date to conversation item
                            conversationItem.appendChild(titleDiv);
                            conversationItem.appendChild(dateDiv);
                            
                            // Add click event to load conversation
                            conversationItem.addEventListener('click', function() {
                                console.log(`Loading conversation: ${conversation.id}`);
                                
                                // Remove active class from all conversation items
                                const allItems = conversationsList.querySelectorAll('.conversation-item');
                                allItems.forEach(item => item.classList.remove('active'));
                                
                                // Add active class to this item
                                conversationItem.classList.add('active');
                                
                                // Load the conversation
                                loadConversation(conversation.id);
                            });
                            
                            conversationsList.appendChild(conversationItem);
                        });
                        
                        // Verify the DOM was updated correctly
                        const itemsAdded = conversationsList.querySelectorAll('.conversation-item');
                        console.log(`Conversation list rebuilt with ${itemsAdded.length} items`);
                    } else {
                        console.error("Cannot update conversation list - conversationsList element not found");
                    }
                } else {
                    console.warn("No conversations returned from server or empty array");
                }
            })
            .catch(error => {
                console.error('Error fetching conversations:', error);
            });
    }
    
    // Function to load a specific conversation
    function loadConversation(conversationId) {
        // Clear the current chat
        chatMessages.innerHTML = '';
        messageHistory = [];
        currentConversationId = conversationId;
        
        console.log(`Loading conversation ID: ${conversationId}`);
        
        // Highlight active conversation in sidebar
        if (conversationsList) {
            const allConversations = conversationsList.querySelectorAll('.conversation-item');
            allConversations.forEach(item => {
                item.classList.remove('active');
                if (item.dataset.id === conversationId.toString()) {
                    item.classList.add('active');
                }
            });
        }
        
        // Add a loading indicator to chat area
        const loadingMessage = document.createElement('div');
        loadingMessage.className = 'system-message';
        loadingMessage.textContent = 'Loading conversation...';
        chatMessages.appendChild(loadingMessage);
        
        // Fetch conversation messages from the server
        fetch(`/conversation/${conversationId}/messages`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Remove loading indicator
                chatMessages.removeChild(loadingMessage);
                
                console.log(`Loaded ${data.messages.length} messages for conversation ${conversationId}`);
                
                // Check if there are messages
                if (data.messages.length === 0) {
                    // Display empty conversation message
                    const emptyMessage = document.createElement('div');
                    emptyMessage.className = 'system-message';
                    emptyMessage.textContent = 'This conversation is empty. Start chatting now!';
                    chatMessages.appendChild(emptyMessage);
                    return;
                }
                
                // Add messages to UI and update message history
                data.messages.forEach(message => {
                    // Add to message history (skip system messages)
                    if (message.role !== 'system') {
                        messageHistory.push({
                            role: message.role,
                            content: message.content
                        });
                    }
                    
                    // Add message to UI (skip system messages)
                    if (message.role !== 'system') {
                        const metadata = {
                            id: message.id,
                            model: message.model,
                            rating: message.rating,
                            created_at: message.created_at,
                            image_url: message.image_url // Include image URL if available
                        };
                        addMessage(message.content, message.role, false, metadata);
                    }
                });
                
                // Scroll to bottom of chat
                chatMessages.scrollTop = chatMessages.scrollHeight;
            })
            .catch(error => {
                console.error('Error loading conversation:', error);
                
                // Remove loading indicator and show error message
                chatMessages.removeChild(loadingMessage);
                
                const errorMessage = document.createElement('div');
                errorMessage.className = 'system-message error';
                errorMessage.textContent = `Error loading conversation: ${error.message}`;
                chatMessages.appendChild(errorMessage);
            });
    }
    
    // Function to send message to backend and process streaming response
    function sendMessageToBackend(message, modelId, typingIndicator) {
        // Check if we need to make a multimodal message
        const isMultimodalMessage = attachedImageUrls.length > 0;
        
        // Always create a content array (OpenRouter's unified format)
        // Even for text-only messages, this ensures consistent payload structure
        let userMessageContent = [
            { type: 'text', text: message }
        ];
        
        // Create payload object with model and conversation info
        const payload = {
            model: modelId,
            stream: true,
            message: message,
            conversation_id: currentConversationId
        };
        
        // Add image objects to content array if available
        if (isMultimodalMessage) {
            // Add each image URL to the content array
            for (const imageUrl of attachedImageUrls) {
                userMessageContent.push({ 
                    type: 'image_url', 
                    image_url: { url: imageUrl } 
                });
            }
            
            // Add first image URL separately for backward compatibility with backend
            // This ensures older endpoints still work
            if (attachedImageUrls.length > 0) {
                payload.image_url = attachedImageUrls[0];
            }
            
            // Add an array of all image URLs as well
            payload.image_urls = attachedImageUrls;
            
            console.log(`📸 Creating multimodal message with ${attachedImageUrls.length} images`);
            
            // Check if the model supports images
            const model = allModels.find(m => m.id === modelId);
            const isMultimodalModel = model && model.is_multimodal === true;
            
            if (!isMultimodalModel) {
                console.warn(`⚠️ Warning: Model ${modelId} does not support images, but images are being sent`);
            }
            
            // Clear all images after sending
            clearAttachedImages();
        }
        
        // Add user message to history with standardized content array format
        messageHistory.push({
            role: 'user',
            content: userMessageContent
        });
        
        // If no model selected, use default
        if (!modelId) {
            modelId = defaultModels['1'];
            console.warn('No model selected, using default:', modelId);
        }
        
        // Add structured message format to payload
        payload.messages = [
            { 
                role: 'user', 
                content: userMessageContent
            }
        ];
        
        // Log the full payload for debugging
        console.log('📤 Sending payload to backend:', JSON.stringify(payload, null, 2));
        
        // Create fetch request to /chat endpoint
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        }).then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            // Setup event source for streaming
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let responseText = '';
            
            // Remove typing indicator
            if (typingIndicator) {
                chatMessages.removeChild(typingIndicator);
            }
            
            // Add empty assistant message
            const assistantMessageElement = addMessage('', 'assistant');
            const messageContent = assistantMessageElement.querySelector('.message-content');
            
            // Function to process chunks
            function processChunks() {
                return reader.read().then(({ done, value }) => {
                    if (done) {
                        console.log("Stream closed by server");
                        // We now let the done/metadata events handle completion
                        return;
                    }
                    
                    // Decode the chunk and add to buffer
                    buffer += decoder.decode(value, { stream: true });
                    
                    // Split by double newlines (SSE standard)
                    const potentialMessages = buffer.split('\n\n');
                    // Keep the last (potentially incomplete) chunk in the buffer
                    buffer = potentialMessages.pop(); // Keep incomplete message in buffer

                    // Process each complete message
                    for (const message of potentialMessages) {
                        if (message.trim() === '') continue;
                        
                        if (message.startsWith('data: ')) {
                            const data = message.substring(6).trim(); // Remove 'data: ' and trim
                            
                            if (!data) continue; // Skip empty data lines

                            try {
                                // Trim the data to ensure there's no whitespace causing parsing issues
                                const trimmedData = data.trim();
                                if (!trimmedData) {
                                    console.log("Empty data after trimming, skipping");
                                    continue;
                                }
                                
                                const parsedData = JSON.parse(trimmedData);
                                console.log("==> Received SSE Data:", parsedData); // ADD THIS LOG
                                
                                // --- Handle different data types ---
                                if (parsedData.type === 'error' || parsedData.error) {
                                    console.log("==> Processing type: error"); // ADD THIS LOG
                                    const errorMsg = parsedData.error || 'Unknown error occurred';
                                    messageContent.innerHTML = `<span class="error">Error: ${errorMsg}</span>`;
                                    console.error("Received error from backend:", errorMsg);
                                    // Optionally re-enable input/button here if desired
                                    // messageInput.disabled = false;
                                    // sendButton.disabled = false;
                                    return; // Stop processing on error
                                
                                } else if (parsedData.type === 'content') {
                                    console.log("==> Processing type: content"); // ADD THIS LOG
                                    // Append content
                                    if (parsedData.content) {
                                        // Track if we need to scroll
                                        const shouldScroll = chatMessages.scrollTop + chatMessages.clientHeight >= chatMessages.scrollHeight - 10;
                                        
                                        responseText += parsedData.content;
                                        // Use your existing formatMessage function
                                        messageContent.innerHTML = formatMessage(responseText); 
                                        
                                        // Only auto-scroll if user was already at the bottom
                                        if (shouldScroll) {
                                            chatMessages.scrollTop = chatMessages.scrollHeight;
                                        }
                                    }
                                    // Update conversation ID if it's the first message
                                    if (parsedData.conversation_id) {
                                        // Always update the current conversation ID to ensure it's correct
                                        currentConversationId = parsedData.conversation_id;
                                        console.log(`Setting conversation ID: ${currentConversationId}`);
                                        // Store conversation ID on the message element for reference
                                        assistantMessageElement.dataset.conversationId = currentConversationId;
                                        
                                        // If this is a new conversation, refresh the list immediately
                                        if (!document.querySelector(`.conversation-item[data-id="${currentConversationId}"]`)) {
                                            console.log("New conversation detected, refreshing list");
                                            fetchConversations(true);
                                        }
                                    }
                                } else if (parsedData.type === 'reasoning') {
                                    console.log("==> Processing type: reasoning");
                                    
                                    if (parsedData.reasoning) {
                                        // Get or create the reasoning container
                                        let reasoningContainer = assistantMessageElement.querySelector('.message-reasoning');
                                        if (!reasoningContainer) {
                                            reasoningContainer = document.createElement('div');
                                            reasoningContainer.className = 'message-reasoning';
                                            
                                            // Create a collapsible header
                                            const reasoningHeader = document.createElement('div');
                                            reasoningHeader.className = 'reasoning-header';
                                            reasoningHeader.innerHTML = '<span class="reasoning-toggle">▶</span> View Reasoning';
                                            reasoningHeader.addEventListener('click', function() {
                                                const reasoningContent = this.nextElementSibling;
                                                const toggle = this.querySelector('.reasoning-toggle');
                                                
                                                if (reasoningContent.style.display === 'none' || !reasoningContent.style.display) {
                                                    reasoningContent.style.display = 'block';
                                                    toggle.textContent = '▼';
                                                    this.parentElement.classList.add('reasoning-expanded');
                                                } else {
                                                    reasoningContent.style.display = 'none';
                                                    toggle.textContent = '▶';
                                                    this.parentElement.classList.remove('reasoning-expanded');
                                                }
                                            });
                                            
                                            // Create content container
                                            const reasoningContent = document.createElement('div');
                                            reasoningContent.className = 'reasoning-content';
                                            reasoningContent.style.display = 'none'; // Collapsed by default
                                            
                                            reasoningContainer.appendChild(reasoningHeader);
                                            reasoningContainer.appendChild(reasoningContent);
                                            
                                            // Insert after the main message content
                                            const messageWrapper = assistantMessageElement.querySelector('.message-wrapper');
                                            if (messageWrapper) {
                                                const metadataContainer = messageWrapper.querySelector('.message-metadata');
                                                if (metadataContainer) {
                                                    messageWrapper.insertBefore(reasoningContainer, metadataContainer);
                                                } else {
                                                    messageWrapper.appendChild(reasoningContainer);
                                                }
                                            }
                                        }
                                        
                                        // Append the reasoning chunk to the content
                                        const reasoningContent = reasoningContainer.querySelector('.reasoning-content');
                                        reasoningContent.textContent += parsedData.reasoning;
                                    }
                                
                                } else if (parsedData.type === 'metadata') {
                                    console.log("==> Processing type: metadata"); 
                                    // Metadata received (usually after content stream ends)
                                    console.log("Received metadata:", parsedData.metadata);
                                    if (parsedData.metadata) {
                                        const meta = parsedData.metadata;
                                        
                                        // Set the definitive message ID on the element
                                        assistantMessageElement.dataset.messageId = meta.id;
                                        
                                        // Update/Create metadata display section
                                        const messageWrapper = assistantMessageElement.querySelector('.message-wrapper');
                                        if (messageWrapper) { // Check if wrapper exists
                                            let metadataContainer = messageWrapper.querySelector('.message-metadata');
                                            if (!metadataContainer) {
                                                metadataContainer = document.createElement('div');
                                                metadataContainer.className = 'message-metadata';
                                                // Insert metadata before action buttons if they exist
                                                const actionsContainer = messageWrapper.querySelector('.message-actions');
                                                if (actionsContainer) {
                                                    messageWrapper.insertBefore(metadataContainer, actionsContainer);
                                                } else {
                                                    // Append if actions aren't there (e.g., if they load later)
                                                    messageWrapper.appendChild(metadataContainer); 
                                                }
                                            }
                                            
                                            // Format metadata text
                                            let metadataText = '';
                                            const modelName = meta.model_id_used ? formatModelName(meta.model_id_used) : 'N/A';
                                            metadataText += `Model: ${modelName}`;
                                            
                                            if (meta.prompt_tokens !== null && meta.completion_tokens !== null) {
                                                 metadataText += ` · Tokens: ${meta.prompt_tokens} prompt + ${meta.completion_tokens} completion`;
                                            }
                                            console.log("Setting metadata text:", metadataText);
                                            metadataContainer.textContent = metadataText;
                                            
                                            // Add a class to highlight the metadata as visible
                                            metadataContainer.classList.add('metadata-visible');
                                        }

                                        // Update action buttons now that we have the final message ID
                                        updateActionButtonsWithMessageId(assistantMessageElement, meta.id);
                                    }
                                
                                } else if (parsedData.type === 'done') {
                                    console.log("==> Processing type: done"); // ADD THIS LOG
                                    // Stream finished successfully
                                    console.log("Stream finished event received.");
                                    
                                    // Ensure the final response text is added to JS history
                                    if (responseText && (!messageHistory.length || messageHistory[messageHistory.length - 1]?.role !== 'assistant')) {
                                         // Add only if history is empty or last message wasn't assistant's
                                         // This prevents duplicates if content was added earlier
                                        messageHistory.push({
                                            role: 'assistant',
                                            content: responseText 
                                        });
                                        console.log("Added final assistant response to JS history.");
                                    } else if (responseText && messageHistory.length > 0 && messageHistory[messageHistory.length - 1]?.role === 'assistant') {
                                        // Update the last history entry's content if needed (less likely needed now)
                                        // messageHistory[messageHistory.length - 1].content = responseText;
                                    }
                                    
                                    // Re-enable input, etc. 
                                    // messageInput.disabled = false;
                                    // sendButton.disabled = false;
                                    
                                    // After conversation completes, refresh the conversation list to get updated titles
                                    // Schedule a single refresh after a 3-second delay
                                    // This gives the backend time to generate the title
                                    console.log("Scheduling a 3-second delayed refresh to fetch updated title...");
                                    
                                    setTimeout(() => {
                                        console.log("Refreshing conversation list after 3s delay to get updated title");
                                        fetchConversations(true);
                                    }, 3000);
                                    
                                    return; // Exit the processing loop
                                } else {
                                    console.warn("==> Received unknown data type:", parsedData.type, parsedData); // ADD THIS LOG
                                }
                                
                            } catch (error) {
                                console.error('Error parsing SSE data JSON:', error, data);
                                // messageContent.innerHTML = `<span class="error">Error processing response data.</span>`;
                                // return; // Stop processing on parsing error
                            }
                        } else {
                            // Handle lines that don't start with 'data: ' if necessary (e.g., comments)
                            // console.log("Received non-data line:", message); 
                        }
                    } // End of loop processing complete messages
                    
                    // Continue reading from the stream
                    return processChunks();
                }); // End of reader.read().then()
            } // End of processChunks function definition

            // Helper function to update action buttons with the message ID
            function updateActionButtonsWithMessageId(messageElement, messageId) {
                // Ensure messageElement is valid
                if (!messageElement) return; 
                
                const upvoteBtn = messageElement.querySelector('.upvote-btn');
                const downvoteBtn = messageElement.querySelector('.downvote-btn');
                const copyBtn = messageElement.querySelector('.copy-btn');
                const shareBtn = messageElement.querySelector('.share-btn');

                // Check if buttons exist before setting dataset properties
                if (upvoteBtn) upvoteBtn.dataset.messageId = messageId;
                if (downvoteBtn) downvoteBtn.dataset.messageId = messageId;
                if (copyBtn) copyBtn.dataset.messageId = messageId; 
                if (shareBtn) shareBtn.dataset.messageId = messageId;
                
                // If using delegated listeners, no need to re-attach handlers.
                // If attaching directly in addMessage, ensure they are attached
                // after the message ID is set.
            }
            
            return processChunks();
        }).catch(error => {
            console.error('Error sending message:', error);
            
            // Remove typing indicator if it exists
            if (typingIndicator && typingIndicator.parentNode) {
                chatMessages.removeChild(typingIndicator);
            }
            
            // Add error message
            const errorMessage = addMessage(`Error: ${error.message}`, 'assistant');
            errorMessage.querySelector('.message-content').classList.add('error');
        });
    }
    
    // Function to format message with markdown, code blocks, etc.
    function formatMessage(text) {
        // Simple markdown-like formatting (this could be expanded or replaced with a proper markdown library)
        
        // Code blocks
        text = text.replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>');
        
        // Inline code
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Bold
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Italic
        text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        // Line breaks
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }
    
    // Function to copy message text to clipboard
    function copyMessageText(messageElement) {
        const messageContent = messageElement.querySelector('.message-content');
        
        // Handle multimodal messages properly by excluding image containers
        const tempElement = document.createElement('div');
        tempElement.innerHTML = messageContent.innerHTML;
        
        // Remove any image containers before copying
        const imageContainers = tempElement.querySelectorAll('.message-image-container');
        imageContainers.forEach(container => container.remove());
        
        // Get the text content without HTML formatting
        const textToCopy = tempElement.textContent || tempElement.innerText;
        
        navigator.clipboard.writeText(textToCopy)
            .then(() => {
                // Visual feedback that copy worked
                const copyButton = messageElement.querySelector('.copy-btn');
                copyButton.innerHTML = '<i class="fa-solid fa-check"></i> Copied';
                copyButton.classList.add('copied');
                
                // Reset after 2 seconds
                setTimeout(() => {
                    copyButton.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
                    copyButton.classList.remove('copied');
                }, 2000);
            })
            .catch(err => {
                console.error('Error copying text: ', err);
                alert('Failed to copy text. Please try again.');
            });
    }
    
    // Function to share conversation
    function shareConversation(messageElement) {
        // Get the current URL and add a share parameter
        const shareButton = messageElement.querySelector('.share-btn');
        
        if (currentConversationId) {
            // Use fetch to get a shareable link from the server
            fetch(`/conversation/${currentConversationId}/share`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.share_url) {
                    const shareUrl = window.location.origin + data.share_url;
                    navigator.clipboard.writeText(shareUrl)
                        .then(() => {
                            // Visual feedback
                            shareButton.innerHTML = '<i class="fa-solid fa-check"></i> Copied link';
                            
                            // Reset after 2 seconds
                            setTimeout(() => {
                                shareButton.innerHTML = '<i class="fa-solid fa-share-nodes"></i> Share';
                            }, 2000);
                        })
                        .catch(err => {
                            console.error('Error copying share link: ', err);
                            alert('Failed to copy share link. Please try again.');
                        });
                } else {
                    console.error('No share URL returned');
                    alert('Could not generate share link. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error sharing conversation:', error);
                alert('Failed to share conversation. Please try again.');
            });
        } else {
            console.error('No conversation ID available for sharing');
            alert('Cannot share this conversation yet. Please send at least one message first.');
        }
    }
    
    // Function to rate a message (upvote/downvote)
    function rateMessage(messageElement, rating) {
        const messageId = messageElement.dataset.messageId;
        const upvoteButton = messageElement.querySelector('.upvote-btn');
        const downvoteButton = messageElement.querySelector('.downvote-btn');
        
        if (!messageId) {
            console.error('No message ID available for rating');
            return;
        }
        
        // Send rating to server
        fetch(`/message/${messageId}/rate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                rating: rating
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update UI based on the rating
                if (rating === 1) {
                    upvoteButton.classList.add('voted');
                    downvoteButton.classList.remove('voted');
                } else if (rating === -1) {
                    downvoteButton.classList.add('voted');
                    upvoteButton.classList.remove('voted');
                }
            } else {
                console.error('Rating was not successful:', data.error);
            }
        })
        .catch(error => {
            console.error('Error rating message:', error);
        });
    }
    
    // Function to clear chat
    function clearChat() {
        // Clear the message history
        messageHistory = [];
        
        // Keep only the welcome container or create it if it doesn't exist
        if (!document.querySelector('.welcome-container')) {
            chatMessages.innerHTML = `
                <div class="welcome-container">
                    <div class="welcome-icon">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                        </svg>
                    </div>
                    <h1 class="welcome-heading">Welcome to GloriaMundo!</h1>
                    <p class="welcome-text">
                        Ask me anything and I'll provide helpful, accurate responses. Sign in to 
                        save your conversations and access them from any device.
                    </p>
                    <button class="example-question-btn" id="example-question-btn">
                        <i class="fa-regular fa-lightbulb"></i> Try an example question
                    </button>
                </div>
            `;
            
            // Re-attach event listener to the new example question button
            document.getElementById('example-question-btn').addEventListener('click', function() {
                const exampleQuestions = [
                    "What are the major differences between renewable and fossil fuel energy sources?",
                    "Can you explain how artificial intelligence works in simple terms?",
                    "What are some effective strategies for reducing carbon emissions?",
                    "How does quantum computing differ from classical computing?",
                    "What are the potential implications of gene editing technologies?"
                ];
                
                const randomQuestion = exampleQuestions[Math.floor(Math.random() * exampleQuestions.length)];
                messageInput.value = randomQuestion;
                sendMessage();
            });
        }
    }
    
    // Initialize by focusing on the input
    messageInput.focus();
    
    // ====== Document Upload Handlers ======
    
    // Store selected files
    let selectedFiles = [];
    
    // Toggle upload modal with premium access check
    if (uploadDocumentsBtn) {
        uploadDocumentsBtn.addEventListener('click', function() {
            // Check premium access before allowing document upload
            if (!checkPremiumAccess('document_upload')) {
                return; // Stop if access check failed
            }
            documentUploadModal.style.display = 'flex';
        });
    }
    
    // Close upload modal
    if (closeUploadModal) {
        closeUploadModal.addEventListener('click', function() {
            documentUploadModal.style.display = 'none';
        });
    }
    
    // Close modal when clicking outside
    if (documentUploadModal) {
        documentUploadModal.addEventListener('click', function(e) {
            if (e.target === documentUploadModal) {
                documentUploadModal.style.display = 'none';
            }
        });
    }
    
    // Handle dropzone click
    if (uploadDropzone) {
        uploadDropzone.addEventListener('click', function() {
            fileUploadInput.click();
        });
        
        // Handle file drag over
        uploadDropzone.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add('dragover');
        });
        
        // Handle file drag leave
        uploadDropzone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('dragover');
        });
        
        // Handle file drop
        uploadDropzone.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelection(files);
            }
        });
    }
    
    // Handle file input change
    if (fileUploadInput) {
        fileUploadInput.addEventListener('change', function() {
            handleFileSelection(this.files);
        });
    }
    
    // Handle file selection
    function handleFileSelection(files) {
        if (!files || files.length === 0) return;
        
        // Add files to the selected files array
        Array.from(files).forEach(file => {
            // Check if file is already in the list
            const isDuplicate = selectedFiles.some(f => f.name === file.name && f.size === file.size);
            if (!isDuplicate) {
                selectedFiles.push(file);
            }
        });
        
        // Update the file list UI
        updateFileList();
    }
    
    // Update file list display
    function updateFileList() {
        if (!uploadFileList) return;
        
        uploadFileList.innerHTML = '';
        
        selectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'upload-file-item';
            
            // Determine file icon based on file type
            let iconClass = 'fa-file';
            const fileExt = file.name.split('.').pop().toLowerCase();
            
            if (['pdf'].includes(fileExt)) {
                iconClass = 'fa-file-pdf';
            } else if (['doc', 'docx'].includes(fileExt)) {
                iconClass = 'fa-file-word';
            } else if (['txt', 'md'].includes(fileExt)) {
                iconClass = 'fa-file-alt';
            } else if (['jpg', 'jpeg', 'png', 'gif'].includes(fileExt)) {
                iconClass = 'fa-file-image';
            } else if (['html', 'htm', 'xml'].includes(fileExt)) {
                iconClass = 'fa-file-code';
            } else if (['csv', 'xls', 'xlsx'].includes(fileExt)) {
                iconClass = 'fa-file-excel';
            }
            
            fileItem.innerHTML = `
                <div class="file-info">
                    <i class="fa-solid ${iconClass} file-icon"></i>
                    <span class="file-name">${file.name}</span>
                </div>
                <button class="remove-file" data-index="${index}">
                    <i class="fa-solid fa-times"></i>
                </button>
            `;
            
            uploadFileList.appendChild(fileItem);
        });
        
        // Add event listeners to remove buttons
        document.querySelectorAll('.remove-file').forEach(button => {
            button.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                selectedFiles.splice(index, 1);
                updateFileList();
            });
        });
        
        // Show or hide the upload button based on file selection
        if (uploadFilesBtn) {
            uploadFilesBtn.style.display = selectedFiles.length > 0 ? 'block' : 'none';
        }
    }
    
    // Handle the upload process
    if (uploadFilesBtn) {
        uploadFilesBtn.addEventListener('click', function() {
            if (selectedFiles.length === 0) return;
            
            uploadStatus.innerHTML = `<p>Uploading ${selectedFiles.length} file(s)...</p>
                                     <div class="upload-progress"><div class="upload-progress-bar"></div></div>`;
            
            const formData = new FormData();
            selectedFiles.forEach(file => {
                formData.append('files[]', file);
            });
            
            // Disable the upload button during upload
            this.disabled = true;
            
            // Send the files to the server
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    uploadStatus.innerHTML = `<p>✅ Successfully processed ${selectedFiles.length} file(s). Your files will now be used to enhance AI responses.</p>`;
                    // Clear selected files
                    selectedFiles = [];
                    updateFileList();
                    
                    // Close modal after 3 seconds
                    setTimeout(() => {
                        documentUploadModal.style.display = 'none';
                        uploadStatus.innerHTML = '';
                    }, 3000);
                } else {
                    uploadStatus.innerHTML = `<p>❌ Error: ${data.error}</p>`;
                }
            })
            .catch(error => {
                uploadStatus.innerHTML = `<p>❌ Upload failed: ${error.message}</p>`;
                console.error('Upload error:', error);
            })
            .finally(() => {
                // Re-enable the upload button
                this.disabled = false;
            });
        });
    }
    
    // Add CSS for disabled button
    const style = document.createElement('style');
    style.textContent = `
        .disabled {
            opacity: 0.5;
            cursor: not-allowed !important;
            pointer-events: none;
        }
        #upload-indicator {
            animation: fadein 0.3s;
        }
        @keyframes fadein {
            from { opacity: 0; }
            to   { opacity: 1; }
        }
    `;
    document.head.appendChild(style);
});
