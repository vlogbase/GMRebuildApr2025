// Admin interface JavaScript functionality

$(document).ready(function() {
    console.log('Admin interface initialized');
    
    // Initialize any Bootstrap tooltips
    $('[data-toggle="tooltip"]').tooltip();
    
    // Initialize Bootstrap popovers
    $('[data-toggle="popover"]').popover();
    
    // Handle confirmation dialogs for delete actions
    $('.btn-delete').on('click', function(e) {
        if (!confirm('Are you sure you want to delete this item?')) {
            e.preventDefault();
            return false;
        }
    });
    
    // Handle confirmation dialogs for approval actions
    $('.btn-approve').on('click', function(e) {
        if (!confirm('Are you sure you want to approve this item?')) {
            e.preventDefault();
            return false;
        }
    });
    
    // Handle confirmation dialogs for rejection actions
    $('.btn-reject').on('click', function(e) {
        if (!confirm('Are you sure you want to reject this item?')) {
            e.preventDefault();
            return false;
        }
    });
    
    // Handle confirmation dialogs for payout actions
    $('.btn-payout').on('click', function(e) {
        if (!confirm('Are you sure you want to process payouts for the selected items?')) {
            e.preventDefault();
            return false;
        }
    });
    
    // Initialize datepickers on date fields
    $('.datepicker').datepicker({
        format: 'yyyy-mm-dd',
        autoclose: true
    });
    
    // Function to format numbers with commas
    function formatNumber(num) {
        return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,');
    }
    
    // Format any elements with the 'format-number' class
    $('.format-number').each(function() {
        var num = parseInt($(this).text().trim());
        if (!isNaN(num)) {
            $(this).text(formatNumber(num));
        }
    });
    
    // Function to format currency values
    function formatCurrency(num) {
        return '£' + num.toFixed(2).replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,');
    }
    
    // Format any elements with the 'format-currency' class
    $('.format-currency').each(function() {
        var num = parseFloat($(this).text().trim().replace('£', ''));
        if (!isNaN(num)) {
            $(this).text(formatCurrency(num));
        }
    });
});