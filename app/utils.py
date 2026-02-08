import os
import uuid
from PIL import Image


def process_upload_image(file_storage, upload_folder, size=(800, 800)):
    """处理上传的图片：压缩并裁剪为正方形"""
    if not file_storage or file_storage.filename == '':
        return ''

    ext = file_storage.filename.rsplit('.', 1)[-1].lower()
    if ext not in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
        return ''

    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(upload_folder, filename)

    img = Image.open(file_storage)
    img = img.convert('RGB')

    # 居中裁剪为正方形
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))

    img = img.resize(size, Image.LANCZOS)
    img.save(filepath, 'JPEG', quality=85)

    return filename
