// Clean implementation of account.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('Account.html: DOMContentLoaded. Admin tab JS should handle activation if ?tab=admin is present.');
    
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // If window.openTab is essential for deep linking or other functionalities
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
    
    // Special handler for the admin tab to ensure it's visible when activated
    window.openAdminTab = function() {
        console.log('Manual admin tab opening requested');
        
        // Get the tab element
        const adminTab = document.getElementById('admin');
        const adminButton = document.getElementById('admin-tab');
        
        if (adminTab && adminButton) {
            // First use Bootstrap's API
            const tab = new bootstrap.Tab(adminButton);
            tab.show();
            
            // Then ensure manually that it's visible (backup approach)
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('show', 'active');
            });
            adminTab.classList.add('show', 'active');
            
            // Also activate the button
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            adminButton.classList.add('active');
            
            console.log('Admin tab should now be visible');
        } else {
            console.error('Admin tab elements not found:', {
                tab: adminTab !== null,
                button: adminButton !== null
            });
        }
    };
    
    // Check if we should activate the admin tab based on URL params
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Checking URL parameters for tab selection');
        const urlParams = new URLSearchParams(window.location.search);
        const tabParam = urlParams.get('tab');
        
        if (tabParam === 'admin') {
            console.log('URL parameter indicates admin tab should be active');
            window.openAdminTab();
        }
    });
});