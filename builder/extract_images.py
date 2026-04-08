"""
PDF論文から図版画像を抽出するスクリプト（html-poster-slides 用）
marp-slides 版から改良：アスペクト比・相対パス・ページレンダリング抽出を追加

使い方:
  python extract_images.py <PDF path> [出力ディレクトリ]
  python extract_images.py paper.pdf ./output/images

出力:
  - 抽出された画像ファイル群
  - images_index.json（HTMLビルダーが参照するメタデータ）
"""

import sys
import os
import json
import re
try:
    import fitz  # PyMuPDF
except ImportError:
    print("エラー: pymupdf が必要です。pip install pymupdf を実行してください。")
    sys.exit(1)


# 抽出対象の最小サイズ（px）。これ未満はアイコン・罫線などとして除外
MIN_WIDTH = 120
MIN_HEIGHT = 120

# ページ全体をレンダリングして抽出するモード（図が埋め込みでなくベクター描画の場合）
PAGE_RENDER_DPI = 150


def extract_images_from_pdf(pdf_path: str, output_dir: str) -> list[dict]:
    """
    PDFから埋め込み画像を抽出して output_dir に保存する。

    戻り値:
      [
        {
          "page": int,          # ページ番号（1始まり）
          "index": int,         # ページ内の図番号
          "path": str,          # 絶対パス（スラッシュ区切り）
          "filename": str,      # ファイル名のみ
          "rel_path": str,      # output_dir からの相対パス（HTML埋め込み用）
          "width": int,         # 幅（px）
          "height": int,        # 高さ（px）
          "aspect_ratio": float,# 幅/高さ
          "caption": str,       # 推定キャプション
        },
        ...
      ]
    """
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    results = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)

        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            img_bytes = base_image["image"]
            img_ext = base_image["ext"]

            width = base_image.get("width", 0)
            height = base_image.get("height", 0)

            # 小さすぎる画像（アイコン・罫線等）はスキップ
            if width < MIN_WIDTH or height < MIN_HEIGHT:
                continue

            filename = f"fig_p{page_num + 1:03d}_{img_index + 1:02d}.{img_ext}"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "wb") as f:
                f.write(img_bytes)

            caption = find_caption(page, img_index)
            aspect = round(width / height, 3) if height > 0 else 1.0

            results.append({
                "page": page_num + 1,
                "index": img_index + 1,
                "path": filepath.replace("\\", "/"),
                "filename": filename,
                "rel_path": filename,  # output_dir からの相対パス
                "width": width,
                "height": height,
                "aspect_ratio": aspect,
                "caption": caption,
            })

    # 埋め込み画像が少ない場合、ページ全体をレンダリングして補完
    if len(results) == 0:
        print("埋め込み画像が見つかりませんでした。ページレンダリングモードで再試行します...")
        results = render_pages_as_images(doc, output_dir)

    doc.close()
    return results


def render_pages_as_images(doc: fitz.Document, output_dir: str) -> list[dict]:
    """
    ページ全体をラスタライズして画像として保存する（ベクター図対応）。
    埋め込み画像抽出が空だった場合のフォールバック。
    """
    results = []
    mat = fitz.Matrix(PAGE_RENDER_DPI / 72, PAGE_RENDER_DPI / 72)

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=mat)
        filename = f"page_render_{page_num + 1:03d}.png"
        filepath = os.path.join(output_dir, filename)
        pix.save(filepath)

        results.append({
            "page": page_num + 1,
            "index": 1,
            "path": filepath.replace("\\", "/"),
            "filename": filename,
            "rel_path": filename,
            "width": pix.width,
            "height": pix.height,
            "aspect_ratio": round(pix.width / pix.height, 3),
            "caption": f"ページ {page_num + 1} のレンダリング",
            "rendered": True,  # レンダリングモードフラグ
        })

    return results


def find_caption(page: fitz.Page, img_index: int) -> str:
    """
    ページテキストから Figure / Fig. / 図 / Table / 表 などのキャプションを探す。
    """
    text = page.get_text()
    patterns = [
        r"(Fig(?:ure)?\.?\s*\d+[A-Z]?[^\.]{0,120}\.)",   # Figure 1A. ...
        r"(図\s*\d+[A-Za-z]?[^。]{0,80}。)",               # 図1. ...（日本語）
        r"(Table\s*\d+[^\.]{0,120}\.)",                    # Table 1. ...
        r"(表\s*\d+[^。]{0,80}。)",                         # 表1. ...
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            idx = min(img_index, len(matches) - 1)
            return matches[idx].strip()
    return ""


def classify_image(entry: dict) -> str:
    """
    アスペクト比とキャプションからおおよその図の種類を推定する。
    HTMLビルダーがレイアウトコンポーネントを選ぶ際に使用する。

    戻り値: "figure" | "table" | "wide_figure" | "tall_figure"
    """
    cap = entry.get("caption", "").lower()
    if "table" in cap or "表" in cap:
        return "table"
    ar = entry.get("aspect_ratio", 1.0)
    if ar > 2.0:
        return "wide_figure"
    if ar < 0.6:
        return "tall_figure"
    return "figure"


def main():
    if len(sys.argv) < 2:
        print("使い方: python extract_images.py <PDFパス> [出力ディレクトリ]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) >= 3 else os.path.join(
        os.path.dirname(os.path.abspath(pdf_path)), "images"
    )

    if not os.path.exists(pdf_path):
        print(f"エラー: ファイルが見つかりません: {pdf_path}")
        sys.exit(1)

    print(f"PDFから画像を抽出中: {pdf_path}")
    print(f"出力先: {output_dir}")

    results = extract_images_from_pdf(pdf_path, output_dir)

    # 図の種類を分類して追記
    for r in results:
        r["type"] = classify_image(r)

    print(f"\n抽出完了: {len(results)} 枚の図版")
    for r in results:
        cap = f" → {r['caption'][:60]}" if r["caption"] else ""
        print(f"  p.{r['page']:3d} [{r['width']}x{r['height']}] ({r['type']}) {r['filename']}{cap}")

    # JSON インデックスを保存（html_builder.py が参照）
    json_path = os.path.join(output_dir, "images_index.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nインデックス保存: {json_path}")
    print("次のステップ: html_builder.py を実行してHTMLスライドを生成してください")


if __name__ == "__main__":
    main()
