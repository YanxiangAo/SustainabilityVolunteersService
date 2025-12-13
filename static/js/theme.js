/**
 * theme.js - Theme and Customization Script
 * A-LEVEL REQUIREMENT: User can customize UI appearance
 * B-LEVEL REQUIREMENT: Different roles have different color schemes
 * 
 * Features:
 * - Dark/Light mode toggle with localStorage persistence
 * - Role-based accent colors (participant=green, organization=blue, admin=purple)
 * - Background pattern customization
 */
(function () {
    // ========================================
    // 1. Initialize saved preferences
    // ========================================
    const savedTheme = localStorage.getItem('theme') || 'light';
    const savedBackground = localStorage.getItem('bgPattern') || 'none';

    // Apply saved theme immediately to prevent flash
    document.documentElement.setAttribute('data-theme', savedTheme);
    document.documentElement.setAttribute('data-bg', savedBackground);

    // Detect user role from page (check sidebar or body class)
    function detectUserRole() {
        const sidebarText = document.querySelector('.sidebar-header')?.textContent || '';

        // Check for participant/volunteer (participant dashboard shows "Volunteer")
        if (sidebarText.includes('Participant') || sidebarText.includes('Volunteer') ||
            document.body.classList.contains('participant-dashboard')) {
            return 'participant';
        } else if (sidebarText.includes('Organization') ||
            document.body.classList.contains('organization-dashboard')) {
            return 'organization';
        } else if (sidebarText.includes('Admin') || sidebarText.includes('Administrator') ||
            document.body.classList.contains('admin-panel')) {
            return 'admin';
        }
        return 'default';
    }

    // ========================================
    // 2. Icon generators for theme toggle
    // ========================================
    function getSunIcon() {
        return `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`;
    }

    function getMoonIcon() {
        return `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;
    }

    function getIcon(theme) {
        return theme === 'dark' ? getSunIcon() : getMoonIcon();
    }

    // ========================================
    // 3. Create theme toggle button
    // ========================================
    function createThemeToggleButton() {
        const btn = document.createElement('button');
        btn.className = 'theme-toggle-btn';
        btn.title = 'Toggle Dark/Light Mode';
        btn.innerHTML = getIcon(savedTheme);

        btn.addEventListener('click', function () {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            btn.innerHTML = getIcon(newTheme);
        });

        return btn;
    }

    // ========================================
    // 4. Create background pattern selector
    // A-LEVEL: Custom background/pattern UI
    // ========================================
    function createBackgroundSelector() {
        const container = document.createElement('div');
        container.className = 'bg-selector';
        container.style.cssText = 'display:flex;gap:0.5rem;align-items:center;margin-top:0.5rem;';

        const patterns = [
            { value: 'none', label: '●', title: 'Solid' },
            { value: 'dots', label: '◉', title: 'Dots' },
            { value: 'grid', label: '⊞', title: 'Grid' },
            { value: 'lines', label: '☰', title: 'Lines' }
        ];

        patterns.forEach(pattern => {
            const btn = document.createElement('button');
            btn.className = 'bg-pattern-btn';
            btn.textContent = pattern.label;
            btn.title = pattern.title;
            btn.style.cssText = 'padding:0.25rem 0.5rem;border:1px solid var(--gray-300);border-radius:4px;background:var(--white);cursor:pointer;font-size:1rem;';
            if (savedBackground === pattern.value) {
                btn.style.borderColor = 'var(--primary-green)';
                btn.style.backgroundColor = '#dcfce7';
            }
            btn.addEventListener('click', () => {
                document.documentElement.setAttribute('data-bg', pattern.value);
                localStorage.setItem('bgPattern', pattern.value);
                // Update button styles
                container.querySelectorAll('.bg-pattern-btn').forEach(b => {
                    b.style.borderColor = 'var(--gray-300)';
                    b.style.backgroundColor = 'var(--white)';
                });
                btn.style.borderColor = 'var(--primary-green)';
                btn.style.backgroundColor = '#dcfce7';
            });
            container.appendChild(btn);
        });

        return container;
    }

    // ========================================
    // 5. Apply role-based theme on load
    // B-LEVEL: Different colors for different roles
    // ========================================
    document.addEventListener('DOMContentLoaded', function () {
        const role = detectUserRole();
        document.documentElement.setAttribute('data-role', role);

        // Create and inject theme toggle button
        const themeBtn = createThemeToggleButton();
        const sidebarHeader = document.querySelector('.sidebar-header');
        const headerContent = document.querySelector('.header-content');
        const authCard = document.querySelector('.auth-card');

        if (sidebarHeader) {
            // Dashboard pages: Add controls to sidebar
            sidebarHeader.style.display = 'flex';
            sidebarHeader.style.flexWrap = 'wrap';
            sidebarHeader.style.justifyContent = 'space-between';
            sidebarHeader.style.alignItems = 'center';

            const controls = document.createElement('div');
            controls.style.cssText = 'display:flex;flex-direction:column;align-items:flex-end;gap:0.5rem;';
            controls.appendChild(themeBtn);
            controls.appendChild(createBackgroundSelector());
            sidebarHeader.appendChild(controls);
        } else if (headerContent) {
            // Find the nav buttons container (the last child div with flex/buttons)
            const navButtons = headerContent.querySelector('.flex');
            if (navButtons) {
                navButtons.appendChild(themeBtn);
            } else {
                headerContent.appendChild(themeBtn);
            }
        } else if (authCard) {
            themeBtn.style.cssText = 'position:fixed;top:1rem;right:1rem;z-index:1000;background:var(--white);box-shadow:var(--shadow);';
            document.body.appendChild(themeBtn);
        } else {
            themeBtn.style.cssText = 'position:fixed;top:1rem;right:1rem;z-index:1000;';
            document.body.appendChild(themeBtn);
        }
    });
})();
