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


# ──────────────────────────────────────────────────
# ポスター生成
# ──────────────────────────────────────────────────

# ポスターサイズ定義
POSTER_SIZES = {
    "a0": {"width": "841mm", "height": "1189mm", "cols": 3, "title": "text-4xl", "body": "text-sm", "pad": "p-8"},
    "a1": {"width": "594mm", "height": "841mm",  "cols": 2, "title": "text-3xl", "body": "text-xs", "pad": "p-6"},
}

# セクション→カラム割り当て
COLUMN_MAP_3 = {
    0: ["background", "objective", "introduction", "methods"],
    1: ["results"],
    2: ["discussion", "conclusion", "references", "acknowledgements"],
}
COLUMN_MAP_2 = {
    0: ["background", "objective", "introduction", "methods"],
    1: ["results", "discussion", "conclusion"],
}


def _poster_boilerplate(title: str, theme_name: str, size: str, body_html: str) -> str:
    """ポスター用の完全な HTML ドキュメントを生成する"""
    from .themes import get_theme_css, get_google_fonts_url
    theme_css = get_theme_css(theme_name)
    fonts_url = get_google_fonts_url(theme_name)
    s = POSTER_SIZES.get(size, POSTER_SIZES["a0"])

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
        @page {{ size: {s["width"]} {s["height"]}; margin: 0; }}
        html, body {{ margin: 0; padding: 0; background: #e0e0e0; }}
        .poster {{ width: {s["width"]}; min-height: {s["height"]}; margin: 20px auto; box-shadow: 0 4px 32px rgba(0,0,0,0.2); }}
        @media print {{
            html, body {{ background: none; }}
            .poster {{ margin: 0; box-shadow: none; }}
            .no-print {{ display: none !important; }}
        }}
    </style>
</head>
<body>
    <button class="no-print" onclick="window.print()" style="position:fixed;bottom:20px;right:20px;z-index:9999;background:#333;color:#fff;border:none;border-radius:8px;padding:10px 18px;font-size:14px;cursor:pointer;">PDF 保存</button>
    {body_html}
</body>
</html>"""


def _poster_section(heading: str, body_html: str, media_html: str = "") -> str:
    """ポスターのセクションブロック"""
    styled = _style_body_html(body_html) if body_html else ""
    return f"""        <div class="mb-6">
            <h2 class="text-lg font-bold text-white bg-brand-accent px-4 py-2 rounded-t-lg">{esc(heading)}</h2>
            <div class="bg-white border border-gray-200 rounded-b-lg px-4 py-3">
                {styled}
                {media_html}
            </div>
        </div>"""


def render_poster(
    bundle,
    size: str = "a0",
    theme_name: str = "academic-blue",
) -> str:
    """学会ポスターを生成する（A0: 3カラム / A1: 2カラム）"""
    from .content_bundle import ContentBundle, ImageEntry, ChartEntry, TableEntry, text_to_html
    from .section_splitter import get_ordered_sections, section_to_label

    s = POSTER_SIZES.get(size, POSTER_SIZES["a0"])
    cols = s["cols"]
    col_map = COLUMN_MAP_3 if cols == 3 else COLUMN_MAP_2
    t = get_theme(theme_name)

    # セクションをカラムに振り分け
    ordered = get_ordered_sections(bundle.sections)
    columns: list[list[tuple[str, str]]] = [[] for _ in range(cols)]

    for section_name, content in ordered:
        placed = False
        for col_idx, allowed in col_map.items():
            if section_name in allowed:
                columns[col_idx].append((section_name, content))
                placed = True
                break
        if not placed:
            # 未分類のセクションは最後のカラムに
            columns[-1].append((section_name, content))

    # リソースキュー
    image_queue = list(bundle.images)
    chart_queue = list(bundle.charts)
    table_queue = list(bundle.tables)

    # カラム HTML 生成
    cols_html = ""
    for col_idx in range(cols):
        sections_html = ""
        for section_name, content in columns[col_idx]:
            heading = section_to_label(section_name, bundle.language)
            body = text_to_html(content)

            # メディア配置
            media = ""
            if section_name == "results" and image_queue:
                # 結果セクションに画像を最大2枚配置
                for _ in range(min(2, len(image_queue))):
                    img = image_queue.pop(0)
                    media += f"""<figure class="my-3 text-center">
                    <img src="{esc(img.rel_path)}" alt="{esc(img.caption)}" class="max-w-full rounded shadow-sm mx-auto" style="max-height: 200mm;" />
                    <figcaption class="text-xs text-gray-500 mt-1">{esc(img.caption)}</figcaption>
                </figure>\n"""
                if chart_queue:
                    chart = chart_queue.pop(0)
                    media += f"""<figure class="my-3 text-center">
                    <img src="{esc(chart.rel_path)}" alt="{esc(chart.caption)}" class="max-w-full mx-auto" />
                    <figcaption class="text-xs text-gray-500 mt-1">{esc(chart.caption)}</figcaption>
                </figure>\n"""
            elif section_name == "methods" and table_queue:
                table = table_queue.pop(0)
                styled_table = _style_table_html(table.html)
                media += f"""<div class="my-3 overflow-auto">
                    <p class="text-xs text-gray-500 mb-1">{esc(table.caption)}</p>
                    {styled_table}
                </div>\n"""
                if image_queue:
                    img = image_queue.pop(0)
                    media += f"""<figure class="my-3 text-center">
                    <img src="{esc(img.rel_path)}" alt="{esc(img.caption)}" class="max-w-full rounded shadow-sm mx-auto" style="max-height: 150mm;" />
                    <figcaption class="text-xs text-gray-500 mt-1">{esc(img.caption)}</figcaption>
                </figure>\n"""
            elif image_queue and section_name not in ("references", "acknowledgements"):
                img = image_queue.pop(0)
                media += f"""<figure class="my-3 text-center">
                    <img src="{esc(img.rel_path)}" alt="{esc(img.caption)}" class="max-w-full rounded shadow-sm mx-auto" style="max-height: 150mm;" />
                    <figcaption class="text-xs text-gray-500 mt-1">{esc(img.caption)}</figcaption>
                </figure>\n"""

            sections_html += _poster_section(heading, body, media)

        cols_html += f"""    <div class="flex flex-col">\n{sections_html}    </div>\n"""

    # 余ったリソース → 最終カラムに追加セクション
    extra_media = ""
    for img in image_queue:
        extra_media += f"""<figure class="my-3 text-center">
            <img src="{esc(img.rel_path)}" alt="{esc(img.caption)}" class="max-w-full rounded shadow-sm mx-auto" style="max-height: 150mm;" />
            <figcaption class="text-xs text-gray-500 mt-1">{esc(img.caption)}</figcaption>
        </figure>\n"""
    for chart in chart_queue:
        extra_media += f"""<figure class="my-3 text-center">
            <img src="{esc(chart.rel_path)}" alt="{esc(chart.caption)}" class="max-w-full mx-auto" />
            <figcaption class="text-xs text-gray-500 mt-1">{esc(chart.caption)}</figcaption>
        </figure>\n"""
    for table in table_queue:
        styled_table = _style_table_html(table.html)
        extra_media += f"""<div class="my-3 overflow-auto">
            <p class="text-xs text-gray-500 mb-1">{esc(table.caption)}</p>
            {styled_table}
        </div>\n"""

    if extra_media:
        cols_html = cols_html.rstrip()
        # 最終カラムの閉じタグ前に追加
        extra_section = _poster_section("追加資料", "", extra_media)
        # 最後のカラムに挿入
        last_close = cols_html.rfind("    </div>")
        if last_close >= 0:
            cols_html = cols_html[:last_close] + extra_section + "\n    </div>\n"

    # ヘッダー
    date_html = f'<p class="text-sm opacity-60 mt-2">{esc(bundle.date)}</p>' if bundle.date else ""
    subtitle_html = f'<p class="{s["body"]} opacity-75 mt-1">{esc(bundle.subtitle)}</p>' if bundle.subtitle else ""

    header_html = f"""    <div class="bg-brand-dark text-white px-12 py-10">
        <h1 class="{s["title"]} font-black leading-tight mb-3">{esc(bundle.title)}</h1>
        <p class="text-lg opacity-90">{esc(bundle.authors)}</p>
        <p class="{s["body"]} opacity-75">{esc(bundle.affiliation)}</p>
        {subtitle_html}
        {date_html}
    </div>"""

    # フッター
    footer_html = f"""    <div class="border-t-2 border-brand-accent px-12 py-6 grid grid-cols-3 gap-8 items-start">
        <div>
            <h3 class="text-sm font-bold text-brand-accent mb-1">参考文献</h3>
            <p class="text-xs text-gray-500">【参考文献をここに記載】</p>
        </div>
        <div class="text-center">
            <p class="text-xs text-gray-400">QR コード</p>
        </div>
        <div class="text-right">
            <h3 class="text-sm font-bold text-brand-accent mb-1">連絡先</h3>
            <p class="text-xs text-gray-600">{esc(bundle.authors)}</p>
            <p class="text-xs text-gray-500">{esc(bundle.affiliation)}</p>
        </div>
    </div>"""

    # 組み立て
    body = f"""<div class="poster bg-white flex flex-col">
{header_html}
    <div class="flex-1 grid grid-cols-{cols} gap-6 {s['pad']}">
{cols_html}    </div>
{footer_html}
</div>"""

    return _poster_boilerplate(bundle.title, theme_name, size, body)
