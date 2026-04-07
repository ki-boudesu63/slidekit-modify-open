"""
ContentBundle → Markdown エクスポーター

Scanner で前処理した論文内容を、slidekit-create に渡せる
Markdown ファイルとして書き出す。画像は相対パスで埋め込む。
"""

from __future__ import annotations

from pathlib import Path

from .content_bundle import ContentBundle, esc
from .section_splitter import section_to_label


# セクションの標準順序
SECTION_ORDER = [
    "background", "objective", "introduction",
    "methods", "results", "discussion",
    "conclusion", "references", "acknowledgements",
]


def export_md(bundle: ContentBundle, output_path: Path | None = None) -> str:
    """
    ContentBundle を Markdown ファイルに書き出す。

    出力先: output_path が指定されなければ bundle.output_dir/content.md
    戻り値: 書き出したファイルの絶対パス
    """
    if output_path is None:
        output_path = Path(bundle.output_dir) / "content.md"

    lines: list[str] = []

    # ── メタ情報（YAML フロントマター風） ──
    lines.append("---")
    lines.append(f"title: \"{bundle.title}\"")
    lines.append(f"authors: \"{bundle.authors}\"")
    lines.append(f"affiliation: \"{bundle.affiliation}\"")
    if bundle.subtitle:
        lines.append(f"subtitle: \"{bundle.subtitle}\"")
    if bundle.date:
        lines.append(f"date: \"{bundle.date}\"")
    lines.append(f"presentation_type: {bundle.presentation_type}")
    lines.append(f"language: {bundle.language}")
    lines.append("---")
    lines.append("")

    # ── タイトル ──
    lines.append(f"# {bundle.title}")
    lines.append("")
    lines.append(f"**{bundle.authors}**")
    lines.append("")
    lines.append(f"*{bundle.affiliation}*")
    lines.append("")

    # ── セクション本文 ──
    ordered = _get_ordered(bundle.sections)

    # 画像・表・グラフのキューを作る（セクションに配分）
    image_queue = list(bundle.images)
    table_queue = list(bundle.tables)
    chart_queue = list(bundle.charts)

    for section_name, content in ordered:
        label = section_to_label(section_name, bundle.language)
        lines.append(f"## {label}")
        lines.append("")

        # 本文
        lines.append(content.strip())
        lines.append("")

        # 結果セクションに画像・グラフを配置
        if section_name == "results":
            while image_queue:
                img = image_queue.pop(0)
                caption = img.caption or img.filename
                lines.append(f"![{caption}]({img.rel_path})")
                lines.append(f"*{caption}*")
                lines.append("")
                # 1セクションに2枚まで（残りは後で）
                if len(image_queue) > 2:
                    break

            if chart_queue:
                chart = chart_queue.pop(0)
                caption = chart.caption or "Chart"
                lines.append(f"![{caption}]({chart.rel_path})")
                lines.append(f"*{caption}*")
                lines.append("")

        # 方法セクションにテーブルを配置
        elif section_name == "methods":
            if table_queue:
                table = table_queue.pop(0)
                if table.caption:
                    lines.append(f"**{table.caption}**")
                    lines.append("")
                # HTML テーブルをそのまま埋め込む（Markdown 内 HTML は有効）
                lines.append(table.html)
                lines.append("")

            # 方法の図（実験スキーム等）
            if image_queue:
                img = image_queue.pop(0)
                caption = img.caption or img.filename
                lines.append(f"![{caption}]({img.rel_path})")
                lines.append(f"*{caption}*")
                lines.append("")

        # その他のセクションに残り画像を配置
        elif image_queue and section_name not in ("references", "acknowledgements"):
            img = image_queue.pop(0)
            caption = img.caption or img.filename
            lines.append(f"![{caption}]({img.rel_path})")
            lines.append(f"*{caption}*")
            lines.append("")

    # ── 余ったリソース ──
    if image_queue or table_queue or chart_queue:
        lines.append("## 追加資料")
        lines.append("")

        for img in image_queue:
            caption = img.caption or img.filename
            lines.append(f"![{caption}]({img.rel_path})")
            lines.append(f"*{caption}*")
            lines.append("")

        for table in table_queue:
            if table.caption:
                lines.append(f"**{table.caption}**")
                lines.append("")
            lines.append(table.html)
            lines.append("")

        for chart in chart_queue:
            caption = chart.caption or "Chart"
            lines.append(f"![{caption}]({chart.rel_path})")
            lines.append(f"*{caption}*")
            lines.append("")

    # 書き出し
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return str(output_path.resolve())


def _get_ordered(sections: dict[str, str]) -> list[tuple[str, str]]:
    """セクション辞書を標準順序でソートする"""
    ordered = []
    seen = set()

    # 標準順序のセクションを先に
    for key in SECTION_ORDER:
        if key in sections:
            ordered.append((key, sections[key]))
            seen.add(key)

    # 残りのセクション（標準外のキー）
    for key, value in sections.items():
        if key not in seen:
            ordered.append((key, value))

    return ordered
