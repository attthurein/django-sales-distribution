/**
 * Global UI utility handlers
 * - Confirmation dialogs via data-confirm
 * - Print buttons via js-print class
 * - Auto-submit forms on change via js-submit-on-change class
 */
document.addEventListener('DOMContentLoaded', function() {
    // Handle form submissions with confirmation
    document.body.addEventListener('submit', function(e) {
        const form = e.target;
        const message = form.getAttribute('data-confirm');
        if (message) {
            if (!confirm(message)) {
                e.preventDefault();
            }
        }
    });

    // Handle clicks on links/buttons with confirmation
    document.body.addEventListener('click', function(e) {
        const target = e.target.closest('[data-confirm-click]');
        if (target) {
            const message = target.getAttribute('data-confirm-click');
            if (!confirm(message)) {
                e.preventDefault();
            }
        }
    });

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
});
