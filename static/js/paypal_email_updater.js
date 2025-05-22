// PayPal email update functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('PayPal email updater initialized');
    
    // Get elements
    const editPaypalBtn = document.getElementById('editPaypalBtn');
    const savePaypalBtn = document.getElementById('savePaypalBtn');
    const cancelEditBtn = document.getElementById('cancelEditBtn');
    const paypalEmailForm = document.getElementById('paypalEmailForm');
    const currentPaypalDisplay = document.getElementById('current-paypal-email');
    const currentPaypalEmail = document.getElementById('currentPaypalEmail');
    const paypalSuccessAlert = document.getElementById('paypalSuccessAlert');
    const paypalErrorAlert = document.getElementById('paypalErrorAlert');
    
    console.log('PayPal elements found:', {
        editButton: Boolean(editPaypalBtn),
        saveButton: Boolean(savePaypalBtn),
        cancelButton: Boolean(cancelEditBtn),
        form: Boolean(paypalEmailForm)
    });
    
    // Helper function to hide alerts
    function hidePaypalAlerts() {
        if (paypalSuccessAlert) paypalSuccessAlert.classList.add('d-none');
        if (paypalErrorAlert) paypalErrorAlert.classList.add('d-none');
    }
    
    // Edit button shows the form
    if (editPaypalBtn && paypalEmailForm) {
        editPaypalBtn.addEventListener('click', function() {
            console.log('Edit PayPal email clicked');
            hidePaypalAlerts();
            paypalEmailForm.style.display = 'block';
            editPaypalBtn.style.display = 'none';
            if (currentPaypalDisplay) currentPaypalDisplay.style.display = 'none';
            
            // Focus on input field
            setTimeout(function() {
                const emailInput = document.getElementById('paypal_email');
                if (emailInput) emailInput.focus();
            }, 100);
        });
    }
    
    // Cancel button hides the form
    if (cancelEditBtn && paypalEmailForm) {
        cancelEditBtn.addEventListener('click', function() {
            console.log('Cancel PayPal edit clicked');
            hidePaypalAlerts();
            paypalEmailForm.style.display = 'none';
            if (editPaypalBtn) editPaypalBtn.style.display = 'inline-block';
            if (currentPaypalDisplay) currentPaypalDisplay.style.display = 'flex';
        });
    }
    
    // Save button submits the form via AJAX
    if (savePaypalBtn && paypalEmailForm) {
        savePaypalBtn.addEventListener('click', function() {
            console.log('Save PayPal email clicked');
            hidePaypalAlerts();
            
            // Get data
            const paypalEmail = document.getElementById('paypal_email').value;
            const csrfToken = document.getElementById('paypal_csrf_token').value;
            
            // Validate email
            if (!paypalEmail || !paypalEmail.includes('@')) {
                if (paypalErrorAlert) {
                    paypalErrorAlert.textContent = 'Please enter a valid email address.';
                    paypalErrorAlert.classList.remove('d-none');
                }
                return;
            }
            
            // Show loading state
            savePaypalBtn.disabled = true;
            savePaypalBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
            
            // Submit via AJAX
            const updateEndpoint = document.getElementById('paypal_update_endpoint').value;
            console.log('Using endpoint:', updateEndpoint);
            
            fetch(updateEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ paypal_email: paypalEmail })
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                // Reset button
                savePaypalBtn.disabled = false;
                savePaypalBtn.innerHTML = 'Save Changes';
                
                if (data.success) {
                    // Update displayed email
                    if (currentPaypalEmail) {
                        currentPaypalEmail.textContent = data.new_email;
                    }
                    
                    // Show success
                    if (paypalSuccessAlert) {
                        paypalSuccessAlert.textContent = data.message || 'PayPal email updated successfully!';
                        paypalSuccessAlert.classList.remove('d-none');
                    }
                    
                    // Hide form after a delay
                    setTimeout(function() {
                        paypalEmailForm.style.display = 'none';
                        if (editPaypalBtn) editPaypalBtn.style.display = 'inline-block';
                        if (currentPaypalDisplay) currentPaypalDisplay.style.display = 'flex';
                        
                        // Hide success after another delay
                        setTimeout(function() {
                            if (paypalSuccessAlert) paypalSuccessAlert.classList.add('d-none');
                        }, 5000);
                    }, 1500);
                } else {
                    // Show error
                    if (paypalErrorAlert) {
                        paypalErrorAlert.textContent = data.error || 'Error updating PayPal email. Please try again.';
                        paypalErrorAlert.classList.remove('d-none');
                    }
                }
            })
            .catch(function(error) {
                console.error('Error updating PayPal email:', error);
                
                // Reset button
                savePaypalBtn.disabled = false;
                savePaypalBtn.innerHTML = 'Save Changes';
                
                // Show error
                if (paypalErrorAlert) {
                    paypalErrorAlert.textContent = 'Network error. Please check your connection and try again.';
                    paypalErrorAlert.classList.remove('d-none');
                }
            });
        });
    }
});