/* PDF Viewer functionality */

// PDF rendering functions
function renderPage(pageNum) {
    if (!currentPDF) return;
    
    currentPDF.getPage(pageNum).then(page => {
        const canvas = document.getElementById('pdf-canvas');
        const context = canvas.getContext('2d');
        
        const viewport = page.getViewport({ scale: scale });
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        
        // Update annotations layer size
        const annotationsLayer = document.getElementById('annotations-layer');
        if (annotationsLayer) {
            annotationsLayer.style.width = viewport.width + 'px';
            annotationsLayer.style.height = viewport.height + 'px';
        }
        
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        
        page.render(renderContext);
        updatePageInfo();
    }).catch(error => {
        console.error('Error rendering page:', error);
        showNotification('Error rendering page', 'error');
    });
}

function generatePageThumbnails() {
    if (!currentPDF) return;
    
    const pagesList = document.getElementById('pages-list');
    pagesList.innerHTML = '';
    
    for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
        createPageThumbnail(pageNum);
    }
}

function createPageThumbnail(pageNum) {
    currentPDF.getPage(pageNum).then(page => {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        const viewport = page.getViewport({ scale: 0.2 });
        
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        canvas.className = 'page-thumbnail';
        canvas.setAttribute('data-page', pageNum);
        
        if (pageNum === currentPage) {
            canvas.classList.add('active');
        }
        
        canvas.addEventListener('click', () => {
            currentPage = pageNum;
            renderPage(currentPage);
            updateActiveThumbnail();
        });
        
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        
        page.render(renderContext);
        
        const pagesList = document.getElementById('pages-list');
        pagesList.appendChild(canvas);
    });
}

function updateActiveThumbnail() {
    document.querySelectorAll('.page-thumbnail').forEach(thumb => {
        thumb.classList.remove('active');
    });
    
    const activeThumb = document.querySelector(`.page-thumbnail[data-page="${currentPage}"]`);
    if (activeThumb) {
        activeThumb.classList.add('active');
    }
}

function updatePageInfo() {
    // Update any page info displays
    const pageInfo = document.querySelector('.page-info');
    if (pageInfo) {
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    }
}

// Navigation functions
function nextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        renderPage(currentPage);
        updateActiveThumbnail();
    }
}

function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        renderPage(currentPage);
        updateActiveThumbnail();
    }
}

function goToPage(pageNum) {
    if (pageNum >= 1 && pageNum <= totalPages) {
        currentPage = pageNum;
        renderPage(currentPage);
        updateActiveThumbnail();
    }
}