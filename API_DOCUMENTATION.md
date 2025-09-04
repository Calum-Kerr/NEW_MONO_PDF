# PDF Tools Platform API Documentation - Phase 3 Features

## Overview

This document covers the new API endpoints and features implemented in Phase 3 of the PDF Tools Platform. These include advanced OCR, batch processing, API key management, analytics, and white-label solutions.

## Authentication

All endpoints support two authentication methods:

### Session Token (Web Users)
```
Authorization: Bearer <jwt_token>
```

### API Key (Third-party Integrations)
```
X-API-Key: sk_<api_key>
```

## Enhanced PDF Processing Endpoints

### Advanced OCR

**POST** `/api/pdf/ocr-advanced`

Extract text from scanned documents with advanced OCR capabilities.

**Parameters:**
- `files` (file): PDF file to process
- `languages` (array): Language codes (e.g., ['eng', 'fra', 'deu'])
- `ocr_type` (string): 'auto', 'force-ocr', or 'skip-text'
- `dpi` (integer): DPI for OCR processing (default: 300)
- `remove_blanks` (boolean): Remove blank pages (default: true)

**Supported Languages:**
- `eng` - English
- `fra` - French  
- `deu` - German
- `spa` - Spanish
- `ita` - Italian
- `por` - Portuguese
- `rus` - Russian
- `chi_sim` - Chinese Simplified
- `chi_tra` - Chinese Traditional
- `jpn` - Japanese
- `kor` - Korean
- `ara` - Arabic
- `hin` - Hindi
- `tha` - Thai
- `vie` - Vietnamese
- `nld` - Dutch
- `swe` - Swedish
- `dan` - Danish
- `nor` - Norwegian

**Response:** PDF file with searchable text

**Example:**
```bash
curl -X POST "https://api.domain.com/api/pdf/ocr-advanced" \
  -H "Authorization: Bearer <token>" \
  -F "files=@document.pdf" \
  -F "languages=eng" \
  -F "languages=fra" \
  -F "ocr_type=auto" \
  -F "dpi=300"
```

### Advanced Text Extraction

**POST** `/api/pdf/extract-text-advanced`

Extract text content in multiple formats.

**Parameters:**
- `files` (file): PDF file to process
- `format` (string): Output format ('txt', 'json', 'xml')
- `include_annotations` (boolean): Include annotations in output

**Response:** Text content in specified format

**Example:**
```bash
curl -X POST "https://api.domain.com/api/pdf/extract-text-advanced" \
  -H "X-API-Key: sk_your_api_key" \
  -F "files=@document.pdf" \
  -F "format=json" \
  -F "include_annotations=true"
```

### Advanced Compression

**POST** `/api/pdf/compress-advanced`

Compress PDFs with advanced algorithms and presets.

**Parameters:**
- `files` (file): PDF file to compress
- `preset` (string): Compression preset
  - `web` - Optimized for web viewing (60% quality)
  - `print` - Optimized for printing (85% quality)
  - `archive` - Maximum compression for archival (40% quality)
  - `balanced` - Balanced quality and size (75% quality)
  - `maximum` - Maximum compression (30% quality)

**Response:** Compressed PDF file

**Example:**
```bash
curl -X POST "https://api.domain.com/api/pdf/compress-advanced" \
  -H "Authorization: Bearer <token>" \
  -F "files=@document.pdf" \
  -F "preset=web"
```

## Batch Processing

### Process Multiple Files

**POST** `/api/pdf/batch-process`

Process multiple files with the same operation.

**Parameters:**
- `files` (array): Multiple PDF files
- `operation` (string): Operation type ('compress', 'ocr', 'extract_text', 'rotate')
- Additional parameters based on operation type

**Response:** JSON with results for each file

**Example:**
```bash
curl -X POST "https://api.domain.com/api/pdf/batch-process" \
  -H "X-API-Key: sk_your_api_key" \
  -F "files=@file1.pdf" \
  -F "files=@file2.pdf" \
  -F "files=@file3.pdf" \
  -F "operation=compress" \
  -F "preset=balanced"
```

**Response Format:**
```json
{
  "success": true,
  "message": "Batch processing completed",
  "data": {
    "results": [
      {
        "filename": "file1.pdf",
        "success": true,
        "result": { "content": "...", "filename": "compressed_file1.pdf" }
      },
      {
        "filename": "file2.pdf", 
        "success": false,
        "error": "Processing failed"
      }
    ],
    "summary": {
      "total": 3,
      "successful": 2,
      "failed": 1,
      "success_rate": 66.67
    }
  }
}
```

## API Key Management

### Create API Key

**POST** `/api/keys/create`

Create a new API key for third-party integrations.

**Parameters:**
```json
{
  "name": "Integration Key",
  "permissions": ["pdf:merge", "pdf:split", "pdf:compress"],
  "rate_limit": 1000,
  "expires_days": 365
}
```

**Response:**
```json
{
  "success": true,
  "message": "API key created successfully",
  "data": {
    "api_key": "sk_abc123...",
    "key_id": "key_xyz789",
    "permissions": ["pdf:merge", "pdf:split", "pdf:compress"],
    "rate_limit": 1000,
    "expires_at": "2025-01-01T00:00:00Z"
  }
}
```

### List API Keys

**GET** `/api/keys/list`

List all API keys for the authenticated user.

**Response:**
```json
{
  "success": true,
  "data": {
    "api_keys": [
      {
        "key_id": "key_xyz789",
        "name": "Integration Key",
        "permissions": ["pdf:merge", "pdf:split"],
        "rate_limit": 1000,
        "created_at": "2024-01-01T00:00:00Z",
        "last_used": "2024-01-15T10:30:00Z",
        "is_active": true,
        "usage_count": 150
      }
    ]
  }
}
```

### Revoke API Key

**POST** `/api/keys/{key_id}/revoke`

Revoke (deactivate) an API key.

**Response:**
```json
{
  "success": true,
  "message": "API key revoked"
}
```

## Analytics Endpoints

### Usage Analytics

**GET** `/api/analytics/usage`

Get usage statistics and analytics.

**Parameters:**
- `days` (integer): Number of days to include (default: 30)
- `global` (boolean): Get platform-wide stats (admin only)

**Response:**
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2024-01-31T23:59:59Z"
    },
    "statistics": {
      "total_events": 1250,
      "successful_events": 1188,
      "success_rate": 95.04,
      "events_by_type": {
        "pdf_merge": 450,
        "pdf_split": 320,
        "pdf_compress": 280,
        "pdf_ocr": 200
      },
      "events_by_day": {
        "2024-01-01": 45,
        "2024-01-02": 52,
        "...": "..."
      },
      "most_popular_operation": "pdf_merge"
    }
  }
}
```

### Performance Analytics

**GET** `/api/analytics/performance`

Get performance metrics and processing times.

**Parameters:**
- `days` (integer): Number of days to include (default: 7)

**Response:**
```json
{
  "success": true,
  "data": {
    "metrics": {
      "average_processing_time": 2.45,
      "median_processing_time": 1.87,
      "slowest_operation": {
        "type": "pdf_ocr",
        "time": 15.23,
        "timestamp": "2024-01-15T14:30:00Z"
      },
      "fastest_operation": {
        "type": "pdf_merge",
        "time": 0.34,
        "timestamp": "2024-01-15T09:15:00Z"
      }
    }
  }
}
```

## White-label Endpoints

### Get Tenant Configuration

**GET** `/api/whitelabel/config/{tenant_id}`

Get white-label configuration for a tenant.

**Response:**
```json
{
  "success": true,
  "data": {
    "tenant_id": "acme_corp",
    "branding": {
      "company_name": "Acme Corporation",
      "logo_url": "https://cdn.example.com/logo.png",
      "primary_color": "#ff6b35",
      "secondary_color": "#2c3e50",
      "accent_color": "#27ae60",
      "font_family": "Roboto, sans-serif",
      "custom_domain": "pdf.acme.com"
    },
    "features": {
      "enabled_features": ["pdf_merge", "pdf_split", "api_access"],
      "api_access": true,
      "analytics_access": true,
      "custom_limits": {
        "monthly_operations": 50000,
        "file_size_mb": 100,
        "api_requests_per_hour": 10000
      }
    }
  }
}
```

### Get Custom CSS

**GET** `/api/whitelabel/css/{tenant_id}`

Get custom CSS for tenant branding.

**Response:** CSS file with custom styling

**Example:**
```css
/* White-label CSS for Acme Corporation */
:root {
    --primary-color: #ff6b35;
    --secondary-color: #2c3e50;
    --accent-color: #27ae60;
    --font-family: Roboto, sans-serif;
}

body {
    font-family: var(--font-family);
}

.btn-primary {
    background-color: var(--primary-color);
    border-color: var(--primary-color);
}
```

## Permissions

API keys can be granted specific permissions:

### PDF Operations
- `pdf:merge` - Merge multiple PDFs
- `pdf:split` - Split PDFs into pages
- `pdf:compress` - Compress PDF files
- `pdf:convert` - Convert files to PDF
- `pdf:ocr` - Perform OCR on PDFs
- `pdf:extract_text` - Extract text from PDFs
- `pdf:rotate` - Rotate PDF pages
- `pdf:watermark` - Add watermarks to PDFs
- `pdf:batch_process` - Process multiple files

### Analytics & Management
- `analytics:read` - Read analytics data
- `user:read` - Read user information

### Admin Permissions
- `admin` - Full access to all features

## Rate Limits

### Default Limits by Plan

**Free Plan:**
- 5 operations per month
- 10MB file size limit
- Basic features only

**Pro Plan:**
- Unlimited operations
- 50MB file size limit
- All features included
- 1000 API requests per hour

**Enterprise Plan:**
- Unlimited operations
- 100MB file size limit
- All features + white-label
- 10,000 API requests per hour
- Custom rate limits available

### Rate Limit Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Error Handling

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `413` - File Too Large
- `422` - Validation Error
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error
- `503` - Service Unavailable

### Error Response Format

```json
{
  "success": false,
  "error": "Error message",
  "details": "Additional error details (optional)"
}
```

## Examples

### Complete Python Integration

```python
import requests

class PDFToolsAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.domain.com/api"
        self.headers = {
            "X-API-Key": api_key
        }
    
    def compress_pdf(self, file_path, preset="balanced"):
        with open(file_path, 'rb') as f:
            files = {'files': f}
            data = {'preset': preset}
            response = requests.post(
                f"{self.base_url}/pdf/compress-advanced",
                headers=self.headers,
                files=files,
                data=data
            )
        return response
    
    def batch_ocr(self, file_paths, languages=['eng']):
        files = []
        for i, path in enumerate(file_paths):
            with open(path, 'rb') as f:
                files.append(('files', f))
        
        data = {
            'operation': 'ocr',
            'languages': languages
        }
        
        response = requests.post(
            f"{self.base_url}/pdf/batch-process",
            headers=self.headers,
            files=files,
            data=data
        )
        return response.json()

# Usage
api = PDFToolsAPI("sk_your_api_key")
result = api.compress_pdf("document.pdf", "web")
```

### JavaScript/Node.js Integration

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

class PDFToolsAPI {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseURL = 'https://api.domain.com/api';
        this.headers = {
            'X-API-Key': apiKey
        };
    }

    async extractText(filePath, format = 'txt') {
        const form = new FormData();
        form.append('files', fs.createReadStream(filePath));
        form.append('format', format);

        const response = await axios.post(
            `${this.baseURL}/pdf/extract-text-advanced`,
            form,
            {
                headers: {
                    ...this.headers,
                    ...form.getHeaders()
                }
            }
        );

        return response.data;
    }

    async getAnalytics(days = 30) {
        const response = await axios.get(
            `${this.baseURL}/analytics/usage?days=${days}`,
            { headers: this.headers }
        );

        return response.data;
    }
}

// Usage
const api = new PDFToolsAPI('sk_your_api_key');
api.extractText('document.pdf', 'json')
    .then(result => console.log(result))
    .catch(error => console.error(error));
```

## Webhooks

For enterprise customers, webhooks can be configured to receive notifications about processing completion, errors, and usage limits.

### Webhook Events

- `processing.completed` - File processing completed
- `processing.failed` - File processing failed
- `quota.warning` - Approaching usage limit
- `quota.exceeded` - Usage limit exceeded

### Webhook Payload Example

```json
{
  "event": "processing.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "user_id": "user_123",
    "operation": "pdf_compress",
    "file_name": "document.pdf",
    "success": true,
    "processing_time": 2.34
  }
}
```

## SDKs and Libraries

Official SDKs are available for:

- **Python**: `pip install pdftools-sdk`
- **Node.js**: `npm install @pdftools/sdk`
- **PHP**: `composer require pdftools/sdk`
- **Ruby**: `gem install pdftools-sdk`
- **Go**: `go get github.com/pdftools/go-sdk`

Community SDKs:
- **C#/.NET**: Available on NuGet
- **Java**: Available on Maven Central

## Support

For API support:
- Documentation: https://docs.pdftools.com
- Support Email: api-support@pdftools.com
- Community Forum: https://community.pdftools.com
- Status Page: https://status.pdftools.com