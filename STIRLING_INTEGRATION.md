# StirlingPDF Integration Guide

This document provides comprehensive information about the StirlingPDF integration in the PDF Tools Platform.

## 🎯 Overview

StirlingPDF is a locally hostable, feature-rich PDF manipulation tool that provides advanced PDF processing capabilities. Our platform integrates with StirlingPDF to offer:

- Advanced PDF operations beyond basic merge/split
- High-quality document processing
- Scalable PDF manipulation for thousands of users
- Privacy-focused document handling

## 🏗️ Integration Architecture

```
PDF Tools Platform
├── Flask API (api/app.py)
│   ├── PDF Operation Endpoints
│   └── Authentication & Rate Limiting
├── StirlingPDF Client (core/stirling_pdf.py)
│   ├── HTTP Client for StirlingPDF API
│   ├── Error Handling & Retries
│   └── File Format Management
└── StirlingPDF Service
    ├── Deployed on Heroku/Docker
    ├── PDF Processing Engine
    └── RESTful API Interface
```

## 🚀 Setup and Configuration

### Option 1: Use Public StirlingPDF Instance

```bash
# Set environment variables
export STIRLING_PDF_URL="https://stirlingpdf.io"
export STIRLING_PDF_API_KEY=""  # Often not required for public instances
```

### Option 2: Deploy Your Own StirlingPDF Instance

**Deploy to Heroku:**
```bash
# Clone StirlingPDF
git clone https://github.com/Stirling-Tools/Stirling-PDF.git
cd Stirling-PDF

# Create Heroku app
heroku create your-stirlingpdf-app

# Configure for Heroku
echo "web: java -jar build/libs/Stirling-PDF-*.jar" > Procfile

# Deploy
git push heroku main

# Set your instance URL
export STIRLING_PDF_URL="https://your-stirlingpdf-app.herokuapp.com"
```

**Deploy with Docker:**
```bash
# Pull and run StirlingPDF
docker run -d \
  -p 8080:8080 \
  -e SERVER_PORT=8080 \
  frooodle/s-pdf:latest

export STIRLING_PDF_URL="http://localhost:8080"
```

### Option 3: Production Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  stirling-pdf:
    image: frooodle/s-pdf:latest
    ports:
      - "8080:8080"
    environment:
      - SERVER_PORT=8080
      - SPRING_PROFILES_ACTIVE=production
    volumes:
      - ./data:/usr/share/tessdata
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - stirling-pdf
```

## 📋 Available Operations

Our StirlingPDF client supports the following operations:

### Core PDF Operations

#### 1. Merge PDFs
```python
# Merge multiple PDF files
result = stirling_client.merge_pdfs(
    pdf_files=[file1_bytes, file2_bytes], 
    filenames=["doc1.pdf", "doc2.pdf"]
)
```

#### 2. Split PDF
```python
# Split PDF into pages
result = stirling_client.split_pdf(
    pdf_content=pdf_bytes,
    filename="document.pdf",
    pages="1-3,5,7-9"  # Optional page ranges
)
```

#### 3. Compress PDF
```python
# Compress PDF file
result = stirling_client.compress_pdf(
    pdf_content=pdf_bytes,
    filename="document.pdf",
    optimization_level=2  # 1-4, higher = more compression
)
```

#### 4. Convert to PDF
```python
# Convert various formats to PDF
result = stirling_client.convert_to_pdf(
    file_content=file_bytes,
    filename="document.docx",
    file_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
```

### Advanced Operations

#### 5. Extract Pages
```python
# Extract specific pages
result = stirling_client.extract_pages(
    pdf_content=pdf_bytes,
    filename="document.pdf",
    page_numbers=[1, 3, 5, 7]
)
```

#### 6. Rotate PDF
```python
# Rotate pages
result = stirling_client.rotate_pdf(
    pdf_content=pdf_bytes,
    filename="document.pdf",
    angle=90,  # 90, 180, 270
    pages="all"  # or specific pages "1,3,5-7"
)
```

#### 7. Add Watermark
```python
# Add text watermark
result = stirling_client.add_watermark(
    pdf_content=pdf_bytes,
    filename="document.pdf",
    watermark_text="CONFIDENTIAL",
    opacity=0.5,
    font_size=30
)
```

#### 8. Password Protection
```python
# Add password protection
result = stirling_client.add_password_protection(
    pdf_content=pdf_bytes,
    filename="document.pdf",
    password="secure123",
    permissions=["canPrint", "canCopy"]
)

# Remove password protection
result = stirling_client.remove_password(
    pdf_content=pdf_bytes,
    filename="document.pdf",
    password="secure123"
)
```

#### 9. OCR Processing
```python
# Perform OCR on PDF
result = stirling_client.ocr_pdf(
    pdf_content=pdf_bytes,
    filename="scanned.pdf",
    languages=["eng", "fra", "deu"]
)
```

#### 10. Text Extraction
```python
# Extract text from PDF
result = stirling_client.extract_text(
    pdf_content=pdf_bytes,
    filename="document.pdf"
)
```

## 🔧 API Integration

### Flask Endpoint Integration

The StirlingPDF client is integrated into Flask endpoints in `api/app.py`:

```python
@app.route('/api/pdf/merge', methods=['POST'])
@require_rate_limit(max_requests=30, window_seconds=3600)
@log_performance("pdf_merge")
def merge_pdfs():
    """Merge multiple PDF files using StirlingPDF."""
    # Authentication and rate limiting
    # File validation and download
    # StirlingPDF processing
    result = stirling_client.merge_pdfs(pdf_files, filenames)
    # Response handling and logging
```

### Error Handling

The client includes comprehensive error handling:

```python
def _make_request(self, endpoint: str, method: str = 'POST', **kwargs):
    """Make a request to StirlingPDF API with error handling."""
    try:
        response = self.session.request(...)
        
        if response.status_code == 200:
            # Success - return processed content
            return {"success": True, "content": response.content}
        else:
            # API error
            return {"success": False, "error": f"API error: {response.status_code}"}
            
    except requests.RequestException as e:
        # Network/connection error
        return {"success": False, "error": f"Request failed: {str(e)}"}
```

### Health Monitoring

Monitor StirlingPDF service health:

```python
# Check service availability
health = stirling_client.health_check()

# API endpoint
@app.route('/api/stirling/health', methods=['GET'])
def stirling_health():
    result = stirling_client.health_check()
    return create_success_response(result)
```

## 🛡️ Security and Performance

### Security Considerations

1. **File Validation:**
   - All uploaded files are validated before processing
   - MIME type verification
   - File size limits enforced

2. **Network Security:**
   - HTTPS communication with StirlingPDF
   - API key authentication when available
   - Request/response sanitization

3. **Data Privacy:**
   - Files processed in memory when possible
   - Temporary files cleaned up automatically
   - No persistent storage on StirlingPDF instance

### Performance Optimization

1. **Connection Pooling:**
   ```python
   self.session = requests.Session()
   # Reuses connections for better performance
   ```

2. **Timeouts:**
   ```python
   self.timeout = int(os.getenv('STIRLING_PDF_TIMEOUT', '120'))
   # Configurable timeouts prevent hanging requests
   ```

3. **Async Processing:**
   ```python
   # For large files, implement async processing
   @app.route('/api/pdf/process-async', methods=['POST'])
   def process_async():
       # Queue job for background processing
       # Return job ID for status checking
   ```

## 📊 Monitoring and Logging

### Performance Metrics

Track key metrics for StirlingPDF operations:

```python
@log_performance("pdf_operation")
def pdf_operation():
    # Automatically logs:
    # - Operation duration
    # - Success/failure rates
    # - Error types and frequencies
```

### Health Checks

Implement comprehensive health monitoring:

```bash
# Test StirlingPDF connectivity
curl https://your-app.com/api/stirling/health

# Expected response
{
  "success": true,
  "status": "healthy",
  "version": "0.20.0"
}
```

### Error Tracking

Common error scenarios and solutions:

1. **Connection Refused:**
   - StirlingPDF service is down
   - Wrong URL configuration
   - Network connectivity issues

2. **Timeout Errors:**
   - Large file processing
   - Increase `STIRLING_PDF_TIMEOUT`
   - Implement async processing

3. **API Errors:**
   - Invalid file format
   - Corrupted PDF files
   - StirlingPDF service overloaded

## 🔄 Scaling for Production

### Load Balancing

For high-traffic deployments:

```yaml
# Multiple StirlingPDF instances
services:
  stirling-pdf-1:
    image: frooodle/s-pdf:latest
    ports: ["8081:8080"]
    
  stirling-pdf-2:
    image: frooodle/s-pdf:latest
    ports: ["8082:8080"]
    
  nginx-lb:
    image: nginx:alpine
    ports: ["80:80"]
    # Load balance between instances
```

### Horizontal Scaling

```python
class StirlingPDFLoadBalancer:
    def __init__(self):
        self.instances = [
            "https://stirling-1.example.com",
            "https://stirling-2.example.com",
            "https://stirling-3.example.com"
        ]
        self.current = 0
    
    def get_next_instance(self):
        # Round-robin load balancing
        instance = self.instances[self.current]
        self.current = (self.current + 1) % len(self.instances)
        return instance
```

### Caching Strategy

```python
import redis

class PDFProcessingCache:
    def __init__(self):
        self.redis_client = redis.from_url(os.getenv('REDIS_URL'))
    
    def get_cached_result(self, file_hash, operation):
        # Check if result is already cached
        cache_key = f"pdf:{operation}:{file_hash}"
        return self.redis_client.get(cache_key)
    
    def cache_result(self, file_hash, operation, result):
        # Cache result for future requests
        cache_key = f"pdf:{operation}:{file_hash}"
        self.redis_client.setex(cache_key, 3600, result)  # 1 hour TTL
```

## 🧪 Testing

### Unit Tests

```python
import unittest
from core.stirling_pdf import StirlingPDFClient

class TestStirlingPDFClient(unittest.TestCase):
    def setUp(self):
        self.client = StirlingPDFClient()
    
    def test_health_check(self):
        result = self.client.health_check()
        self.assertTrue(result['success'])
    
    def test_merge_pdfs(self):
        # Test with sample PDF files
        pdf1 = b'%PDF-1.4 sample content...'
        pdf2 = b'%PDF-1.4 sample content...'
        
        result = self.client.merge_pdfs([pdf1, pdf2], ["test1.pdf", "test2.pdf"])
        self.assertTrue(result['success'])
```

### Integration Tests

```python
def test_full_pdf_workflow():
    """Test complete PDF processing workflow."""
    # Upload files
    # Process with StirlingPDF
    # Verify output
    # Clean up resources
```

## 📚 Troubleshooting

### Common Issues

**1. StirlingPDF Service Unavailable:**
```python
# The client gracefully handles this
result = stirling_client.merge_pdfs(files, names)
if not result['success']:
    # Fallback to alternative processing
    # Or queue for retry
```

**2. Large File Timeouts:**
```python
# Increase timeout for large files
STIRLING_PDF_TIMEOUT=300  # 5 minutes
```

**3. Memory Issues:**
```python
# Process files in chunks
def process_large_pdf(pdf_content):
    if len(pdf_content) > 10_000_000:  # 10MB
        # Implement chunked processing
        return process_in_chunks(pdf_content)
    else:
        return stirling_client.process_pdf(pdf_content)
```

### Debug Mode

Enable debug logging:

```python
import logging

# Enable debug logging for StirlingPDF client
logging.getLogger('core.stirling_pdf').setLevel(logging.DEBUG)
```

For additional support:
- StirlingPDF GitHub: https://github.com/Stirling-Tools/Stirling-PDF
- StirlingPDF Documentation: https://stirlingtools.com/docs
- Docker Hub: https://hub.docker.com/r/frooodle/s-pdf