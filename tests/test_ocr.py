"""Tests for app/ocr.py"""
import base64
import io
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from app.ocr import (
    OCRHandler,
    file_to_image_content,
    get_image_mime_type,
    image_to_base64,
    is_supported_file,
    ocr_handler,
    pdf_to_images,
)


class TestImageToBase64:
    """测试图片转 base64"""

    def test_jpeg_conversion(self, tmp_path):
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (100, 100), color="red")
        img.save(img_path, "JPEG")

        result = image_to_base64(str(img_path))
        assert isinstance(result, str)
        # 验证是有效的 base64
        decoded = base64.b64decode(result)
        assert decoded[:3] == b"\xff\xd8\xff"  # JPEG magic number

    def test_png_with_alpha(self, tmp_path):
        """RGBA 图片应转换为 RGB"""
        img_path = tmp_path / "test.png"
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        img.save(img_path, "PNG")

        result = image_to_base64(str(img_path))
        decoded = base64.b64decode(result)
        assert decoded[:3] == b"\xff\xd8\xff"  # 转换为 JPEG

    def test_large_image_resized(self, tmp_path):
        """大图片应该被缩放"""
        img_path = tmp_path / "large.jpg"
        img = Image.new("RGB", (3000, 3000), color="blue")
        img.save(img_path, "JPEG")

        result = image_to_base64(str(img_path), max_size=(1920, 1920))
        # 验证 base64 解码后尺寸正确
        decoded = base64.b64decode(result)
        loaded = Image.open(io.BytesIO(decoded))
        assert loaded.width <= 1920
        assert loaded.height <= 1920

    def test_small_image_not_resized(self, tmp_path):
        """小图片不应该被缩放"""
        img_path = tmp_path / "small.jpg"
        img = Image.new("RGB", (100, 100), color="green")
        img.save(img_path, "JPEG")

        result = image_to_base64(str(img_path), max_size=(1920, 1920))
        decoded = base64.b64decode(result)
        loaded = Image.open(io.BytesIO(decoded))
        assert loaded.width == 100
        assert loaded.height == 100


class TestGetImageMimeType:
    """测试获取图片 MIME 类型"""

    def test_jpg(self):
        assert get_image_mime_type("photo.jpg") == "image/jpeg"

    def test_jpeg(self):
        assert get_image_mime_type("photo.jpeg") == "image/jpeg"

    def test_png(self):
        assert get_image_mime_type("image.png") == "image/png"

    def test_webp(self):
        assert get_image_mime_type("image.webp") == "image/webp"

    def test_unknown_defaults_to_jpeg(self):
        assert get_image_mime_type("image.unknown") == "image/jpeg"

    def test_case_insensitive(self):
        assert get_image_mime_type("photo.JPG") == "image/jpeg"
        assert get_image_mime_type("photo.Jpeg") == "image/jpeg"


class TestOCRHandler:
    """测试 OCR 处理器"""

    def test_initial_state(self):
        handler = OCRHandler()
        assert handler._initialized is False
        assert handler._ocr is None

    def test_is_supported_file_image(self):
        handler = OCRHandler()
        assert handler.is_supported_file("test.jpg") is True
        assert handler.is_supported_file("test.png") is True

    def test_is_supported_file_pdf(self):
        handler = OCRHandler()
        assert handler.is_supported_file("test.pdf") is True

    def test_is_supported_file_unsupported(self):
        handler = OCRHandler()
        assert handler.is_supported_file("test.txt") is False
        assert handler.is_supported_file("test.docx") is False

    def test_extract_text_unsupported_format(self):
        handler = OCRHandler()
        # 直接设置 _ocr 避免初始化
        handler._ocr = MagicMock()
        handler._initialized = True
        with pytest.raises(ValueError, match="不支持的文件格式"):
            handler.extract_text("test.txt")

    def test_extract_text_image_ocr_none(self):
        """OCR 不可用时返回空字符串"""
        handler = OCRHandler()
        handler._ocr = None
        handler._initialized = True
        result = handler._extract_from_image("test.jpg")
        assert result == ""

    def test_extract_text_image_with_ocr(self):
        """OCR 可用时提取文字"""
        handler = OCRHandler()
        mock_ocr = MagicMock()
        mock_ocr.ocr.return_value = [[
            [None, ["Hello World", 0.99]],
            [None, ["Second line", 0.95]],
        ]]
        handler._ocr = mock_ocr
        handler._initialized = True

        result = handler._extract_from_image("test.jpg")
        assert "Hello World" in result
        assert "Second line" in result
        mock_ocr.ocr.assert_called_once()

    def test_extract_text_pdf_with_text(self):
        """PDF 有文字时直接提取"""
        handler = OCRHandler()
        handler._ocr = None
        handler._initialized = True

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            # 创建一个最小化的有效 PDF
            pdf_content = (
                b"%PDF-1.4\n"
                b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
                b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
                b"3 0 obj\n"
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n"
                b"   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n"
                b"endobj\n"
                b"4 0 obj\n"
                b"<< /Length 44 >>\nstream\n"
                b"BT /F1 12 Tf 100 700 Td (Hello PDF) Tj ET\n"
                b"endstream\nendobj\n"
                b"5 0 obj\n"
                b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n"
                b"endobj\n"
                b"xref\n0 6\n0000000000 65535 f\n"
                b"0000000009 00000 n\n"
                b"0000000058 00000 n\n"
                b"0000000115 00000 n\n"
                b"0000000266 00000 n\n"
                b"0000000360 00000 n\n"
                b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
                b"startxref\n441\n%%EOF\n"
            )
            f.write(pdf_content)
            pdf_path = f.name

        try:
            result = handler.extract_text(pdf_path)
            assert "Hello PDF" in result
        finally:
            os.unlink(pdf_path)

    def test_extract_text_empty_result(self):
        """OCR 返回空结果"""
        handler = OCRHandler()
        mock_ocr = MagicMock()
        mock_ocr.ocr.return_value = [[]]
        handler._ocr = mock_ocr
        handler._initialized = True

        result = handler._extract_from_image("test.jpg")
        assert result == ""

    def test_extract_text_none_result(self):
        """OCR 返回 None"""
        handler = OCRHandler()
        mock_ocr = MagicMock()
        mock_ocr.ocr.return_value = None
        handler._ocr = mock_ocr
        handler._initialized = True

        result = handler._extract_from_image("test.jpg")
        assert result == ""


class TestPdfToImages:
    """测试 PDF 转图片"""

    def test_pdf_to_images(self):
        """将有效 PDF 转换为图片"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_content = (
                b"%PDF-1.4\n"
                b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
                b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
                b"3 0 obj\n"
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>\n"
                b"endobj\n"
                b"xref\n0 4\n0000000000 65535 f\n"
                b"0000000009 00000 n\n"
                b"0000000058 00000 n\n"
                b"0000000115 00000 n\n"
                b"trailer\n<< /Size 4 /Root 1 0 R >>\n"
                b"startxref\n194\n%%EOF\n"
            )
            f.write(pdf_content)
            pdf_path = f.name

        try:
            images = pdf_to_images(pdf_path)
            assert len(images) == 1
            assert images[0]["type"] == "image_url"
            assert "data:image/jpeg;base64," in images[0]["image_url"]["url"]
        finally:
            os.unlink(pdf_path)


class TestFileToImageContent:
    """测试文件转图片内容"""

    def test_pdf_file(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_content = (
                b"%PDF-1.4\n"
                b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
                b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
                b"3 0 obj\n"
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>\n"
                b"endobj\n"
                b"xref\n0 4\n0000000000 65535 f\n"
                b"0000000009 00000 n\n"
                b"0000000058 00000 n\n"
                b"0000000115 00000 n\n"
                b"trailer\n<< /Size 4 /Root 1 0 R >>\n"
                b"startxref\n194\n%%EOF\n"
            )
            f.write(pdf_content)
            pdf_path = f.name

        try:
            result = file_to_image_content(pdf_path)
            assert isinstance(result, list)
            assert len(result) == 1
        finally:
            os.unlink(pdf_path)

    def test_image_file(self, tmp_path):
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(img_path, "JPEG")

        result = file_to_image_content(str(img_path))
        assert isinstance(result, list)
        assert len(result) == 1
        assert "data:image/jpeg;base64," in result[0]["image_url"]["url"]

    def test_unsupported_file(self):
        with pytest.raises(ValueError, match="不支持的文件格式"):
            file_to_image_content("test.txt")


class TestModuleFunctions:
    """测试模块级便捷函数"""

    def test_extract_text_from_file_with_mock(self):
        with patch.object(ocr_handler, "extract_text", return_value="test text") as mock_extract:
            from app.ocr import extract_text_from_file
            result = extract_text_from_file("test.jpg")
            assert result == "test text"
            mock_extract.assert_called_once_with("test.jpg")

    def test_is_supported_file_module(self):
        assert is_supported_file("test.jpg") is True
        assert is_supported_file("test.pdf") is True
        assert is_supported_file("test.txt") is False
