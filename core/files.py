"""
File handling utilities for PDF operations.
Manages uploads, downloads, and temporary file storage.
"""

import os
import uuid
import mimetypes
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from werkzeug.utils import secure_filename
from supabase import create_client, Client
import boto3
from botocore.exceptions import ClientError

class FileManager:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.storage_bucket = os.getenv('SUPABASE_STORAGE_BUCKET', 'pdf-files')
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE', 50 * 1024 * 1024))  # 50MB default
        
        if not all([self.supabase_url, self.service_key]):
            raise ValueError("Missing Supabase configuration")
        
        self.supabase: Client = create_client(self.supabase_url, self.service_key)
        
        # Allowed file types
        self.allowed_extensions = {
            'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt',
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff',
            'ppt', 'pptx', 'xls', 'xlsx'
        }
        
        # PDF-specific MIME types
        self.pdf_mime_types = {
            'application/pdf',
            'application/x-pdf',
            'application/acrobat',
            'applications/vnd.pdf',
            'text/pdf',
            'text/x-pdf'
        }
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed."""
        if '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in self.allowed_extensions
    
    def is_pdf_file(self, filename: str, content_type: str = None) -> bool:
        """Check if file is a PDF."""
        if filename:
            extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            if extension == 'pdf':
                return True
        
        if content_type and content_type.lower() in self.pdf_mime_types:
            return True
        
        return False
    
    def validate_file(self, file_data: bytes, filename: str, content_type: str = None) -> Dict[str, Any]:
        """Validate uploaded file."""
        errors = []
        
        # Check filename
        if not filename:
            errors.append("Filename is required")
        elif not self.is_allowed_file(filename):
            errors.append(f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}")
        
        # Check file size
        if len(file_data) > self.max_file_size:
            errors.append(f"File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB")
        
        # Check if file is empty
        if len(file_data) == 0:
            errors.append("File is empty")
        
        # Basic PDF validation if it's a PDF file
        if self.is_pdf_file(filename, content_type):
            if not file_data.startswith(b'%PDF-'):
                errors.append("Invalid PDF file format")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "file_size": len(file_data),
            "is_pdf": self.is_pdf_file(filename, content_type)
        }
    
    def generate_secure_filename(self, original_filename: str) -> str:
        """Generate a secure filename with UUID prefix."""
        if not original_filename:
            return f"{uuid.uuid4().hex}.pdf"
        
        # Secure the filename
        secured = secure_filename(original_filename)
        
        # Add UUID prefix to avoid conflicts
        file_uuid = uuid.uuid4().hex
        name, ext = os.path.splitext(secured)
        
        return f"{file_uuid}_{name}{ext}"
    
    def upload_file(self, file_data: bytes, filename: str, user_id: str = None, 
                   folder: str = "uploads") -> Dict[str, Any]:
        """Upload file to Supabase storage."""
        try:
            # Validate file
            validation = self.validate_file(file_data, filename)
            if not validation["valid"]:
                return {"success": False, "errors": validation["errors"]}
            
            # Generate secure filename
            secure_name = self.generate_secure_filename(filename)
            
            # Create file path
            if user_id:
                file_path = f"{folder}/{user_id}/{secure_name}"
            else:
                file_path = f"{folder}/anonymous/{secure_name}"
            
            # Calculate file hash
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # Upload to Supabase storage
            response = self.supabase.storage.from_(self.storage_bucket).upload(
                file_path, file_data, {"content-type": mimetypes.guess_type(filename)[0] or "application/octet-stream"}
            )
            
            if hasattr(response, 'error') and response.error:
                return {"success": False, "error": f"Upload failed: {response.error}"}
            
            # Get public URL
            public_url = self.supabase.storage.from_(self.storage_bucket).get_public_url(file_path)
            
            return {
                "success": True,
                "file_path": file_path,
                "secure_filename": secure_name,
                "public_url": public_url,
                "file_size": len(file_data),
                "file_hash": file_hash,
                "is_pdf": validation["is_pdf"]
            }
            
        except Exception as e:
            return {"success": False, "error": f"Upload error: {str(e)}"}
    
    def download_file(self, file_path: str) -> Dict[str, Any]:
        """Download file from Supabase storage."""
        try:
            response = self.supabase.storage.from_(self.storage_bucket).download(file_path)
            
            if hasattr(response, 'error') and response.error:
                return {"success": False, "error": f"Download failed: {response.error}"}
            
            return {
                "success": True,
                "file_data": response,
                "file_path": file_path
            }
            
        except Exception as e:
            return {"success": False, "error": f"Download error: {str(e)}"}
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Delete file from Supabase storage."""
        try:
            response = self.supabase.storage.from_(self.storage_bucket).remove([file_path])
            
            if hasattr(response, 'error') and response.error:
                return {"success": False, "error": f"Delete failed: {response.error}"}
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": f"Delete error: {str(e)}"}
    
    def create_signed_url(self, file_path: str, expires_in: int = 3600) -> Optional[str]:
        """Create a signed URL for temporary file access."""
        try:
            response = self.supabase.storage.from_(self.storage_bucket).create_signed_url(
                file_path, expires_in
            )
            
            if hasattr(response, 'error') and response.error:
                return None
            
            return response.get('signedURL')
            
        except Exception:
            return None
    
    def cleanup_expired_files(self) -> Dict[str, Any]:
        """Clean up expired PDF job files."""
        try:
            # Get expired jobs
            expired_jobs = self.supabase.table('pdf_jobs').select(
                'input_file_url, output_file_url'
            ).lt('expires_at', datetime.utcnow().isoformat()).execute()
            
            deleted_count = 0
            errors = []
            
            for job in expired_jobs.data:
                # Delete input file
                if job.get('input_file_url'):
                    file_path = self._extract_path_from_url(job['input_file_url'])
                    if file_path:
                        result = self.delete_file(file_path)
                        if result["success"]:
                            deleted_count += 1
                        else:
                            errors.append(f"Failed to delete {file_path}: {result['error']}")
                
                # Delete output file
                if job.get('output_file_url'):
                    file_path = self._extract_path_from_url(job['output_file_url'])
                    if file_path:
                        result = self.delete_file(file_path)
                        if result["success"]:
                            deleted_count += 1
                        else:
                            errors.append(f"Failed to delete {file_path}: {result['error']}")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "errors": errors
            }
            
        except Exception as e:
            return {"success": False, "error": f"Cleanup error: {str(e)}"}
    
    def _extract_path_from_url(self, url: str) -> Optional[str]:
        """Extract file path from Supabase storage URL."""
        try:
            # Parse URL to extract file path
            # Supabase storage URLs typically look like:
            # https://[project].supabase.co/storage/v1/object/public/[bucket]/[path]
            parts = url.split(f'/storage/v1/object/public/{self.storage_bucket}/')
            if len(parts) > 1:
                return parts[1]
            return None
        except Exception:
            return None
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information from storage."""
        try:
            # This would need to be implemented based on Supabase storage API
            # For now, return basic info
            return {
                "success": True,
                "file_path": file_path,
                "exists": True  # Would need actual check
            }
            
        except Exception as e:
            return {"success": False, "error": f"Info error: {str(e)}"}
    
    def create_temp_folder(self, user_id: str = None) -> str:
        """Create a temporary folder for processing."""
        folder_id = uuid.uuid4().hex
        if user_id:
            return f"temp/{user_id}/{folder_id}"
        else:
            return f"temp/anonymous/{folder_id}"
    
    def list_user_files(self, user_id: str, folder: str = "uploads", limit: int = 50) -> Dict[str, Any]:
        """List files for a specific user."""
        try:
            # Get files from database records
            jobs_response = self.supabase.table('pdf_jobs').select(
                'original_filename, input_file_url, output_file_url, created_at, tool_type'
            ).eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            files = []
            for job in jobs_response.data:
                files.append({
                    "filename": job['original_filename'],
                    "input_url": job.get('input_file_url'),
                    "output_url": job.get('output_file_url'),
                    "created_at": job['created_at'],
                    "tool_type": job['tool_type']
                })
            
            return {
                "success": True,
                "files": files,
                "count": len(files)
            }
            
        except Exception as e:
            return {"success": False, "error": f"List error: {str(e)}"}

# Global file manager instance
file_manager = FileManager()