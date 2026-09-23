import os
import shutil
import uuid
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename

# Base directory for uploads
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_ORG_DIR = os.path.join(BASE_DIR, "static", "uploads", "org")
UPLOAD_THUMB_DIR = os.path.join(BASE_DIR, "static", "uploads", "thumb")

# Ensure upload directories exist
os.makedirs(UPLOAD_ORG_DIR, exist_ok=True)
os.makedirs(UPLOAD_THUMB_DIR, exist_ok=True)

ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed(name):
    return "." in name and name.rsplit(".", 1)[-1].lower() in ALLOWED_EXT


allowed_file = allowed


def save_profile_image(file):
    if not file or not file.filename or not allowed(file.filename):
        return None

    # Ensure directories exist
    os.makedirs(UPLOAD_ORG_DIR, exist_ok=True)
    os.makedirs(UPLOAD_THUMB_DIR, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1].lower()
    raw_name = secure_filename(file.filename)
    unique_prefix = uuid.uuid4().hex[:12]

    if raw_name:
        filename = f"{unique_prefix}_{raw_name}"
    else:
        filename = f"{unique_prefix}.{ext}"

    org_path = os.path.join(UPLOAD_ORG_DIR, filename)
    thumb_path = os.path.join(UPLOAD_THUMB_DIR, filename)

    # 1. Save original image (100% full quality)
    file.save(org_path)

    # 2. Create thumbnail image (reduced ~80% size / quality compression)
    try:
        with Image.open(org_path) as image:
            # Handle orientation from EXIF metadata
            image = ImageOps.exif_transpose(image)

            width, height = image.size
            new_width = max(1, int(width * 0.2))
            new_height = max(1, int(height * 0.2))

            thumb_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert non-RGB mode (RGBA, LA, P, etc.) to RGB for JPEG format
            if ext in ("jpg", "jpeg") and thumb_image.mode != "RGB":
                thumb_image = thumb_image.convert("RGB")

            if ext in ("jpg", "jpeg"):
                thumb_image.save(thumb_path, quality=40, optimize=True)
            else:
                thumb_image.save(thumb_path, optimize=True)
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        if not os.path.exists(thumb_path):
            shutil.copyfile(org_path, thumb_path)

    return filename