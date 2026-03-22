#!/usr/bin/env python3
"""
报销统计报表生成器
用法: python generate_report.py <output_dir> <invoice_data_json>

invoice_data_json 格式:
[
  {
    "file_path": "文件路径",
    "type": "taxi|train|flight|hotel|meal|other",
    "category_name": "打车票",
    "amount": 35.00,
    "date": "2024-01-15",
    "service_date": "2024-01-15",
    "merchant": "滴滴出行",
    "subtype": "滴滴出行",
    "invoice_number": "12345678",
    "is_invoice": true,
    "description": "简要描述"
  }
]
"""
import json
import sys
from pathlib import Path
from datetime import datetime

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    from openpyxl.utils import get_column_letter
except ImportError:
    print("openpyxl 未安装，正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl", "-q"])
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    from openpyxl.utils import get_column_letter


def sanitize_sheet_name(name: str) -> str:
    for char in [':', '/', '\\', '?', '*', '[', ']']:
        name = name.replace(char, '_')
    return name[:31]


def generate_report(output_dir: str, invoices: list) -> str:
    output_path = Path(output_dir)
    wb = Workbook()
    wb.remove(wb.active)

    # Styles
    header_font_white = Font(bold=True, size=11, color="FFFFFF")
    header_font = Font(bold=True, size=11)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    center_align = Alignment(horizontal='center', vertical='center')
    right_align = Alignment(horizontal='right', vertical='center')
    wrap_align = Alignment(horizontal='left', vertical='center', wrap_text=True)

    # Group by category - only invoices (is_invoice=true)
    categories = {}
    category_order = ['打车票', '火车飞机票', '住宿费', '餐费', '其他']

    for inv in invoices:
        if not inv.get('is_invoice', True):
            continue
        cat = inv.get('category_name', '其他')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(inv)

    # Create detail sheets
    sheet_info = {}
    for cat_name in category_order:
        if cat_name not in categories or not categories[cat_name]:
            continue
        items = sorted(categories[cat_name], key=lambda x: x.get('date', '') or '')
        sheet_name = sanitize_sheet_name(cat_name)
        ws = wb.create_sheet(sheet_name)

        headers = ['序号', '日期', '商家/平台', '金额（元）', '发票号码', '描述']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font_white
            cell.fill = header_fill
            cell.border = border
            cell.alignment = center_align

        for idx, inv in enumerate(items, 1):
            row = idx + 1
            ws.cell(row=row, column=1, value=idx).border = border
            ws.cell(row=row, column=1).alignment = center_align

            date_val = inv.get('service_date') or inv.get('date', '')
            ws.cell(row=row, column=2, value=date_val).border = border
            ws.cell(row=row, column=2).alignment = center_align

            merchant = inv.get('subtype') or inv.get('merchant', '')
            ws.cell(row=row, column=3, value=merchant).border = border

            cell = ws.cell(row=row, column=4, value=inv.get('amount', 0))
            cell.border = border
            cell.alignment = right_align
            cell.number_format = '#,##0.00'

            ws.cell(row=row, column=5, value=inv.get('invoice_number', '')).border = border

            ws.cell(row=row, column=6, value=inv.get('description', '')).border = border
            ws.cell(row=row, column=6).alignment = wrap_align

        # Sum row
        sum_row = len(items) + 2
        ws.cell(row=sum_row, column=3, value="合计").font = header_font
        ws.cell(row=sum_row, column=3).border = border
        sum_formula = f'=SUM(D2:D{sum_row - 1})'
        cell = ws.cell(row=sum_row, column=4, value=sum_formula)
        cell.font = header_font
        cell.border = border
        cell.alignment = right_align
        cell.number_format = '#,##0.00'
        for col in [1, 2, 5, 6]:
            ws.cell(row=sum_row, column=col, value="").border = border

        col_widths = [6, 12, 20, 12, 20, 30]
        for col, width in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

        sheet_info[cat_name] = (sheet_name, len(items))

    # Summary sheet
    ws = wb.create_sheet("汇总", 0)
    ws.merge_cells('A1:D1')
    ws['A1'] = f"报销汇总表 - {datetime.now().strftime('%Y-%m-%d')}"
    ws['A1'].font = Font(bold=True, size=16)
    ws['A1'].alignment = center_align

    headers = ['类别', '发票数量', '金额（元）', '备注']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = header_font_white
        cell.fill = header_fill
        cell.border = border
        cell.alignment = center_align

    row = 4
    count_cells = []
    amount_cells = []

    for cat_name in category_order:
        if cat_name not in sheet_info:
            continue
        sname, count = sheet_info[cat_name]
        last_data_row = count + 1

        ws.cell(row=row, column=1, value=cat_name).border = border

        count_formula = f"=COUNTA('{sname}'!A2:A{last_data_row})"
        c = ws.cell(row=row, column=2, value=count_formula)
        c.border = border
        c.alignment = center_align
        count_cells.append(f"B{row}")

        amount_formula = f"='{sname}'!D{last_data_row + 1}"
        c = ws.cell(row=row, column=3, value=amount_formula)
        c.border = border
        c.alignment = right_align
        c.number_format = '#,##0.00'
        amount_cells.append(f"C{row}")

        ws.cell(row=row, column=4, value="").border = border
        row += 1

    # Total row
    ws.cell(row=row, column=1, value="合计").font = header_font
    ws.cell(row=row, column=1).border = border

    if count_cells:
        c = ws.cell(row=row, column=2, value=f"=SUM({','.join(count_cells)})")
    else:
        c = ws.cell(row=row, column=2, value=0)
    c.font = header_font
    c.border = border
    c.alignment = center_align

    if amount_cells:
        c = ws.cell(row=row, column=3, value=f"=SUM({','.join(amount_cells)})")
    else:
        c = ws.cell(row=row, column=3, value=0)
    c.font = header_font
    c.border = border
    c.alignment = right_align
    c.number_format = '#,##0.00'

    ws.cell(row=row, column=4, value="").border = border

    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 20

    report_path = output_path / "报销统计.xlsx"
    wb.save(str(report_path))
    print(f"报表已生成: {report_path}")
    return str(report_path)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"用法: python {sys.argv[0]} <output_dir> <invoice_data.json>")
        sys.exit(1)

    output_dir = sys.argv[1]
    json_path = sys.argv[2]

    with open(json_path, 'r', encoding='utf-8') as f:
        invoices = json.load(f)

    generate_report(output_dir, invoices)
