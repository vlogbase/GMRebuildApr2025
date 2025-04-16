document.addEventListener('DOMContentLoaded', function() {
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
    
    // App state
    let activePresetButton = null; // Currently selected preset button
    let currentModel = null; // Model ID of the currently selected preset
    let currentPresetId = '1'; // Default to first preset
    let currentConversationId = null;
    let messageHistory = [];
    
    // Model data
    let allModels = []; // All models from OpenRouter
    let userPreferences = {}; // User preferences for preset buttons
    
    // Filter configurations for each preset
    const presetFilters = {
        '1': (model) => true, // All models
        '2': (model) => true, // All models
        '3': (model) => model.is_reasoning === true,
        '4': (model) => model.is_multimodal === true,
        '5': (model) => model.is_perplexity === true,
        '6': (model) => model.is_free === true
    };
    
    // Default model IDs for each preset button
    const defaultModels = {
        '1': 'google/gemini-2.5-pro-preview-03-25',
        '2': 'anthropic/claude-3.7-sonnet',
        '3': 'openai/o3-Mini-High',
        '4': 'openai/gpt-4.1-mini',
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
    
    // Fetch conversations on load
    fetchConversations();
    
    // Event Listeners
    messageInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
        
        // Auto-resize textarea
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    sendButton.addEventListener('click', sendMessage);
    
    // Initialize model data
    fetchUserPreferences();
    
    // Model preset button click handlers
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
    
    // Close model selector on button click
    closeSelector.addEventListener('click', function() {
        closeModelSelector();
    });
    
    // Close model selector when clicking outside
    document.addEventListener('click', function(e) {
        if (modelSelector.style.display === 'block' && 
            !modelSelector.contains(e.target) && 
            !e.target.matches('.model-preset-btn') && 
            !e.target.closest('.model-preset-btn')) {
            closeModelSelector();
        }
    });
    
    // Search functionality for model selector
    modelSearch.addEventListener('input', function() {
        filterModelList(this.value.toLowerCase());
    });
    
    // Function to select a preset button and update the current model
    function selectPresetButton(presetId) {
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
        }
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
                    userPreferences = data.preferences;
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
        const maxLength = isFreePrefixed ? 8 : 12;
        if (name.length > maxLength) {
            name = name.substring(0, maxLength - 2) + '...';
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
    
    // New chat button
    newChatButton.addEventListener('click', function() {
        // Clear chat messages except the welcome message
        clearChat();
    });
    
    // Clear conversations button
    clearConversationsButton.addEventListener('click', function() {
        // Clear chat and reset conversation items in sidebar
        clearChat();
        // In a real app, you would also clear the storage/backend
    });
    
    // Example question button
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
    
    // Function to send message
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Clear input
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        // First time? Clear welcome message
        if (document.querySelector('.welcome-container')) {
            chatMessages.innerHTML = '';
        }
        
        // Add user message to chat
        addMessage(message, 'user');
        
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
            // Process markdown and code blocks if needed
            messageContent.innerHTML = formatMessage(content);
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
    function fetchConversations() {
        fetch('/conversations')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.conversations && data.conversations.length > 0) {
                    // Clear existing conversations
                    if (conversationsList) {
                        conversationsList.innerHTML = '';
                        
                        // Add each conversation to the sidebar
                        data.conversations.forEach(conversation => {
                            const conversationItem = document.createElement('div');
                            conversationItem.className = 'conversation-item';
                            conversationItem.dataset.id = conversation.id;
                            conversationItem.textContent = conversation.title;
                            
                            // Add click event to load conversation
                            conversationItem.addEventListener('click', function() {
                                loadConversation(conversation.id);
                            });
                            
                            conversationsList.appendChild(conversationItem);
                        });
                    }
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
        
        // In a full implementation, you would fetch the messages for this conversation
        // For now, simply set the current conversation ID
        console.log(`Loading conversation ID: ${conversationId}`);
    }
    
    // Function to send message to backend and process streaming response
    function sendMessageToBackend(message, modelId, typingIndicator) {
        // Add user message to history
        messageHistory.push({
            role: 'user',
            content: message
        });
        
        // If no model selected, use default
        if (!modelId) {
            modelId = defaultModels['1'];
            console.warn('No model selected, using default:', modelId);
        }
        
        // Create fetch request to /chat endpoint
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                model: modelId,
                history: messageHistory,
                conversation_id: currentConversationId
            })
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
                        // Add the complete assistant response to the message history
                        if (responseText) {
                            messageHistory.push({
                                role: 'assistant',
                                content: responseText
                            });
                        }
                        return;
                    }
                    
                    // Decode the chunk and add to buffer
                    buffer += decoder.decode(value, { stream: true });
                    
                    // Process each line in the buffer
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop(); // Keep the last incomplete line in the buffer
                    
                    // Process each complete line
                    for (const line of lines) {
                        if (line.trim() === '') continue;
                        
                        // Check if line starts with 'data: '
                        if (line.startsWith('data: ')) {
                            const data = line.substring(6); // Remove 'data: ' prefix
                            
                            // Check for [DONE] marker
                            if (data.trim() === '[DONE]') {
                                continue;
                            }
                            
                            try {
                                const parsedData = JSON.parse(data);
                                
                                if (parsedData.error) {
                                    messageContent.innerHTML = `<span class="error">Error: ${parsedData.error}</span>`;
                                    return;
                                }
                                
                                // Update conversation ID if provided
                                if (parsedData.conversation_id && !currentConversationId) {
                                    currentConversationId = parsedData.conversation_id;
                                    console.log(`Setting conversation ID: ${currentConversationId}`);
                                    
                                    // Refresh conversations list to show the new conversation
                                    fetchConversations();
                                }
                                
                                // Handle done marker
                                if (parsedData.done) {
                                    console.log("Conversation finished");
                                    return;
                                }
                                
                                // Handle content
                                if (parsedData.content) {
                                    responseText += parsedData.content;
                                    messageContent.innerHTML = formatMessage(responseText);
                                    chatMessages.scrollTop = chatMessages.scrollHeight;
                                }
                                
                                // Update message element with metadata if provided at end of stream
                                if (parsedData.metadata) {
                                    // Store the message ID for later use (rating, etc.)
                                    assistantMessageElement.dataset.messageId = parsedData.metadata.id;
                                    
                                    // Update with metadata display
                                    const messageWrapper = assistantMessageElement.querySelector('.message-wrapper');
                                    
                                    // Create or update metadata container
                                    let metadataContainer = messageWrapper.querySelector('.message-metadata');
                                    if (!metadataContainer) {
                                        metadataContainer = document.createElement('div');
                                        metadataContainer.className = 'message-metadata';
                                        messageWrapper.appendChild(metadataContainer);
                                    }
                                    
                                    // Format metadata
                                    let metadataText = '';
                                    if (parsedData.metadata.model_id_used) {
                                        const shortModelName = formatModelName(parsedData.metadata.model_id_used);
                                        metadataText += `Model: ${shortModelName}`;
                                    } else if (parsedData.metadata.model) {
                                        const shortModelName = formatModelName(parsedData.metadata.model);
                                        metadataText += `Model: ${shortModelName}`;
                                    }
                                    
                                    if (parsedData.metadata.prompt_tokens && parsedData.metadata.completion_tokens) {
                                        if (metadataText) metadataText += ' · ';
                                        metadataText += `Tokens: ${parsedData.metadata.prompt_tokens} prompt + ${parsedData.metadata.completion_tokens} completion`;
                                    }
                                    
                                    metadataContainer.textContent = metadataText;
                                }
                            } catch (error) {
                                console.error('Error parsing SSE data:', error, data);
                            }
                        }
                    }
                    
                    // Continue reading
                    return processChunks();
                });
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
        // Get the text content without HTML formatting
        const tempElement = document.createElement('div');
        tempElement.innerHTML = messageContent.innerHTML;
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
});
