import os
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from supabase import create_client, Client
from functools import wraps
from flask import request, jsonify

class FileManager:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.allowed_extensions = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'}
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.upload_folder = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
        
        # Create upload folder if it doesn't exist
        os.makedirs(self.upload_folder, exist_ok=True)

    def allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def validate_pdf_file(self, file) -> bool:
        """Validate uploaded PDF file"""
        if not file:
            return False
        
        if not self.allowed_file(file.filename):
            return False
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size > self.max_file_size:
            return False
        
        return True

    def upload_file(self, file, user_id: str = None, session_id: str = None):
        """Upload file and create database records"""
        try:
            if not self.validate_pdf_file(file):
                return {'success': False, 'error': 'Invalid file'}

            # Generate unique filename
            filename = secure_filename(file.filename)
            file_id = str(uuid.uuid4())
            stored_filename = f"{file_id}_{filename}"
            
            # Get file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)

            # Save file locally (in production, this would be cloud storage)
            file_path = os.path.join(self.upload_folder, stored_filename)
            file.save(file_path)

            # Create PDF job record
            job_data = {
                'user_id': user_id,
                'session_id': session_id,
                'job_type': 'upload',
                'application': 'snackpdf',  # Default to snackpdf
                'input_file_name': filename,
                'input_file_size': file_size
            }

            job_result = self.supabase.table('pdf_jobs').insert(job_data).execute()
            
            if not job_result.data:
                # Clean up file if database insert fails
                if os.path.exists(file_path):
                    os.remove(file_path)
                return {'success': False, 'error': 'Failed to create job record'}

            job_id = job_result.data[0]['id']

            # Create file storage record
            storage_data = {
                'user_id': user_id,
                'job_id': job_id,
                'file_name': filename,
                'file_size': file_size,
                'file_type': filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown',
                'storage_path': file_path,
                'storage_provider': 'local',
                'is_temporary': True,
                'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }

            storage_result = self.supabase.table('file_storage').insert(storage_data).execute()
            
            if not storage_result.data:
                # Clean up if storage record creation fails
                if os.path.exists(file_path):
                    os.remove(file_path)
                return {'success': False, 'error': 'Failed to create storage record'}

            file_record_id = storage_result.data[0]['id']

            # Create initial job status
            status_data = {
                'job_id': job_id,
                'status': 'completed',
                'progress_percentage': 100,
                'started_at': datetime.utcnow().isoformat(),
                'completed_at': datetime.utcnow().isoformat()
            }

            self.supabase.table('job_status').insert(status_data).execute()

            return {
                'success': True,
                'file_id': file_record_id,
                'job_id': job_id,
                'filename': filename,
                'file_size': file_size
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_file(self, file_id: str):
        """Get file information by ID"""
        try:
            result = self.supabase.table('file_storage').select('*').eq('id', file_id).execute()
            
            if result.data:
                return {'success': True, 'file': result.data[0]}
            else:
                return {'success': False, 'error': 'File not found'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_download_file(self, file_id: str):
        """Get file for download"""
        try:
            result = self.supabase.table('file_storage').select('*').eq('id', file_id).execute()
            
            if not result.data:
                return {'success': False, 'error': 'File not found'}

            file_record = result.data[0]
            file_path = file_record['storage_path']

            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found on disk'}

            return {
                'success': True,
                'file_path': file_path,
                'filename': file_record['file_name']
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete_file(self, file_id: str):
        """Delete file and its records"""
        try:
            # Get file info
            file_result = self.get_file(file_id)
            if not file_result['success']:
                return file_result

            file_record = file_result['file']
            
            # Delete physical file
            if os.path.exists(file_record['storage_path']):
                os.remove(file_record['storage_path'])

            # Delete database record
            self.supabase.table('file_storage').delete().eq('id', file_id).execute()

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cleanup_expired_files(self):
        """Clean up expired temporary files"""
        try:
            # Get expired files
            current_time = datetime.utcnow().isoformat()
            expired_files = self.supabase.table('file_storage').select('*').lt(
                'expires_at', current_time
            ).eq('is_temporary', True).execute()

            for file_record in expired_files.data:
                # Delete physical file
                if os.path.exists(file_record['storage_path']):
                    os.remove(file_record['storage_path'])

                # Delete database record
                self.supabase.table('file_storage').delete().eq(
                    'id', file_record['id']
                ).execute()

            return {'success': True, 'cleaned_files': len(expired_files.data)}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_usage(self, user_id: str, file_size: int):
        """Update user's file size usage"""
        try:
            # Get current usage
            current_time = datetime.utcnow()
            usage_result = self.supabase.table('usage_limits').select('*').eq(
                'user_id', user_id
            ).lte('period_start', current_time.isoformat()).gte(
                'period_end', current_time.isoformat()
            ).execute()

            if usage_result.data:
                # Update existing usage
                current_usage = usage_result.data[0]
                new_file_size_used = current_usage['file_size_used'] + file_size
                
                self.supabase.table('usage_limits').update({
                    'file_size_used': new_file_size_used,
                    'jobs_used': current_usage['jobs_used'] + 1
                }).eq('id', current_usage['id']).execute()

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}


def validate_session(f):
    """Decorator to validate session for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            # For routes that support both authenticated and anonymous users
            request.current_user = None
            return f(*args, **kwargs)

        try:
            from core.auth import AuthManager
            
            token = auth_header.replace('Bearer ', '')
            auth_manager = AuthManager()
            result = auth_manager.validate_session(token)
            
            if result['success']:
                request.current_user = result['user']
                return f(*args, **kwargs)
            else:
                return jsonify({'error': 'Invalid session'}), 401
                
        except Exception as e:
            return jsonify({'error': 'Authentication failed'}), 401

    return decorated_function


class UsageTracker:
    """Track and enforce usage limits"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

    def check_and_update_usage(self, user_id: str, file_size: int = 0, job_type: str = 'unknown'):
        """Check usage limits and update if within limits"""
        try:
            if not user_id:
                # Anonymous users have basic limits
                return self.check_anonymous_limits(file_size)

            # Get current usage
            usage_result = self.supabase.table('user_current_usage').select('*').eq(
                'user_id', user_id
            ).execute()

            if not usage_result.data:
                return {'success': False, 'error': 'User usage data not found'}

            usage = usage_result.data[0]

            # Check limits
            if usage['jobs_used'] >= usage['jobs_limit']:
                return {
                    'success': False,
                    'error': 'Job limit exceeded. Please upgrade your plan.',
                    'limit_type': 'jobs'
                }

            if usage['file_size_used'] + file_size > usage['file_size_limit']:
                return {
                    'success': False,
                    'error': 'File size limit exceeded. Please upgrade your plan.',
                    'limit_type': 'file_size'
                }

            # Update usage
            new_jobs_used = usage['jobs_used'] + 1
            new_file_size_used = usage['file_size_used'] + file_size

            self.supabase.table('usage_limits').update({
                'jobs_used': new_jobs_used,
                'file_size_used': new_file_size_used
            }).eq('user_id', user_id).eq(
                'period_start', '<=', datetime.utcnow().isoformat()
            ).eq(
                'period_end', '>=', datetime.utcnow().isoformat()
            ).execute()

            return {
                'success': True,
                'remaining_jobs': usage['jobs_limit'] - new_jobs_used,
                'remaining_file_size': usage['file_size_limit'] - new_file_size_used
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def check_anonymous_limits(self, file_size: int):
        """Check limits for anonymous users"""
        # Anonymous users have very basic limits
        max_file_size = 5 * 1024 * 1024  # 5MB
        
        if file_size > max_file_size:
            return {
                'success': False,
                'error': 'File too large. Please register for higher limits.',
                'limit_type': 'file_size'
            }

        return {'success': True}

    def reset_monthly_usage(self):
        """Reset usage limits for all users (monthly job)"""
        try:
            current_time = datetime.utcnow()
            month_start = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

            # Create new usage periods for all users
            users_result = self.supabase.table('users').select('id, subscription_status').execute()

            for user in users_result.data:
                # Define limits based on subscription
                if user['subscription_status'] == 'premium':
                    jobs_limit = 100
                    file_size_limit = 104857600  # 100MB
                elif user['subscription_status'] == 'enterprise':
                    jobs_limit = 1000
                    file_size_limit = 1073741824  # 1GB
                else:  # free
                    jobs_limit = 5
                    file_size_limit = 10485760  # 10MB

                # Insert new usage period
                usage_data = {
                    'user_id': user['id'],
                    'period_start': month_start.isoformat(),
                    'period_end': month_end.isoformat(),
                    'jobs_used': 0,
                    'jobs_limit': jobs_limit,
                    'file_size_used': 0,
                    'file_size_limit': file_size_limit
                }

                self.supabase.table('usage_limits').insert(usage_data).execute()

            return {'success': True, 'users_updated': len(users_result.data)}

        except Exception as e:
            return {'success': False, 'error': str(e)}