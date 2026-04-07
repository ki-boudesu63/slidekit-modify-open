"""
データクラス定義（html_builder.py から移植）

ContentBundle が前処理（Scanner）と後処理（Builder）の境界。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ── 対応ファイル形式 ──

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".tiff", ".bmp"}
TABLE_EXTENSIONS = {".csv", ".xlsx", ".xls"}
CHART_EXTENSIONS = {".json"}
TEXT_EXTENSIONS  = {".txt", ".md"}
PDF_EXTENSIONS   = {".pdf"}

# ── テンプレートタイプと表示名 ──

TEMPLATE_TYPES = {
    "basic-research":    "基礎研究（17枚型）",
    "clinical-research": "臨床研究（13枚型）",
    "case-report":       "症例報告（17枚型）",
    "seminar":           "ゼミ・勉強会（10枚型）",
}

# ── デフォルト meta.json ──

DEFAULT_META = {
    "title":             "【研究タイトル】",
    "authors":           "【著者名】",
    "affiliation":       "【所属】",
    "subtitle":          "",
    "presentation_type": "basic-research",
    "output_type":       "slides",
    "theme":             "academic-blue",
    "date":              "",
    "language":          "ja",
}


# ── データクラス ──

@dataclass
class ImageEntry:
    path: str               # 絶対パス（スラッシュ区切り）
    rel_path: str           # 出力 images/ からの相対パス
    filename: str
    caption: str = ""
    width: int = 0
    height: int = 0
    aspect_ratio: float = 1.0
    image_type: str = "figure"  # "figure" | "table" | "wide_figure"


@dataclass
class TableEntry:
    html: str               # <table>...</table> HTML 文字列
    caption: str = ""
    source_file: str = ""


@dataclass
class ChartEntry:
    svg_path: str           # 生成された SVG ファイルのパス
    rel_path: str
    caption: str = ""
    source_json: str = ""


@dataclass
class ContentBundle:
    """スキャン結果を保持するデータクラス"""
    title: str = "【研究タイトル】"
    authors: str = "【著者名】"
    affiliation: str = "【所属】"
    subtitle: str = ""
    date: str = ""
    presentation_type: str = "basic-research"
    output_type: str = "slides"
    theme: str = "academic-blue"
    language: str = "ja"

    sections: dict[str, str] = field(default_factory=dict)
    images: list[ImageEntry] = field(default_factory=list)
    tables: list[TableEntry] = field(default_factory=list)
    charts: list[ChartEntry] = field(default_factory=list)

    output_dir: str = ""
    _plan_slides: list = field(default_factory=list)


# ── ユーティリティ ──

def esc(text: str) -> str:
    """HTML エスケープ"""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def slug(text: str) -> str:
    """ファイル名に使えるスラグ文字列に変換"""
    return re.sub(r'[^\w\-]', '_', str(text))[:40]


def classify_image_type(aspect: float, stem: str) -> str:
    """アスペクト比とファイル名から図の種類を推定"""
    if re.search(r'table|tbl|表', stem, re.IGNORECASE):
        return "table"
    if aspect > 2.0:
        return "wide_figure"
    if aspect < 0.6:
        return "tall_figure"
    return "figure"


def text_to_html(text: str) -> str:
    """テキスト文字列を段落分割して HTML に変換する（slide_plan.json 用）"""
    if not text:
        return ""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs_to_html(paragraphs)


def paragraphs_to_html(paragraphs: list[str]) -> str:
    """段落リストを HTML に変換。箇条書き・番号付きリストも検出する。"""
    if not paragraphs:
        return ""

    html_parts = []
    for para in paragraphs[:4]:  # SlideKit は 1280x720 なので段落数を制限
        lines = [l.strip() for l in para.split("\n") if l.strip()]
        if not lines:
            continue

        bullet_lines = [l for l in lines if re.match(r'^[・\-\*•]\s+', l)]
        number_lines = [l for l in lines if re.match(r'^\d+[.)）]\s+', l)]

        if len(bullet_lines) == len(lines):
            items = "\n".join(
                f"<li>{esc(re.sub(r'^[・\\-\\*•]\\s+', '', l))}</li>"
                for l in lines
            )
            html_parts.append(f"<ul>\n{items}\n</ul>")
        elif len(number_lines) == len(lines):
            items = "\n".join(
                f"<li>{esc(re.sub(r'^\\d+[.)）]\\s+', '', l))}</li>"
                for l in lines
            )
            html_parts.append(f"<ol>\n{items}\n</ol>")
        else:
            html_parts.append(f"<p>{esc(para)}</p>")

    return "\n".join(html_parts)


def template_label(key: str, value: str) -> str:
    """設定値を表示ラベルに変換"""
    if key == "presentation_type":
        return TEMPLATE_TYPES.get(value, value)
    return value
