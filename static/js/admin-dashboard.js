/**
 * Admin Dashboard Functionality
 * 
 * Specialized functionality for the admin dashboard, including:
 * - Commission selection and batch processing
 * - Payout status checking
 * - Search and filtering
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('admin-dashboard.js loaded');
    
    // Initialize the search functionality
    const searchInput = document.getElementById('commissionSearch');
    if (searchInput) {
        searchInput.addEventListener('input', filterCommissions);
    }
    
    // Filter commissions based on search input
    function filterCommissions() {
        const searchTerm = searchInput.value.toLowerCase();
        const commissionRows = document.querySelectorAll('.commission-row');
        
        commissionRows.forEach(row => {
            const affiliateText = row.querySelector('.affiliate-name').textContent.toLowerCase();
            const emailText = row.querySelector('.affiliate-email').textContent.toLowerCase();
            const amountText = row.querySelector('.commission-amount').textContent.toLowerCase();
            const matchesSearch = 
                affiliateText.includes(searchTerm) || 
                emailText.includes(searchTerm) || 
                amountText.includes(searchTerm);
            
            row.style.display = matchesSearch ? '' : 'none';
        });
        
        // Update empty state message
        updateEmptyState();
    }
    
    // Update empty state message based on search results
    function updateEmptyState() {
        const visibleRows = document.querySelectorAll('.commission-row[style=""]').length;
        const emptyMessage = document.getElementById('emptyCommissionsMessage');
        const tableBody = document.getElementById('commissionsTableBody');
        
        if (emptyMessage && tableBody) {
            if (visibleRows === 0) {
                // No visible rows - show empty message
                if (searchInput.value) {
                    // Empty due to search filter
                    emptyMessage.textContent = 'No commissions match your search criteria.';
                } else {
                    // Empty because there are no commissions
                    emptyMessage.textContent = 'No commissions are currently available for processing.';
                }
                emptyMessage.style.display = 'block';
                tableBody.style.display = 'none';
            } else {
                // Has visible rows - hide empty message
                emptyMessage.style.display = 'none';
                tableBody.style.display = '';
            }
        }
    }
    
    // Initialize the date filters
    const startDateFilter = document.getElementById('startDateFilter');
    const endDateFilter = document.getElementById('endDateFilter');
    
    if (startDateFilter && endDateFilter) {
        startDateFilter.addEventListener('change', applyDateFilters);
        endDateFilter.addEventListener('change', applyDateFilters);
    }
    
    // Apply date filters to the commissions table
    function applyDateFilters() {
        const startDate = startDateFilter.value ? new Date(startDateFilter.value) : null;
        const endDate = endDateFilter.value ? new Date(endDateFilter.value) : null;
        
        if (!startDate && !endDate) {
            // If no date filters, reset visibility
            document.querySelectorAll('.commission-row').forEach(row => {
                row.classList.remove('date-filtered');
            });
            
            // Re-apply search filter
            filterCommissions();
            return;
        }
        
        document.querySelectorAll('.commission-row').forEach(row => {
            const dateStr = row.querySelector('.commission-date').getAttribute('data-date');
            const rowDate = new Date(dateStr);
            
            let isVisible = true;
            
            if (startDate && rowDate < startDate) {
                isVisible = false;
            }
            
            if (endDate) {
                // Add one day to end date to include the end date itself
                const inclusiveEndDate = new Date(endDate);
                inclusiveEndDate.setDate(inclusiveEndDate.getDate() + 1);
                
                if (rowDate >= inclusiveEndDate) {
                    isVisible = false;
                }
            }
            
            if (isVisible) {
                row.classList.remove('date-filtered');
            } else {
                row.classList.add('date-filtered');
                row.style.display = 'none';
            }
        });
        
        // Re-apply search filter
        filterCommissions();
    }
    
    // Reset all filters
    const resetFiltersButton = document.getElementById('resetFilters');
    if (resetFiltersButton) {
        resetFiltersButton.addEventListener('click', function() {
            if (searchInput) searchInput.value = '';
            if (startDateFilter) startDateFilter.value = '';
            if (endDateFilter) endDateFilter.value = '';
            
            // Reset all rows
            document.querySelectorAll('.commission-row').forEach(row => {
                row.classList.remove('date-filtered');
                row.style.display = '';
            });
            
            // Update empty state
            updateEmptyState();
        });
    }
    
    // Initialize payout status refresh buttons
    const refreshButtons = document.querySelectorAll('.refresh-status');
    refreshButtons.forEach(button => {
        button.addEventListener('click', function() {
            const batchId = this.getAttribute('data-batch-id');
            if (!batchId) return;
            
            // Show spinner and disable button
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
            
            // Fetch updated status
            fetch(`/admin/payouts/check-status/${batchId}`)
                .then(response => response.json())
                .then(data => {
                    // Update status in the table
                    const statusCell = document.querySelector(`.status-cell[data-batch-id="${batchId}"]`);
                    if (statusCell) {
                        statusCell.textContent = data.status;
                        
                        // Update status class
                        statusCell.classList.remove('text-warning', 'text-success', 'text-danger');
                        if (data.status === 'SUCCESS') {
                            statusCell.classList.add('text-success');
                        } else if (data.status === 'PENDING') {
                            statusCell.classList.add('text-warning');
                        } else if (data.status === 'FAILED') {
                            statusCell.classList.add('text-danger');
                        }
                    }
                    
                    // Reset button
                    this.disabled = false;
                    this.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
                    
                    // Update details if available
                    if (data.details) {
                        const detailsCell = document.querySelector(`.details-cell[data-batch-id="${batchId}"]`);
                        if (detailsCell) {
                            detailsCell.textContent = data.details;
                        }
                    }
                })
                .catch(error => {
                    console.error('Error refreshing payout status:', error);
                    this.disabled = false;
                    this.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Failed';
                    setTimeout(() => {
                        this.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
                    }, 3000);
                });
        });
    });
    
    // Call updateEmptyState initially to set the correct state
    updateEmptyState();
});