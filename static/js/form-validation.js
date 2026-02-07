// Form Validation
const FormValidator = {
    init() {
        const forms = document.querySelectorAll('form[data-validate]');
        forms.forEach(form => this.setupForm(form));
    },

    setupForm(form) {
        const inputs = form.querySelectorAll('input, select, textarea');

        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearError(input));
        });

        form.addEventListener('submit', (e) => {
            if (!this.validateForm(form)) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    },

    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let errorMessage = '';

        // Required validation
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'This field is required';
        }

        // Email validation
        if (field.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address';
            }
        }

        // Number validation
        if (field.type === 'number' && value) {
            const min = field.getAttribute('min');
            const max = field.getAttribute('max');

            if (min && parseFloat(value) < parseFloat(min)) {
                isValid = false;
                errorMessage = `Value must be at least ${min}`;
            }
            if (max && parseFloat(value) > parseFloat(max)) {
                isValid = false;
                errorMessage = `Value must be at most ${max}`;
            }
        }

        // Update UI
        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
            this.removeError(field);
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
            this.showError(field, errorMessage);
        }

        return isValid;
    },

    validateForm(form) {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });

        return isValid;
    },

    showError(field, message) {
        this.removeError(field);

        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = message;
        feedback.setAttribute('data-validation-error', '');

        field.parentNode.appendChild(feedback);
    },

    removeError(field) {
        const error = field.parentNode.querySelector('[data-validation-error]');
        if (error) {
            error.remove();
        }
    },

    clearError(field) {
        field.classList.remove('is-invalid', 'is-valid');
        this.removeError(field);
    }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    FormValidator.init();
});
