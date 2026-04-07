"""
Kroki.io URL 生成ヘルパー（html-poster-slides 用）
marp-slides 版から改良：HTML埋め込みスニペット・<img> タグ出力を追加

テキスト形式の図定義（Mermaid / PlantUML / Graphviz など）を
Kroki.io の GET URL に変換して HTML スライドに埋め込む。

追加インストール不要（標準ライブラリのみ・Kroki 公式 Web API を使用）

使い方:
  # ファイルからURL生成
  python kroki_url.py mermaid diagram.mmd

  # 標準入力からURL生成（パイプ）
  echo "graph TD; A-->B" | python kroki_url.py mermaid -

対応タイプ: mermaid, plantuml, graphviz, blockdiag, seqdiag, actdiag,
           nwdiag, excalidraw, etc.
           → 詳細: https://kroki.io/#support

注意: 図のソーステキストが Kroki.io 外部サーバーへ送信されます。
      機密情報を含む図の生成には使用しないでください。
"""

import sys
import base64
import zlib


def kroki_url(diagram_type: str, source: str, output_format: str = "svg") -> str:
    """
    Kroki.io GET URL を生成する。

    Args:
        diagram_type: "mermaid", "plantuml", "graphviz" など
        source: 図の定義テキスト
        output_format: "svg"（デフォルト）または "png"

    Returns:
        Kroki.io GET URL 文字列
    """
    compressed = zlib.compress(source.encode('utf-8'), 9)
    encoded = base64.urlsafe_b64encode(compressed).decode('ascii')
    return f"https://kroki.io/{diagram_type}/{output_format}/{encoded}"


def print_html_snippet(url: str, alt: str = "フロー図"):
    """HTML への埋め込みスニペットを表示する"""
    print("\n--- HTML 埋め込みスニペット ---")
    print(f'<!-- 通常の img タグ -->')
    print(f'<img src="{url}" alt="{alt}" class="diagram">')
    print()
    print(f'<!-- WebSlides の2カラムレイアウトに使う場合 -->')
    print(f'<div class="grid">')
    print(f'  <div class="column"><!-- テキスト --></div>')
    print(f'  <div class="column">')
    print(f'    <figure>')
    print(f'      <img src="{url}" alt="{alt}">')
    print(f'      <figcaption>{alt}</figcaption>')
    print(f'    </figure>')
    print(f'  </div>')
    print(f'</div>')
    print()
    print(f'<!-- ポスターのセクション内に使う場合 -->')
    print(f'<div class="poster-figure">')
    print(f'  <img src="{url}" alt="{alt}">')
    print(f'  <p class="caption">{alt}</p>')
    print(f'</div>')


def main():
    if len(sys.argv) < 3:
        print("使い方: python kroki_url.py <diagram_type> <file または ->")
        print("  例: python kroki_url.py mermaid flow.mmd")
        print("      echo 'graph TD; A-->B' | python kroki_url.py mermaid -")
        sys.exit(1)

    diagram_type = sys.argv[1]
    source_path = sys.argv[2]
    output_format = sys.argv[3] if len(sys.argv) >= 4 else "svg"

    if source_path == '-':
        source = sys.stdin.read()
    else:
        with open(source_path, encoding='utf-8') as f:
            source = f.read()

    url = kroki_url(diagram_type, source, output_format)
    print(url)
    print_html_snippet(url)


# =====================================================
# Mermaid テンプレート集
# （html_builder.py がコンテンツに合わせて差し替えて使う）
# =====================================================

MERMAID_TEMPLATES = {

    # 実験プロトコルのフロー図（縦型）
    "protocol_flow": """
flowchart TD
    A["ステップ1\\n（詳細）"] --> B
    B["ステップ2\\n（詳細）"] --> C
    C["ステップ3\\n（詳細）"] --> D
    D["ステップ4\\n（詳細）"] --> E
    E["完了・評価"]

    style A fill:#dbeafe,stroke:#1a5f9c
    style E fill:#dcfce7,stroke:#16a34a
""",

    # 実験デザイン図（グループ分け）
    "experimental_design": """
flowchart LR
    A["介入 (Day 0)"] --> B["介入群"]
    A --> C["コントロール群"]
    B --> D["短期評価 n=X"]
    B --> E["長期評価 n=X"]
    C --> F["短期評価 n=X"]
    C --> G["長期評価 n=X"]

    style B fill:#dbeafe,stroke:#1a5f9c
    style C fill:#f3f4f6,stroke:#aaaaaa
""",

    # 結果サマリー（縦型フロー）
    "result_summary": """
flowchart TD
    A["介入"] --> B["主要アウトカム1"]
    B --> C["主要アウトカム2"]
    C --> D["最終評価・結論"]

    style A fill:#dbeafe,stroke:#1a5f9c
    style D fill:#dcfce7,stroke:#16a34a
""",

    # PlantUML シーケンス図
    "sequence": """
@startuml
participant "要素A" as A
participant "要素B" as B
participant "要素C" as C

A -> B : ステップ1
B -> C : ステップ2
C -> C : 処理
C --> B : 結果
B --> A : 完了
@enduml
""",

    # 概念図（マインドマップ的な構造）
    "concept_map": """
flowchart TD
    ROOT["中心概念"] --> A["要素1"]
    ROOT --> B["要素2"]
    ROOT --> C["要素3"]
    A --> A1["詳細1-1"]
    A --> A2["詳細1-2"]
    B --> B1["詳細2-1"]
    C --> C1["詳細3-1"]

    style ROOT fill:#1a5f9c,color:#ffffff,stroke:#1a5f9c
"""
}


if __name__ == "__main__":
    main()
