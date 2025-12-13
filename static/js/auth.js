/**
 * auth.js - Authentication Page Script
 * Handles login and registration functionality:
 * - Tab switching between login and register forms
 * - Password visibility toggle
 * - Real-time form validation with visual feedback (B-level: JS modifies CSS dynamically)
 * - Input error styling with shake animation
 */

// ============================================================
// Tab Switching Logic
// Allows users to switch between Login and Register tabs
// ============================================================
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', function () {
        const tabName = this.getAttribute('data-tab');

        // Remove active class from all tabs and contents
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        // Add active class to clicked tab and corresponding content
        this.classList.add('active');
        document.getElementById(tabName + '-tab').classList.add('active');
    });
});

// ============================================================
// Password Toggle Functionality
// Shows/hides password text for better user experience
// ============================================================
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    if (input.type === 'password') {
        input.type = 'text';
    } else {
        input.type = 'password';
    }
}

// ============================================================
// B-LEVEL REQUIREMENT: JS dynamically modifies CSS styles
// Real-time validation with visual feedback (error/success styling)
// ============================================================

// Validate single field and show error styling
function validateField(input, validationFn, errorMsg) {
    const existingError = input.parentNode.querySelector('.error-message');
    if (existingError) existingError.remove();

    if (!validationFn(input.value)) {
        input.classList.remove('input-success');
        input.classList.add('input-error', 'shake');
        const error = document.createElement('span');
        error.className = 'error-message';
        error.textContent = errorMsg;
        input.parentNode.appendChild(error);
        setTimeout(() => input.classList.remove('shake'), 500);
        return false;
    } else {
        input.classList.remove('input-error');
        input.classList.add('input-success');
        return true;
    }
}

// Email validation regex
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Add real-time validation on blur
document.getElementById('register-email')?.addEventListener('blur', function () {
    validateField(this, v => emailRegex.test(v), 'Please enter a valid email address');
});

document.getElementById('register-password')?.addEventListener('blur', function () {
    validateField(this, v => v.length >= 6, 'Password must be at least 6 characters');
});

document.getElementById('register-confirm-password')?.addEventListener('blur', function () {
    const password = document.getElementById('register-password').value;
    validateField(this, v => v === password, 'Passwords do not match');
});

document.getElementById('register-username')?.addEventListener('blur', function () {
    validateField(this, v => v.length >= 3, 'Username must be at least 3 characters');
});

// Form validation for registration
document.getElementById('register-form')?.addEventListener('submit', function (e) {
    const username = document.getElementById('register-username');
    const email = document.getElementById('register-email');
    const password = document.getElementById('register-password');
    const confirmPassword = document.getElementById('register-confirm-password');

    let isValid = true;

    if (!validateField(username, v => v.length >= 3, 'Username must be at least 3 characters')) isValid = false;
    if (!validateField(email, v => emailRegex.test(v), 'Please enter a valid email address')) isValid = false;
    if (!validateField(password, v => v.length >= 6, 'Password must be at least 6 characters')) isValid = false;
    if (!validateField(confirmPassword, v => v === password.value, 'Passwords do not match')) isValid = false;

    if (!isValid) {
        e.preventDefault();
        return false;
    }
});

// Login form validation
document.getElementById('login-form')?.addEventListener('submit', function (e) {
    const username = document.getElementById('login-username');
    const password = document.getElementById('login-password');

    let isValid = true;

    if (!validateField(username, v => v.length >= 1, 'Username or email is required')) isValid = false;
    if (!validateField(password, v => v.length >= 1, 'Password is required')) isValid = false;

    if (!isValid) {
        e.preventDefault();
        return false;
    }
});
