document.addEventListener('DOMContentLoaded', function() {
    // Any client-side JavaScript can go here
    console.log('Warehouse Management System loaded');
    
    // Example: Confirm before deleting
    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });
    
    // Example: Date picker initialization (if you add one later)
    // flatpickr("#incoming_date", {});
    // flatpickr("#expiry_date", {});
});