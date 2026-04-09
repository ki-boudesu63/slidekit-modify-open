"""Markdown → 論文風 PDF 変換（fpdf2）"""
import os
import re
from fpdf import FPDF

BASE = os.path.dirname(os.path.abspath(__file__))
MD_PATH = os.path.join(BASE, "dummy_paper.md")
PDF_PATH = os.path.join(BASE, "dummy_paper.pdf")

with open(MD_PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

class PaperPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("NotoSerif", "I", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 5, "Yamamoto et al. - AI-Assisted Triage in ED", align="R")
            self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("NotoSerif", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"{self.page_no()}", align="C")

pdf = PaperPDF()
pdf.set_auto_page_break(auto=True, margin=20)

# フォント登録（add_page より前に行う）
pdf.add_font("NotoSerif", "", "C:/Windows/Fonts/times.ttf")
pdf.add_font("NotoSerif", "B", "C:/Windows/Fonts/timesbd.ttf")
pdf.add_font("NotoSerif", "I", "C:/Windows/Fonts/timesi.ttf")

pdf.add_page()

FONT = "NotoSerif"
img_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
bold_pattern = re.compile(r'\*\*(.+?)\*\*')

def write_text(pdf, text, size=10, style="", align="J"):
    """太字マーカーを含むテキストを書く"""
    pdf.set_font(FONT, style, size)
    parts = bold_pattern.split(text)
    for i, part in enumerate(parts):
        if not part:
            continue
        if i % 2 == 1:  # 太字部分
            pdf.set_font(FONT, "B", size)
            pdf.write(5, part)
            pdf.set_font(FONT, style, size)
        else:
            pdf.write(5, part)

in_list = False

for line in lines:
    line = line.rstrip("\n")

    # 空行
    if not line.strip():
        pdf.ln(4)
        in_list = False
        continue

    # 画像
    img_match = img_pattern.match(line)
    if img_match:
        caption = img_match.group(1)
        img_path = os.path.join(BASE, img_match.group(2))
        if os.path.exists(img_path):
            # 中央配置
            pdf.ln(4)
            img_w = 130
            x = (210 - img_w) / 2
            pdf.image(img_path, x=x, w=img_w)
            if caption:
                pdf.set_font(FONT, "I", 8)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 5, caption, align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.set_text_color(0, 0, 0)
            pdf.ln(4)
        continue

    # H1 タイトル
    if line.startswith("# ") and not line.startswith("## "):
        title = line[2:]
        pdf.set_font(FONT, "B", 15)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 7, title, align="C")
        pdf.ln(3)
        continue

    # H2 セクション
    if line.startswith("## "):
        heading = line[3:]
        pdf.ln(5)
        pdf.set_font(FONT, "B", 12)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 7, heading, new_x="LMARGIN", new_y="NEXT")
        # 下線
        pdf.set_draw_color(200, 200, 200)
        pdf.line(pdf.l_margin, pdf.get_y(), 210 - pdf.r_margin, pdf.get_y())
        pdf.ln(3)
        continue

    # H3
    if line.startswith("### "):
        heading = line[4:]
        pdf.ln(3)
        pdf.set_font(FONT, "B", 10.5)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 6, heading, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        continue

    # リスト
    if line.startswith("- "):
        item = line[2:]
        pdf.set_font(FONT, "", 10)
        pdf.set_text_color(0, 0, 0)
        x = pdf.get_x()
        pdf.cell(8, 5, chr(8226))  # bullet
        write_text(pdf, item, 10)
        pdf.ln(5)
        in_list = True
        continue

    # 通常テキスト
    pdf.set_font(FONT, "", 10)
    pdf.set_text_color(0, 0, 0)
    write_text(pdf, line, 10)
    pdf.ln(5)

pdf.output(PDF_PATH)
print(f"PDF generated: {PDF_PATH}")
print(f"Pages: {pdf.page_no()}")
