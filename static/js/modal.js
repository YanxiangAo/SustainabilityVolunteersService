/**
 * Custom Modal System
 * Replaces native alert(), confirm(), and prompt() with beautiful custom modals
 */

const Modal = {
    /**
     * Show an alert modal
     * @param {string} message - The message to display
     * @param {Object} options - Optional configuration
     * @param {string} options.title - Modal title (default: based on type)
     * @param {string} options.type - 'success' | 'error' | 'warning' | 'info' (default: 'info')
     * @param {string} options.buttonText - OK button text (default: 'OK')
     * @returns {Promise<void>}
     */
    alert(message, options = {}) {
        return new Promise((resolve) => {
            const type = options.type || 'info';
            const title = options.title || this._getDefaultTitle(type);
            const buttonText = options.buttonText || 'OK';

            const overlay = this._createOverlay();
            const modal = document.createElement('div');
            modal.className = 'custom-modal';
            modal.innerHTML = `
                <div class="custom-modal-header">
                    <div class="custom-modal-icon ${type}">
                        ${this._getIcon(type)}
                    </div>
                    <h3 class="custom-modal-title">${this._escapeHtml(title)}</h3>
                </div>
                <div class="custom-modal-body">
                    <p class="custom-modal-message">${this._escapeHtml(message)}</p>
                </div>
                <div class="custom-modal-footer">
                    <button class="custom-modal-btn custom-modal-btn-primary" id="modal-ok-btn">${this._escapeHtml(buttonText)}</button>
                </div>
            `;

            overlay.appendChild(modal);
            document.body.appendChild(overlay);

            const okBtn = modal.querySelector('#modal-ok-btn');
            okBtn.focus();

            const close = () => {
                overlay.remove();
                resolve();
            };

            okBtn.addEventListener('click', close);
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) close();
            });
            document.addEventListener('keydown', function handler(e) {
                if (e.key === 'Escape' || e.key === 'Enter') {
                    document.removeEventListener('keydown', handler);
                    close();
                }
            });
        });
    },

    /**
     * Show a confirm modal
     * @param {string} message - The message to display
     * @param {Object} options - Optional configuration
     * @param {string} options.title - Modal title (default: 'Confirm')
     * @param {string} options.type - 'confirm' | 'warning' | 'error' (default: 'confirm')
     * @param {string} options.confirmText - Confirm button text (default: 'Confirm')
     * @param {string} options.cancelText - Cancel button text (default: 'Cancel')
     * @returns {Promise<boolean>}
     */
    confirm(message, options = {}) {
        return new Promise((resolve) => {
            const type = options.type || 'confirm';
            const title = options.title || 'Confirm';
            const confirmText = options.confirmText || 'Confirm';
            const cancelText = options.cancelText || 'Cancel';

            const overlay = this._createOverlay();
            const modal = document.createElement('div');
            modal.className = 'custom-modal';

            const btnClass = type === 'error' ? 'custom-modal-btn-danger' : 'custom-modal-btn-primary';

            modal.innerHTML = `
                <div class="custom-modal-header">
                    <div class="custom-modal-icon ${type}">
                        ${this._getIcon(type)}
                    </div>
                    <h3 class="custom-modal-title">${this._escapeHtml(title)}</h3>
                </div>
                <div class="custom-modal-body">
                    <p class="custom-modal-message">${this._escapeHtml(message)}</p>
                </div>
                <div class="custom-modal-footer">
                    <button class="custom-modal-btn custom-modal-btn-secondary" id="modal-cancel-btn">${this._escapeHtml(cancelText)}</button>
                    <button class="custom-modal-btn ${btnClass}" id="modal-confirm-btn">${this._escapeHtml(confirmText)}</button>
                </div>
            `;

            overlay.appendChild(modal);
            document.body.appendChild(overlay);

            const confirmBtn = modal.querySelector('#modal-confirm-btn');
            const cancelBtn = modal.querySelector('#modal-cancel-btn');
            confirmBtn.focus();

            const close = (result) => {
                overlay.remove();
                resolve(result);
            };

            confirmBtn.addEventListener('click', () => close(true));
            cancelBtn.addEventListener('click', () => close(false));
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) close(false);
            });
            document.addEventListener('keydown', function handler(e) {
                if (e.key === 'Escape') {
                    document.removeEventListener('keydown', handler);
                    close(false);
                } else if (e.key === 'Enter') {
                    document.removeEventListener('keydown', handler);
                    close(true);
                }
            });
        });
    },

    /**
     * Show a prompt modal
     * @param {string} message - The message to display
     * @param {Object} options - Optional configuration
     * @param {string} options.title - Modal title (default: 'Input Required')
     * @param {string} options.defaultValue - Default input value
     * @param {string} options.placeholder - Input placeholder
     * @param {string} options.confirmText - Confirm button text (default: 'OK')
     * @param {string} options.cancelText - Cancel button text (default: 'Cancel')
     * @returns {Promise<string|null>}
     */
    prompt(message, options = {}) {
        return new Promise((resolve) => {
            const title = options.title || 'Input Required';
            const defaultValue = options.defaultValue || '';
            const placeholder = options.placeholder || '';
            const confirmText = options.confirmText || 'OK';
            const cancelText = options.cancelText || 'Cancel';

            const overlay = this._createOverlay();
            const modal = document.createElement('div');
            modal.className = 'custom-modal';
            modal.innerHTML = `
                <div class="custom-modal-header">
                    <div class="custom-modal-icon info">
                        ${this._getIcon('info')}
                    </div>
                    <h3 class="custom-modal-title">${this._escapeHtml(title)}</h3>
                </div>
                <div class="custom-modal-body">
                    <p class="custom-modal-message">${this._escapeHtml(message)}</p>
                    <input type="text" class="custom-modal-input" id="modal-input" value="${this._escapeHtml(defaultValue)}" placeholder="${this._escapeHtml(placeholder)}">
                </div>
                <div class="custom-modal-footer">
                    <button class="custom-modal-btn custom-modal-btn-secondary" id="modal-cancel-btn">${this._escapeHtml(cancelText)}</button>
                    <button class="custom-modal-btn custom-modal-btn-primary" id="modal-confirm-btn">${this._escapeHtml(confirmText)}</button>
                </div>
            `;

            overlay.appendChild(modal);
            document.body.appendChild(overlay);

            const input = modal.querySelector('#modal-input');
            const confirmBtn = modal.querySelector('#modal-confirm-btn');
            const cancelBtn = modal.querySelector('#modal-cancel-btn');
            input.focus();
            input.select();

            const close = (result) => {
                overlay.remove();
                resolve(result);
            };

            confirmBtn.addEventListener('click', () => close(input.value));
            cancelBtn.addEventListener('click', () => close(null));
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) close(null);
            });
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    close(input.value);
                }
            });
            document.addEventListener('keydown', function handler(e) {
                if (e.key === 'Escape') {
                    document.removeEventListener('keydown', handler);
                    close(null);
                }
            });
        });
    },

    /**
     * Show a success message (shorthand)
     */
    success(message, title = 'Success') {
        return this.alert(message, { type: 'success', title });
    },

    /**
     * Show an error message (shorthand)
     */
    error(message, title = 'Error') {
        return this.alert(message, { type: 'error', title });
    },

    /**
     * Show a warning message (shorthand)
     */
    warning(message, title = 'Warning') {
        return this.alert(message, { type: 'warning', title });
    },

    /**
     * Show an info message (shorthand)
     */
    info(message, title = 'Information') {
        return this.alert(message, { type: 'info', title });
    },

    // Private helper methods
    _createOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'custom-modal-overlay';
        return overlay;
    },

    _escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = String(text);
        return div.innerHTML;
    },

    _getDefaultTitle(type) {
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Notice',
            confirm: 'Confirm'
        };
        return titles[type] || 'Notice';
    },

    _getIcon(type) {
        const icons = {
            success: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>`,
            error: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>`,
            warning: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>`,
            info: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>`,
            confirm: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>`
        };
        return icons[type] || icons.info;
    }
};

// Make Modal available globally
window.Modal = Modal;
