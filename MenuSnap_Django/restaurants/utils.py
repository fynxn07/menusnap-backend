from io import BytesIO

import qrcode
from django.core.files.base import ContentFile


def generate_qr_code(url: str):
    qr = qrcode.make(url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue())
