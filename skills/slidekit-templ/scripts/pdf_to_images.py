#!/usr/bin/env python3
"""PDF を個別スライド画像に変換する。

通常モード: PDF の各ページを1スライドとして画像化
グリッドモード: 1ページに複数スライドがグリッド配置された PDF（Figma エクスポート等）を自動分割

使い方:
    # 通常（1ページ = 1スライド）
    python pdf_to_images.py input.pdf output_dir

    # グリッドモード（自動検出）
    python pdf_to_images.py input.pdf output_dir --grid

出力:
    output_dir/slide-01.jpg, slide-02.jpg, ...

依存:
    - pymupdf (pip install pymupdf)
    - Pillow (pip install Pillow)
    - numpy (pip install numpy)  ※グリッドモード時
"""

import argparse
import sys
from pathlib import Path

try:
    import fitz  # pymupdf
except ImportError:
    print("Error: pymupdf が必要です。pip install pymupdf", file=sys.stderr)
    sys.exit(1)


def pdf_to_images(pdf_path: Path, output_dir: Path, dpi: int = 150) -> list[Path]:
    """通常モード: PDF の各ページを JPEG 画像に変換する。"""
    doc = fitz.open(str(pdf_path))
    images = []
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)

    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat)
        filename = output_dir / f"slide-{i + 1:02d}.jpg"
        pix.save(str(filename))
        images.append(filename)

    doc.close()
    return images


def pdf_grid_to_images(
    pdf_path: Path,
    output_dir: Path,
    page_num: int = 0,
    min_variance: float = 50.0,
) -> list[Path]:
    """グリッドモード: 隙間を自動検出してスライドを分割する。"""
    try:
        from PIL import Image
        import numpy as np
        Image.MAX_IMAGE_PIXELS = None
    except ImportError:
        print("Error: Pillow と numpy が必要です。pip install Pillow numpy", file=sys.stderr)
        sys.exit(1)

    doc = fitz.open(str(pdf_path))
    page = doc[page_num]

    # フル解像度で取得
    pix = page.get_pixmap(matrix=fitz.Matrix(1.0, 1.0))
    full_path = output_dir / "_grid_full.png"
    pix.save(str(full_path))
    full_w, full_h = pix.width, pix.height
    doc.close()

    # 解析用に縮小（メモリ節約）
    scale = 0.3
    img_full = Image.open(str(full_path))
    small_w, small_h = int(full_w * scale), int(full_h * scale)
    img_small = img_full.resize((small_w, small_h), Image.LANCZOS)
    arr = np.array(img_small)

    print(f"画像サイズ: {full_w}x{full_h}px")

    # 各行・各列の標準偏差を計算（均一な色 = 隙間）
    row_std = arr.std(axis=(1, 2))
    col_std = arr.std(axis=(0, 2))

    # 隙間の行をグループ化
    def find_gaps(std_arr, threshold=5):
        gap_indices = np.where(std_arr < threshold)[0]
        if len(gap_indices) == 0:
            return []
        groups = []
        start = gap_indices[0]
        for i in range(1, len(gap_indices)):
            if gap_indices[i] - gap_indices[i - 1] > 1:
                groups.append((start, gap_indices[i - 1] + 1))
                start = gap_indices[i]
        groups.append((start, gap_indices[-1] + 1))
        # 短すぎる隙間はノイズなので除外（フル解像度で20px以上）
        return [(int(g[0] / scale), int(g[1] / scale)) for g in groups if (g[1] - g[0]) / scale > 20]

    gaps_y = find_gaps(row_std)
    gaps_x = find_gaps(col_std)

    cols = len(gaps_x) + 1
    rows = len(gaps_y) + 1
    print(f"検出グリッド: {cols}列 x {rows}行")
    print(f"水平隙間: {len(gaps_x)}箇所, 垂直隙間: {len(gaps_y)}箇所")

    # スライド境界を算出
    x_bounds = [0]
    for gx in gaps_x:
        x_bounds.append(gx[0])  # 隙間の左端 = スライドの右端
        x_bounds.append(gx[1])  # 隙間の右端 = 次のスライドの左端
    x_bounds.append(full_w)

    y_bounds = [0]
    for gy in gaps_y:
        y_bounds.append(gy[0])
        y_bounds.append(gy[1])
    y_bounds.append(full_h)

    # スライド領域のペア（左端, 右端）を作成
    slide_xs = [(x_bounds[i], x_bounds[i + 1]) for i in range(0, len(x_bounds), 2)]
    slide_ys = [(y_bounds[i], y_bounds[i + 1]) for i in range(0, len(y_bounds), 2)]

    # 分割
    images = []
    count = 0
    for y1, y2 in slide_ys:
        for x1, x2 in slide_xs:
            sw = x2 - x1
            sh = y2 - y1
            # 小さすぎるブロックはスキップ
            if sw < 100 or sh < 100:
                continue

            crop = img_full.crop((x1, y1, x2, y2))

            # 空白スライドをスキップ（内容の分散が低い = 単色）
            crop_small = crop.resize((64, 36), Image.LANCZOS)
            crop_arr = np.array(crop_small)
            variance = crop_arr.std()
            if variance < min_variance:
                continue

            count += 1
            filename = output_dir / f"slide-{count:02d}.jpg"
            crop.save(str(filename), quality=95)
            images.append(filename)

    # 一時ファイル削除
    full_path.unlink(missing_ok=True)

    return images


def main():
    parser = argparse.ArgumentParser(
        description="PDF をスライド画像に変換（通常 / グリッドモード）"
    )
    parser.add_argument("input", help="入力 PDF ファイル (.pdf)")
    parser.add_argument(
        "output_dir",
        nargs="?",
        default="slides",
        help="出力ディレクトリ (デフォルト: slides)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="画像解像度 DPI (デフォルト: 150、通常モード時)",
    )
    parser.add_argument(
        "--grid",
        action="store_true",
        help="グリッドモード: スライド間の隙間を自動検出して分割",
    )
    parser.add_argument(
        "--page",
        type=int,
        default=0,
        help="グリッドモード時の対象ページ番号 (デフォルト: 0)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    if not input_path.exists():
        print(f"Error: ファイルが見つかりません: {args.input}", file=sys.stderr)
        sys.exit(1)

    if input_path.suffix.lower() != ".pdf":
        print(f"Error: PDF ファイルを指定してください: {input_path.suffix}", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    if args.grid:
        print(f"グリッドモード（自動検出）: {input_path.name}...")
        images = pdf_grid_to_images(input_path, output_dir, page_num=args.page)
    else:
        print(f"スライド画像を生成中: {input_path.name} (DPI={args.dpi})...")
        images = pdf_to_images(input_path, output_dir, args.dpi)

    print(f"\n完了! {len(images)} スライド:")
    for img in images:
        print(f"  {img}")


if __name__ == "__main__":
    main()
