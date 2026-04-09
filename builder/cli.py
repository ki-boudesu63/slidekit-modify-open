"""
CLI エントリポイント

使い方:
    python -m builder.cli paper.pdf
    python -m builder.cli ./input_folder/
    python -m builder.cli paper.txt
    python -m builder.cli slide_plan.json
    python -m builder.cli paper.pdf --output ./my_deck/
    python -m builder.cli paper.pdf --theme academic-blue
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from .content_bundle import ContentBundle
from .scanners import FolderScanner, PDFScanner, TextScanner, PlanScanner
from .slidekit_builder import SlideKitBuilder
from .md_exporter import export_md
from .plan_exporter import export_plan, export_content

# プロジェクトルート（slidekit/）
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_BASE = PROJECT_ROOT / "output"


def _make_output_dir(input_path: Path) -> Path:
    """入力名 + タイムスタンプで output/<name>_YYYYMMDD_HHMM/ を生成する"""
    stem = input_path.stem if input_path.is_file() else input_path.name
    # ファイル名を短縮（長い論文名対策）
    short = re.sub(r'[^\w\-]', '_', stem)[:40]
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    out = OUTPUT_BASE / f"{short}_{ts}"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _export_both_json(bundle: ContentBundle, output_dir: Path, quiet: bool = False) -> None:
    """slide_plan.json と slide_content.json を両方出力する"""
    plan_result = export_plan(bundle, output_dir / "slide_plan.json")
    content_result = export_content(bundle, output_dir / "slide_content.json")
    if not quiet:
        print(f"構成モード用: {plan_result}")
        print(f"素材モード用: {content_result}")
        print(f"  → slide_reviewer.html でレビュー・編集できます")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="論文PDF/フォルダ/テキストから SlideKit HTML スライドを自動生成する",
    )
    parser.add_argument(
        "input",
        help="入力ファイルまたはフォルダ（PDF / フォルダ / テキスト / slide_plan.json）",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="出力ディレクトリ（省略時は output/<入力名>_日時/ に自動生成）",
    )
    parser.add_argument(
        "--theme", "-t",
        default=None,
        help="テーマ名（academic-blue / medical-teal / modern-minimal）",
    )
    parser.add_argument(
        "--export-md",
        action="store_true",
        help="スライド生成せず、Markdown ファイルのみ書き出す（slidekit-create に渡す用）",
    )
    parser.add_argument(
        "--export-plan",
        action="store_true",
        help="スライド生成せず、slide_plan.json のみ書き出す（builder 用）",
    )
    parser.add_argument(
        "--export-content",
        action="store_true",
        help="スライド生成せず、slide_content.json のみ書き出す（slidekit-create 用、type なし）",
    )
    parser.add_argument(
        "--poster",
        action="store_true",
        help="学会ポスターを生成する（デフォルト: A0 3カラム）",
    )
    parser.add_argument(
        "--size",
        default="a0",
        choices=["a0", "a1"],
        help="ポスターサイズ（a0: 3カラム / a1: 2カラム、デフォルト: a0）",
    )

    args = parser.parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"エラー: 入力が見つかりません: {input_path}")
        sys.exit(1)

    # 出力ディレクトリ決定
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = _make_output_dir(input_path)

    # スキャナ選択
    if input_path.is_dir():
        print(f"入力モード: フォルダ（{input_path}）")
        scanner = FolderScanner(input_path, output_dir)
    elif input_path.suffix.lower() == ".pdf":
        print(f"入力モード: PDF（{input_path}）")
        scanner = PDFScanner(input_path, output_dir)
    elif input_path.suffix.lower() == ".json":
        print(f"入力モード: スライドプラン（{input_path}）")
        scanner = PlanScanner(input_path, output_dir)
    elif input_path.suffix.lower() in (".txt", ".md"):
        print(f"入力モード: テキスト（{input_path}）")
        scanner = TextScanner(input_path, output_dir)
    else:
        print(f"エラー: 未対応の入力形式です: {input_path.suffix}")
        sys.exit(1)

    # スキャン
    bundle = scanner.scan()

    # テーマ上書き
    if args.theme:
        bundle.theme = args.theme

    # Markdown エクスポートモード（両 JSON も同時出力）
    if args.export_md:
        md_path = output_dir / "content.md"
        result = export_md(bundle, md_path)
        print(f"Markdown 出力: {result}")
        _export_both_json(bundle, output_dir)
        return

    # slide_plan.json エクスポートモード
    if args.export_plan:
        _export_both_json(bundle, output_dir)
        print(f"  → python -m builder.cli {output_dir / 'slide_plan.json'} で HTML を生成できます")
        return

    # slide_content.json エクスポートモード（create 用）
    if args.export_content:
        _export_both_json(bundle, output_dir)
        print(f"  → /slidekit-create に slide_content.json を渡してスライドを作成できます")
        return

    # 両 JSON を自動保存（ビルド前）
    _export_both_json(bundle, output_dir, quiet=True)

    # ビルド
    builder = SlideKitBuilder()
    poster_size = args.size if args.poster else None
    result = builder.build(bundle, output_dir, poster_size=poster_size)
    print(f"出力: {result}")


if __name__ == "__main__":
    main()
