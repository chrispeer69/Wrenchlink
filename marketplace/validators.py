from pathlib import Path

from django.core.exceptions import ValidationError


MAX_DOCUMENT_SIZE = 10 * 1024 * 1024
MAX_TECHNICIAN_STORAGE = 100 * 1024 * 1024
MAX_UPLOADS_PER_HOUR = 20
ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}
ALLOWED_DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
}


def validate_private_document(upload):
    if upload.size > MAX_DOCUMENT_SIZE:
        raise ValidationError("Files must be 10 MB or smaller.")

    extension = Path(upload.name).suffix.lower().lstrip(".")
    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError("Upload a PDF, DOC, DOCX, JPG, or PNG file.")

    content_type = getattr(upload, "content_type", "")
    if content_type and content_type not in ALLOWED_DOCUMENT_MIME_TYPES:
        raise ValidationError("The file type does not match an allowed document format.")

    position = upload.tell()
    header = upload.read(8)
    upload.seek(position)
    signatures = {
        "pdf": (b"%PDF-",),
        "png": (b"\x89PNG\r\n\x1a\n",),
        "jpg": (b"\xff\xd8\xff",),
        "jpeg": (b"\xff\xd8\xff",),
        "doc": (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",),
        "docx": (b"PK\x03\x04",),
    }
    if not any(header.startswith(signature) for signature in signatures[extension]):
        raise ValidationError("The file contents do not match its extension.")
