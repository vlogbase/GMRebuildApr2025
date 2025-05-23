/**
 * Account Tabs Navigation Module
 * Handles desktop and mobile tab navigation for the account page
 */

function initMobileTabNavigation() {
    // Handle dropdown selector for mobile
    const mobileTabSelector = document.querySelector('.mobile-tab-selector');
    if (mobileTabSelector) {
        mobileTabSelector.addEventListener('change', function(e) {
            const selectedTab = e.target.value;
            console.log('Mobile tab selector changed to:', selectedTab);

            // Update active button states
            document.querySelectorAll('.mobile-tab-btn').forEach(btn => {
                if (btn.dataset.tab === selectedTab) {
                    btn.classList.remove('btn-outline-secondary');
                    btn.classList.add('btn-outline-primary');
                } else {
                    btn.classList.remove('btn-outline-primary');
                    btn.classList.add('btn-outline-secondary');
                }
            });

            // Find the Bootstrap tab trigger and activate it
            const tabTrigger = document.querySelector(`[data-bs-target="#${selectedTab}"]`);
            if (tabTrigger) {
                const bsTab = new bootstrap.Tab(tabTrigger);
                bsTab.show();
            }
        });
    }

    // Handle mobile tab buttons
    document.querySelectorAll('.mobile-tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            console.log('Mobile tab button clicked:', tabName);

            // Update dropdown value
            if (mobileTabSelector) {
                mobileTabSelector.value = tabName;
            }

            // Update active button states
            document.querySelectorAll('.mobile-tab-btn').forEach(btn => {
                if (btn.dataset.tab === tabName) {
                    btn.classList.remove('btn-outline-secondary');
                    btn.classList.add('btn-outline-primary');
                } else {
                    btn.classList.remove('btn-outline-primary');
                    btn.classList.add('btn-outline-secondary');
                }
            });

            // Find the Bootstrap tab trigger and activate it
            const tabTrigger = document.querySelector(`[data-bs-target="#${tabName}"]`);
            if (tabTrigger) {
                const bsTab = new bootstrap.Tab(tabTrigger);
                bsTab.show();
            }
        });
    });

    // Check URL for tab parameter
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab');
    if (tabParam) {
        // Update mobile UI if on mobile
        if (window.innerWidth < 768) {
            // Update dropdown value
            if (mobileTabSelector) {
                mobileTabSelector.value = tabParam;
            }

            // Update active button states
            document.querySelectorAll('.mobile-tab-btn').forEach(btn => {
                if (btn.dataset.tab === tabParam) {
                    btn.classList.remove('btn-outline-secondary');
                    btn.classList.add('btn-outline-primary');
                } else {
                    btn.classList.remove('btn-outline-primary');
                    btn.classList.add('btn-outline-secondary');
                }
            });
        }

        // Find the Bootstrap tab trigger and activate it
        const tabTrigger = document.querySelector(`[data-bs-target="#${tabParam}"]`);
        if (tabTrigger) {
            const bsTab = new bootstrap.Tab(tabTrigger);
            bsTab.show();
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded event fired - Initializing account page tab navigation');
    initMobileTabNavigation();
});