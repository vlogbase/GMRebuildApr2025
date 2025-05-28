// Import required modules
import { forceRepaint } from './utils.js';
import { sendMessageAPI, shareConversationAPI, rateMessageAPI } from './apiService.js';
import { messageInput, sendButton } from './uiSetup.js';

// Get chat messages container
const chatMessages = document.getElementById('chat-messages');

// Chat state management
export let messageHistory = [];
export let currentConversationId = null;
export let attachedImageUrls = [];
export let attachedPdfUrl = null;
export let attachedPdfName = null;

// Setter function for currentConversationId to avoid const assignment errors
export function setCurrentConversationId(id) {
    currentConversationId = id;
}

// Clear attachment functions (matching original behavior)
export function clearAttachedImages() {
    attachedImageUrls.length = 0;
}

export function clearAttachedPdf() {
    attachedPdfUrl = null;
    attachedPdfName = null;
}

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
    
    // Set message ID for rating/sharing functionality (from original behavior)
    if (metadata && metadata.id) {
        messageElement.dataset.messageId = metadata.id;
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



// Function to clear chat
export function clearChat() {
    // Clear the message history
    messageHistory.length = 0;
    
    // Get chat messages container
    const chatMessages = document.getElementById('chat-messages');
    
    // Make sure chatMessages exists
    if (!chatMessages) {
        console.warn('Chat messages container not found - cannot clear chat');
        return;
    }
    
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
        const exampleBtn = document.getElementById('example-question-btn');
        if (exampleBtn) {
            exampleBtn.addEventListener('click', function() {
                const exampleQuestions = [
                    "What are the major differences between renewable and fossil fuel energy sources?",
                    "Can you explain how artificial intelligence works in simple terms?",
                    "What are some effective strategies for reducing carbon emissions?",
                    "How does quantum computing differ from classical computing?",
                    "What are the potential implications of gene editing technologies?"
                ];
                
                const randomQuestion = exampleQuestions[Math.floor(Math.random() * exampleQuestions.length)];
                if (messageInput) {
                    messageInput.value = randomQuestion;
                    // Trigger the send message function
                    sendMessage();
                }
            });
        }
    }
}

// Copy message text function (original behavior)
export function copyMessageText(messageElement) {
    // Find message content and strip out image elements
    const messageContent = messageElement.querySelector('.message-content');
    if (!messageContent) return;
    
    // Clone the content to avoid modifying the original
    const contentClone = messageContent.cloneNode(true);
    
    // Remove image elements from the clone
    const images = contentClone.querySelectorAll('img, .message-image-container, .message-multi-image');
    images.forEach(img => img.remove());
    
    const textContent = contentClone.textContent.trim();
    
    // Copy to clipboard
    navigator.clipboard.writeText(textContent).then(() => {
        // Update button text briefly
        const copyBtn = messageElement.querySelector('.copy-btn');
        if (copyBtn) {
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copied';
            copyBtn.disabled = true;
            
            // Restore after 2 seconds
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
                copyBtn.disabled = false;
            }, 2000);
        }
    }).catch(err => {
        console.error('Failed to copy text:', err);
    });
}

// Share conversation function (original behavior)
export async function shareConversation(messageElement) {
    if (!currentConversationId) {
        console.warn('No conversation ID available for sharing');
        return;
    }
    
    try {
        const response = await shareConversationAPI(currentConversationId);
        
        if (response.share_url) {
            // Copy share URL to clipboard
            await navigator.clipboard.writeText(response.share_url);
            
            // Update button text briefly
            const shareBtn = messageElement.querySelector('.share-btn');
            if (shareBtn) {
                const originalText = shareBtn.innerHTML;
                shareBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copied link';
                shareBtn.disabled = true;
                
                // Restore after 2 seconds
                setTimeout(() => {
                    shareBtn.innerHTML = originalText;
                    shareBtn.disabled = false;
                }, 2000);
            }
        }
    } catch (error) {
        console.error('Failed to share conversation:', error);
    }
}

// Rate message function (original behavior)
export async function rateMessage(messageElement, rating) {
    const messageId = messageElement.dataset.messageId;
    if (!messageId) {
        console.warn('No message ID found for rating');
        return;
    }
    
    try {
        const response = await rateMessageAPI(messageId, rating);
        
        if (response.success) {
            // Update UI buttons - toggle voted class
            const upvoteBtn = messageElement.querySelector('.upvote-btn');
            const downvoteBtn = messageElement.querySelector('.downvote-btn');
            
            if (upvoteBtn && downvoteBtn) {
                // Clear existing votes
                upvoteBtn.classList.remove('voted');
                downvoteBtn.classList.remove('voted');
                
                // Add voted class to the selected button
                if (rating === 1) {
                    upvoteBtn.classList.add('voted');
                } else if (rating === -1) {
                    downvoteBtn.classList.add('voted');
                }
            }
        }
    } catch (error) {
        console.error('Failed to rate message:', error);
    }
}

// Show login prompt function (original behavior)
export function showLoginPrompt() {
    console.log('Showing login prompt for unauthenticated user');
    
    // Check if prompt already exists
    if (document.querySelector('.login-prompt-sidebar')) {
        return;
    }
    
    // Create login prompt element
    const loginPrompt = document.createElement('div');
    loginPrompt.className = 'login-prompt-sidebar';
    loginPrompt.innerHTML = `
        <div class="login-prompt-content">
            <h3>Ready for more?</h3>
            <p>Create a free account to continue your conversation and unlock additional features.</p>
            <a href="/login" class="btn btn-primary">Sign in / Sign up</a>
        </div>
    `;
    
    // Find the sidebar and insert the prompt
    const sidebar = document.querySelector('.sidebar') || document.querySelector('#sidebar');
    if (sidebar) {
        // Insert at the top of the sidebar
        sidebar.insertBefore(loginPrompt, sidebar.firstChild);
    }
}

// Send message to backend function (original behavior)
async function sendMessageToBackend(message, selectedModel, typingIndicator) {
    try {
        // Build the payload with the same structure as the original
        const payload = {
            messages: [
                { role: 'user', content: message }
            ]
        };
        
        // Add selected model if available
        if (selectedModel) {
            payload.model_id = selectedModel;
        }
        
        // Add conversation ID if available
        if (currentConversationId) {
            payload.conversation_id = currentConversationId;
        }
        
        // Add attachments to the payload (images and PDFs)
        if (attachedImageUrls && attachedImageUrls.length > 0) {
            // Create content array with text and images
            const userContent = [
                { type: 'text', text: message || 'Image:' }
            ];
            
            // Add image URLs
            attachedImageUrls.forEach(imageUrl => {
                userContent.push({
                    type: 'image_url',
                    image_url: { url: imageUrl }
                });
            });
            
            payload.messages[0].content = userContent;
        }
        
        // Add PDF to payload if present
        if (attachedPdfUrl) {
            if (Array.isArray(payload.messages[0].content)) {
                payload.messages[0].content.push({
                    type: 'file',
                    file: {
                        filename: attachedPdfName || 'document.pdf',
                        file_data: attachedPdfUrl
                    }
                });
            } else {
                payload.messages[0].content = [
                    { type: 'text', text: message || 'Document:' },
                    {
                        type: 'file',
                        file: {
                            filename: attachedPdfName || 'document.pdf',
                            file_data: attachedPdfUrl
                        }
                    }
                ];
            }
        }
        
        console.log('🚀 Sending message to backend:', payload);
        
        // Send message via API
        const response = await sendMessageAPI(payload);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Handle streaming response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        // Remove typing indicator
        if (typingIndicator) {
            typingIndicator.remove();
        }
        
        // Create message element for assistant response
        const assistantMessage = addMessage('', 'assistant', false);
        const messageContent = assistantMessage.querySelector('.message-content');
        
        let fullResponse = '';
        
        // Process stream
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') continue;
                    
                    try {
                        const parsed = JSON.parse(data);
                        if (parsed.content) {
                            fullResponse += parsed.content;
                            messageContent.innerHTML = formatMessage(fullResponse);
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        }
                    } catch (e) {
                        // Ignore JSON parse errors for partial chunks
                    }
                }
            }
        }
        
        console.log('✅ Message sent successfully');
        
    } catch (error) {
        console.error('❌ Error sending message:', error);
        
        // Remove typing indicator on error
        if (typingIndicator) {
            typingIndicator.remove();
        }
        
        // Show error message
        addMessage('Sorry, there was an error processing your message. Please try again.', 'assistant');
    }
}