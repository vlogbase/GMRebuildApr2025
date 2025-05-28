/**
 * Advanced Chat Preferences JavaScript
 * Handles the UI and API interactions for advanced chat parameter settings
 */

document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if advanced chat preferences section exists
    if (!document.getElementById('advancedChatPrefs')) return;
    
    // Initialize variables to track stop sequences
    let stopSequences = [];
    
    // Initialize the preferences interface
    initializeAdvancedPrefs();
    
    // Load user preferences from API
    loadUserChatSettings();
    
    // Attach event listeners
    setupEventListeners();
    
    /**
     * Initialize the advanced preferences interface
     */
    function initializeAdvancedPrefs() {
        // Initialize sliders to match number inputs
        syncSliderWithInput('temperature', 'temperatureSlider');
        syncSliderWithInput('topP', 'topPSlider');
        syncSliderWithInput('maxTokens', 'maxTokensSlider');
        syncSliderWithInput('frequencyPenalty', 'frequencyPenaltySlider');
        syncSliderWithInput('presencePenalty', 'presencePenaltySlider');
        syncSliderWithInput('topK', 'topKSlider');
        
        // Max tokens radio button handling
        document.getElementById('maxTokensMax').addEventListener('change', function() {
            const inputEl = document.getElementById('maxTokens');
            const sliderEl = document.getElementById('maxTokensSlider');
            
            inputEl.disabled = true;
            sliderEl.disabled = true;
            updateBadgeValue('maxTokens', 'Default (Max)');
        });
        
        document.getElementById('maxTokensSpecific').addEventListener('change', function() {
            const inputEl = document.getElementById('maxTokens');
            const sliderEl = document.getElementById('maxTokensSlider');
            
            inputEl.disabled = false;
            sliderEl.disabled = false;
            
            // If value is empty, set a reasonable default
            if (!inputEl.value) {
                inputEl.value = 2000;
                sliderEl.value = 2000;
            }
            
            updateBadgeValue('maxTokens', inputEl.value);
        });
        
        // Stop sequences handling
        document.getElementById('stopSequences').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const value = this.value.trim();
                if (value) {
                    addStopSequence(value);
                    this.value = '';
                }
            }
        });
    }
    
    /**
     * Load user chat settings from the API
     */
    function loadUserChatSettings() {
        fetch('/api/user/chat_settings')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    populateFormWithSettings(data.settings);
                }
            })
            .catch(error => {
                console.error('Error loading chat settings:', error);
            });
    }
    
    /**
     * Populate the form with user settings
     */
    function populateFormWithSettings(settings) {
        // Numeric parameters
        if (settings.temperature !== null && settings.temperature !== undefined) {
            document.getElementById('temperature').value = settings.temperature;
            document.getElementById('temperatureSlider').value = settings.temperature;
            updateBadgeValue('temperature', settings.temperature);
        }
        
        if (settings.top_p !== null && settings.top_p !== undefined) {
            document.getElementById('topP').value = settings.top_p;
            document.getElementById('topPSlider').value = settings.top_p;
            updateBadgeValue('topP', settings.top_p);
        }
        
        if (settings.max_tokens !== null && settings.max_tokens !== undefined) {
            document.getElementById('maxTokensSpecific').checked = true;
            document.getElementById('maxTokensMax').checked = false;
            
            const inputEl = document.getElementById('maxTokens');
            const sliderEl = document.getElementById('maxTokensSlider');
            
            inputEl.disabled = false;
            sliderEl.disabled = false;
            
            inputEl.value = settings.max_tokens;
            sliderEl.value = settings.max_tokens;
            updateBadgeValue('maxTokens', settings.max_tokens);
        }
        
        if (settings.frequency_penalty !== null && settings.frequency_penalty !== undefined) {
            document.getElementById('frequencyPenalty').value = settings.frequency_penalty;
            document.getElementById('frequencyPenaltySlider').value = settings.frequency_penalty;
            updateBadgeValue('frequencyPenalty', settings.frequency_penalty);
        }
        
        if (settings.presence_penalty !== null && settings.presence_penalty !== undefined) {
            document.getElementById('presencePenalty').value = settings.presence_penalty;
            document.getElementById('presencePenaltySlider').value = settings.presence_penalty;
            updateBadgeValue('presencePenalty', settings.presence_penalty);
        }
        
        if (settings.top_k !== null && settings.top_k !== undefined) {
            document.getElementById('topK').value = settings.top_k;
            document.getElementById('topKSlider').value = settings.top_k;
            updateBadgeValue('topK', settings.top_k);
        }
        
        // Stop sequences
        if (settings.stop_sequences) {
            try {
                stopSequences = JSON.parse(settings.stop_sequences);
                renderStopSequences();
            } catch (e) {
                console.error('Error parsing stop sequences:', e);
            }
        }
        
        // Response format
        if (settings.response_format) {
            if (settings.response_format === 'json') {
                document.getElementById('responseFormatJson').checked = true;
                document.getElementById('responseFormatText').checked = false;
            } else {
                document.getElementById('responseFormatText').checked = true;
                document.getElementById('responseFormatJson').checked = false;
            }
        }
    }
    
    /**
     * Set up event listeners for the form controls
     */
    function setupEventListeners() {
        // Individual reset buttons
        document.querySelectorAll('.reset-param').forEach(button => {
            button.addEventListener('click', function() {
                const param = this.getAttribute('data-param');
                resetParameter(param);
            });
        });
        
        // Reset all parameters button
        document.getElementById('resetAllDefaults').addEventListener('click', function() {
            resetAllParameters();
        });
        
        // Save button
        document.getElementById('saveAdvancedPrefs').addEventListener('click', function() {
            saveAdvancedPreferences();
        });
        
        // Link sliders and number inputs
        document.querySelectorAll('input[type="range"]').forEach(slider => {
            const inputId = slider.id.replace('Slider', '');
            const input = document.getElementById(inputId);
            
            slider.addEventListener('input', function() {
                input.value = this.value;
                updateBadgeValue(inputId, this.value);
            });
        });
        
        document.querySelectorAll('input[type="number"]').forEach(input => {
            const sliderId = input.id + 'Slider';
            const slider = document.getElementById(sliderId);
            
            input.addEventListener('input', function() {
                slider.value = this.value;
                updateBadgeValue(input.id, this.value);
            });
        });
    }
    
    /**
     * Sync a slider with its corresponding number input
     */
    function syncSliderWithInput(inputId, sliderId) {
        const input = document.getElementById(inputId);
        const slider = document.getElementById(sliderId);
        
        if (input && slider) {
            slider.addEventListener('input', function() {
                input.value = this.value;
                updateBadgeValue(inputId, this.value);
            });
            
            input.addEventListener('input', function() {
                slider.value = this.value;
                updateBadgeValue(inputId, this.value);
            });
        }
    }
    
    /**
     * Update the badge value display for a parameter
     */
    function updateBadgeValue(paramId, value) {
        const badgeId = paramId + 'Value';
        const badge = document.getElementById(badgeId);
        
        if (badge) {
            badge.textContent = value;
            badge.classList.remove('bg-secondary');
            badge.classList.add('bg-primary');
        }
    }
    
    /**
     * Reset a parameter to its default value
     */
    function resetParameter(param) {
        switch (param) {
            case 'temperature':
                document.getElementById('temperature').value = '';
                document.getElementById('temperatureSlider').value = 0.7;
                document.getElementById('temperatureValue').textContent = 'Default';
                document.getElementById('temperatureValue').classList.remove('bg-primary');
                document.getElementById('temperatureValue').classList.add('bg-secondary');
                break;
                
            case 'topP':
                document.getElementById('topP').value = '';
                document.getElementById('topPSlider').value = 0.9;
                document.getElementById('topPValue').textContent = 'Default';
                document.getElementById('topPValue').classList.remove('bg-primary');
                document.getElementById('topPValue').classList.add('bg-secondary');
                break;
                
            case 'maxTokens':
                document.getElementById('maxTokensMax').checked = true;
                document.getElementById('maxTokensSpecific').checked = false;
                document.getElementById('maxTokens').disabled = true;
                document.getElementById('maxTokensSlider').disabled = true;
                document.getElementById('maxTokens').value = '';
                document.getElementById('maxTokensSlider').value = 2000;
                document.getElementById('maxTokensValue').textContent = 'Default (Max)';
                document.getElementById('maxTokensValue').classList.remove('bg-primary');
                document.getElementById('maxTokensValue').classList.add('bg-secondary');
                break;
                
            case 'frequencyPenalty':
                document.getElementById('frequencyPenalty').value = '';
                document.getElementById('frequencyPenaltySlider').value = 0;
                document.getElementById('frequencyPenaltyValue').textContent = 'Default';
                document.getElementById('frequencyPenaltyValue').classList.remove('bg-primary');
                document.getElementById('frequencyPenaltyValue').classList.add('bg-secondary');
                break;
                
            case 'presencePenalty':
                document.getElementById('presencePenalty').value = '';
                document.getElementById('presencePenaltySlider').value = 0;
                document.getElementById('presencePenaltyValue').textContent = 'Default';
                document.getElementById('presencePenaltyValue').classList.remove('bg-primary');
                document.getElementById('presencePenaltyValue').classList.add('bg-secondary');
                break;
                
            case 'topK':
                document.getElementById('topK').value = '';
                document.getElementById('topKSlider').value = 0;
                document.getElementById('topKValue').textContent = 'Default';
                document.getElementById('topKValue').classList.remove('bg-primary');
                document.getElementById('topKValue').classList.add('bg-secondary');
                break;
                
            case 'stopSequences':
                stopSequences = [];
                renderStopSequences();
                break;
                
            case 'responseFormat':
                document.getElementById('responseFormatText').checked = true;
                document.getElementById('responseFormatJson').checked = false;
                break;
        }
    }
    
    /**
     * Reset all parameters to their default values
     */
    function resetAllParameters() {
        const params = ['temperature', 'topP', 'maxTokens', 'frequencyPenalty', 'presencePenalty', 'topK', 'stopSequences', 'responseFormat'];
        params.forEach(param => resetParameter(param));
    }
    
    /**
     * Add a stop sequence to the list
     */
    function addStopSequence(sequence) {
        if (!stopSequences.includes(sequence)) {
            stopSequences.push(sequence);
            renderStopSequences();
        }
    }
    
    /**
     * Render the stop sequences in the UI
     */
    function renderStopSequences() {
        const container = document.getElementById('stopSequencesList');
        container.innerHTML = '';
        
        stopSequences.forEach(sequence => {
            const badge = document.createElement('div');
            badge.className = 'badge bg-secondary d-flex align-items-center py-2 px-3';
            badge.innerHTML = `
                <span class="me-2">${escapeHtml(sequence)}</span>
                <button type="button" class="btn-close btn-close-white" style="font-size: 0.5rem;" aria-label="Remove"></button>
            `;
            
            badge.querySelector('.btn-close').addEventListener('click', function() {
                removeStopSequence(sequence);
            });
            
            container.appendChild(badge);
        });
    }
    
    /**
     * Remove a stop sequence from the list
     */
    function removeStopSequence(sequence) {
        stopSequences = stopSequences.filter(seq => seq !== sequence);
        renderStopSequences();
    }
    
    /**
     * Save the advanced preferences to the server
     */
    function saveAdvancedPreferences() {
        const settings = {
            temperature: document.getElementById('temperature').value ? parseFloat(document.getElementById('temperature').value) : null,
            top_p: document.getElementById('topP').value ? parseFloat(document.getElementById('topP').value) : null,
            max_tokens: document.getElementById('maxTokensSpecific').checked ? parseInt(document.getElementById('maxTokens').value) : null,
            frequency_penalty: document.getElementById('frequencyPenalty').value ? parseFloat(document.getElementById('frequencyPenalty').value) : null,
            presence_penalty: document.getElementById('presencePenalty').value ? parseFloat(document.getElementById('presencePenalty').value) : null,
            top_k: document.getElementById('topK').value ? parseInt(document.getElementById('topK').value) : null,
            stop_sequences: stopSequences.length > 0 ? JSON.stringify(stopSequences) : null,
            response_format: document.getElementById('responseFormatJson').checked ? 'json' : null,
        };
        
        // Send settings to the server
        fetch('/api/user/chat_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            credentials: 'same-origin', // Include cookies for session authentication
            body: JSON.stringify(settings)
        })
        .then(response => {
            if (!response.ok) {
                // Handle HTTP error status
                console.error('HTTP error:', response.status, response.statusText);
                return response.text().then(text => {
                    try {
                        // Try to parse as JSON for structured error
                        const errorData = JSON.parse(text);
                        throw new Error(errorData.error || 'Unknown error');
                    } catch {
                        // If not JSON, use text or status
                        throw new Error(text || `HTTP error ${response.status}`);
                    }
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Show success message
                showToast('success', 'Advanced preferences saved successfully!');
            } else {
                showToast('error', 'Error saving preferences: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error saving settings:', error);
            showToast('error', 'Failed to save preferences: ' + error.message);
        });
    }
    
    /**
     * Show a toast notification
     */
    function showToast(message, type) {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast element
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.className = `toast ${type === 'error' ? 'bg-danger text-white' : 'bg-success text-white'}`;
        toast.id = toastId;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">${type === 'error' ? 'Error' : 'Success'}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Initialize and show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});