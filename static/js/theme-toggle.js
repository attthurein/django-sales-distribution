// Dark Mode Toggle
const ThemeToggle = {
    STORAGE_KEY: 'theme-preference',

    init() {
        this.applyTheme(this.getPreference());
        this.createToggleButton();
    },

    getPreference() {
        return localStorage.getItem(this.STORAGE_KEY) || 'light';
    },

    setPreference(theme) {
        localStorage.setItem(this.STORAGE_KEY, theme);
        this.applyTheme(theme);
    },

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);

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

    createToggleButton() {
        const navbarNav = document.querySelector('.navbar-nav:last-of-type');
        if (!navbarNav) return;

        const li = document.createElement('li');
        li.className = 'nav-item';

        const button = document.createElement('button');
        button.className = 'nav-link btn btn-link';
        button.setAttribute('aria-label', 'Toggle dark mode');
        button.innerHTML = `<i id="theme-toggle-icon" class="bi bi-moon-fill"></i>`;
        button.addEventListener('click', () => this.toggle());

        li.appendChild(button);
        navbarNav.insertBefore(li, navbarNav.firstChild);

        // Update icon based on current theme
        this.applyTheme(this.getPreference());
    }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    ThemeToggle.init();
});
