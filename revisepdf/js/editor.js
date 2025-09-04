/* RevisePDF Editor JavaScript */

// Global variables
let currentPDF = null;
let currentPage = 1;
let totalPages = 0;
let scale = 1.0;
let currentTool = 'select';
let annotations = [];

// Initialize editor
document.addEventListener('DOMContentLoaded', function() {
    console.log('RevisePDF Editor initialized');
    initializeEditor();
});

function initializeEditor() {
    // Initialize PDF.js worker
    if (typeof pdfjsLib !== 'undefined') {
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    }
    
    // Initialize event listeners
    initializeEventListeners();
}

function initializeEventListeners() {
    // File input change
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
    
    // Tool selection
    document.querySelectorAll('.tool-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const tool = this.getAttribute('data-tool');
            if (tool) {
                selectTool(tool);
            }
        });
    });
}

// File handling
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
        loadPDF(file);
    } else {
        showNotification('Please select a valid PDF file', 'error');
    }
}

function handleFileDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    
    const files = event.dataTransfer.files;
    if (files.length > 0 && files[0].type === 'application/pdf') {
        loadPDF(files[0]);
    } else {
        showNotification('Please drop a valid PDF file', 'error');
    }
}

function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.classList.remove('dragover');
}

// PDF loading
function loadPDF(file) {
    showLoading(true);
    hideWelcomeScreen();
    
    const fileReader = new FileReader();
    fileReader.onload = function(e) {
        const typedArray = new Uint8Array(e.target.result);
        
        if (typeof pdfjsLib !== 'undefined') {
            pdfjsLib.getDocument(typedArray).promise.then(pdf => {
                currentPDF = pdf;
                totalPages = pdf.numPages;
                currentPage = 1;
                
                renderPage(currentPage);
                generatePageThumbnails();
                showLoading(false);
            }).catch(error => {
                console.error('Error loading PDF:', error);
                showNotification('Error loading PDF file', 'error');
                showLoading(false);
                showWelcomeScreen();
            });
        } else {
            showNotification('PDF.js not loaded', 'error');
            showLoading(false);
            showWelcomeScreen();
        }
    };
    
    fileReader.readAsArrayBuffer(file);
}

// Tool selection
function selectTool(tool) {
    currentTool = tool;
    
    // Update UI
    document.querySelectorAll('.tool-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const activeBtn = document.querySelector(`.tool-btn[data-tool="${tool}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    // Change cursor based on tool
    const canvas = document.getElementById('pdf-canvas');
    if (canvas) {
        switch (tool) {
            case 'select':
                canvas.style.cursor = 'default';
                break;
            case 'text':
                canvas.style.cursor = 'text';
                break;
            case 'signature':
                canvas.style.cursor = 'crosshair';
                break;
            case 'highlight':
                canvas.style.cursor = 'crosshair';
                break;
            case 'draw':
                canvas.style.cursor = 'crosshair';
                break;
            default:
                canvas.style.cursor = 'default';
        }
    }
}

// UI functions
function showWelcomeScreen() {
    document.getElementById('welcome-screen').classList.remove('d-none');
    document.getElementById('editor-interface').classList.add('d-none');
}

function hideWelcomeScreen() {
    document.getElementById('welcome-screen').classList.add('d-none');
    document.getElementById('editor-interface').classList.remove('d-none');
}

function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        if (show) {
            overlay.classList.remove('d-none');
        } else {
            overlay.classList.add('d-none');
        }
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// Placeholder functions for missing functionality
function renderPage(pageNum) {
    console.log('Rendering page:', pageNum);
}

function generatePageThumbnails() {
    console.log('Generating page thumbnails');
}

function openFile() {
    document.getElementById('file-input').click();
}

function savePDF() {
    showNotification('PDF save functionality coming soon', 'info');
}

function newDocument() {
    showNotification('New document functionality coming soon', 'info');
}

function zoomIn() {
    scale = Math.min(scale * 1.2, 3.0);
    updateZoomLevel();
}

function zoomOut() {
    scale = Math.max(scale / 1.2, 0.3);
    updateZoomLevel();
}

function updateZoomLevel() {
    const zoomBtn = document.getElementById('zoom-level');
    if (zoomBtn) {
        zoomBtn.textContent = Math.round(scale * 100) + '%';
    }
}

// Auth functions (placeholders)
function showLoginModal() {
    const modal = new bootstrap.Modal(document.getElementById('loginModal'));
    modal.show();
}

function showRegisterModal() {
    const modal = new bootstrap.Modal(document.getElementById('registerModal'));
    modal.show();
}

function logout() {
    showNotification('Logout functionality coming soon', 'info');
}