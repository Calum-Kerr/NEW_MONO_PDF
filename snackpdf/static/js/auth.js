// Authentication module for SnackPDF
class AuthManager {
    constructor() {
        this.apiBaseUrl = '/api';
        this.token = localStorage.getItem('authToken');
        this.user = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAuthStatus();
    }

    setupEventListeners() {
        // Logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        }
    }

    async checkAuthStatus() {
        if (!this.token) return false;

        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/verify-session`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.user = data.user;
                this.updateUIForLoggedInUser();
                return true;
            } else {
                this.clearAuthData();
                return false;
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            this.clearAuthData();
            return false;
        }
    }

    async login(email, password) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                this.token = data.session_token;
                this.user = data.user;
                
                localStorage.setItem('authToken', this.token);
                this.updateUIForLoggedInUser();
                
                return { success: true, user: this.user };
            } else {
                return { success: false, error: data.error };
            }
        } catch (error) {
            return { success: false, error: 'Login failed. Please try again.' };
        }
    }

    async register(userData) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });

            const data = await response.json();

            if (response.ok) {
                return { success: true, user: data.user };
            } else {
                return { success: false, error: data.error };
            }
        } catch (error) {
            return { success: false, error: 'Registration failed. Please try again.' };
        }
    }

    async logout() {
        try {
            if (this.token) {
                await fetch(`${this.apiBaseUrl}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    }
                });
            }
        } catch (error) {
            console.error('Logout request failed:', error);
        }

        this.clearAuthData();
        this.updateUIForLoggedOutUser();
        
        // Redirect to home page
        window.location.href = '/';
    }

    clearAuthData() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('authToken');
    }

    updateUIForLoggedInUser() {
        const authButtons = document.getElementById('auth-buttons');
        const userMenu = document.getElementById('user-menu');
        
        if (authButtons) authButtons.classList.add('d-none');
        if (userMenu) {
            userMenu.classList.remove('d-none');
            const userNameElement = document.getElementById('user-name');
            if (userNameElement && this.user) {
                userNameElement.textContent = this.user.first_name || this.user.email;
            }
        }
    }

    updateUIForLoggedOutUser() {
        const authButtons = document.getElementById('auth-buttons');
        const userMenu = document.getElementById('user-menu');
        
        if (authButtons) authButtons.classList.remove('d-none');
        if (userMenu) userMenu.classList.add('d-none');
    }

    isAuthenticated() {
        return this.token && this.user;
    }

    getUser() {
        return this.user;
    }

    getToken() {
        return this.token;
    }

    async refreshToken() {
        if (!this.token) return false;

        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/refresh-token`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.token = data.session_token;
                localStorage.setItem('authToken', this.token);
                return true;
            } else {
                this.clearAuthData();
                return false;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
            this.clearAuthData();
            return false;
        }
    }

    // Helper method for authenticated API requests
    async authenticatedFetch(url, options = {}) {
        if (!this.token) {
            throw new Error('Not authenticated');
        }

        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`,
            ...options.headers
        };

        const response = await fetch(url, {
            ...options,
            headers
        });

        // Handle token expiration
        if (response.status === 401) {
            const refreshed = await this.refreshToken();
            if (refreshed) {
                // Retry with new token
                headers['Authorization'] = `Bearer ${this.token}`;
                return fetch(url, {
                    ...options,
                    headers
                });
            } else {
                throw new Error('Authentication expired');
            }
        }

        return response;
    }
}

// Login form handler
class LoginForm {
    constructor() {
        this.form = document.getElementById('login-form');
        this.authManager = new AuthManager();
        
        if (this.form) {
            this.init();
        }
    }

    init() {
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });
    }

    async handleSubmit() {
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const submitBtn = this.form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Signing in...';

        try {
            const result = await this.authManager.login(email, password);

            if (result.success) {
                // Redirect to dashboard or previous page
                const returnUrl = new URLSearchParams(window.location.search).get('return') || '/dashboard';
                window.location.href = returnUrl;
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            this.showError('Login failed. Please try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    showError(message) {
        const errorDiv = document.getElementById('login-error');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.classList.remove('d-none');
        }
    }
}

// Registration form handler
class RegisterForm {
    constructor() {
        this.form = document.getElementById('register-form');
        this.authManager = new AuthManager();
        
        if (this.form) {
            this.init();
        }
    }

    init() {
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });

        // Password confirmation validation
        const password = document.getElementById('password');
        const confirmPassword = document.getElementById('confirm-password');
        
        if (password && confirmPassword) {
            confirmPassword.addEventListener('input', () => {
                this.validatePasswordMatch();
            });
        }
    }

    validatePasswordMatch() {
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        const confirmPasswordField = document.getElementById('confirm-password');

        if (password !== confirmPassword) {
            confirmPasswordField.setCustomValidity('Passwords do not match');
        } else {
            confirmPasswordField.setCustomValidity('');
        }
    }

    async handleSubmit() {
        const formData = new FormData(this.form);
        const userData = {
            email: formData.get('email'),
            password: formData.get('password'),
            first_name: formData.get('first_name'),
            last_name: formData.get('last_name')
        };

        const submitBtn = this.form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creating account...';

        try {
            const result = await this.authManager.register(userData);

            if (result.success) {
                this.showSuccess('Account created successfully! Please log in.');
                // Redirect to login page after delay
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            this.showError('Registration failed. Please try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    showError(message) {
        const errorDiv = document.getElementById('register-error');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.classList.remove('d-none');
        }
    }

    showSuccess(message) {
        const successDiv = document.getElementById('register-success');
        if (successDiv) {
            successDiv.textContent = message;
            successDiv.classList.remove('d-none');
        }
    }
}

// Profile management
class ProfileManager {
    constructor() {
        this.authManager = new AuthManager();
        this.form = document.getElementById('profile-form');
        
        if (this.form) {
            this.init();
        }
    }

    init() {
        this.loadUserProfile();
        
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.updateProfile();
        });
    }

    async loadUserProfile() {
        try {
            const response = await this.authManager.authenticatedFetch('/api/users/profile');
            
            if (response.ok) {
                const data = await response.json();
                this.populateForm(data.user);
            }
        } catch (error) {
            console.error('Failed to load profile:', error);
        }
    }

    populateForm(user) {
        document.getElementById('first_name').value = user.first_name || '';
        document.getElementById('last_name').value = user.last_name || '';
        document.getElementById('email').value = user.email || '';
    }

    async updateProfile() {
        const formData = new FormData(this.form);
        const updateData = {
            first_name: formData.get('first_name'),
            last_name: formData.get('last_name')
        };

        const submitBtn = this.form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Updating...';

        try {
            const response = await this.authManager.authenticatedFetch('/api/users/profile', {
                method: 'PUT',
                body: JSON.stringify(updateData)
            });

            const data = await response.json();

            if (response.ok) {
                this.showSuccess('Profile updated successfully!');
                // Update the auth manager's user data
                this.authManager.user = data.user;
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('Failed to update profile. Please try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    showError(message) {
        this.showAlert(message, 'danger');
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showAlert(message, type) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        const alertContainer = document.getElementById('profile-alerts');
        if (alertContainer) {
            alertContainer.innerHTML = alertHtml;
        }
    }
}

// Initialize auth components when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize global auth manager
    window.authManager = new AuthManager();
    
    // Initialize form handlers based on current page
    new LoginForm();
    new RegisterForm();
    new ProfileManager();
});

// Export for global access
window.AuthManager = AuthManager;