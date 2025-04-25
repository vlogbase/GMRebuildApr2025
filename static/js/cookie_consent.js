/**
 * Cookie Consent Manager for GloriaMundo
 * 
 * This script handles:
 * 1. Displaying the cookie consent banner
 * 2. Saving user preferences
 * 3. Managing the cookie settings modal
 */

// Default cookie consent settings
const DEFAULT_COOKIE_SETTINGS = {
    essential: true,      // Cannot be disabled
    functional: true,     // Default on
    analytics: true,      // Default on
    authenticated: false  // Default off, updated based on login state
};

// Cookie names
const COOKIE_CONSENT_NAME = 'gloriamundo_cookie_consent';
const COOKIE_SETTINGS_NAME = 'gloriamundo_cookie_settings';

// DOM Elements - defined in init()
let banner;
let modal;
let bannerAcceptAllBtn;
let bannerCustomizeBtn;
let bannerRejectBtn;
let modalSaveBtn;
let modalAcceptAllBtn;
let modalCloseBtn;
let toggles = {};

/**
 * Initialize the cookie consent functionality
 */
function initCookieConsent() {
    // Create and append banner markup to body if it doesn't exist
    if (!document.getElementById('cookie-consent-banner')) {
        createCookieConsentElements();
    }
    
    // Capture references to DOM elements
    banner = document.getElementById('cookie-consent-banner');
    modal = document.getElementById('cookie-settings-modal');
    bannerAcceptAllBtn = document.getElementById('cookie-accept-all');
    bannerCustomizeBtn = document.getElementById('cookie-customize');
    bannerRejectBtn = document.getElementById('cookie-reject');
    modalSaveBtn = document.getElementById('cookie-save-preferences');
    modalAcceptAllBtn = document.getElementById('cookie-modal-accept-all');
    modalCloseBtn = document.getElementById('cookie-settings-close');
    
    // Cookie toggle inputs
    toggles = {
        essential: document.getElementById('cookie-essential'),
        functional: document.getElementById('cookie-functional'),
        analytics: document.getElementById('cookie-analytics'),
        authenticated: document.getElementById('cookie-authenticated')
    };
    
    // Set up event listeners
    bannerAcceptAllBtn.addEventListener('click', acceptAllCookies);
    bannerCustomizeBtn.addEventListener('click', openCookieSettings);
    bannerRejectBtn.addEventListener('click', rejectNonEssentialCookies);
    modalSaveBtn.addEventListener('click', savePreferences);
    modalAcceptAllBtn.addEventListener('click', () => {
        acceptAllCookies();
        closeModal();
    });
    modalCloseBtn.addEventListener('click', closeModal);
    
    // Open cookie settings when footer link is clicked
    const openCookieSettingsLinks = document.querySelectorAll('#open-cookie-settings');
    openCookieSettingsLinks.forEach(link => {
        link.addEventListener('click', openCookieSettings);
    });
    
    // Handle clicking outside the modal to close it
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // Check if the user has already set preferences
    const consentGiven = getCookie(COOKIE_CONSENT_NAME);
    if (!consentGiven) {
        // No consent given yet, show the banner
        setTimeout(() => {
            banner.classList.add('visible');
        }, 1000); // Delay to let the page load first
    } else {
        // Consent already given, apply saved settings
        applySavedSettings();
    }
    
    // Always make cookie settings accessible via footer link
    // (even if banner is not shown because consent was already given)
}

/**
 * Create and append the cookie consent elements to the DOM
 */
function createCookieConsentElements() {
    // Create banner HTML
    const bannerHTML = `
        <div id="cookie-consent-banner" class="cookie-consent-banner">
            <div class="cookie-consent-content">
                <div class="cookie-consent-title">Cookie Preferences</div>
                <p class="cookie-consent-text">
                    We use cookies to provide essential functionality, improve your experience, and analyze site usage.
                    Click "Accept All" to allow all cookies or "Customize" to manage your preferences.
                </p>
            </div>
            <div class="cookie-consent-actions">
                <button id="cookie-customize" class="cookie-btn cookie-btn-secondary">Customize</button>
                <button id="cookie-reject" class="cookie-btn cookie-btn-tertiary">Reject All</button>
                <button id="cookie-accept-all" class="cookie-btn cookie-btn-primary">Accept All</button>
            </div>
        </div>
    `;
    
    // Create settings modal HTML
    const modalHTML = `
        <div id="cookie-settings-modal" class="cookie-settings-modal">
            <div class="cookie-settings-content">
                <div class="cookie-settings-header">
                    <h2 class="cookie-settings-title">Cookie Settings</h2>
                    <button id="cookie-settings-close" class="cookie-settings-close">&times;</button>
                </div>
                <div class="cookie-settings-body">
                    <div class="cookie-category">
                        <div class="cookie-category-header">
                            <h3 class="cookie-category-title">Essential Cookies</h3>
                            <label class="cookie-toggle">
                                <input type="checkbox" id="cookie-essential" checked disabled>
                                <span class="cookie-toggle-slider"></span>
                            </label>
                        </div>
                        <p class="cookie-category-description">
                            These cookies are necessary for the website to function properly. They enable core functionality 
                            such as security, network management, and account access. You cannot disable these cookies.
                        </p>
                    </div>
                    
                    <div class="cookie-category">
                        <div class="cookie-category-header">
                            <h3 class="cookie-category-title">Functional Cookies</h3>
                            <label class="cookie-toggle">
                                <input type="checkbox" id="cookie-functional" checked>
                                <span class="cookie-toggle-slider"></span>
                            </label>
                        </div>
                        <p class="cookie-category-description">
                            These cookies allow the website to remember choices you make and provide enhanced features.
                            For instance, they may remember your language preferences or the region you are in.
                        </p>
                    </div>
                    
                    <div class="cookie-category">
                        <div class="cookie-category-header">
                            <h3 class="cookie-category-title">Analytics Cookies</h3>
                            <label class="cookie-toggle">
                                <input type="checkbox" id="cookie-analytics" checked>
                                <span class="cookie-toggle-slider"></span>
                            </label>
                        </div>
                        <p class="cookie-category-description">
                            These cookies collect information about how you use the website, such as which pages you visit most often.
                            This helps us improve how our website works. All information these cookies collect is aggregated and anonymous.
                        </p>
                    </div>
                    
                    <div class="cookie-category">
                        <div class="cookie-category-header">
                            <h3 class="cookie-category-title">Authentication Cookies</h3>
                            <label class="cookie-toggle">
                                <input type="checkbox" id="cookie-authenticated">
                                <span class="cookie-toggle-slider"></span>
                            </label>
                        </div>
                        <p class="cookie-category-description">
                            These cookies help us recognize you when you log in and remember your login session.
                            These are needed if you want to stay logged in between visits.
                        </p>
                    </div>
                </div>
                <div class="cookie-settings-footer">
                    <button id="cookie-modal-accept-all" class="cookie-btn cookie-btn-secondary">Accept All</button>
                    <button id="cookie-save-preferences" class="cookie-btn cookie-btn-primary">Save Preferences</button>
                </div>
            </div>
        </div>
    `;
    
    // Append the elements to the document
    document.body.insertAdjacentHTML('beforeend', bannerHTML);
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

/**
 * Accept all cookies and hide the banner
 */
function acceptAllCookies() {
    const settings = {
        essential: true,
        functional: true,
        analytics: true,
        authenticated: true
    };
    
    // Save settings
    saveSettings(settings);
    
    // Hide banner
    banner.classList.remove('visible');
}

/**
 * Reject all non-essential cookies
 */
function rejectNonEssentialCookies() {
    const settings = {
        essential: true,     // Always required
        functional: false,
        analytics: false,
        authenticated: false
    };
    
    // Save settings
    saveSettings(settings);
    
    // Hide banner
    banner.classList.remove('visible');
}

/**
 * Open the cookie settings modal
 */
function openCookieSettings() {
    // Load current settings into toggles
    loadCurrentSettingsIntoModal();
    
    // Show modal
    modal.classList.add('visible');
}

/**
 * Close the cookie settings modal
 */
function closeModal() {
    modal.classList.remove('visible');
}

/**
 * Save the user's cookie preferences
 */
function savePreferences() {
    // Get current toggle states
    const settings = {
        essential: true,  // Always on
        functional: toggles.functional.checked,
        analytics: toggles.analytics.checked,
        authenticated: toggles.authenticated.checked
    };
    
    // Save settings
    saveSettings(settings);
    
    // Hide modal and banner
    closeModal();
    banner.classList.remove('visible');
}

/**
 * Load the current cookie settings into the modal toggles
 */
function loadCurrentSettingsIntoModal() {
    // Get current settings or defaults
    const settings = getCurrentSettings();
    
    // Update toggles
    toggles.essential.checked = true; // Always on
    toggles.functional.checked = settings.functional;
    toggles.analytics.checked = settings.analytics;
    toggles.authenticated.checked = settings.authenticated;
}

/**
 * Get the current cookie settings
 */
function getCurrentSettings() {
    // Try to get saved settings
    const savedSettings = getCookie(COOKIE_SETTINGS_NAME);
    
    if (savedSettings) {
        try {
            return JSON.parse(atob(savedSettings));
        } catch (e) {
            console.error('Error parsing cookie settings:', e);
        }
    }
    
    // Return defaults if no saved settings or error
    return {...DEFAULT_COOKIE_SETTINGS};
}

/**
 * Save cookie settings and set consent cookie
 */
function saveSettings(settings) {
    // Save the settings
    setCookie(COOKIE_SETTINGS_NAME, btoa(JSON.stringify(settings)), 365);
    
    // Set consent given
    setCookie(COOKIE_CONSENT_NAME, 'true', 365);
    
    // Apply the settings
    applySettings(settings);
}

/**
 * Apply saved cookie settings
 */
function applySavedSettings() {
    const settings = getCurrentSettings();
    applySettings(settings);
}

/**
 * Apply cookie settings to the website
 */
function applySettings(settings) {
    // This function would typically:
    // 1. Enable/disable various tracking and functional scripts
    // 2. Clear cookies for disabled categories
    
    // For demonstration, we'll just log the settings
    console.log('Applied cookie settings:', settings);
    
    // Example implementation:
    if (!settings.analytics) {
        // Disable analytics scripts/cookies
        disableAnalytics();
    }
    
    if (!settings.functional) {
        // Disable functional cookies
        disableFunctionalCookies();
    }
    
    if (!settings.authenticated && !isUserLoggedIn()) {
        // Clear authentication cookies if user is not logged in
        clearAuthCookies();
    }
}

// Helper functions for applying settings
function disableAnalytics() {
    // This would disable analytics scripts
    // For example, if using Google Analytics:
    window['ga-disable-UA-XXXXX-Y'] = true;
}

function disableFunctionalCookies() {
    // Clear functional cookies
    // Implementation depends on what functional cookies you use
}

function clearAuthCookies() {
    // Clear authentication cookies, except for the current session if logged in
    // Implementation depends on your authentication system
}

function isUserLoggedIn() {
    // Check if user is logged in
    // This is a placeholder - implement according to your auth system
    return document.body.classList.contains('logged-in') || 
           !!document.querySelector('.user-info') ||
           !!getCookie('session'); // Or whatever cookie name you use
}

/**
 * Set a cookie
 */
function setCookie(name, value, days) {
    let expires = '';
    
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = '; expires=' + date.toUTCString();
    }
    
    document.cookie = name + '=' + value + expires + '; path=/; SameSite=Lax';
}

/**
 * Get a cookie by name
 */
function getCookie(name) {
    const nameEQ = name + '=';
    const cookies = document.cookie.split(';');
    
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i];
        while (cookie.charAt(0) === ' ') {
            cookie = cookie.substring(1, cookie.length);
        }
        
        if (cookie.indexOf(nameEQ) === 0) {
            return cookie.substring(nameEQ.length, cookie.length);
        }
    }
    
    return null;
}

/**
 * Delete a cookie by name
 */
function deleteCookie(name) {
    setCookie(name, '', -1);
}

// Initialize when the document is ready
document.addEventListener('DOMContentLoaded', initCookieConsent);