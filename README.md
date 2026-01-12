# 报销助手

> 一款基于 AI 的智能发票识别与报销整理工具，让报销从此告别繁琐。

[![GitHub release](https://img.shields.io/badge/下载-桌面版-blue)](https://github.com/frankfika/ExpenseReimbursement/releases)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 它能帮你做什么？

每次出差回来，面对一堆发票是不是很头疼？打车票、火车票、酒店发票、餐饮发票混在一起，还要一张张核对金额、分类整理、制作报销单...

**报销助手**帮你自动完成这一切：

1. **扔进去** — 把所有发票扔进去
2. **等一下** — 自动识别分类
3. **拿结果** — 分类好的文件夹 + Excel 报表

---

## 核心功能

### 🔍 智能识别
- 支持图片（JPG/PNG）和 PDF 格式
- 自动识别扫描件和电子发票
- 提取发票金额、日期、商家、发票号等关键信息

### 📂 自动分类
| 类别 | 识别范围 |
|:---|:---|
| 🚕 打车票 | 滴滴、高德、美团打车、曹操、首汽、出租车 |
| 🚄 火车飞机票 | 12306、各航空公司、携程、飞猪 |
| 🏨 住宿费 | 酒店、宾馆、民宿（如家、汉庭、亚朵等） |
| 🍜 餐费 | 餐厅、外卖、美团、饿了么 |
| 📦 其他 | 未能识别的发票 |

### 🔗 智能配对
出差打车经常会有「行程单 + 发票」两份文件，系统会自动配对：
- 识别同一平台的凭证和发票
- 匹配相近日期（±1天）
- 匹配相近金额（±5%）
- 配对后放入同一文件夹，方便核对

### 📊 报表生成
自动生成 Excel 报表：
- 汇总表：各类别小计 + 总金额
- 明细表：每张发票的详细信息
- 直接用于报销，无需二次整理

---

## 快速开始

### 方式一：桌面版（推荐）

**无需安装 Python，开箱即用！**

1. 访问 [Releases 页面](https://github.com/frankfika/ExpenseReimbursement/releases)
2. 下载对应平台安装包：
   - Mac: `报销助手-Installer.dmg`
   - Windows: `报销助手.exe`
3. 安装并运行

首次运行会引导配置 API Key（只需配置一次）。

---

### 方式二：网页版

本地开发或局域网使用。

```bash
# 安装依赖
pip3 install -r requirements.txt

# 启动服务
python3 web_app.py
```

浏览器自动打开 `http://localhost:5000`

---

### 方式三：命令行版

适合脚本化、自动化场景。

```bash
# 安装依赖
pip3 install -r requirements.txt

# 运行
python3 reimbursement.py -i ./发票 -o ./报销结果
```

---

## 配置说明

### API Key

程序使用 [硅基流动](https://cloud.siliconflow.cn/i/Wd45d1wI) 提供的大模型 API（注册可获得额外额度）。

**获取步骤：**
1. 访问 https://cloud.siliconflow.cn/i/Wd45d1wI 注册/登录
2. 点击左侧菜单「API 密钥」
3. 点击「新建 API 密钥」，复制生成的密钥

首次运行程序时会提示输入 API Key，配置后自动保存，无需重复输入。

---

## 输出结果

### 文件夹结构

```
报销结果_20240114_120000/
├── 打车票/
│   ├── 2024-01-15_滴滴出行_35.00元/
│   │   ├── 01_凭证_滴滴出行_35.00元.jpg
│   │   └── 02_发票_滴滴出行_35.00元.pdf
│   └── ...
├── 火车飞机票/
├── 住宿费/
├── 餐费/
├── 其他/
└── 报销统计_20240114_120000.xlsx
```

### Excel 报表

**汇总表**

| 类别 | 数量 | 金额（元） |
|:---|:---:|---:|
| 打车票 | 4 | 186.50 |
| 火车飞机票 | 2 | 1,256.00 |
| 住宿费 | 3 | 897.00 |
| 餐费 | 2 | 156.00 |
| **合计** | **11** | **2,495.50** |

**明细表**（每个类别一个 Sheet）

| 序号 | 日期 | 商家 | 金额 | 发票号 | 类型 |
|:---:|:---|:---|---:|:---|:---:|
| 1 | 2024-01-15 | 滴滴出行 | 35.00 | 12345678 | 发票 |

---

## 常见问题

<details>
<summary><b>Q: 首次运行很慢？</b></summary>

首次运行需要下载 PaddleOCR 模型（约 100MB），请耐心等待。后续运行会很快。
</details>

<details>
<summary><b>Q: 识别不准确怎么办？</b></summary>

- 确保图片清晰、光线充足
- 扫描件比手机拍照效果更好
- 电子 PDF 发票识别率最高
</details>

<details>
<summary><b>Q: API 调用失败？</b></summary>

1. 检查 API Key 是否正确
2. 确认网络连接正常
3. 确认硅基流动账户余额充足
</details>

<details>
<summary><b>Q: 如何重新配置 API Key？</b></summary>

删除项目目录下的 `.env` 文件，重新运行程序即可重新配置。
</details>

---

## 技术栈

- **OCR**: [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 中文 OCR
- **PDF**: [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF 解析
- **AI**: [硅基流动](https://cloud.siliconflow.cn) - 大模型 API
- **Web**: [Flask](https://flask.palletsprojects.com/) - Web 框架
- **桌面**: [PyWebView](https://pywebview.flowrl.com/) - 桌面包装

---

## 许可证

MIT License
