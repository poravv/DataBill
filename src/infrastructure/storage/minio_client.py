import os
import mimetypes
from datetime import datetime
from minio import Minio
from minio.error import S3Error

class MinioClient:
    def __init__(self):
        try:
            self.secure = os.getenv('MINIO_SECURE', 'False').lower() == 'true'
            self.endpoint = os.getenv('MINIO_ENDPOINT')
            self.bucket = os.getenv('MINIO_BUCKET')
            self.external_endpoint = os.getenv('MINIO_EXTERNAL_ENDPOINT', self.endpoint)
            
            self.client = Minio(
                self.endpoint,
                access_key=os.getenv('MINIO_ACCESS_KEY'),
                secret_key=os.getenv('MINIO_SECRET_KEY'),
                secure=self.secure
            )
            self._ensure_bucket_exists()
            self.is_connected = True
        except Exception as e:
            print(f"Warning: Could not initialize Minio client: {e}")
            self.is_connected = False

    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            print(f"Error checking/creating bucket: {e}")

    def get_direct_url(self, object_name):
        """Generate a direct URL to the object"""
        protocol = 'https' if self.secure else 'http'
        # Usar el endpoint externo si está configurado
        return f"{protocol}://{self.external_endpoint}/{self.bucket}/{object_name}"

    def upload_file(self, file_path, object_name=None):
        if not self.is_connected:
            return None
            
        if object_name is None:
            # Si no se proporciona nombre, generar uno con timestamp
            ext = os.path.splitext(file_path)[1]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            object_name = f"invoice_{timestamp}{ext}"

        try:
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return None

            # Detectar el tipo de contenido
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                # Si no se puede detectar, intentar determinar por la extensión
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.jpg', '.jpeg']:
                    content_type = 'image/jpeg'
                elif ext == '.png':
                    content_type = 'image/png'
                else:
                    content_type = 'application/octet-stream'

            print(f"Uploading file {file_path} to {self.bucket}/{object_name}")
            self.client.fput_object(
                self.bucket, 
                object_name, 
                file_path,
                content_type=content_type
            )
            
            direct_url = self.get_direct_url(object_name)
            print(f"File uploaded successfully. URL: {direct_url}")
            
            return {
                'bucket': self.bucket,
                'object_name': object_name,
                'endpoint': os.getenv('MINIO_ENDPOINT'),
                'secure': self.secure,  # Usar el atributo de clase
                'content_type': content_type,
                'direct_url': direct_url
            }
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            return None

    def get_file_url(self, object_name):
        """Get file URL, preferring direct URL over presigned URL"""
        try:
            # First try to use direct URL
            return self.get_direct_url(object_name)
        except Exception as e:
            print(f"Falling back to presigned URL: {e}")
            try:
                # Fallback to presigned URL if needed
                stat = self.client.stat_object(self.bucket, object_name)
                return self.client.presigned_get_object(
                    self.bucket, 
                    object_name,
                    response_headers={
                        'response-content-type': stat.content_type
                    }
                )
            except S3Error as e:
                print(f"Error getting file URL: {e}")
                return None
