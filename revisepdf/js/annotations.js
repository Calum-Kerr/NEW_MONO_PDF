/* Annotations functionality */

// Annotation management
function createAnnotation(type, x, y, width, height) {
    const annotation = {
        id: generateAnnotationId(),
        type: type,
        x: x,
        y: y,
        width: width,
        height: height,
        page: currentPage,
        data: {}
    };
    
    annotations.push(annotation);
    renderAnnotation(annotation);
    return annotation;
}

function renderAnnotation(annotation) {
    const annotationsLayer = document.getElementById('annotations-layer');
    if (!annotationsLayer) return;
    
    const element = document.createElement('div');
    element.className = `annotation ${annotation.type}-annotation`;
    element.setAttribute('data-annotation-id', annotation.id);
    
    element.style.position = 'absolute';
    element.style.left = annotation.x + 'px';
    element.style.top = annotation.y + 'px';
    element.style.width = annotation.width + 'px';
    element.style.height = annotation.height + 'px';
    
    // Add content based on annotation type
    switch (annotation.type) {
        case 'text':
            renderTextAnnotation(element, annotation);
            break;
        case 'signature':
            renderSignatureAnnotation(element, annotation);
            break;
        case 'highlight':
            renderHighlightAnnotation(element, annotation);
            break;
        case 'drawing':
            renderDrawingAnnotation(element, annotation);
            break;
    }
    
    // Make annotation draggable and resizable
    makeAnnotationInteractive(element, annotation);
    
    annotationsLayer.appendChild(element);
}

function renderTextAnnotation(element, annotation) {
    const input = document.createElement('input');
    input.type = 'text';
    input.value = annotation.data.text || '';
    input.style.fontSize = (annotation.data.fontSize || 14) + 'px';
    input.style.color = annotation.data.color || '#000000';
    
    input.addEventListener('input', (e) => {
        annotation.data.text = e.target.value;
    });
    
    element.appendChild(input);
}

function renderSignatureAnnotation(element, annotation) {
    if (annotation.data.imageData) {
        const img = document.createElement('img');
        img.src = annotation.data.imageData;
        element.appendChild(img);
    }
}

function renderHighlightAnnotation(element, annotation) {
    element.style.backgroundColor = annotation.data.color || 'rgba(255, 193, 7, 0.3)';
}

function renderDrawingAnnotation(element, annotation) {
    if (annotation.data.svgData) {
        element.innerHTML = annotation.data.svgData;
    }
}

function makeAnnotationInteractive(element, annotation) {
    let isDragging = false;
    let startX, startY, startLeft, startTop;
    
    element.addEventListener('mousedown', (e) => {
        if (e.target.classList.contains('resize-handle')) return;
        
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        startLeft = parseInt(element.style.left, 10);
        startTop = parseInt(element.style.top, 10);
        
        element.classList.add('selected');
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        
        const deltaX = e.clientX - startX;
        const deltaY = e.clientY - startY;
        
        const newLeft = startLeft + deltaX;
        const newTop = startTop + deltaY;
        
        element.style.left = newLeft + 'px';
        element.style.top = newTop + 'px';
        
        annotation.x = newLeft;
        annotation.y = newTop;
    });
    
    document.addEventListener('mouseup', () => {
        isDragging = false;
    });
    
    // Add resize handles
    addResizeHandles(element, annotation);
}

function addResizeHandles(element, annotation) {
    const handles = ['top-left', 'top-right', 'bottom-left', 'bottom-right'];
    
    handles.forEach(handle => {
        const handleElement = document.createElement('div');
        handleElement.className = `resize-handle ${handle}`;
        element.appendChild(handleElement);
        
        handleElement.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            startResize(e, element, annotation, handle);
        });
    });
}

function startResize(e, element, annotation, handle) {
    let isResizing = true;
    const startX = e.clientX;
    const startY = e.clientY;
    const startWidth = parseInt(element.style.width, 10);
    const startHeight = parseInt(element.style.height, 10);
    const startLeft = parseInt(element.style.left, 10);
    const startTop = parseInt(element.style.top, 10);
    
    const handleMouseMove = (e) => {
        if (!isResizing) return;
        
        const deltaX = e.clientX - startX;
        const deltaY = e.clientY - startY;
        
        let newWidth = startWidth;
        let newHeight = startHeight;
        let newLeft = startLeft;
        let newTop = startTop;
        
        switch (handle) {
            case 'top-left':
                newWidth = startWidth - deltaX;
                newHeight = startHeight - deltaY;
                newLeft = startLeft + deltaX;
                newTop = startTop + deltaY;
                break;
            case 'top-right':
                newWidth = startWidth + deltaX;
                newHeight = startHeight - deltaY;
                newTop = startTop + deltaY;
                break;
            case 'bottom-left':
                newWidth = startWidth - deltaX;
                newHeight = startHeight + deltaY;
                newLeft = startLeft + deltaX;
                break;
            case 'bottom-right':
                newWidth = startWidth + deltaX;
                newHeight = startHeight + deltaY;
                break;
        }
        
        // Minimum size constraints
        newWidth = Math.max(newWidth, 20);
        newHeight = Math.max(newHeight, 20);
        
        element.style.width = newWidth + 'px';
        element.style.height = newHeight + 'px';
        element.style.left = newLeft + 'px';
        element.style.top = newTop + 'px';
        
        annotation.width = newWidth;
        annotation.height = newHeight;
        annotation.x = newLeft;
        annotation.y = newTop;
    };
    
    const handleMouseUp = () => {
        isResizing = false;
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
}

function generateAnnotationId() {
    return 'annotation_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Tool-specific functions
function addTextElement() {
    const textContent = document.getElementById('text-content').value;
    const textSize = document.getElementById('text-size').value;
    const textColor = document.getElementById('text-color').value;
    
    if (!textContent.trim()) {
        showNotification('Please enter some text', 'warning');
        return;
    }
    
    const annotation = createAnnotation('text', 100, 100, 200, 30);
    annotation.data = {
        text: textContent,
        fontSize: parseInt(textSize),
        color: textColor
    };
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('textModal'));
    modal.hide();
    
    // Clear form
    document.getElementById('text-content').value = '';
}

function addSignature() {
    const canvas = document.getElementById('signature-canvas');
    const imageData = canvas.toDataURL();
    
    if (!imageData || imageData === 'data:,') {
        showNotification('Please create a signature first', 'warning');
        return;
    }
    
    const annotation = createAnnotation('signature', 100, 100, 150, 75);
    annotation.data = { imageData: imageData };
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('signatureModal'));
    modal.hide();
    
    // Clear canvas
    clearSignature();
}

function clearSignature() {
    const canvas = document.getElementById('signature-canvas');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}