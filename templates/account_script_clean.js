document.addEventListener('DOMContentLoaded', function() {
    console.log('Account.html: DOMContentLoaded. Admin tab JS should handle activation if ?tab=admin is present.');
    // Any other critical, simple, and non-conflicting initializations for other parts of the page can remain,
    // but tab activation logic for the main tabs should primarily be handled by Bootstrap's data attributes
    // or specific, non-conflicting small scripts.
});

// If window.openTab is essential for deep linking or other functionalities,
// ensure it's defined correctly and doesn't conflict.
// A safe version for Bootstrap 5:
window.openTab = function(tabId) {
    console.log('window.openTab called for:', tabId);
    const tabTriggerEl = document.querySelector(`[data-bs-target="#${tabId}"]`);
    if (tabTriggerEl) {
        const tab = new bootstrap.Tab(tabTriggerEl);
        tab.show();
    } else {
        console.error(`Tab trigger element not found for target: #${tabId}`);
    }
};