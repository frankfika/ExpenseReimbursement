"""发票分析模块测试"""
import pytest
import json


class TestSafeFloat:
    """_safe_float 函数测试"""

    def test_none_returns_default(self):
        """测试 None 返回默认值"""
        from app.analyzer import _safe_float
        assert _safe_float(None) == 0.0
        assert _safe_float(None, 10.0) == 10.0

    def test_int_converted(self):
        """测试整数转换"""
        from app.analyzer import _safe_float
        assert _safe_float(100) == 100.0
        assert _safe_float(0) == 0.0

    def test_float_passthrough(self):
        """测试浮点数直接通过"""
        from app.analyzer import _safe_float
        assert _safe_float(35.50) == 35.50

    def test_string_conversion(self):
        """测试字符串转换"""
        from app.analyzer import _safe_float
        assert _safe_float("35.50") == 35.50
        assert _safe_float("  35.50  ") == 35.50

    def test_currency_symbols_removed(self):
        """测试货币符号被移除"""
        from app.analyzer import _safe_float
        assert _safe_float("¥35.50") == 35.50
        assert _safe_float("￥35.50") == 35.50

    def test_comma_removed(self):
        """测试逗号被移除"""
        from app.analyzer import _safe_float
        assert _safe_float("1,234.56") == 1234.56

    def test_invalid_string_returns_default(self):
        """测试无效字符串返回默认值"""
        from app.analyzer import _safe_float
        assert _safe_float("abc") == 0.0
        assert _safe_float("") == 0.0


class TestExtractJsonFromResponse:
    """_extract_json_from_response 函数测试"""

    def test_pure_json(self):
        """测试纯 JSON 响应"""
        from app.analyzer import _extract_json_from_response
        content = '{"type": "taxi", "amount": 35.50}'
        result = _extract_json_from_response(content)
        assert result["type"] == "taxi"
        assert result["amount"] == 35.50

    def test_json_in_markdown_code_block(self):
        """测试 markdown 代码块中的 JSON"""
        from app.analyzer import _extract_json_from_response
        content = '''这是一个发票分析结果：
```json
{"type": "taxi", "amount": 35.50}
```
'''
        result = _extract_json_from_response(content)
        assert result["type"] == "taxi"

    def test_json_with_surrounding_text(self):
        """测试带有周围文本的 JSON"""
        from app.analyzer import _extract_json_from_response
        content = '''分析结果如下：
{"type": "taxi", "amount": 35.50}
以上是分析结果。'''
        result = _extract_json_from_response(content)
        assert result["type"] == "taxi"

    def test_empty_content_raises(self):
        """测试空内容抛出异常"""
        from app.analyzer import _extract_json_from_response
        with pytest.raises(ValueError, match="响应内容为空"):
            _extract_json_from_response("")

    def test_no_json_raises(self):
        """测试无 JSON 时抛出异常"""
        from app.analyzer import _extract_json_from_response
        with pytest.raises(ValueError, match="无法从响应中提取JSON"):
            _extract_json_from_response("这里没有JSON内容")


class TestInvoiceInfo:
    """InvoiceInfo 数据类测试"""

    def test_to_dict(self, sample_invoice_info):
        """测试转换为字典"""
        result = sample_invoice_info.to_dict()
        assert isinstance(result, dict)
        assert result["type"] == "taxi"
        assert result["amount"] == 35.50

    def test_get_actual_date_with_service_date(self, sample_invoice_info):
        """测试获取实际日期（有 service_date）"""
        assert sample_invoice_info.get_actual_date() == "2024-01-15"

    def test_get_actual_date_fallback_to_date(self, sample_invoice_info):
        """测试获取实际日期（回退到 date）"""
        sample_invoice_info.service_date = ""
        assert sample_invoice_info.get_actual_date() == "2024-01-15"

    def test_get_actual_date_empty(self, sample_invoice_info):
        """测试获取实际日期（都为空）"""
        sample_invoice_info.service_date = ""
        sample_invoice_info.date = ""
        assert sample_invoice_info.get_actual_date() == ""


class TestLocalAnalyzer:
    """本地分析器测试"""

    def test_detect_taxi_type(self):
        """测试检测打车类型"""
        from app.analyzer import LocalAnalyzer
        analyzer = LocalAnalyzer()
        text = "滴滴出行 电子发票 金额：35.50元"
        inv_type, subtype = analyzer._detect_type(text)
        assert inv_type == "taxi"

    def test_detect_train_type(self):
        """测试检测火车票类型"""
        from app.analyzer import LocalAnalyzer
        analyzer = LocalAnalyzer()
        text = "12306 火车票 北京-上海"
        inv_type, subtype = analyzer._detect_type(text)
        assert inv_type == "train"

    def test_detect_hotel_type(self):
        """测试检测酒店类型"""
        from app.analyzer import LocalAnalyzer
        analyzer = LocalAnalyzer()
        text = "如家酒店 住宿费 入住日期：2024-01-15"
        inv_type, subtype = analyzer._detect_type(text)
        assert inv_type == "hotel"

    def test_extract_amount(self):
        """测试提取金额"""
        from app.analyzer import LocalAnalyzer
        analyzer = LocalAnalyzer()

        assert analyzer._extract_amount("金额：35.50元") == 35.50
        assert analyzer._extract_amount("合计：¥100.00") == 100.00
        assert analyzer._extract_amount("价税合计 ￥235.00") == 235.00

    def test_extract_date(self):
        """测试提取日期"""
        from app.analyzer import LocalAnalyzer
        analyzer = LocalAnalyzer()

        assert analyzer._extract_date("日期：2024年1月15日") == "2024-01-15"
        assert analyzer._extract_date("2024-01-15") == "2024-01-15"
        assert analyzer._extract_date("2024/01/15") == "2024-01-15"

    def test_is_formal_invoice(self):
        """测试判断是否为正式发票"""
        from app.analyzer import LocalAnalyzer
        analyzer = LocalAnalyzer()

        assert analyzer._is_formal_invoice("发票代码：123456 发票号码：78901234") is True
        assert analyzer._is_formal_invoice("价税合计：￥100.00") is True
        assert analyzer._is_formal_invoice("行程单 金额：35.50") is False
