/**
 * SnackPDF Frontend JavaScript
 * Handles file uploads, authentication, and PDF processing
 */

// Configuration
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000' 
    : 'https://api.snackpdf.com';

// Global state
let currentTool = null;
let selectedFiles = [];
let authToken = localStorage.getItem('auth_token');
let currentUser = null;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    checkAuthStatus();
});

// Initialize application
function initializeApp() {
    console.log('SnackPDF app initialized');
    
    // Check if user is logged in
    if (authToken) {
        updateAuthUI(true);
        loadUserProfile();
    }
}

// Setup event listeners
function setupEventListeners() {
    // File input change
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
    
    // Drag and drop
    const uploadArea = document.getElementById('upload-area');
    if (uploadArea) {
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleFileDrop);
        uploadArea.addEventListener('click', () => fileInput.click());
    }
    
    // Form submissions
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
}

// Authentication functions
async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        showLoadingButton(e.target.querySelector('button[type="submit"]'), true);
        
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            authToken = data.data.session.access_token;
            localStorage.setItem('auth_token', authToken);
            currentUser = data.data.user;
            
            updateAuthUI(true);
            hideModal('loginModal');
            showNotification('Login successful!', 'success');
        } else {
            showNotification(data.message || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Login failed. Please try again.', 'error');
    } finally {
        showLoadingButton(e.target.querySelector('button[type="submit"]'), false);
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const fullName = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    
    if (password.length < 8) {
        showNotification('Password must be at least 8 characters long', 'error');
        return;
    }
    
    try {
        showLoadingButton(e.target.querySelector('button[type="submit"]'), true);
        
        const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                email, 
                password, 
                full_name: fullName 
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            authToken = data.data.session.access_token;
            localStorage.setItem('auth_token', authToken);
            currentUser = data.data.user;
            
            updateAuthUI(true);
            hideModal('registerModal');
            showNotification('Account created successfully!', 'success');
        } else {
            showNotification(data.message || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showNotification('Registration failed. Please try again.', 'error');
    } finally {
        showLoadingButton(e.target.querySelector('button[type="submit"]'), false);
    }
}

async function logout() {
    try {
        if (authToken) {
            await fetch(`${API_BASE_URL}/api/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
        }
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        authToken = null;
        currentUser = null;
        localStorage.removeItem('auth_token');
        updateAuthUI(false);
        showNotification('Logged out successfully', 'success');
    }
}

async function loadUserProfile() {
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/profile`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentUser = data.data;
            updateUserDisplay();
        } else {
            // Token might be expired
            logout();
        }
    } catch (error) {
        console.error('Profile error:', error);
    }
}

function updateAuthUI(isLoggedIn) {
    const authButtons = document.getElementById('auth-buttons');
    const userMenu = document.getElementById('user-menu');
    
    if (isLoggedIn) {
        authButtons.classList.add('d-none');
        userMenu.classList.remove('d-none');
    } else {
        authButtons.classList.remove('d-none');
        userMenu.classList.add('d-none');
    }
}

function updateUserDisplay() {
    if (currentUser) {
        const userName = document.getElementById('user-name');
        if (userName) {
            userName.textContent = currentUser.full_name || currentUser.email;
        }
    }
}

function checkAuthStatus() {
    if (authToken) {
        loadUserProfile();
    }
}

// File handling functions
function selectTool(toolName) {
    currentTool = toolName;
    
    // Update modal content
    updateModalForTool(toolName);
    
    // Show upload modal
    showModal('uploadModal');
}

function updateModalForTool(toolName) {
    const toolNames = {
        'merge': 'Merge PDF',
        'split': 'Split PDF',
        'compress': 'Compress PDF',
        'convert': 'Convert to PDF',
        'extract': 'Extract Pages',
        'rotate': 'Rotate PDF'
    };
    
    const modalTitle = document.getElementById('modal-tool-name');
    if (modalTitle) {
        modalTitle.textContent = toolNames[toolName] || 'PDF Tool';
    }
    
    // Reset file input and lists
    resetFileUpload();
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    addFilesToList(files);
}

function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
}

function handleFileDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    
    const files = Array.from(e.dataTransfer.files);
    addFilesToList(files);
}

function addFilesToList(files) {
    // Validate files
    const validFiles = files.filter(file => {
        const isValidSize = file.size <= 50 * 1024 * 1024; // 50MB
        const isValidType = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
        
        if (!isValidSize) {
            showNotification(`File ${file.name} is too large. Maximum size is 50MB.`, 'error');
        }
        
        if (!isValidType && currentTool !== 'convert') {
            showNotification(`File ${file.name} is not a PDF file.`, 'error');
        }
        
        return isValidSize && (isValidType || currentTool === 'convert');
    });
    
    if (validFiles.length === 0) return;
    
    selectedFiles = [...selectedFiles, ...validFiles];
    updateFileList();
}

function updateFileList() {
    const fileList = document.getElementById('file-list');
    const filesContainer = document.getElementById('files-container');
    
    if (selectedFiles.length === 0) {
        fileList.classList.add('d-none');
        return;
    }
    
    fileList.classList.remove('d-none');
    
    filesContainer.innerHTML = selectedFiles.map((file, index) => `
        <div class="file-item d-flex align-items-center justify-content-between">
            <div class="file-info">
                <strong>${file.name}</strong>
                <small class="text-muted d-block">${formatFileSize(file.size)}</small>
            </div>
            <button class="btn btn-sm btn-outline-danger" onclick="removeFile(${index})">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    `).join('');
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFileList();
}

function resetFileUpload() {
    selectedFiles = [];
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.value = '';
    }
    updateFileList();
    
    // Hide processing state
    const processing = document.getElementById('processing');
    if (processing) {
        processing.classList.add('d-none');
    }
}

async function processFiles() {
    if (selectedFiles.length === 0) {
        showNotification('Please select files first', 'error');
        return;
    }
    
    // Show processing state
    const processing = document.getElementById('processing');
    processing.classList.remove('d-none');
    
    try {
        // Upload files first
        const uploadedFiles = [];
        
        for (const file of selectedFiles) {
            const uploadResult = await uploadFile(file);
            if (uploadResult.success) {
                uploadedFiles.push(uploadResult.data);
            } else {
                throw new Error(`Failed to upload ${file.name}`);
            }
        }
        
        // Process files based on tool
        let result;
        switch (currentTool) {
            case 'merge':
                result = await mergePDFs(uploadedFiles);
                break;
            case 'split':
                result = await splitPDF(uploadedFiles[0]);
                break;
            case 'compress':
                result = await compressPDF(uploadedFiles[0]);
                break;
            default:
                throw new Error('Tool not implemented yet');
        }
        
        if (result.success) {
            showNotification('Files processed successfully!', 'success');
            // TODO: Handle download or show results
        } else {
            throw new Error(result.message || 'Processing failed');
        }
        
    } catch (error) {
        console.error('Processing error:', error);
        showNotification(error.message || 'Processing failed', 'error');
    } finally {
        processing.classList.add('d-none');
    }
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const headers = {};
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const response = await fetch(`${API_BASE_URL}/api/files/upload`, {
        method: 'POST',
        headers: headers,
        body: formData
    });
    
    return await response.json();
}

// PDF processing functions
async function mergePDFs(files) {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const response = await fetch(`${API_BASE_URL}/api/pdf/merge`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            file_urls: files.map(f => f.upload_url)
        })
    });
    
    return await response.json();
}

async function splitPDF(file) {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const response = await fetch(`${API_BASE_URL}/api/pdf/split`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            file_url: file.upload_url
        })
    });
    
    return await response.json();
}

async function compressPDF(file) {
    // TODO: Implement compress endpoint
    return { success: false, message: 'Compress tool coming soon!' };
}

// UI utility functions
function showModal(modalId) {
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();
}

function hideModal(modalId) {
    const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
    if (modal) {
        modal.hide();
    }
}

function showLoginModal() {
    hideModal('registerModal');
    showModal('loginModal');
}

function showRegisterModal() {
    hideModal('loginModal');
    showModal('registerModal');
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function showLoadingButton(button, loading) {
    if (loading) {
        button.disabled = true;
        button.innerHTML = '<span class="loading-dots"></span> Loading...';
    } else {
        button.disabled = false;
        button.innerHTML = button.getAttribute('data-original-text') || 'Submit';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Export functions for global access
window.selectTool = selectTool;
window.processFiles = processFiles;
window.removeFile = removeFile;
window.showLoginModal = showLoginModal;
window.showRegisterModal = showRegisterModal;
window.logout = logout;