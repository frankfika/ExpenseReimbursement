"""发票分析模块 - 支持本地规则分析、API 文本分析和视觉模型分析"""
import json
import re
from dataclasses import dataclass, asdict
from typing import Optional, List
import requests

from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, VISION_MODEL, CATEGORY_KEYWORDS
from .ocr import file_to_image_content


@dataclass
class InvoiceInfo:
    """发票信息"""
    type: str  # taxi, train, flight, hotel, meal, other
    subtype: str  # 具体类型，如"滴滴出行"、"12306"等
    amount: float  # 金额
    date: str  # 开票日期 YYYY-MM-DD
    service_date: str  # 实际消费/服务日期 YYYY-MM-DD（打车时间、入住时间等）
    merchant: str  # 商家名称
    invoice_number: str  # 发票号码
    is_invoice: bool  # True=发票, False=凭证/行程单/水单
    description: str  # 简要描述
    raw_text: str  # 原始OCR文字
    file_path: str  # 文件路径
    order_number: str = ""  # 订单号（用于配对发票和水单/凭证）

    def to_dict(self) -> dict:
        return asdict(self)

    def get_actual_date(self) -> str:
        """获取实际消费日期（优先 service_date）"""
        return self.service_date or self.date or ""


def _safe_float(value, default: float = 0.0) -> float:
    """安全地将值转换为浮点数"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # 移除可能的货币符号和空格
        cleaned = value.strip().replace('¥', '').replace('￥', '').replace(',', '')
        if not cleaned:
            return default
        try:
            return float(cleaned)
        except ValueError:
            return default
    return default


def _extract_json_from_response(content: str) -> dict:
    """从 API 响应中安全提取 JSON"""
    if not content:
        raise ValueError("响应内容为空")

    # 尝试直接解析（响应可能就是纯 JSON）
    content = content.strip()
    if content.startswith('{'):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

    # 尝试提取 markdown 代码块中的 JSON
    code_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', content)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试提取任何 JSON 对象（贪婪匹配最外层的 {}）
    # 使用非贪婪匹配可能会截断嵌套对象
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        json_str = json_match.group()
        # 尝试找到正确闭合的 JSON
        brace_count = 0
        end_pos = 0
        for i, char in enumerate(json_str):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i + 1
                    break
        if end_pos > 0:
            try:
                return json.loads(json_str[:end_pos])
            except json.JSONDecodeError:
                pass

    raise ValueError(f"无法从响应中提取JSON: {content[:200]}...")


class InvoiceAnalyzer:
    """发票分析器"""

    SYSTEM_PROMPT = """你是一个专业的发票识别助手。请分析以下发票/凭证的OCR文字内容，提取关键信息。

请严格按照以下JSON格式返回，不要返回其他内容：
{
    "type": "taxi|train|flight|hotel|meal|other",
    "subtype": "具体平台或类型，如滴滴出行、12306、XX航空、XX酒店、XX餐厅等",
    "amount": 123.45,
    "date": "YYYY-MM-DD",
    "service_date": "YYYY-MM-DD",
    "merchant": "商家/公司名称",
    "invoice_number": "发票号码，如果没有则为空字符串",
    "order_number": "订单号/交易号/流水号，用于配对发票和水单，如果没有则为空字符串",
    "is_invoice": true或false,
    "description": "简要描述这是什么"
}

分类说明：
- taxi: 出租车、网约车（滴滴、高德、美团打车等）
- train: 火车票（12306、高铁、动车等）
- flight: 机票（各航空公司、机场）
- hotel: 住宿（酒店、宾馆、民宿）
- meal: 餐饮（餐厅、外卖）
- other: 其他类型

is_invoice 说明：
- true: 这是正式发票（有发票代码、发票号码、税额等）
- false: 这是行程单、收据、凭证、水单等非正式发票

日期说明（非常重要）：
- date: 开票日期（发票上的开票时间）
- service_date: 实际消费/服务日期，这是最重要的日期！
  - 打车：乘车时间、行程开始时间
  - 火车/飞机：乘车/乘机日期、出发时间
  - 酒店：入住日期
  - 餐饮：消费日期
  - 注意：发票可能是后补开的，开票日期可能晚于实际消费日期

注意：
1. 金额请提取实际支付金额，不是税额
2. 日期请转换为 YYYY-MM-DD 格式
3. service_date 比 date 更重要，请优先准确提取实际消费日期
4. 如果某字段无法识别，请合理推断或留空
5. 只返回JSON，不要有其他文字"""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.base_url = base_url or DEEPSEEK_BASE_URL

        if not self.api_key:
            raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量或传入 api_key")

    def analyze(self, ocr_text: str, file_path: str) -> InvoiceInfo:
        """
        分析发票内容

        Args:
            ocr_text: OCR 提取的文字
            file_path: 文件路径

        Returns:
            InvoiceInfo 对象
        """
        if not ocr_text.strip():
            return self._create_empty_info(file_path, "无法识别内容")

        # 调用 DeepSeek API
        try:
            result = self._call_api(ocr_text)
            return self._parse_result(result, ocr_text, file_path)
        except Exception as e:
            print(f"  [警告] 分析失败: {e}")
            return self._create_empty_info(file_path, f"分析失败: {str(e)}", ocr_text)

    def _call_api(self, ocr_text: str) -> dict:
        """调用 DeepSeek API"""
        url = f"{self.base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"请分析以下发票内容：\n\n{ocr_text}"}
            ],
            "temperature": 0.1,  # 低温度，更确定性的输出
            "max_tokens": 1000
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # 使用安全的 JSON 提取
        return _extract_json_from_response(content)

    def _parse_result(self, result: dict, ocr_text: str, file_path: str) -> InvoiceInfo:
        """解析 API 返回结果"""
        return InvoiceInfo(
            type=result.get("type", "other"),
            subtype=result.get("subtype", "未知"),
            amount=_safe_float(result.get("amount")),
            date=result.get("date", "") or "",
            service_date=result.get("service_date", "") or "",
            merchant=result.get("merchant", "") or "",
            invoice_number=result.get("invoice_number", "") or "",
            is_invoice=bool(result.get("is_invoice", True)),
            description=result.get("description", "") or "",
            raw_text=ocr_text,
            file_path=file_path,
            order_number=result.get("order_number", "") or ""
        )

    def _create_empty_info(self, file_path: str, description: str, ocr_text: str = "") -> InvoiceInfo:
        """创建空的发票信息"""
        return InvoiceInfo(
            type="other",
            subtype="未识别",
            amount=0.0,
            date="",
            service_date="",
            merchant="",
            invoice_number="",
            is_invoice=False,
            description=description,
            raw_text=ocr_text,
            file_path=file_path,
            order_number=""
        )


class VisionAnalyzer:
    """视觉模型分析器 - 直接发送图片给视觉模型分析，无需本地 OCR"""

    SYSTEM_PROMPT = """你是一个专业的发票识别助手。请仔细查看图片中的发票/凭证内容，提取关键信息。

请严格按照以下JSON格式返回，不要返回其他内容：
{
    "type": "taxi|train|flight|hotel|meal|other",
    "subtype": "具体平台或类型，如滴滴出行、12306、XX航空、XX酒店、XX餐厅等",
    "amount": 123.45,
    "date": "YYYY-MM-DD",
    "service_date": "YYYY-MM-DD",
    "merchant": "商家/公司名称",
    "invoice_number": "发票号码，如果没有则为空字符串",
    "order_number": "订单号/交易号/流水号，用于配对发票和水单，如果没有则为空字符串",
    "is_invoice": true或false,
    "description": "简要描述这是什么",
    "ocr_text": "图片中识别出的主要文字内容"
}

分类说明：
- taxi: 出租车、网约车（滴滴、高德、美团打车等）
- train: 火车票（12306、高铁、动车等）
- flight: 机票（各航空公司、机场）
- hotel: 住宿（酒店、宾馆、民宿）
- meal: 餐饮（餐厅、外卖）
- other: 其他类型

is_invoice 说明：
- true: 这是正式发票（有发票代码、发票号码、税额等）
- false: 这是行程单、收据、凭证、水单等非正式发票

日期说明（非常重要）：
- date: 开票日期（发票上的开票时间）
- service_date: 实际消费/服务日期，这是最重要的日期！
  - 打车：乘车时间、行程开始时间
  - 火车/飞机：乘车/乘机日期、出发时间
  - 酒店：入住日期
  - 餐饮：消费日期
  - 注意：发票可能是后补开的，开票日期可能晚于实际消费日期

注意：
1. 金额请提取实际支付金额，不是税额
2. 日期请转换为 YYYY-MM-DD 格式
3. service_date 比 date 更重要，请优先准确提取实际消费日期
4. ocr_text 字段请提取图片中的主要文字，供后续参考
5. 只返回JSON，不要有其他文字"""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.base_url = base_url or DEEPSEEK_BASE_URL

        if not self.api_key:
            raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量或传入 api_key")

    def analyze(self, file_path: str) -> InvoiceInfo:
        """
        使用视觉模型直接分析图片

        Args:
            file_path: 文件路径（图片或PDF）

        Returns:
            InvoiceInfo 对象
        """
        try:
            # 将文件转换为图片内容
            image_contents = file_to_image_content(file_path)
            result = self._call_vision_api(image_contents)
            return self._parse_result(result, file_path)
        except Exception as e:
            print(f"  [警告] 视觉模型分析失败: {e}")
            return self._create_empty_info(file_path, f"视觉分析失败: {str(e)}")

    def _call_vision_api(self, image_contents: List[dict]) -> dict:
        """调用视觉模型 API"""
        url = f"{self.base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 构建消息内容：系统提示 + 图片
        user_content = [{"type": "text", "text": "请分析这张发票/凭证图片："}]
        user_content.extend(image_contents)

        data = {
            "model": VISION_MODEL,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.1,
            "max_tokens": 2000
        }

        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # 使用安全的 JSON 提取
        return _extract_json_from_response(content)

    def _parse_result(self, result: dict, file_path: str) -> InvoiceInfo:
        """解析 API 返回结果"""
        return InvoiceInfo(
            type=result.get("type", "other"),
            subtype=result.get("subtype", "未知"),
            amount=_safe_float(result.get("amount")),
            date=result.get("date", "") or "",
            service_date=result.get("service_date", "") or "",
            merchant=result.get("merchant", "") or "",
            invoice_number=result.get("invoice_number", "") or "",
            is_invoice=bool(result.get("is_invoice", True)),
            description=result.get("description", "") or "",
            raw_text=result.get("ocr_text", "") or "",  # 视觉模型提取的文字
            file_path=file_path,
            order_number=result.get("order_number", "") or ""
        )

    def _create_empty_info(self, file_path: str, description: str) -> InvoiceInfo:
        """创建空的发票信息"""
        return InvoiceInfo(
            type="other",
            subtype="未识别",
            amount=0.0,
            date="",
            service_date="",
            merchant="",
            invoice_number="",
            is_invoice=False,
            description=description,
            raw_text="",
            file_path=file_path,
            order_number=""
        )


class LocalAnalyzer:
    """本地规则分析器 - 无需 API，使用关键词和正则匹配"""

    # 金额匹配模式
    AMOUNT_PATTERNS = [
        r'(?:合计|总计|实付|实收|金额|价税合计|应付|支付)[：:]*\s*[¥￥]?\s*(\d+\.?\d*)',
        r'[¥￥]\s*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*元',
        r'(?:小计|总额)[：:]*\s*(\d+\.?\d*)',
    ]

    # 日期匹配模式
    DATE_PATTERNS = [
        r'(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})[日号]?',
        r'(\d{4})(\d{2})(\d{2})',  # 20240115 格式
    ]

    # 发票号码模�式
    INVOICE_PATTERNS = [
        r'发票号码[：:]*\s*(\d+)',
        r'No[\.:]?\s*(\d+)',
        r'发票代码[：:]*\s*(\d+)',
    ]

    def analyze(self, ocr_text: str, file_path: str) -> InvoiceInfo:
        """使用本地规则分析发票"""
        if not ocr_text.strip():
            return self._create_empty_info(file_path, "无法识别内容")

        # 识别类型
        inv_type, subtype = self._detect_type(ocr_text)

        # 提取金额
        amount = self._extract_amount(ocr_text)

        # 提取日期
        date = self._extract_date(ocr_text)

        # 提取发票号码
        invoice_number = self._extract_invoice_number(ocr_text)

        # 判断是否为正式发票
        is_invoice = self._is_formal_invoice(ocr_text)

        # 提取商家名称
        merchant = self._extract_merchant(ocr_text)

        return InvoiceInfo(
            type=inv_type,
            subtype=subtype,
            amount=amount,
            date=date,
            service_date=date,  # 本地分析无法区分，使用相同日期
            merchant=merchant,
            invoice_number=invoice_number,
            is_invoice=is_invoice,
            description=f"本地识别: {subtype}",
            raw_text=ocr_text,
            file_path=file_path,
            order_number=""
        )

    def _detect_type(self, text: str) -> tuple:
        """检测发票类型"""
        text_lower = text.lower()

        for type_key, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text or keyword.lower() in text_lower:
                    type_map = {
                        'taxi': ('taxi', '打车出行'),
                        'train': ('train', '火车票'),
                        'flight': ('flight', '机票'),
                        'hotel': ('hotel', '住宿'),
                        'meal': ('meal', '餐饮'),
                    }
                    if type_key in type_map:
                        return type_map[type_key]

        return ('other', '其他')

    def _extract_amount(self, text: str) -> float:
        """提取金额"""
        for pattern in self.AMOUNT_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                # 取最大金额（通常是合计）
                amounts = [float(m) for m in matches if float(m) > 0]
                if amounts:
                    return max(amounts)
        return 0.0

    def _extract_date(self, text: str) -> str:
        """提取日期"""
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                year, month, day = match.groups()
                return f"{year}-{int(month):02d}-{int(day):02d}"
        return ""

    def _extract_invoice_number(self, text: str) -> str:
        """提取发票号码"""
        for pattern in self.INVOICE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""

    def _is_formal_invoice(self, text: str) -> bool:
        """判断是否为正式发票"""
        invoice_keywords = ['发票代码', '发票号码', '税额', '价税合计', '增值税', '电子发票']
        return any(kw in text for kw in invoice_keywords)

    def _extract_merchant(self, text: str) -> str:
        """提取商家名称"""
        # 尝试提取公司名称
        patterns = [
            r'销售方[：:]*\s*([^\n]+)',
            r'(?:名称|公司)[：:]*\s*([^\n]+?(?:公司|店|餐厅|酒店))',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()[:50]  # 限制长度
        return ""

    def _create_empty_info(self, file_path: str, description: str) -> InvoiceInfo:
        """创建空的发票信息"""
        return InvoiceInfo(
            type="other",
            subtype="未识别",
            amount=0.0,
            date="",
            service_date="",
            merchant="",
            invoice_number="",
            is_invoice=False,
            description=description,
            raw_text="",
            file_path=file_path,
            order_number=""
        )


# 全局实例（延迟初始化）
_api_analyzer = None
_local_analyzer = None
_vision_analyzer = None


def get_analyzer(api_key: str = None, use_api: bool = True) -> InvoiceAnalyzer:
    """获取 API 分析器实例"""
    global _api_analyzer
    if _api_analyzer is None:
        _api_analyzer = InvoiceAnalyzer(api_key)
    return _api_analyzer


def get_local_analyzer() -> LocalAnalyzer:
    """获取本地分析器实例"""
    global _local_analyzer
    if _local_analyzer is None:
        _local_analyzer = LocalAnalyzer()
    return _local_analyzer


def get_vision_analyzer(api_key: str = None) -> VisionAnalyzer:
    """获取视觉模型分析器实例"""
    global _vision_analyzer
    if _vision_analyzer is None:
        _vision_analyzer = VisionAnalyzer(api_key)
    return _vision_analyzer


def analyze_invoice(ocr_text: str, file_path: str, api_key: str = None, use_api: bool = True) -> InvoiceInfo:
    """
    分析发票（使用 OCR 文本）

    Args:
        ocr_text: OCR 提取的文字
        file_path: 文件路径
        api_key: API Key（可选）
        use_api: 是否使用 API（默认 True，如果有 API Key 则使用）

    Returns:
        InvoiceInfo 对象
    """
    # 决定使用哪种分析器
    actual_api_key = api_key or DEEPSEEK_API_KEY

    if use_api and actual_api_key:
        # 使用 API 分析（更精准）
        try:
            analyzer = get_analyzer(actual_api_key)
            return analyzer.analyze(ocr_text, file_path)
        except Exception as e:
            print(f"  [API 分析失败，回退到本地分析] {e}")
            # API 失败时回退到本地分析
            return get_local_analyzer().analyze(ocr_text, file_path)
    else:
        # 使用本地分析
        return get_local_analyzer().analyze(ocr_text, file_path)


def analyze_invoice_vision(file_path: str, api_key: str = None) -> InvoiceInfo:
    """
    使用视觉模型直接分析发票图片（无需本地 OCR）

    Args:
        file_path: 文件路径（图片或PDF）
        api_key: API Key（可选）

    Returns:
        InvoiceInfo 对象
    """
    actual_api_key = api_key or DEEPSEEK_API_KEY

    if not actual_api_key:
        raise ValueError("视觉模型分析需要配置 API Key")

    try:
        analyzer = get_vision_analyzer(actual_api_key)
        return analyzer.analyze(file_path)
    except Exception as e:
        print(f"  [视觉模型分析失败] {e}")
        raise
