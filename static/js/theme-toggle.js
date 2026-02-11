// Dark Mode Toggle
const ThemeToggle = {
    STORAGE_KEY: 'theme-preference',

    init() {
        this.applyTheme(this.getPreference());
        this.initToggleButton();
    },

    getPreference() {
        return localStorage.getItem(this.STORAGE_KEY) || 'light';
    },

    setPreference(theme) {
        localStorage.setItem(this.STORAGE_KEY, theme);
        this.applyTheme(theme);
    },

    applyTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);

        // Update toggle button icon if it exists
        const icon = document.querySelector('#theme-toggle-icon');
        if (icon) {
            icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
        }
    },

    toggle() {
        const current = this.getPreference();
        const newTheme = current === 'light' ? 'dark' : 'light';
        this.setPreference(newTheme);
    },

    initToggleButton() {
        const button = document.querySelector('#theme-toggle-btn');
        if (button) {
            // Remove any existing event listeners to prevent duplicates (though init runs once usually)
            button.replaceWith(button.cloneNode(true));
            const newButton = document.querySelector('#theme-toggle-btn');
            newButton.addEventListener('click', () => this.toggle());
        }
    }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    ThemeToggle.init();
});
