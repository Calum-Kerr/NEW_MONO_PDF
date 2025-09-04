// Main JavaScript for SnackPDF
class SnackPDF {
    constructor() {
        this.currentTool = null;
        this.selectedFiles = [];
        this.uploadedFiles = [];
        this.currentJobId = null;
        this.apiBaseUrl = '/api';
        
        this.init();
    }

    init() {
        // Initialize event listeners
        this.setupEventListeners();
        this.setupDragAndDrop();
        
        // Check authentication status
        this.checkAuthStatus();
        
        // Load usage stats if authenticated
        this.loadUsageStats();
    }

    setupEventListeners() {
        // File input change
        document.getElementById('file-input').addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files);
        });

        // Process button click
        document.getElementById('process-btn').addEventListener('click', () => {
            this.processFiles();
        });

        // Modal events
        const uploadModal = document.getElementById('uploadModal');
        uploadModal.addEventListener('hidden.bs.modal', () => {
            this.resetUploadModal();
        });
    }

    setupDragAndDrop() {
        const uploadArea = document.getElementById('upload-area');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('dragover');
            });
        });

        uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            this.handleFileSelect(files);
        });

        // Click to upload
        uploadArea.addEventListener('click', () => {
            document.getElementById('file-input').click();
        });
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    async checkAuthStatus() {
        const token = localStorage.getItem('authToken');
        if (!token) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/verify-session`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateUIForLoggedInUser(data.user);
            } else {
                localStorage.removeItem('authToken');
            }
        } catch (error) {
            console.error('Auth check failed:', error);
        }
    }

    updateUIForLoggedInUser(user) {
        const authButtons = document.getElementById('auth-buttons');
        const userMenu = document.getElementById('user-menu');
        
        authButtons.classList.add('d-none');
        userMenu.classList.remove('d-none');
        
        document.getElementById('user-name').textContent = user.first_name || user.email;
    }

    async loadUsageStats() {
        const token = localStorage.getItem('authToken');
        if (!token) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/payments/usage`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const usage = await response.json();
                this.displayUsageStats(usage);
            }
        } catch (error) {
            console.error('Failed to load usage stats:', error);
        }
    }

    displayUsageStats(usage) {
        // Create usage stats display
        const usageHtml = `
            <div class="usage-stats">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6 class="mb-0">Monthly Usage</h6>
                    <span class="badge bg-light text-dark">${usage.subscription_status}</span>
                </div>
                <div class="mb-3">
                    <div class="d-flex justify-content-between text-sm mb-1">
                        <span>Files processed: ${usage.jobs_used}/${usage.jobs_limit}</span>
                        <span>${usage.jobs_remaining} remaining</span>
                    </div>
                    <div class="usage-bar">
                        <div class="usage-fill" style="width: ${(usage.jobs_used / usage.jobs_limit) * 100}%"></div>
                    </div>
                </div>
                <div>
                    <div class="d-flex justify-content-between text-sm mb-1">
                        <span>Storage: ${this.formatFileSize(usage.file_size_used)}/${this.formatFileSize(usage.file_size_limit)}</span>
                        <span>${this.formatFileSize(usage.file_size_remaining)} remaining</span>
                    </div>
                    <div class="usage-bar">
                        <div class="usage-fill" style="width: ${(usage.file_size_used / usage.file_size_limit) * 100}%"></div>
                    </div>
                </div>
            </div>
        `;

        // Add to modal or create a persistent widget
        const container = document.querySelector('.container');
        const usageWidget = document.createElement('div');
        usageWidget.innerHTML = usageHtml;
        usageWidget.className = 'position-fixed top-0 end-0 m-3';
        usageWidget.style.zIndex = '1050';
        usageWidget.style.width = '300px';
        
        container.appendChild(usageWidget);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    selectTool(toolName) {
        this.currentTool = toolName;
        
        // Update modal title
        const titles = {
            'merge': 'Merge PDF Files',
            'split': 'Split PDF File',
            'compress': 'Compress PDF',
            'convert-to-pdf': 'Convert to PDF',
            'pdf-to-image': 'PDF to Image'
        };
        
        document.getElementById('uploadModalTitle').textContent = titles[toolName] || 'Upload Files';
        
        // Show upload modal
        const modal = new bootstrap.Modal(document.getElementById('uploadModal'));
        modal.show();
        
        // Update file input accept based on tool
        this.updateFileInputAccept(toolName);
    }

    updateFileInputAccept(toolName) {
        const fileInput = document.getElementById('file-input');
        const uploadArea = document.querySelector('#upload-area p');
        
        switch (toolName) {
            case 'merge':
            case 'split':
            case 'compress':
            case 'pdf-to-image':
                fileInput.accept = '.pdf';
                uploadArea.textContent = 'Supports PDF files only (Max 10MB for free users)';
                break;
            case 'convert-to-pdf':
                fileInput.accept = '.doc,.docx,.txt,.jpg,.jpeg,.png';
                uploadArea.textContent = 'Supports DOC, DOCX, TXT, JPG, PNG (Max 10MB for free users)';
                break;
            default:
                fileInput.accept = '.pdf,.doc,.docx,.jpg,.jpeg,.png';
                uploadArea.textContent = 'Supports PDF, DOC, DOCX, JPG, PNG (Max 10MB for free users)';
        }
    }

    handleFileSelect(files) {
        this.selectedFiles = Array.from(files);
        this.displaySelectedFiles();
        this.showToolOptions();
        
        // Enable process button if files are selected
        const processBtn = document.getElementById('process-btn');
        processBtn.disabled = this.selectedFiles.length === 0;
    }

    displaySelectedFiles() {
        const container = document.getElementById('files-container');
        const fileList = document.getElementById('file-list');
        
        if (this.selectedFiles.length === 0) {
            fileList.classList.add('d-none');
            return;
        }
        
        fileList.classList.remove('d-none');
        container.innerHTML = '';
        
        this.selectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item d-flex justify-content-between align-items-center';
            fileItem.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="bi bi-file-earmark-pdf text-danger me-2"></i>
                    <div>
                        <div class="fw-bold">${file.name}</div>
                        <small class="text-muted">${this.formatFileSize(file.size)}</small>
                    </div>
                </div>
                <button class="btn btn-sm btn-outline-danger" onclick="app.removeFile(${index})">
                    <i class="bi bi-trash"></i>
                </button>
            `;
            container.appendChild(fileItem);
        });
    }

    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.displaySelectedFiles();
        
        const processBtn = document.getElementById('process-btn');
        processBtn.disabled = this.selectedFiles.length === 0;
    }

    showToolOptions() {
        const optionsContainer = document.getElementById('tool-options');
        optionsContainer.innerHTML = '';
        
        switch (this.currentTool) {
            case 'split':
                this.showSplitOptions(optionsContainer);
                break;
            case 'compress':
                this.showCompressionOptions(optionsContainer);
                break;
            case 'convert-to-pdf':
            case 'pdf-to-image':
                this.showConversionOptions(optionsContainer);
                break;
        }
        
        if (optionsContainer.innerHTML) {
            optionsContainer.classList.remove('d-none');
        }
    }

    showSplitOptions(container) {
        container.innerHTML = `
            <h6>Split Options</h6>
            <div class="mb-3">
                <label class="form-label">Page Ranges (e.g., 1-3, 5, 7-10)</label>
                <input type="text" class="form-control" id="page-ranges" placeholder="1-3, 5, 7-10">
                <small class="text-muted">Separate multiple ranges with commas</small>
            </div>
        `;
    }

    showCompressionOptions(container) {
        container.innerHTML = `
            <h6>Compression Level</h6>
            <div class="compression-levels">
                <div class="compression-option" data-level="low">
                    <h6>Low</h6>
                    <small>Best quality, larger file</small>
                </div>
                <div class="compression-option selected" data-level="medium">
                    <h6>Medium</h6>
                    <small>Balanced quality and size</small>
                </div>
                <div class="compression-option" data-level="high">
                    <h6>High</h6>
                    <small>Smaller file, reduced quality</small>
                </div>
            </div>
        `;

        // Add click handlers
        container.querySelectorAll('.compression-option').forEach(option => {
            option.addEventListener('click', () => {
                container.querySelectorAll('.compression-option').forEach(o => o.classList.remove('selected'));
                option.classList.add('selected');
            });
        });
    }

    showConversionOptions(container) {
        if (this.currentTool === 'pdf-to-image') {
            container.innerHTML = `
                <h6>Output Format</h6>
                <div class="format-grid">
                    <div class="format-option selected" data-format="jpg">
                        <i class="bi bi-image"></i>
                        <div>JPG</div>
                    </div>
                    <div class="format-option" data-format="png">
                        <i class="bi bi-image"></i>
                        <div>PNG</div>
                    </div>
                </div>
            `;

            container.querySelectorAll('.format-option').forEach(option => {
                option.addEventListener('click', () => {
                    container.querySelectorAll('.format-option').forEach(o => o.classList.remove('selected'));
                    option.classList.add('selected');
                });
            });
        }
    }

    async processFiles() {
        if (this.selectedFiles.length === 0) return;

        // Show processing modal
        const uploadModal = bootstrap.Modal.getInstance(document.getElementById('uploadModal'));
        uploadModal.hide();

        const processingModal = new bootstrap.Modal(document.getElementById('processingModal'));
        processingModal.show();

        try {
            // First upload files
            await this.uploadFiles();
            
            // Then process based on tool
            await this.performToolOperation();
            
        } catch (error) {
            this.showError('Processing failed: ' + error.message);
            processingModal.hide();
        }
    }

    async uploadFiles() {
        this.updateProcessingStatus('Uploading files...', 10);

        const uploadPromises = this.selectedFiles.map(async (file) => {
            const formData = new FormData();
            formData.append('file', file);

            const token = localStorage.getItem('authToken');
            const headers = {};
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch(`${this.apiBaseUrl}/pdf/upload`, {
                method: 'POST',
                headers: headers,
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Upload failed');
            }

            return response.json();
        });

        this.uploadedFiles = await Promise.all(uploadPromises);
        this.updateProcessingStatus('Files uploaded successfully', 30);
    }

    async performToolOperation() {
        switch (this.currentTool) {
            case 'merge':
                await this.mergePDFs();
                break;
            case 'split':
                await this.splitPDF();
                break;
            case 'compress':
                await this.compressPDF();
                break;
            case 'convert-to-pdf':
            case 'pdf-to-image':
                await this.convertFile();
                break;
        }
    }

    async mergePDFs() {
        const fileIds = this.uploadedFiles.map(file => file.file_id);
        
        const token = localStorage.getItem('authToken');
        const headers = {'Content-Type': 'application/json'};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${this.apiBaseUrl}/pdf/merge`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                file_ids: fileIds,
                session_id: this.generateSessionId()
            })
        });

        const result = await response.json();
        
        if (response.ok) {
            this.handleProcessingComplete(result);
        } else {
            throw new Error(result.error);
        }
    }

    async splitPDF() {
        const fileId = this.uploadedFiles[0].file_id;
        const pageRanges = document.getElementById('page-ranges').value || '1';
        const pages = pageRanges.split(',').map(range => range.trim());

        const token = localStorage.getItem('authToken');
        const headers = {'Content-Type': 'application/json'};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${this.apiBaseUrl}/pdf/split`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                file_id: fileId,
                pages: pages,
                session_id: this.generateSessionId()
            })
        });

        const result = await response.json();
        
        if (response.ok) {
            this.handleProcessingComplete(result);
        } else {
            throw new Error(result.error);
        }
    }

    async compressPDF() {
        const fileId = this.uploadedFiles[0].file_id;
        const compressionLevel = document.querySelector('.compression-option.selected').dataset.level;

        const token = localStorage.getItem('authToken');
        const headers = {'Content-Type': 'application/json'};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${this.apiBaseUrl}/pdf/compress`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                file_id: fileId,
                compression_level: compressionLevel,
                session_id: this.generateSessionId()
            })
        });

        const result = await response.json();
        
        if (response.ok) {
            this.handleProcessingComplete(result);
        } else {
            throw new Error(result.error);
        }
    }

    async convertFile() {
        const fileId = this.uploadedFiles[0].file_id;
        let targetFormat;

        if (this.currentTool === 'convert-to-pdf') {
            targetFormat = 'pdf';
        } else {
            targetFormat = document.querySelector('.format-option.selected')?.dataset.format || 'jpg';
        }

        const token = localStorage.getItem('authToken');
        const headers = {'Content-Type': 'application/json'};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${this.apiBaseUrl}/pdf/convert`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                file_id: fileId,
                target_format: targetFormat,
                session_id: this.generateSessionId()
            })
        });

        const result = await response.json();
        
        if (response.ok) {
            this.handleProcessingComplete(result);
        } else {
            throw new Error(result.error);
        }
    }

    handleProcessingComplete(result) {
        this.updateProcessingStatus('Processing complete!', 100);
        
        setTimeout(() => {
            const processingModal = bootstrap.Modal.getInstance(document.getElementById('processingModal'));
            processingModal.hide();
            
            if (result.download_url) {
                this.downloadFile(result.download_url);
            } else if (result.download_urls) {
                result.download_urls.forEach(url => this.downloadFile(url));
            }
            
            this.showSuccess('Files processed successfully!');
        }, 1000);
    }

    downloadFile(url) {
        const link = document.createElement('a');
        link.href = url;
        link.download = '';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    updateProcessingStatus(message, progress) {
        document.getElementById('processing-status').textContent = message;
        document.getElementById('progress-bar').style.width = progress + '%';
    }

    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9);
    }

    resetUploadModal() {
        this.selectedFiles = [];
        this.uploadedFiles = [];
        this.currentTool = null;
        
        document.getElementById('file-list').classList.add('d-none');
        document.getElementById('tool-options').classList.add('d-none');
        document.getElementById('files-container').innerHTML = '';
        document.getElementById('process-btn').disabled = true;
        document.getElementById('file-input').value = '';
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showError(message) {
        this.showAlert(message, 'danger');
    }

    showAlert(message, type) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3" style="z-index: 9999;">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            const alert = document.querySelector('.alert');
            if (alert) {
                const alertInstance = new bootstrap.Alert(alert);
                alertInstance.close();
            }
        }, 5000);
    }
}

// Global functions for HTML onclick handlers
function selectTool(toolName) {
    app.selectTool(toolName);
}

function scrollToTools() {
    document.getElementById('tools').scrollIntoView({ behavior: 'smooth' });
}

// Initialize app when DOM is loaded
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new SnackPDF();
});

// Export for global access
window.SnackPDF = SnackPDF;