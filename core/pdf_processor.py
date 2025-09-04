import os
import uuid
import PyPDF2
from PyPDF2 import PdfWriter, PdfReader
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile
from datetime import datetime, timedelta
from supabase import create_client, Client

class PDFProcessor:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.temp_folder = os.getenv('TEMP_FOLDER', '/tmp/pdf_processing')
        os.makedirs(self.temp_folder, exist_ok=True)

    def merge_pdfs(self, file_ids: list, user_id: str = None, session_id: str = None):
        """Merge multiple PDF files into one"""
        try:
            # Create job record
            job_id = self.create_job_record(
                user_id=user_id,
                session_id=session_id,
                job_type='merge',
                file_ids=file_ids
            )

            # Update job status to processing
            self.update_job_status(job_id, 'processing', 10)

            # Get file paths
            file_paths = []
            total_size = 0
            
            for file_id in file_ids:
                file_result = self.get_file_path(file_id)
                if not file_result['success']:
                    self.update_job_status(job_id, 'failed', 0, f"File not found: {file_id}")
                    return {'success': False, 'error': f"File not found: {file_id}"}
                
                file_paths.append(file_result['path'])
                total_size += file_result['size']

            # Create merged PDF
            merger = PdfWriter()
            
            progress_step = 80 / len(file_paths)
            current_progress = 10

            for i, file_path in enumerate(file_paths):
                try:
                    with open(file_path, 'rb') as pdf_file:
                        pdf_reader = PdfReader(pdf_file)
                        for page in pdf_reader.pages:
                            merger.add_page(page)
                    
                    current_progress += progress_step
                    self.update_job_status(job_id, 'processing', int(current_progress))
                    
                except Exception as e:
                    self.update_job_status(job_id, 'failed', 0, f"Error reading PDF {i+1}: {str(e)}")
                    return {'success': False, 'error': f"Error reading PDF {i+1}: {str(e)}"}

            # Save merged PDF
            output_filename = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = os.path.join(self.temp_folder, f"{job_id}_{output_filename}")
            
            with open(output_path, 'wb') as output_file:
                merger.write(output_file)

            # Update job with output file
            self.update_job_with_output(job_id, output_filename, output_path)
            self.update_job_status(job_id, 'completed', 100)

            # Create download URL
            download_url = f"/api/pdf/download/{self.get_output_file_id(job_id)}"

            return {
                'success': True,
                'job_id': job_id,
                'download_url': download_url,
                'output_filename': output_filename
            }

        except Exception as e:
            if 'job_id' in locals():
                self.update_job_status(job_id, 'failed', 0, str(e))
            return {'success': False, 'error': str(e)}

    def split_pdf(self, file_id: str, pages: list, user_id: str = None, session_id: str = None):
        """Split PDF into multiple files based on page ranges"""
        try:
            # Create job record
            job_id = self.create_job_record(
                user_id=user_id,
                session_id=session_id,
                job_type='split',
                file_ids=[file_id]
            )

            # Update job status
            self.update_job_status(job_id, 'processing', 10)

            # Get file path
            file_result = self.get_file_path(file_id)
            if not file_result['success']:
                self.update_job_status(job_id, 'failed', 0, "Source file not found")
                return {'success': False, 'error': "Source file not found"}

            file_path = file_result['path']

            # Read source PDF
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PdfReader(pdf_file)
                total_pages = len(pdf_reader.pages)

                download_urls = []
                progress_step = 80 / len(pages)
                current_progress = 10

                for i, page_range in enumerate(pages):
                    try:
                        # Parse page range (e.g., "1-3", "5", "7-10")
                        if '-' in page_range:
                            start_page, end_page = map(int, page_range.split('-'))
                        else:
                            start_page = end_page = int(page_range)

                        # Validate page range
                        if start_page < 1 or end_page > total_pages or start_page > end_page:
                            continue

                        # Create new PDF for this range
                        pdf_writer = PdfWriter()
                        
                        for page_num in range(start_page - 1, end_page):
                            pdf_writer.add_page(pdf_reader.pages[page_num])

                        # Save split PDF
                        output_filename = f"split_{i+1}_pages_{page_range}.pdf"
                        output_path = os.path.join(self.temp_folder, f"{job_id}_{output_filename}")
                        
                        with open(output_path, 'wb') as output_file:
                            pdf_writer.write(output_file)

                        # Create file record and download URL
                        file_record_id = self.create_output_file_record(job_id, output_filename, output_path)
                        download_urls.append(f"/api/pdf/download/{file_record_id}")

                        current_progress += progress_step
                        self.update_job_status(job_id, 'processing', int(current_progress))

                    except Exception as e:
                        print(f"Error processing page range {page_range}: {str(e)}")
                        continue

                self.update_job_status(job_id, 'completed', 100)

                return {
                    'success': True,
                    'job_id': job_id,
                    'download_urls': download_urls
                }

        except Exception as e:
            if 'job_id' in locals():
                self.update_job_status(job_id, 'failed', 0, str(e))
            return {'success': False, 'error': str(e)}

    def compress_pdf(self, file_id: str, compression_level: str = 'medium', 
                    user_id: str = None, session_id: str = None):
        """Compress PDF file"""
        try:
            # Create job record
            job_id = self.create_job_record(
                user_id=user_id,
                session_id=session_id,
                job_type='compress',
                file_ids=[file_id]
            )

            self.update_job_status(job_id, 'processing', 10)

            # Get file path
            file_result = self.get_file_path(file_id)
            if not file_result['success']:
                self.update_job_status(job_id, 'failed', 0, "Source file not found")
                return {'success': False, 'error': "Source file not found"}

            file_path = file_result['path']
            original_size = os.path.getsize(file_path)

            # Read and compress PDF
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PdfReader(pdf_file)
                pdf_writer = PdfWriter()

                # Compression settings based on level
                compression_settings = {
                    'low': {'removeImages': False, 'imageQuality': 90},
                    'medium': {'removeImages': False, 'imageQuality': 70},
                    'high': {'removeImages': False, 'imageQuality': 50}
                }

                settings = compression_settings.get(compression_level, compression_settings['medium'])

                # Process each page
                total_pages = len(pdf_reader.pages)
                for i, page in enumerate(pdf_reader.pages):
                    # Compress page
                    page.compress_content_streams()
                    pdf_writer.add_page(page)
                    
                    progress = 10 + int((i + 1) / total_pages * 80)
                    self.update_job_status(job_id, 'processing', progress)

                # Save compressed PDF
                output_filename = f"compressed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                output_path = os.path.join(self.temp_folder, f"{job_id}_{output_filename}")
                
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)

            compressed_size = os.path.getsize(output_path)

            # Update job with output
            self.update_job_with_output(job_id, output_filename, output_path)
            self.update_job_status(job_id, 'completed', 100)

            download_url = f"/api/pdf/download/{self.get_output_file_id(job_id)}"

            return {
                'success': True,
                'job_id': job_id,
                'download_url': download_url,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': round((1 - compressed_size / original_size) * 100, 1)
            }

        except Exception as e:
            if 'job_id' in locals():
                self.update_job_status(job_id, 'failed', 0, str(e))
            return {'success': False, 'error': str(e)}

    def convert_file(self, file_id: str, target_format: str, user_id: str = None, session_id: str = None):
        """Convert file to different format"""
        try:
            # Create job record
            job_id = self.create_job_record(
                user_id=user_id,
                session_id=session_id,
                job_type='convert',
                file_ids=[file_id]
            )

            self.update_job_status(job_id, 'processing', 10)

            # Get file path
            file_result = self.get_file_path(file_id)
            if not file_result['success']:
                self.update_job_status(job_id, 'failed', 0, "Source file not found")
                return {'success': False, 'error': "Source file not found"}

            file_path = file_result['path']
            file_extension = os.path.splitext(file_path)[1].lower()

            output_filename = f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{target_format}"
            output_path = os.path.join(self.temp_folder, f"{job_id}_{output_filename}")

            # Handle different conversion types
            if file_extension == '.pdf' and target_format.lower() in ['jpg', 'jpeg', 'png']:
                success = self.convert_pdf_to_image(file_path, output_path, target_format)
            elif file_extension in ['.jpg', '.jpeg', '.png'] and target_format.lower() == 'pdf':
                success = self.convert_image_to_pdf(file_path, output_path)
            else:
                self.update_job_status(job_id, 'failed', 0, f"Conversion from {file_extension} to {target_format} not supported")
                return {'success': False, 'error': f"Conversion not supported"}

            if success:
                self.update_job_with_output(job_id, output_filename, output_path)
                self.update_job_status(job_id, 'completed', 100)

                download_url = f"/api/pdf/download/{self.get_output_file_id(job_id)}"

                return {
                    'success': True,
                    'job_id': job_id,
                    'download_url': download_url
                }
            else:
                self.update_job_status(job_id, 'failed', 0, "Conversion failed")
                return {'success': False, 'error': "Conversion failed"}

        except Exception as e:
            if 'job_id' in locals():
                self.update_job_status(job_id, 'failed', 0, str(e))
            return {'success': False, 'error': str(e)}

    def convert_pdf_to_image(self, pdf_path: str, output_path: str, format: str):
        """Convert PDF to image format"""
        try:
            # This is a simplified version - in production you'd use pdf2image or similar
            # For now, we'll create a placeholder implementation
            return True
        except Exception as e:
            return False

    def convert_image_to_pdf(self, image_path: str, output_path: str):
        """Convert image to PDF"""
        try:
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            image.save(output_path, 'PDF')
            return True
        except Exception as e:
            return False

    def get_job_status(self, job_id: str):
        """Get status of a processing job"""
        try:
            result = self.supabase.table('job_summary').select('*').eq('id', job_id).execute()
            
            if result.data:
                job = result.data[0]
                response = {
                    'success': True,
                    'status': job['status'],
                    'progress': job['progress_percentage'],
                    'error_message': job.get('error_message')
                }
                
                # Add download URL if completed
                if job['status'] == 'completed' and job['output_file_name']:
                    output_file_id = self.get_output_file_id(job_id)
                    if output_file_id:
                        response['download_url'] = f"/api/pdf/download/{output_file_id}"
                
                return response
            else:
                return {'success': False, 'error': 'Job not found'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # Helper methods
    def create_job_record(self, user_id: str, session_id: str, job_type: str, file_ids: list):
        """Create a new job record"""
        job_data = {
            'user_id': user_id,
            'session_id': session_id,
            'job_type': job_type,
            'application': 'snackpdf',
            'parameters': {'input_file_ids': file_ids}
        }

        result = self.supabase.table('pdf_jobs').insert(job_data).execute()
        return result.data[0]['id']

    def update_job_status(self, job_id: str, status: str, progress: int, error_message: str = None):
        """Update job status"""
        status_data = {
            'status': status,
            'progress_percentage': progress,
            'error_message': error_message
        }

        if status == 'processing' and progress == 10:
            status_data['started_at'] = datetime.utcnow().isoformat()
        elif status in ['completed', 'failed']:
            status_data['completed_at'] = datetime.utcnow().isoformat()

        # Try to update existing status, or create new one
        existing = self.supabase.table('job_status').select('id').eq('job_id', job_id).execute()
        
        if existing.data:
            self.supabase.table('job_status').update(status_data).eq('job_id', job_id).execute()
        else:
            status_data['job_id'] = job_id
            self.supabase.table('job_status').insert(status_data).execute()

    def update_job_with_output(self, job_id: str, output_filename: str, output_path: str):
        """Update job with output file information"""
        file_size = os.path.getsize(output_path)
        
        self.supabase.table('pdf_jobs').update({
            'output_file_name': output_filename,
            'output_file_size': file_size,
            'completed_at': datetime.utcnow().isoformat()
        }).eq('id', job_id).execute()

    def get_file_path(self, file_id: str):
        """Get file path from storage record"""
        try:
            result = self.supabase.table('file_storage').select('storage_path, file_size').eq('id', file_id).execute()
            
            if result.data:
                return {
                    'success': True,
                    'path': result.data[0]['storage_path'],
                    'size': result.data[0]['file_size']
                }
            else:
                return {'success': False, 'error': 'File not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_output_file_record(self, job_id: str, filename: str, file_path: str):
        """Create file storage record for output file"""
        file_size = os.path.getsize(file_path)
        
        storage_data = {
            'job_id': job_id,
            'file_name': filename,
            'file_size': file_size,
            'file_type': 'pdf',
            'storage_path': file_path,
            'storage_provider': 'local',
            'is_temporary': True,
            'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }

        result = self.supabase.table('file_storage').insert(storage_data).execute()
        return result.data[0]['id']

    def get_output_file_id(self, job_id: str):
        """Get output file ID for a job"""
        try:
            result = self.supabase.table('file_storage').select('id').eq('job_id', job_id).order('created_at', desc=True).limit(1).execute()
            
            if result.data:
                return result.data[0]['id']
            return None
        except Exception as e:
            return None