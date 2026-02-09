"""OCR 处理模块 - 支持本地OCR和API视觉模型"""
import os
import base64
import tempfile
from pathlib import Path
from typing import Optional
import fitz  # PyMuPDF
from PIL import Image
import io

from .config import SUPPORTED_IMAGE_FORMATS, SUPPORTED_PDF_FORMAT


def image_to_base64(image_path: str) -> str:
    """将图片转换为 base64 编码"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_image_mime_type(file_path: str) -> str:
    """获取图片的 MIME 类型"""
    suffix = Path(file_path).suffix.lower()
    mime_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
        '.webp': 'image/webp',
    }
    return mime_map.get(suffix, 'image/jpeg')


class OCRHandler:
    """OCR 处理器 - 使用本地 PaddleOCR"""

    def __init__(self):
        self._ocr = None
        self._initialized = False

    @property
    def ocr(self):
        """延迟加载 PaddleOCR（首次使用时才加载，避免启动慢）"""
        if not self._initialized:
            self._initialized = True
            try:
                from paddleocr import PaddleOCR
                # 使用中英文模型，禁用GPU（更通用）
                self._ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False, show_log=False)
            except ImportError:
                print("[警告] PaddleOCR 未安装，将使用 API 视觉模型")
                self._ocr = None
            except Exception as e:
                print(f"[警告] PaddleOCR 初始化失败: {e}，将使用 API 视觉模型")
                self._ocr = None
        return self._ocr

    def extract_text(self, file_path: str) -> str:
        """
        从文件中提取文字

        Args:
            file_path: 文件路径（图片或PDF）

        Returns:
            提取的文字内容
        """
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()

        if suffix in SUPPORTED_IMAGE_FORMATS:
            return self._extract_from_image(str(file_path))
        elif suffix == SUPPORTED_PDF_FORMAT:
            return self._extract_from_pdf(str(file_path))
        else:
            raise ValueError(f"不支持的文件格式: {suffix}")

    def _extract_from_image(self, image_path: str) -> str:
        """从图片提取文字"""
        if self.ocr is None:
            # PaddleOCR 不可用，返回空字符串（后续会用视觉模型）
            return ""

        result = self.ocr.ocr(image_path, cls=True)

        if not result or not result[0]:
            return ""

        # 提取所有识别的文字
        texts = []
        for line in result[0]:
            if line and len(line) >= 2:
                text = line[1][0]  # 获取识别的文字
                texts.append(text)

        return "\n".join(texts)

    def _extract_from_pdf(self, pdf_path: str) -> str:
        """从 PDF 提取文字"""
        texts = []

        # 打开 PDF
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]

            # 首先尝试直接提取文字（电子 PDF）
            text = page.get_text()

            if text.strip():
                texts.append(text)
            elif self.ocr is not None:
                # 如果没有文字且有 OCR，说明是扫描件，用 OCR
                # 将页面转为图片
                pix = page.get_pixmap(dpi=200)
                img_data = pix.tobytes("png")

                # 使用 OCR 识别
                img = Image.open(io.BytesIO(img_data))
                # 使用 tempfile 创建临时文件，确保自动清理
                temp_file = None
                try:
                    temp_file = tempfile.NamedTemporaryFile(
                        suffix='.png', prefix=f'pdf_page_{page_num}_', delete=False
                    )
                    temp_path = temp_file.name
                    temp_file.close()
                    img.save(temp_path)

                    ocr_text = self._extract_from_image(temp_path)
                    if ocr_text:
                        texts.append(ocr_text)
                finally:
                    # 确保清理临时文件
                    if temp_file and os.path.exists(temp_path):
                        os.remove(temp_path)

        doc.close()
        return "\n".join(texts)

    def is_supported_file(self, file_path: str) -> bool:
        """检查文件是否支持"""
        suffix = Path(file_path).suffix.lower()
        return suffix in SUPPORTED_IMAGE_FORMATS or suffix == SUPPORTED_PDF_FORMAT


def pdf_to_images(pdf_path: str) -> list:
    """将 PDF 转换为图片列表（用于视觉模型）"""
    images = []
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)  # 150 DPI 足够识别且不会太大
        img_data = pix.tobytes("png")

        # 转换为 base64
        img_base64 = base64.b64encode(img_data).decode("utf-8")
        images.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{img_base64}"
            }
        })

    doc.close()
    return images


def file_to_image_content(file_path: str) -> list:
    """将文件转换为视觉模型可用的图片内容"""
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return pdf_to_images(str(file_path))
    elif suffix in SUPPORTED_IMAGE_FORMATS:
        img_base64 = image_to_base64(str(file_path))
        mime_type = get_image_mime_type(str(file_path))
        return [{
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{img_base64}"
            }
        }]
    else:
        raise ValueError(f"不支持的文件格式: {suffix}")


# 全局实例
ocr_handler = OCRHandler()


def extract_text_from_file(file_path: str) -> str:
    """便捷函数：从文件提取文字"""
    return ocr_handler.extract_text(file_path)


def is_supported_file(file_path: str) -> bool:
    """便捷函数：检查文件是否支持"""
    return ocr_handler.is_supported_file(file_path)
