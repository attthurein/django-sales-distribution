document.addEventListener('DOMContentLoaded', function() {
    // Check if the modal element exists before trying to initialize it
    const modalEl = document.getElementById('confirmationModal');
    if (!modalEl) return;

    const confirmModal = new bootstrap.Modal(modalEl);
    let targetForm = null;
    let targetLink = null;
    
    // Helper function to show modal
    function showModal(trigger, messageOverride) {
        const title = trigger.dataset.title || 'Confirmation';
        const message = messageOverride || trigger.dataset.message || 'Are you sure you want to proceed?';
        const btnClass = trigger.dataset.btnClass || 'btn-primary';
        const btnText = trigger.dataset.btnText || 'Confirm';

        document.getElementById('modalTitle').textContent = title;
        document.getElementById('modalBody').textContent = message;
        
        const confirmBtn = document.getElementById('modalConfirmBtn');
        confirmBtn.className = 'btn';
        confirmBtn.classList.add(btnClass);
        confirmBtn.textContent = btnText;

        confirmModal.show();
    }

    document.getElementById('modalConfirmBtn').addEventListener('click', function() {
        if (targetForm) {
            targetForm.submit();
        } else if (targetLink) {
            window.location.href = targetLink;
        }
        confirmModal.hide();
    });

    // Expose confirmAction globally (for onclick usage)
    window.confirmAction = function(event) {
        const trigger = event.currentTarget;
        let form = null;

        // Determine the form involved, if any
        if (trigger.tagName === 'FORM') {
            form = trigger;
        } else if (trigger.form) {
            form = trigger.form;
        } else {
            form = trigger.closest('form');
        }

        // If triggered by a click on a submit button (not form onsubmit), check validation first
        if (event.type === 'click' && form && trigger.type === 'submit') {
            if (!form.checkValidity()) {
                form.reportValidity();
                event.preventDefault();
                return false;
            }
        }

        event.preventDefault();
        
        targetForm = null;
        targetLink = null;

        if (trigger.tagName === 'FORM') {
            targetForm = trigger;
        } else if (trigger.tagName === 'A') {
            targetLink = trigger.href;
        } else if (form) {
            targetForm = form;
        }
        
        showModal(trigger);
        return false;
    };

    // Handle data-confirm on forms (replaces ui_utils.js logic)
    document.body.addEventListener('submit', function(e) {
        const form = e.target;
        const message = form.dataset.confirm;
        
        // If message exists, prevent default and show modal
        // Note: If confirmAction was used, it would have already prevented default and stopped propagation?
        // Actually inline onclick runs before addEventListener.
        // If onclick returned false, this listener shouldn't fire if default was prevented? 
        // Wait, event propagation continues unless stopPropagation is called.
        // But if default prevented, we shouldn't do anything?
        if (e.defaultPrevented) return;

        if (message) {
            e.preventDefault();
            targetForm = form;
            targetLink = null;
            showModal(form, message);
        }
    });

    // Handle data-confirm-click (replaces ui_utils.js logic)
    document.body.addEventListener('click', function(e) {
        const target = e.target.closest('[data-confirm-click]');
        if (!target) return;
        if (e.defaultPrevented) return;

        const message = target.dataset.confirmClick;
        if (message) {
            e.preventDefault();
            
            targetForm = null;
            targetLink = null;

            if (target.tagName === 'A') {
                targetLink = target.href;
            } else if (target.type === 'submit' && target.form) {
                targetForm = target.form;
            }

            showModal(target, message);
        }
    });
});
