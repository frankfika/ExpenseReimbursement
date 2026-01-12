#!/usr/bin/env python3
"""
报销助手 - 桌面版
使用 pywebview 将 Flask 应用包装成原生桌面应用
"""

import os
import sys
import webview
import threading
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def start_flask():
    """在后台线程中启动 Flask 服务器"""
    from web_app import app

    # 检查配置
    from config import is_configured, setup_wizard
    if not is_configured():
        print("\n" + "=" * 50)
        print("首次运行，需要配置 API Key")
        print("=" * 50)
        setup_wizard()

    # 禁用 Flask 的日志输出
    import flask.logging
    flask.logging.default_handler.setFormatter(logging.Formatter('%(message)s'))

    # 在随机端口上启动（避免端口冲突）
    port = 5000
    max_retries = 10
    for i in range(max_retries):
        try:
            app.run(host='127.0.0.1', port=port, debug=False, threaded=True, use_reloader=False)
            break
        except OSError as e:
            if e.errno == 48 or e.errno == 10048:  # Address already in use
                port += 1
            else:
                raise


def main():
    """启动桌面应用"""
    # 确保资源文件路径正确
    if getattr(sys, 'frozen', False):
        # 打包后的可执行文件运行
        application_path = sys._MEIPASS
    else:
        # 正常 Python 脚本运行
        application_path = str(Path(__file__).parent)

    # 在后台线程中启动 Flask
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # 等待 Flask 启动
    import time
    time.sleep(2)

    # 创建 WebView 窗口
    window = webview.create_window(
        title='报销助手',
        url='http://127.0.0.1:5000',
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        frameless=False,
        easy_drag=False,
        background_color='#FFFFFF'
    )

    # 设置应用图标（如果存在）
    icon_path = os.path.join(application_path, 'assets', 'icon.png')
    if os.path.exists(icon_path):
        # webview 会自动使用图标
        pass

    logger.info("报销助手桌面版已启动")
    webview.start(debug=False)


if __name__ == '__main__':
    main()
