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

    # ビルド
    builder = SlideKitBuilder()
    result = builder.build(bundle, output_dir)
    print(f"出力: {result}")


if __name__ == "__main__":
    main()
