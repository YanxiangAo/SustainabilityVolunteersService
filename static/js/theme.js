/**
 * Theme Toggle Functionality
 * Handles dark/light mode switching with localStorage persistence
 */

(function() {
    'use strict';

    const THEME_STORAGE_KEY = 'theme-preference';
    const THEME_ATTRIBUTE = 'data-theme';

    /**
     * Get the current theme preference
     * Priority: localStorage > system preference > 'light'
     */
    function getThemePreference() {
        // Check localStorage first
        const stored = localStorage.getItem(THEME_STORAGE_KEY);
        if (stored === 'dark' || stored === 'light') {
            return stored;
        }

        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }

        // Default to light
        return 'light';
    }

    /**
     * Apply theme to document
     */
    function applyTheme(theme) {
        const root = document.documentElement;
        
        // Always set the attribute to prevent system preference from overriding
        root.setAttribute(THEME_ATTRIBUTE, theme);

        // Save preference
        localStorage.setItem(THEME_STORAGE_KEY, theme);
    }

    /**
     * Toggle between dark and light theme
     */
    function toggleTheme() {
        const currentTheme = getThemePreference();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
        updateThemeIcon(newTheme);
    }

    /**
     * Update theme toggle button icon
     */
    function updateThemeIcon(theme) {
        const sunIcons = document.querySelectorAll('.theme-icon-sun');
        const moonIcons = document.querySelectorAll('.theme-icon-moon');

        // Show sun icon in dark mode (to switch to light), moon icon in light mode (to switch to dark)
        if (theme === 'dark') {
            sunIcons.forEach(icon => icon.style.display = 'flex');
            moonIcons.forEach(icon => icon.style.display = 'none');
        } else {
            sunIcons.forEach(icon => icon.style.display = 'none');
            moonIcons.forEach(icon => icon.style.display = 'flex');
        }
    }

    /**
     * Initialize theme on page load
     */
    function initTheme() {
        const theme = getThemePreference();
        applyTheme(theme);
        updateThemeIcon(theme);

        // Listen for system theme changes (if no manual preference is set)
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', (e) => {
                // Only apply system preference if user hasn't manually set a preference
                const stored = localStorage.getItem(THEME_STORAGE_KEY);
                if (!stored) {
                    const systemTheme = e.matches ? 'dark' : 'light';
                    applyTheme(systemTheme);
                    updateThemeIcon(systemTheme);
                }
            });
        }
    }

    /**
     * Set up theme toggle button event listeners
     */
    function setupThemeToggleButtons() {
        const toggleButtons = document.querySelectorAll('.theme-toggle');
        
        toggleButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                toggleTheme();
            });
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            initTheme();
            setupThemeToggleButtons();
        });
    } else {
        initTheme();
        setupThemeToggleButtons();
    }

    // Export for external use if needed
    window.themeToggle = {
        toggle: toggleTheme,
        setTheme: applyTheme,
        getTheme: getThemePreference
    };
})();
