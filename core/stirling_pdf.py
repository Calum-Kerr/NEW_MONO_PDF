"""
StirlingPDF integration for advanced PDF processing operations.
Handles communication with StirlingPDF API for various PDF operations.
"""

import os
import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StirlingPDFClient:
    """Client for interacting with StirlingPDF API."""
    
    def __init__(self):
        self.base_url = os.getenv('STIRLING_PDF_URL', 'http://localhost:8080')
        self.api_key = os.getenv('STIRLING_PDF_API_KEY')
        self.timeout = int(os.getenv('STIRLING_PDF_TIMEOUT', '120'))  # 2 minutes default
        
        # Remove trailing slash if present
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
        
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
    
    def _make_request(self, endpoint: str, method: str = 'POST', files: Dict = None, 
                      data: Dict = None, json_data: Dict = None) -> Dict[str, Any]:
        """Make a request to StirlingPDF API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                files=files,
                data=data,
                json=json_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                # StirlingPDF returns PDF files directly for most operations
                if response.headers.get('content-type', '').startswith('application/pdf'):
                    return {
                        'success': True,
                        'content': response.content,
                        'content_type': 'application/pdf',
                        'filename': self._extract_filename(response.headers)
                    }
                else:
                    # JSON response
                    try:
                        return {
                            'success': True,
                            'data': response.json()
                        }
                    except:
                        return {
                            'success': True,
                            'data': response.text
                        }
            else:
                logger.error(f"StirlingPDF API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"API error: {response.status_code}",
                    'details': response.text
                }
                
        except requests.RequestException as e:
            logger.error(f"StirlingPDF request failed: {str(e)}")
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }
    
    def _extract_filename(self, headers: Dict) -> str:
        """Extract filename from response headers."""
        content_disposition = headers.get('content-disposition', '')
        if 'filename=' in content_disposition:
            return content_disposition.split('filename=')[1].strip('"')
        return f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    def merge_pdfs(self, pdf_files: List[bytes], filenames: List[str]) -> Dict[str, Any]:
        """Merge multiple PDF files into one."""
        if len(pdf_files) < 2:
            return {
                'success': False,
                'error': 'At least 2 PDF files are required for merging'
            }
        
        files = {}
        for i, (pdf_content, filename) in enumerate(zip(pdf_files, filenames)):
            files[f'fileInput{i+1}'] = (filename, pdf_content, 'application/pdf')
        
        return self._make_request('/api/v1/general/merge-pdfs', files=files)
    
    def split_pdf(self, pdf_content: bytes, filename: str, pages: str = None) -> Dict[str, Any]:
        """Split a PDF file into separate pages or specified page ranges."""
        files = {
            'fileInput': (filename, pdf_content, 'application/pdf')
        }
        
        data = {}
        if pages:
            data['pages'] = pages  # e.g., "1-3,5,7-9"
        
        return self._make_request('/api/v1/general/split-pages', files=files, data=data)
    
    def compress_pdf(self, pdf_content: bytes, filename: str, 
                     optimization_level: int = 1, quality: int = 75,
                     compression_algorithm: str = 'auto') -> Dict[str, Any]:
        """Compress a PDF file with advanced compression algorithms."""
        files = {
            'fileInput': (filename, pdf_content, 'application/pdf')
        }
        
        # Advanced compression options
        data = {
            'optimizeLevel': str(optimization_level),  # 1-4, higher = more compression
            'imageQuality': str(quality),  # 10-100, image quality percentage
            'algorithm': compression_algorithm,  # auto, lossless, lossy, hybrid
            'removeMetadata': 'true',  # Remove metadata for smaller size
            'linearize': 'true'  # Optimize for web viewing
        }
        
        return self._make_request('/api/v1/general/compress-pdf', files=files, data=data)
    
    def advanced_compress(self, pdf_content: bytes, filename: str,
                         preset: str = 'balanced') -> Dict[str, Any]:
        """Apply advanced compression presets for different use cases."""
        presets = {
            'web': {'optimization_level': 3, 'quality': 60, 'algorithm': 'lossy'},
            'print': {'optimization_level': 2, 'quality': 85, 'algorithm': 'hybrid'},
            'archive': {'optimization_level': 4, 'quality': 40, 'algorithm': 'lossy'},
            'balanced': {'optimization_level': 2, 'quality': 75, 'algorithm': 'auto'},
            'maximum': {'optimization_level': 4, 'quality': 30, 'algorithm': 'lossy'}
        }
        
        settings = presets.get(preset, presets['balanced'])
        return self.compress_pdf(pdf_content, filename, **settings)
    
    def convert_to_pdf(self, file_content: bytes, filename: str, 
                       file_type: str = None) -> Dict[str, Any]:
        """Convert various file formats to PDF."""
        if not file_type:
            # Detect file type from extension
            ext = filename.lower().split('.')[-1]
            if ext in ['doc', 'docx']:
                file_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif ext in ['xls', 'xlsx']:
                file_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif ext in ['ppt', 'pptx']:
                file_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            elif ext in ['jpg', 'jpeg']:
                file_type = 'image/jpeg'
            elif ext == 'png':
                file_type = 'image/png'
            else:
                file_type = 'application/octet-stream'
        
        files = {
            'fileInput': (filename, file_content, file_type)
        }
        
        return self._make_request('/api/v1/convert/file/pdf', files=files)
    
    def extract_pages(self, pdf_content: bytes, filename: str, 
                      page_numbers: List[int]) -> Dict[str, Any]:
        """Extract specific pages from a PDF."""
        files = {
            'fileInput': (filename, pdf_content, 'application/pdf')
        }
        
        data = {
            'pageNumbers': ','.join(map(str, page_numbers))
        }
        
        return self._make_request('/api/v1/general/extract-pages', files=files, data=data)
    
    def rotate_pdf(self, pdf_content: bytes, filename: str, 
                   angle: int = 90, pages: str = 'all') -> Dict[str, Any]:
        """Rotate pages in a PDF document."""
        files = {
            'fileInput': (filename, pdf_content, 'application/pdf')
        }
        
        data = {
            'angle': str(angle),  # 90, 180, 270
            'pageNumbers': pages  # 'all' or specific pages like '1,3,5-7'
        }
        
        return self._make_request('/api/v1/general/rotate-pdf', files=files, data=data)
    
    def add_watermark(self, pdf_content: bytes, filename: str, 
                      watermark_text: str, opacity: float = 0.5,
                      font_size: int = 30) -> Dict[str, Any]:
        """Add watermark to PDF pages."""
        files = {
            'fileInput': (filename, pdf_content, 'application/pdf')
        }
        
        data = {
            'watermarkText': watermark_text,
            'opacity': str(opacity),
            'fontSize': str(font_size),
            'rotation': '45'  # Default diagonal watermark
        }
        
        return self._make_request('/api/v1/security/add-watermark', files=files, data=data)
    
    def add_password_protection(self, pdf_content: bytes, filename: str,
                               password: str, permissions: List[str] = None) -> Dict[str, Any]:
        """Add password protection to a PDF."""
        files = {
            'fileInput': (filename, pdf_content, 'application/pdf')
        }
        
        data = {
            'password': password,
            'keyLength': '256'  # AES-256 encryption
        }
        
        if permissions:
            # Permissions like 'canPrint', 'canModify', 'canCopy', etc.
            for perm in permissions:
                data[perm] = 'true'
        
        return self._make_request('/api/v1/security/add-password', files=files, data=data)
    
    def remove_password(self, pdf_content: bytes, filename: str, 
                        password: str) -> Dict[str, Any]:
        """Remove password protection from a PDF."""
        files = {
            'fileInput': (filename, pdf_content, 'application/pdf')
        }
        
        data = {
            'password': password
        }
        
        return self._make_request('/api/v1/security/remove-password', files=files, data=data)
    
    def ocr_pdf(self, pdf_content: bytes, filename: str, 
                languages: List[str] = None, ocr_type: str = 'auto',
                dpi: int = 300, remove_blanks: bool = True) -> Dict[str, Any]:
        """Perform OCR on a PDF to make it searchable with advanced options."""
        files = {
            'fileInput': (filename, pdf_content, 'application/pdf')
        }
        
        # Extended language support
        supported_languages = [
            'eng', 'fra', 'deu', 'spa', 'ita', 'por', 'rus', 'chi_sim', 'chi_tra',
            'jpn', 'kor', 'ara', 'hin', 'tha', 'vie', 'nld', 'swe', 'dan', 'nor'
        ]
        
        if languages:
            # Validate languages
            valid_languages = [lang for lang in languages if lang in supported_languages]
            if not valid_languages:
                valid_languages = ['eng']  # Default fallback
        else:
            valid_languages = ['eng']
        
        data = {
            'ocrType': ocr_type,  # auto, force-ocr, skip-text
            'languages': ','.join(valid_languages),
            'dpi': str(dpi),
            'removeBlanks': str(remove_blanks).lower()
        }
        
        return self._make_request('/api/v1/convert/pdf/ocr', files=files, data=data)
    
    def extract_text(self, pdf_content: bytes, filename: str, 
                     format: str = 'txt', include_annotations: bool = False) -> Dict[str, Any]:
        """Extract text content from a PDF with multiple format options."""
        files = {
            'fileInput': (filename, pdf_content, 'application/pdf')
        }
        
        data = {
            'format': format,  # 'txt', 'json', 'xml'
            'includeAnnotations': str(include_annotations).lower()
        }
        
        endpoint_map = {
            'txt': '/api/v1/convert/pdf/txt',
            'json': '/api/v1/convert/pdf/json', 
            'xml': '/api/v1/convert/pdf/xml'
        }
        
        endpoint = endpoint_map.get(format, '/api/v1/convert/pdf/txt')
        return self._make_request(endpoint, files=files, data=data)
    
    def health_check(self) -> Dict[str, Any]:
        """Check if StirlingPDF service is available."""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/info/status", timeout=10)
            if response.status_code == 200:
                return {
                    'success': True,
                    'status': 'healthy',
                    'version': response.json().get('version', 'unknown')
                }
            else:
                return {
                    'success': False,
                    'error': f"Service returned {response.status_code}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Health check failed: {str(e)}"
            }
    
    def batch_process(self, operation: str, files_data: List[Dict], 
                      operation_params: Dict = None) -> Dict[str, Any]:
        """Process multiple files in batch with the same operation."""
        if not files_data:
            return {
                'success': False,
                'error': 'No files provided for batch processing'
            }
        
        results = []
        successful = 0
        failed = 0
        
        for i, file_data in enumerate(files_data):
            try:
                pdf_content = file_data.get('content')
                filename = file_data.get('filename', f'file_{i}.pdf')
                
                # Apply operation based on type
                if operation == 'compress':
                    preset = operation_params.get('preset', 'balanced') if operation_params else 'balanced'
                    result = self.advanced_compress(pdf_content, filename, preset)
                elif operation == 'ocr':
                    languages = operation_params.get('languages', ['eng']) if operation_params else ['eng']
                    result = self.ocr_pdf(pdf_content, filename, languages)
                elif operation == 'extract_text':
                    format = operation_params.get('format', 'txt') if operation_params else 'txt'
                    result = self.extract_text(pdf_content, filename, format)
                elif operation == 'rotate':
                    angle = operation_params.get('angle', 90) if operation_params else 90
                    result = self.rotate_pdf(pdf_content, filename, angle)
                else:
                    result = {
                        'success': False,
                        'error': f'Unsupported batch operation: {operation}'
                    }
                
                results.append({
                    'filename': filename,
                    'success': result['success'],
                    'result': result if result['success'] else None,
                    'error': result.get('error') if not result['success'] else None
                })
                
                if result['success']:
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                results.append({
                    'filename': file_data.get('filename', f'file_{i}.pdf'),
                    'success': False,
                    'error': f'Processing error: {str(e)}'
                })
                failed += 1
        
        return {
            'success': True,
            'results': results,
            'summary': {
                'total': len(files_data),
                'successful': successful,
                'failed': failed,
                'success_rate': (successful / len(files_data)) * 100 if files_data else 0
            }
        }

# Global instance
stirling_client = StirlingPDFClient()