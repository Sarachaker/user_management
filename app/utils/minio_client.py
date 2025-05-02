from minio import Minio
from minio.error import S3Error
from settings.config import settings
import os


# Initialize MinIO client
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=os.environ.get("MINIO_ROOT_USER"),
    secret_key=os.environ.get("MINIO_ROOT_PASSWORD"),
    secure=settings.MINIO_USE_SSL,
)


# Ensure the bucket exists
def ensure_bucket_exists(bucket_name):
    """
    Ensures that the specified bucket exists. If not, creates it.
    
    Args:
        bucket_name (str): The name of the bucket to check or create.
    """
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' created.")
        else:
            print(f"Bucket '{bucket_name}' already exists.")
    except S3Error as exc:
        print("Error ensuring bucket existence:", exc)


# Upload profile picture
def upload_profile_picture(file_data, file_name):
    """
    Uploads a profile picture to MinIO.

    Args:
        file_data (bytes): File content to upload.
        file_name (str): Name of the file.

    Returns:
        str: URL to the uploaded file.

    Raises:
        ValueError: If the file type is unsupported.
    """
    allowed_extensions = {"jpg", "jpeg", "png", "gif"}
    file_extension = file_name.split(".")[-1].lower()

    if file_extension not in allowed_extensions:
        raise ValueError("Unsupported file type")

    try:
        minio_client.put_object(
            settings.MINIO_BUCKET_NAME,
            file_name,
            file_data,
            length=-1,  # Automatically determine content length
            part_size=10 * 1024 * 1024  # Set part size to 10 MB
        )
        print(f"File '{file_name}' successfully uploaded to bucket '{settings.MINIO_BUCKET_NAME}'.")
        return f"{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_NAME}/{file_name}"
    except S3Error as exc:
        print("Error uploading file:", exc)
        raise


# Get presigned URL for profile picture
def get_profile_picture_url(file_name):
    """
    Generates a presigned URL for a profile picture.

    Args:
        file_name (str): Name of the file.

    Returns:
        str: Presigned URL for the file.
    """
    try:
        url = minio_client.get_presigned_url('GET', settings.MINIO_BUCKET_NAME, file_name)
        print(f"Generated presigned URL for '{file_name}': {url}")
        return url
    except S3Error as exc:
        print("Error generating presigned URL:", exc)
        raise


# Main function for testing
if __name__ == "__main__":
    try:
        # Ensure 'demo' bucket exists
        ensure_bucket_exists("demo")

        # Example of uploading a file
        file_path = "./njit.jpeg"
        file_name = "njit.jpeg"

        with open(file_path, "rb") as file_data:
            upload_profile_picture(file_data, file_name)

        # Example of generating a presigned URL
        presigned_url = get_profile_picture_url(file_name)
        print("Presigned URL:", presigned_url)

    except S3Error as exc:
        print("Error occurred:", exc)