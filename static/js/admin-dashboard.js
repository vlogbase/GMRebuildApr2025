/**
 * Admin Dashboard JavaScript
 * 
 * This script handles the functionality specific to the admin dashboard,
 * including commission management, status updates, and payouts processing.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin dashboard JS loaded');
    
    // Function to handle the "Select All" checkbox
    const selectAllCheckbox = document.getElementById('selectAllCommissions');
    if (selectAllCheckbox) {
        console.log('Select all checkbox found');
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            document.querySelectorAll('.commission-checkbox').forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            updateSelectedCount();
        });
    }
    
    // Add event listeners to individual commission checkboxes
    document.querySelectorAll('.commission-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateSelectedCount);
    });
    
    // Function to update the selected count and enable/disable batch actions
    function updateSelectedCount() {
        const selectedCount = document.querySelectorAll('.commission-checkbox:checked').length;
        const countDisplay = document.getElementById('selectedCount');
        const processButton = document.getElementById('processPayoutsBtn');
        
        if (countDisplay) {
            countDisplay.textContent = `${selectedCount} commissions selected`;
        }
        
        if (processButton) {
            if (selectedCount > 0) {
                processButton.removeAttribute('disabled');
            } else {
                processButton.setAttribute('disabled', 'disabled');
            }
        }
    }
    
    // Handle form submission for batch processing
    const batchForm = document.getElementById('commissionBatchForm');
    if (batchForm) {
        batchForm.addEventListener('submit', function(e) {
            const selectedCount = document.querySelectorAll('.commission-checkbox:checked').length;
            
            if (selectedCount === 0) {
                e.preventDefault();
                alert('Please select at least one commission to process.');
                return false;
            }
            
            if (!confirm(`Are you sure you want to process ${selectedCount} commissions for payment?`)) {
                e.preventDefault();
                return false;
            }
            
            return true;
        });
    }
    
    // Initialize tooltips from Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Add filter functionality for the commissions table
    const searchInput = document.getElementById('commission-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const tableRows = document.querySelectorAll('#commissionsTable tbody tr');
            
            tableRows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Simple statistics chart initialization (if Chart.js is available)
    if (typeof Chart !== 'undefined') {
        const ctx = document.getElementById('adminStatsChart');
        if (ctx) {
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Held', 'Approved', 'Paid', 'Rejected'],
                    datasets: [{
                        label: 'Commission Status',
                        data: [
                            document.querySelectorAll('.badge.bg-warning').length,
                            document.querySelectorAll('.badge.bg-success').length,
                            document.querySelectorAll('.badge.bg-info').length,
                            document.querySelectorAll('.badge.bg-danger').length
                        ],
                        backgroundColor: [
                            'rgba(255, 193, 7, 0.5)',
                            'rgba(40, 167, 69, 0.5)',
                            'rgba(23, 162, 184, 0.5)',
                            'rgba(220, 53, 69, 0.5)'
                        ],
                        borderColor: [
                            'rgba(255, 193, 7, 1)',
                            'rgba(40, 167, 69, 1)',
                            'rgba(23, 162, 184, 1)',
                            'rgba(220, 53, 69, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });
        }
    }
    
    // Log that initialization is complete
    console.log('Admin dashboard JS initialization complete');
});