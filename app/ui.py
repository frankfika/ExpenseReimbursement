"""UI工具模块 - 共享的终端输出函数"""


class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def color_print(text: str, color: str = ""):
    """带颜色打印"""
    print(f"{color}{text}{Colors.END}")


def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")


def print_success(text: str):
    """打印成功消息"""
    color_print(f"✓ {text}", Colors.GREEN)


def print_warning(text: str):
    """打印警告消息"""
    color_print(f"⚠ {text}", Colors.YELLOW)


def print_error(text: str):
    """打印错误消息"""
    color_print(f"✗ {text}", Colors.RED)


def print_info(text: str):
    """打印信息消息"""
    color_print(f"ℹ {text}", Colors.BLUE)
