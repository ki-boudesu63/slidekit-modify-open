"""
パターン HTML 生成関数群

SlideKit 形式（1280×720px、Tailwind CSS）の完全な HTML ドキュメントを返す。
patterns.md の DOM 構造を参照して実装。
"""

from __future__ import annotations

import re

from .themes import get_theme, get_theme_css, get_google_fonts_url
from .content_bundle import esc


# ──────────────────────────────────────────────────
# 共通ヘルパー
# ──────────────────────────────────────────────────

def _boilerplate(title: str, theme_name: str, body_html: str) -> str:
    """完全な HTML ドキュメントを生成する"""
    theme_css = get_theme_css(theme_name)
    fonts_url = get_google_fonts_url(theme_name)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8" />
    <meta content="width=device-width, initial-scale=1.0" name="viewport" />
    <title>{esc(title)}</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet" />
    <link href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.4.0/css/all.min.css" rel="stylesheet" />
    <link href="{fonts_url}" rel="stylesheet" />
    <style>
        {theme_css}
    </style>
</head>
<body>
    {body_html}
</body>
</html>"""


def _hbf_header(heading: str, theme_name: str) -> str:
    """HBF (Header-Body-Footer) パターンのヘッダー部分（Pattern 3 準拠）"""
    t = get_theme(theme_name)
    icon = t["brand_icon"]
    return f"""    <div class="px-16 pt-10 pb-4 flex justify-between items-end border-b border-gray-200 mx-16">
        <div class="flex items-center space-x-4">
            <div class="w-1.5 h-10 bg-brand-accent"></div>
            <div>
                <h1 class="text-3xl font-bold text-brand-dark tracking-tight">{esc(heading)}</h1>
            </div>
        </div>
        <div class="flex items-center space-x-2 text-brand-dark opacity-50">
            <i class="fas {icon} text-lg"></i>
        </div>
    </div>"""


def _hbf_footer(page_no: int, total: int) -> str:
    """HBF パターンのフッター"""
    return f"""    <div class="h-12 w-full flex justify-between items-center px-16 bg-white border-t border-gray-100">
        <p class="text-xs text-gray-400 tracking-wider">Confidential</p>
        <div class="flex items-center space-x-2">
            <span class="text-xs text-gray-400">Page</span>
            <span class="text-sm font-bold text-brand-accent font-accent">{page_no:02d}</span>
        </div>
    </div>"""


def _style_body_html(raw_html: str) -> str:
    """<p>, <ul>, <ol>, <li> に Tailwind クラスを追加する"""
    html = raw_html
    # <p> タグ
    html = re.sub(
        r'<p>',
        '<p class="text-sm text-gray-600 leading-relaxed mb-3">',
        html
    )
    # <ul> タグ
    html = re.sub(
        r'<ul>',
        '<ul class="space-y-2">',
        html
    )
    # <ol> タグ
    html = re.sub(
        r'<ol>',
        '<ol class="space-y-2 list-decimal list-inside">',
        html
    )
    # <li> タグ — アクセント色ドット付き
    html = re.sub(
        r'<li>(.*?)</li>',
        r'<li class="flex items-start gap-2 text-sm text-gray-600">'
        r'<span class="w-1.5 h-1.5 rounded-full bg-brand-accent mt-2 flex-shrink-0"></span>'
        r'<span>\1</span></li>',
        html
    )
    return html


def _style_table_html(raw_html: str) -> str:
    """<table> に Tailwind クラスを追加する"""
    html = raw_html
    html = html.replace(
        "<table>",
        '<table class="w-full text-xs border-collapse">'
    )
    html = html.replace(
        "<thead>",
        '<thead class="bg-brand-dark text-white">'
    )
    html = html.replace(
        "<th>",
        '<th class="px-3 py-2 text-left font-semibold">'
    )
    html = html.replace(
        "<td>",
        '<td class="px-3 py-2 border-b border-gray-100">'
    )
    html = html.replace(
        "<tr>",
        '<tr class="even:bg-gray-50">'
    )
    return html


# ──────────────────────────────────────────────────
# パターン関数
# ──────────────────────────────────────────────────

def render_cover_slide(
    title: str,
    authors: str,
    affiliation: str,
    date: str = "",
    subtitle: str = "",
    theme_name: str = "academic-blue",
) -> str:
    """タイトルスライド — Pattern 1 (Center)"""
    t = get_theme(theme_name)
    icon = t["brand_icon"]

    date_html = ""
    if date:
        date_html = f"""
                <div class="flex items-center">
                    <i class="fas fa-calendar-alt mr-2 text-brand-accent"></i>
                    <span>{esc(date)}</span>
                </div>"""

    subtitle_html = ""
    if subtitle:
        subtitle_html = f'<p class="text-lg text-gray-500 mb-2">{esc(subtitle)}</p>'

    body = f"""<div class="slide bg-white flex flex-col items-center justify-center relative">
        <div class="absolute top-10 right-10 w-64 h-64 rounded-full bg-brand-warm opacity-40 -z-10"></div>
        <div class="absolute bottom-16 left-16 w-40 h-40 rounded-full bg-brand-accent opacity-10 -z-10"></div>

        <div class="text-center z-10 relative max-w-4xl px-12">
            <div class="mb-8">
                <i class="fas {icon} text-4xl text-brand-accent"></i>
            </div>
            {subtitle_html}
            <h1 class="text-5xl font-black text-brand-dark leading-tight mb-6">{esc(title)}</h1>
            <div class="w-20 h-1 bg-brand-accent mx-auto mb-8"></div>
            <p class="text-lg text-gray-600 mb-1">{esc(authors)}</p>
            <p class="text-sm text-gray-500 mb-6">{esc(affiliation)}</p>

            <div class="flex items-center justify-center gap-8 text-sm text-gray-500">
                {date_html}
            </div>
        </div>
    </div>"""

    return _boilerplate(title, theme_name, body)


def render_section_divider(
    heading: str,
    chapter_no: int,
    theme_name: str = "academic-blue",
) -> str:
    """セクション区切り — Pattern 17 (Chapter Divider)"""
    body = f"""<div class="slide flex relative overflow-hidden">
        <div class="w-1/4 h-full bg-brand-dark flex flex-col justify-center items-center relative overflow-hidden">
            <div class="z-10 flex flex-col items-center">
                <p class="text-brand-accent text-lg font-accent uppercase mb-2" style="letter-spacing: 0.3em;">Chapter</p>
                <h2 class="font-accent font-light text-white leading-none" style="font-size: 6rem; line-height: 1;">{chapter_no:02d}</h2>
                <div class="w-12 h-1 bg-brand-accent mt-6"></div>
            </div>
        </div>
        <div class="w-3/4 h-full flex flex-col justify-center px-20 bg-white">
            <h1 class="text-5xl font-bold text-brand-dark tracking-tight leading-tight mb-4">{esc(heading)}</h1>
            <div class="w-24 h-1 bg-brand-accent"></div>
        </div>
    </div>"""

    return _boilerplate(heading, theme_name, body)


def render_text_slide(
    heading: str,
    body_html: str,
    page_no: int,
    total: int,
    theme_name: str = "academic-blue",
) -> str:
    """テキストのみ — Pattern 3 (HBF)"""
    styled = _style_body_html(body_html)
    header = _hbf_header(heading, theme_name)
    footer = _hbf_footer(page_no, total)

    body = f"""<div class="slide flex flex-col bg-white">
{header}
    <div class="flex-1 px-16 py-8">
        <div class="max-w-4xl">
            {styled}
        </div>
    </div>
{footer}
    </div>"""

    return _boilerplate(heading, theme_name, body)


def render_image_text_slide(
    heading: str,
    body_html: str,
    image_path: str,
    caption: str,
    page_no: int,
    total: int,
    theme_name: str = "academic-blue",
) -> str:
    """テキスト + 画像 — Pattern 4 (HBF + 2-Column)"""
    styled = _style_body_html(body_html)
    header = _hbf_header(heading, theme_name)
    footer = _hbf_footer(page_no, total)

    body = f"""<div class="slide flex flex-col bg-white">
{header}
    <div class="flex-1 px-16 py-6 flex gap-8">
        <div class="w-2/5 flex flex-col justify-center">
            {styled}
        </div>
        <div class="w-3/5 flex flex-col justify-center items-center">
            <img src="{esc(image_path)}" alt="{esc(caption)}" class="max-h-96 max-w-full object-contain rounded-lg shadow-sm" />
            <p class="text-xs text-gray-400 mt-2 text-center">{esc(caption)}</p>
        </div>
    </div>
{footer}
    </div>"""

    return _boilerplate(heading, theme_name, body)


def render_figure_slide(
    heading: str,
    image_path: str,
    caption: str,
    body_html: str = "",
    page_no: int = 0,
    total: int = 0,
    theme_name: str = "academic-blue",
) -> str:
    """図メイン — Pattern 30 風（図を大きく表示）"""
    header = _hbf_header(heading, theme_name)
    footer = _hbf_footer(page_no, total)

    text_section = ""
    if body_html:
        styled = _style_body_html(body_html)
        text_section = f"""
        <div class="w-2/5 flex flex-col justify-center">
            {styled}
        </div>"""
        img_width = "w-3/5"
    else:
        img_width = "w-full"

    body = f"""<div class="slide flex flex-col bg-white">
{header}
    <div class="flex-1 px-16 py-6 flex gap-8">
        {text_section}
        <div class="{img_width} flex flex-col justify-center items-center">
            <img src="{esc(image_path)}" alt="{esc(caption)}" class="max-h-96 max-w-full object-contain rounded-lg shadow-sm" />
            <p class="text-xs text-gray-400 mt-2 text-center">{esc(caption)}</p>
        </div>
    </div>
{footer}
    </div>"""

    return _boilerplate(heading, theme_name, body)


def render_table_slide(
    heading: str,
    table_html: str,
    caption: str,
    body_html: str = "",
    page_no: int = 0,
    total: int = 0,
    theme_name: str = "academic-blue",
) -> str:
    """テーブル表示 — Pattern 11 (HBF + Grid Table)"""
    styled_table = _style_table_html(table_html)
    header = _hbf_header(heading, theme_name)
    footer = _hbf_footer(page_no, total)

    text_section = ""
    if body_html:
        styled = _style_body_html(body_html)
        text_section = f'<div class="mb-4">{styled}</div>'

    body = f"""<div class="slide flex flex-col bg-white">
{header}
    <div class="flex-1 px-16 py-6 overflow-hidden">
        <p class="text-xs text-gray-500 mb-3">{esc(caption)}</p>
        <div class="overflow-auto max-h-80">
            {styled_table}
        </div>
        {text_section}
    </div>
{footer}
    </div>"""

    return _boilerplate(heading, theme_name, body)


def render_kpi_slide(
    heading: str,
    image_path: str,
    caption: str,
    body_html: str = "",
    page_no: int = 0,
    total: int = 0,
    theme_name: str = "academic-blue",
) -> str:
    """グラフ + データ — Pattern 10 (HBF + KPI Dashboard)"""
    header = _hbf_header(heading, theme_name)
    footer = _hbf_footer(page_no, total)

    text_section = ""
    if body_html:
        styled = _style_body_html(body_html)
        text_section = f"""
        <div class="w-2/5 flex flex-col justify-center">
            {styled}
        </div>"""
        img_width = "w-3/5"
    else:
        img_width = "w-full"

    body = f"""<div class="slide flex flex-col bg-white">
{header}
    <div class="flex-1 px-16 py-6 flex gap-8">
        <div class="{img_width} flex flex-col justify-center items-center">
            <img src="{esc(image_path)}" alt="{esc(caption)}" class="max-h-80 max-w-full object-contain" />
            <p class="text-xs text-gray-400 mt-2 text-center">{esc(caption)}</p>
        </div>
        {text_section}
    </div>
{footer}
    </div>"""

    return _boilerplate(heading, theme_name, body)


def render_conclusion_slide(
    title: str,
    authors: str,
    affiliation: str,
    theme_name: str = "academic-blue",
) -> str:
    """謝辞スライド — Pattern 1 (Center)"""
    t = get_theme(theme_name)
    icon = t["brand_icon"]

    body = f"""<div class="slide bg-white flex flex-col items-center justify-center relative">
        <div class="absolute top-10 left-10 w-48 h-48 rounded-full bg-brand-warm opacity-30 -z-10"></div>
        <div class="absolute bottom-10 right-10 w-32 h-32 rounded-full bg-brand-accent opacity-10 -z-10"></div>

        <div class="text-center z-10 relative">
            <i class="fas {icon} text-3xl text-brand-accent mb-6"></i>
            <h1 class="text-4xl font-black text-brand-dark mb-4">ご清聴ありがとうございました</h1>
            <div class="w-16 h-1 bg-brand-accent mx-auto mb-6"></div>
            <p class="text-xl text-gray-600 mb-2">{esc(title)}</p>
            <p class="text-sm text-gray-500">{esc(authors)}</p>
            <p class="text-sm text-gray-400">{esc(affiliation)}</p>
        </div>
    </div>"""

    return _boilerplate("謝辞", theme_name, body)
