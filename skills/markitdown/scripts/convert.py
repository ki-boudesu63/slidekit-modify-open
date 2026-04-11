#!/usr/bin/env python3
"""ファイルを Markdown に変換する（markitdown ラッパー）。

単体変換:
    python convert.py input.pptx
    python convert.py input.pptx -o output.md

バッチ変換:
    python convert.py input_dir/ -o output_dir/

対応フォーマット:
    PPTX, DOCX, XLSX, XLS, PDF, HTML, CSV, JSON, XML,
    EPUB, ZIP, MSG, 画像 (JPG/PNG/etc.), 音声 (MP3/WAV/etc.)

依存:
    - markitdown[all] (pip install 'markitdown[all]')
"""

import argparse
import sys
from pathlib import Path

try:
    from markitdown import MarkItDown
except ImportError:
    print(
        "Error: markitdown が必要です。pip install 'markitdown[all]'",
        file=sys.stderr,
    )
    sys.exit(1)

# markitdown が対応する拡張子
SUPPORTED_EXTENSIONS = {
    # ドキュメント
    ".pptx", ".docx", ".xlsx", ".xls", ".pdf",
    # Web / データ
    ".html", ".htm", ".csv", ".json", ".xml",
    # アーカイブ / 電子書籍
    ".zip", ".epub",
    # メール
    ".msg",
    # 画像（EXIF メタデータ抽出）
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg",
    # 音声（文字起こし）
    ".mp3", ".wav", ".m4a", ".flac", ".ogg",
}


def convert_file(md: MarkItDown, input_path: Path, output_path: Path) -> bool:
    """単一ファイルを Markdown に変換する。"""
    try:
        result = md.convert(str(input_path))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.text_content, encoding="utf-8")
        return True
    except Exception as e:
        print(f"  Error: {input_path.name} の変換に失敗: {e}", file=sys.stderr)
        return False


def convert_batch(
    md: MarkItDown, input_dir: Path, output_dir: Path
) -> tuple[int, int]:
    """ディレクトリ内の対応ファイルを一括変換する。"""
    files = sorted(
        f
        for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not files:
        print(f"Warning: 対応ファイルが見つかりません: {input_dir}", file=sys.stderr)
        return 0, 0

    print(f"バッチ変換: {len(files)} ファイル検出")
    success = 0
    failed = 0

    for f in files:
        out = output_dir / f"{f.stem}.md"
        print(f"  変換中: {f.name} → {out.name} ...", end=" ")
        if convert_file(md, f, out):
            print("OK")
            success += 1
        else:
            failed += 1

    return success, failed


def main():
    parser = argparse.ArgumentParser(
        description="ファイルを Markdown に変換（markitdown ラッパー）"
    )
    parser.add_argument(
        "input",
        help="入力ファイルまたはディレクトリ",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="出力先（ファイルまたはディレクトリ）。未指定時は入力と同じ場所に .md で出力",
    )
    parser.add_argument(
        "--plugins",
        action="store_true",
        help="プラグインを有効化（markitdown-ocr 等）",
    )
    args = parser.parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: パスが見つかりません: {args.input}", file=sys.stderr)
        sys.exit(1)

    # MarkItDown インスタンス生成
    md_kwargs: dict = {}
    if args.plugins:
        md_kwargs["enable_plugins"] = True
    md = MarkItDown(**md_kwargs)

    # バッチモード（ディレクトリ指定時）
    if input_path.is_dir():
        output_dir = Path(args.output) if args.output else input_path
        output_dir.mkdir(parents=True, exist_ok=True)
        success, failed = convert_batch(md, input_path, output_dir)
        print(f"\n完了! 成功: {success}, 失敗: {failed}")
        if failed > 0:
            sys.exit(1)
        return

    # 単体ファイルモード
    if input_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        print(f"Warning: 非対応の拡張子です: {input_path.suffix}", file=sys.stderr)
        print("変換を試みます...", file=sys.stderr)

    if args.output:
        output_path = Path(args.output)
        if output_path.is_dir() or str(args.output).endswith(("/", "\\")):
            output_path = output_path / f"{input_path.stem}.md"
    else:
        output_path = input_path.with_suffix(".md")

    print(f"変換中: {input_path.name} → {output_path.name} ...")
    if convert_file(md, input_path, output_path):
        print(f"完了! 出力: {output_path}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
