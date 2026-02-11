/**
 * Global UI utility handlers
 * - Confirmation dialogs via data-confirm
 * - Print buttons via js-print class
 * - Auto-submit forms on change via js-submit-on-change class
 */
document.addEventListener('DOMContentLoaded', function() {
    // Note: Confirmation dialogs via data-confirm and data-confirm-click
    // are now handled globally by confirm_modal.js

    // Handle print buttons
    const printButtons = document.querySelectorAll('.js-print');
    printButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            window.print();
        });
    });

    // Handle auto-submit on change
    const autoSubmitElements = document.querySelectorAll('.js-submit-on-change');
    autoSubmitElements.forEach(element => {
        element.addEventListener('change', function() {
            this.form.submit();
        });
    });

    // Dynamic body padding adjustment for fixed header
    function adjustBodyPadding() {
        const header = document.querySelector('.app-header');
        if (header) {
            // Add a small buffer (e.g. 10px) to the height
            document.body.style.paddingTop = (header.offsetHeight + 10) + 'px';
        }
    }
    
    // Run on load and resize
    adjustBodyPadding();
    window.addEventListener('resize', adjustBodyPadding);
});
