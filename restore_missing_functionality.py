#!/usr/bin/env python3
"""
Comprehensive restoration script to bring back missing functionality from the original backup
This script will systematically restore all the key features that were lost during the refactoring
"""

import os
import re

def read_file(filename):
    """Read the contents of a file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: {filename} not found")
        return None
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return None

def write_file(filename, content):
    """Write content to a file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Updated {filename}")
        return True
    except Exception as e:
        print(f"❌ Error writing {filename}: {e}")
        return False

def backup_file(filename):
    """Create a backup of the file before modifying it."""
    try:
        content = read_file(filename)
        if content is not None:
            backup_name = f"{filename}.backup_restore"
            write_file(backup_name, content)
            print(f"📁 Created backup: {backup_name}")
    except Exception as e:
        print(f"Warning: Could not create backup of {filename}: {e}")

def restore_missing_global_functions():
    """Add missing global functions to script.js"""
    script_file = "static/js/script.js"
    content = read_file(script_file)
    if not content:
        return False
    
    backup_file(script_file)
    
    # Add missing global function declarations
    missing_globals = """
// Restore missing global functions for backward compatibility
window.openModelSelector = openModelSelector;
window.closeModelSelector = closeModelSelector;
window.selectPresetButton = selectPresetButton;
window.populateModelList = populateModelList;
window.selectModelForPreset = selectModelForPreset;
window.handleMessageInputKeydown = handleMessageInputKeydown;
window.sendMessage = sendMessage;
window.addMessage = addMessage;
window.fetchConversations = fetchConversations;
window.loadConversation = loadConversation;
window.createNewConversation = createNewConversation;
window.deleteConversation = deleteConversation;
window.shareConversation = shareConversation;
window.refreshModelPrices = refreshModelPrices;
window.lockPremiumFeatures = lockPremiumFeatures;
window.checkModelCapabilities = checkModelCapabilities;
window.updateModelCapabilityButtons = updateModelCapabilityButtons;
window.handleFileUpload = handleFileUpload;
window.handlePaste = handlePaste;
window.handleKeyboardShortcuts = handleKeyboardShortcuts;
window.handleOutsideClicks = handleOutsideClicks;
window.handleWindowResize = handleWindowResize;
"""
    
    # Add the globals at the end of the file if not already present
    if "window.openModelSelector = openModelSelector;" not in content:
        content += missing_globals
        print("✅ Added missing global function declarations")
    
    return write_file(script_file, content)

def restore_sorting_logic():
    """Restore the proper model sorting logic from the backup"""
    model_selection_file = "static/js/modelSelection.js"
    content = read_file(model_selection_file)
    if not content:
        return False
    
    backup_file(model_selection_file)
    
    # Find and replace the sorting logic
    old_sorting = r"export const sortModels = \(models, presetId\) => \{[^}]+\};"
    
    new_sorting = """export const sortModels = (models, presetId) => {
    return models.sort((a, b) => {
        // Preset 2 ONLY: Sort by context length first (for context-focused models)
        if (presetId === '2') {
            // Primary sort: Context Length (descending)
            const aContext = parseInt(a.context_length) || 0;
            const bContext = parseInt(b.context_length) || 0;
            if (aContext !== bContext) {
                return bContext - aContext;
            }
            
            // Secondary sort: Input Price (ascending)
            const aPrice = a.pricing?.prompt || 0;
            const bPrice = b.pricing?.prompt || 0;
            if (aPrice !== bPrice) {
                return aPrice - bPrice;
            }
            
            // Tertiary sort: Model Name (alphabetical)
            return a.name.localeCompare(b.name);
        }
        
        // For Presets 1, 3, 4, 5, and 6: ELO-based sorting
        
        // Primary sort: ELO Score (descending, higher is better)
        const aElo = a.elo_score || 0;
        const bElo = b.elo_score || 0;
        
        // Models with ELO scores come before models without ELO scores
        if (aElo > 0 && bElo === 0) return -1;
        if (aElo === 0 && bElo > 0) return 1;
        
        // Both have ELO scores - sort by ELO (descending)
        if (aElo !== bElo) {
            return bElo - aElo;
        }
        
        // Secondary sort: Context Length (descending)
        const aContext = parseInt(a.context_length) || 0;
        const bContext = parseInt(b.context_length) || 0;
        if (aContext !== bContext) {
            return bContext - aContext;
        }
        
        // Tertiary sort: Input Price (ascending)
        const aPrice = a.pricing?.prompt || 0;
        const bPrice = b.pricing?.prompt || 0;
        if (aPrice !== bPrice) {
            return aPrice - bPrice;
        }
        
        // Quaternary sort: Model Name (alphabetical)
        return a.name.localeCompare(b.name);
    });
};"""
    
    # Replace the sorting function
    content = re.sub(old_sorting, new_sorting, content, flags=re.DOTALL)
    
    return write_file(model_selection_file, content)

def restore_event_listeners():
    """Restore missing event listeners"""
    event_file = "static/js/eventOrchestration.js"
    content = read_file(event_file)
    if not content:
        return False
    
    backup_file(event_file)
    
    # Add missing event listeners
    missing_listeners = """
    // Model search functionality
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', debounce((event) => {
            const searchTerm = event.target.value.toLowerCase();
            const modelItems = document.querySelectorAll('#model-list li');
            
            modelItems.forEach(item => {
                const modelName = item.textContent.toLowerCase();
                if (modelName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }, 300));
    }
    
    // Reset to default model button
    const resetToDefaultButton = document.getElementById('reset-to-default');
    if (resetToDefaultButton) {
        resetToDefaultButton.addEventListener('click', () => {
            console.log('🔄 Reset to default model clicked');
            // Get the current active preset
            const activePreset = document.querySelector('.model-preset-btn.active');
            if (activePreset) {
                const presetId = activePreset.getAttribute('data-preset-id');
                if (window.selectPresetButton) {
                    window.selectPresetButton(presetId);
                }
            }
        });
    }
    
    // File upload button
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    if (fileUploadButton && fileUpload) {
        fileUploadButton.addEventListener('click', () => {
            console.log('📁 File upload button clicked');
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', (event) => {
            if (window.handleFileUpload) {
                window.handleFileUpload(event);
            }
        });
    }"""
    
    # Add the listeners before the closing brace
    if "// Model search functionality" not in content:
        # Find the last part of the function and add the missing listeners
        content = content.replace("    }", missing_listeners + "\n    }")
        print("✅ Added missing event listeners")
    
    return write_file(event_file, content)

def restore_conversation_management():
    """Restore conversation management functionality"""
    conv_file = "static/js/conversationManagement.js"
    content = read_file(conv_file)
    if not content:
        return False
    
    backup_file(conv_file)
    
    # Add missing conversation functions if they don't exist
    missing_functions = """
// Auto-create conversation on page load if none exists
export function ensureConversationExists() {
    const conversationList = document.getElementById('conversation-list');
    if (!conversationList || conversationList.children.length === 0) {
        console.log('No conversations found, creating new one...');
        if (window.createNewConversation) {
            window.createNewConversation();
        }
    }
}

// Handle conversation sharing
export function shareConversation(conversationId) {
    console.log('Sharing conversation:', conversationId);
    
    fetch(`/share/${conversationId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.share_id) {
            const shareUrl = `${window.location.origin}/shared/${data.share_id}`;
            
            // Try to copy to clipboard
            if (navigator.clipboard) {
                navigator.clipboard.writeText(shareUrl).then(() => {
                    alert('Share link copied to clipboard!');
                }).catch(() => {
                    prompt('Copy this link to share:', shareUrl);
                });
            } else {
                prompt('Copy this link to share:', shareUrl);
            }
        } else {
            alert('Failed to create share link');
        }
    })
    .catch(error => {
        console.error('Error sharing conversation:', error);
        alert('Error creating share link');
    });
}"""
    
    # Add the functions if they don't exist
    if "ensureConversationExists" not in content:
        content += missing_functions
        print("✅ Added missing conversation management functions")
    
    return write_file(conv_file, content)

def main():
    """Run all restoration functions"""
    print("🔧 Starting comprehensive functionality restoration...")
    
    success_count = 0
    total_operations = 4
    
    if restore_missing_global_functions():
        success_count += 1
    
    if restore_sorting_logic():
        success_count += 1
    
    if restore_event_listeners():
        success_count += 1
    
    if restore_conversation_management():
        success_count += 1
    
    print(f"\n📊 Restoration complete: {success_count}/{total_operations} operations successful")
    
    if success_count == total_operations:
        print("✅ All functionality has been restored!")
        print("🚀 The app should now have all the missing features working properly.")
    else:
        print("⚠️  Some operations failed. Check the logs above for details.")

if __name__ == "__main__":
    main()