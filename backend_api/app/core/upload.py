import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from app.core.config import settings

# IN PRODUCTION: Add these to your .env file and config.py
# CLOUDINARY_CLOUD_NAME = "your_cloud_name"
# CLOUDINARY_API_KEY = "your_api_key"
# CLOUDINARY_API_SECRET = "your_api_secret"

cloudinary.config(secure=True)

async def upload_image_to_cloud(file: UploadFile, folder: str = "riftdrop") -> str:
    """Uploads an image file to Cloudinary and returns the secure URL."""
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, and WEBP are allowed.")
    
    # Validate file size (e.g., max 5MB)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0) # Reset cursor
    
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")

    if not all([settings.CLOUDINARY_CLOUD_NAME, settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET]):
        raise HTTPException(status_code=503, detail="Image uploads are not configured")
    try:
        # Read the file into memory and upload
        contents = await file.read()
        cloudinary.config(cloud_name=settings.CLOUDINARY_CLOUD_NAME, api_key=settings.CLOUDINARY_API_KEY, api_secret=settings.CLOUDINARY_API_SECRET, secure=True)
        response = cloudinary.uploader.upload(
            contents, 
            folder=folder,
            resource_type="image"
        )
        return response.get("secure_url")
    except Exception as e:
        print(f"Cloudinary Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload image to the cloud.")
