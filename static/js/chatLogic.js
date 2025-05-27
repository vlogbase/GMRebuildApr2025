// Import required modules
import { forceRepaint } from './utils.js';
import { sendMessageAPI } from './apiService.js';
import { messageInput, sendButton } from './uiSetup.js';

// Chat state management
export let messageHistory = [];
export let currentConversationId = null;
export let attachedImageUrls = [];
export let attachedPdfUrl = null;
export let attachedPdfName = null;

// Export functions for external access
export function sendMessage() {
    // Add null check for messageInput
    if (!messageInput) {
        console.warn('Message input not found');
        return;
    }
    
    const message = messageInput.value.trim();
    const hasAttachments = (attachedImageUrls && attachedImageUrls.length > 0) || attachedPdfUrl;
    
    // Don't send empty messages with no attachments
    if (!message && !hasAttachments) return;
    
    // Check if user is not authenticated and handle message counting
    if (typeof userIsLoggedIn !== 'undefined' && !userIsLoggedIn) {
        // Get the current message count
        let nonAuthMessageCount = parseInt(localStorage.getItem('nonAuthMessageCount') || 0);
        
        // Increment the count for this new message
        nonAuthMessageCount++;
        localStorage.setItem('nonAuthMessageCount', nonAuthMessageCount);
        
        console.log(`Non-auth message count: ${nonAuthMessageCount}`);
        
        // Check if we need to show the login prompt (every 3 messages)
        if (nonAuthMessageCount % 3 === 0) {
            // Show login prompt after processing this message
            setTimeout(() => {
                showLoginPrompt();
            }, 1000); // Slight delay to ensure the message is displayed first
        }
    }
    
    // Clear input and reset textarea height to initial state
    messageInput.value = '';
    messageInput.style.height = '40px'; // Reset to initial height
    
    // First time? Clear welcome message
    if (document.querySelector('.welcome-container') && chatMessages) {
        chatMessages.innerHTML = '';
    }
    
    // Check if we're sending a message with attachments (images or PDF)
    if (hasAttachments) {
        // Create a standardized content array for user messages with attachments
        const userContent = [
            { type: 'text', text: message || (attachedPdfUrl ? 'Document:' : 'Image:') }
        ];
        
        // Add all image URLs to the content array
        if (attachedImageUrls && attachedImageUrls.length > 0) {
            for (const imageUrl of attachedImageUrls) {
                userContent.push({
                    type: 'image_url',
                    image_url: { url: imageUrl }
                });
            }
        }
        
        // Add PDF to content array if present
        if (attachedPdfUrl) {
            userContent.push({
                type: 'file',
                file: { 
                    filename: attachedPdfName || 'document.pdf',
                    file_data: attachedPdfUrl
                }
            });
        }
        
        // Add user message with attachments to chat
        addMessage(userContent, 'user');
    } else {
        // Add text-only user message to chat
        addMessage(message, 'user');
    }
    
    // Show typing indicator
    const typingIndicator = addTypingIndicator();
    
    // IMPORTANT: Keep the PDF/image data available until AFTER sending to backend
    // Store current attachment states
    const storedImageUrls = [...attachedImageUrls];
    const storedPdfUrl = attachedPdfUrl;
    const storedPdfName = attachedPdfName;
    
    // Clear UI indicators (we've already displayed them in the message)
    // But preserve the actual data for the backend call
    if (attachedImageUrls.length > 0) {
        // Just clear the UI indicators
        const uploadIndicators = document.querySelectorAll('.image-preview-container');
        uploadIndicators.forEach(indicator => indicator.remove());
    }
    
    // Clear PDF UI indicators but keep the data
    if (attachedPdfUrl) {
        // Just clear the UI indicator
        const pdfIndicators = document.querySelectorAll('.pdf-indicator');
        pdfIndicators.forEach(indicator => indicator.remove());
    }
    
    // Send message to backend with the data still intact
    sendMessageToBackend(message, currentModel, typingIndicator);
    
    // NOW we can clear the actual attachment data after sending
    clearAttachedImages();
    clearAttachedPdf();
}

export function addMessage(content, sender, isTyping = false, metadata = null) {
    // Get message elements
    const elements = createMessageElement(content, sender, isTyping, metadata);
    const { messageElement, avatar, messageWrapper, messageContent } = elements;
    
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
                // Force a repaint to ensure text content is visible
                forceRepaint(textDiv);
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
                    messageImage.loading = 'lazy'; // Add lazy loading for better performance
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
                        thumbnail.loading = 'lazy'; // Add lazy loading for better performance
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
            const formattedMessage = formatMessage(content);
            messageContent.innerHTML = formattedMessage;
            
            // Apply the repaint to ensure content is visible
            forceRepaint(messageContent);
            
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
                metadataContainer.className = 'message-metadata message-metadata-outside';
                
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
                
                // Add document reference indicator if using documents
                if (metadata && metadata.using_documents) {
                    const documentRef = document.createElement('span');
                    documentRef.className = 'document-reference';
                    documentRef.innerHTML = '<i class="fa-solid fa-file-lines"></i> Using your documents';
                    
                    // Add document sources if available
                    if (metadata.document_sources && metadata.document_sources.length > 0) {
                        const sourceCount = metadata.document_sources.length;
                        const sourceText = sourceCount === 1 
                            ? metadata.document_sources[0] 
                            : `${sourceCount} documents`;
                        documentRef.innerHTML = `<i class="fa-solid fa-file-lines"></i> Using ${sourceText}`;
                    }
                    
                    metadataContainer.appendChild(documentRef);
                }
                
                if (metadataText || (metadata && metadata.using_documents)) {
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
    
    // Add to chat container if it exists
    if (chatMessages) {
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } else {
        console.warn('Chat messages container not found');
    }
    
    return messageElement;
}

export function formatMessage(text) {
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
    
    // URL Detection - convert plain URLs to links
    // Regular expression to match URLs
    const urlRegex = /https?:\/\/[^\s<>"]+/gi;
    
    // Use placeholder markers for URLs with unique IDs
    const urlPlaceholders = {};
    let placeholderCounter = 0;
    
    // First step: Extract and protect URLs in HTML tags
    let protectedHtml = text.replace(/<a\s+[^>]*>(.*?)<\/a>|<[^>]*>/g, match => {
        // Only process <a> tags, leave other tags as is
        if (match.startsWith('<a ')) {
            return match.replace(urlRegex, url => {
                const placeholder = `__PROTECTED_URL_${placeholderCounter++}__`;
                urlPlaceholders[placeholder] = url;
                return placeholder;
            });
        }
        return match;
    });
    
    // Second step: Convert plain URLs to links
    protectedHtml = protectedHtml.replace(urlRegex, url => {
        // Create a safe display URL (truncate if too long)
        let displayUrl = url;
        if (url.length > 50) {
            displayUrl = url.substring(0, 47) + '...';
        }
        return `<a href="${url}" target="_blank" rel="noopener noreferrer">${displayUrl}</a>`;
    });
    
    // Final step: Restore protected URLs
    text = protectedHtml.replace(/__PROTECTED_URL_(\d+)__/g, (match, id) => {
        return urlPlaceholders[match] || match;
    });
    
    return text;
}

// Helper functions that will need to be defined or imported
export function addTypingIndicator() {
    return addMessage('', 'assistant', true);
}

export function clearAttachedImages() {
    attachedImageUrls = [];
}

export function clearAttachedPdf() {
    attachedPdfUrl = null;
    attachedPdfName = null;
}