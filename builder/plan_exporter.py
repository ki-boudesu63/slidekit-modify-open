"""
ContentBundle → slide_plan.json / slide_content.json エクスポーター

slide_plan.json:   builder 用（type 付き、レイアウト指定あり）
slide_content.json: slidekit-create 用（type なし、素材のみ）

レビューアプリでの確認・編集や、各スキルからの再読み込みに対応。
"""

from __future__ import annotations

import json
from pathlib import Path

from .content_bundle import ContentBundle
from .section_splitter import get_ordered_sections, section_to_label


def export_plan(bundle: ContentBundle, output_path: Path | None = None) -> str:
    """
    ContentBundle を slide_plan.json に書き出す。

    出力先: output_path が指定されなければ bundle.output_dir/slide_plan.json
    戻り値: 書き出したファイルの絶対パス
    """
    if output_path is None:
        output_path = Path(bundle.output_dir) / "slide_plan.json"

    # 既に plan_slides がある場合（PlanScanner 経由）はそのまま保存
    if bundle._plan_slides:
        plan = _plan_from_existing(bundle)
    else:
        plan = _plan_from_sections(bundle)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(output_path.resolve())


def _build_meta(bundle: ContentBundle) -> dict:
    """ContentBundle から meta 辞書を構築する"""
    return {
        "title": bundle.title,
        "authors": bundle.authors,
        "affiliation": bundle.affiliation,
        "subtitle": bundle.subtitle,
        "theme": bundle.theme,
        "date": bundle.date,
        "presentation_type": bundle.presentation_type,
        "language": bundle.language,
    }


def _plan_from_existing(bundle: ContentBundle) -> dict:
    """既存の _plan_slides をそのまま JSON 化する"""
    return {
        "meta": _build_meta(bundle),
        "slides": bundle._plan_slides,
    }


def _plan_from_sections(bundle: ContentBundle) -> dict:
    """セクション内容から slide_plan.json を自動生成する"""
    slides: list[dict] = []

    # タイトルスライド
    slides.append({"type": "title", "notes": ""})

    ordered = get_ordered_sections(bundle.sections)
    image_queue = list(bundle.images)
    table_queue = list(bundle.tables)

    # セクション区切りを入れるセクション
    divider_sections = {"methods", "results", "discussion"}

    for section_name, content in ordered:
        # セクション区切り
        if section_name in divider_sections:
            label = section_to_label(section_name, bundle.language)
            slides.append({
                "type": "section-break",
                "heading": label,
                "notes": "",
            })

        heading = section_to_label(section_name, bundle.language)
        # 本文を箇条書き形式に整形
        body = _content_to_bullets(content)

        # 結果セクション → 画像付き
        if section_name == "results" and image_queue:
            img = image_queue.pop(0)
            slides.append({
                "type": "two-column",
                "heading": heading,
                "body": body,
                "image": img.rel_path,
                "image_caption": img.caption or img.filename,
                "notes": "",
            })
        # 方法セクション → テーブル or 画像
        elif section_name == "methods":
            if table_queue:
                table = table_queue.pop(0)
                slides.append({
                    "type": "data-table",
                    "heading": heading,
                    "body": body,
                    "table_html": table.html,
                    "table_caption": table.caption,
                    "notes": "",
                })
            elif image_queue:
                img = image_queue.pop(0)
                slides.append({
                    "type": "two-column",
                    "heading": heading,
                    "body": body,
                    "image": img.rel_path,
                    "image_caption": img.caption or img.filename,
                    "notes": "",
                })
            else:
                slides.append({
                    "type": "text-only",
                    "heading": heading,
                    "body": body,
                    "notes": "",
                })
        # 画像が残っていれば 2 カラム
        elif image_queue and section_name not in ("references", "acknowledgements"):
            img = image_queue.pop(0)
            slides.append({
                "type": "two-column",
                "heading": heading,
                "body": body,
                "image": img.rel_path,
                "image_caption": img.caption or img.filename,
                "notes": "",
            })
        # テキストのみ
        else:
            slides.append({
                "type": "text-only",
                "heading": heading,
                "body": body,
                "notes": "",
            })

    # 余った画像をスライドに
    for img in image_queue:
        slides.append({
            "type": "figure-focus",
            "heading": img.caption or img.filename,
            "body": "",
            "image": img.rel_path,
            "image_caption": img.caption or img.filename,
            "notes": "",
        })

    # 余ったテーブルをスライドに
    for table in table_queue:
        slides.append({
            "type": "data-table",
            "heading": table.caption or "Data",
            "body": "",
            "table_html": table.html,
            "table_caption": table.caption,
            "notes": "",
        })

    # 結論スライド
    slides.append({"type": "conclusion", "notes": ""})

    return {
        "meta": _build_meta(bundle),
        "slides": slides,
    }


def export_content(bundle: ContentBundle, output_path: Path | None = None) -> str:
    """
    ContentBundle を slide_content.json（create 用、type なし）に書き出す。

    出力先: output_path が指定されなければ bundle.output_dir/slide_content.json
    戻り値: 書き出したファイルの絶対パス
    """
    if output_path is None:
        output_path = Path(bundle.output_dir) / "slide_content.json"

    # plan を生成してから type を除去
    if bundle._plan_slides:
        base = _plan_from_existing(bundle)
    else:
        base = _plan_from_sections(bundle)

    content_data = {
        "meta": base["meta"],
        "mode": "content",
        "slides": [],
    }

    for slide in base["slides"]:
        # title / conclusion は meta から自動生成されるのでスキップ
        if slide.get("type") in ("title", "conclusion", "section-break"):
            continue

        images = []
        if slide.get("image"):
            images.append({
                "path": slide["image"],
                "caption": slide.get("image_caption", ""),
            })

        content_data["slides"].append({
            "heading": slide.get("heading", ""),
            "body": slide.get("body", ""),
            "images": images,
            "notes": slide.get("notes", ""),
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(content_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(output_path.resolve())


def _content_to_bullets(content: str) -> str:
    """セクション本文を箇条書き形式に変換する"""
    if not content.strip():
        return ""

    lines = content.strip().split("\n")
    bullets = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 既に箇条書き形式ならそのまま
        if line.startswith(("・", "- ", "* ", "• ")):
            bullets.append(line)
        # Markdown 見出しは除外
        elif line.startswith("#"):
            continue
        # 長い段落は要約的に箇条書き化
        else:
            # 文ごとに分割して箇条書きにする
            sentences = [s.strip() for s in line.replace("。", "。\n").split("\n") if s.strip()]
            for s in sentences:
                if len(s) > 5:  # 短すぎる断片は除外
                    bullets.append(f"・{s}")

    return "\n".join(bullets)
