"""
Vega-Lite JSON → SVG 変換スクリプト（html-poster-slides 用）
marp-slides 版から改良：HTML埋め込みスニペット・インライン SVG 出力を追加

依存: pip install vl-convert-python

使い方:
  # JSONファイルから生成
  python make_chart.py spec.json images/chart.svg

  # 標準入力から生成（パイプ）
  echo '{"$schema":...}' | python make_chart.py - images/chart.svg

HTML への埋め込み例:
  <img src="images/chart.svg" alt="グラフ" class="chart">
  または（インライン SVG として埋め込む場合）
  <div class="chart-inline"><!-- SVGコードをここに貼り付け --></div>
"""

import sys
import json
import os


def vegalite_to_svg(spec: dict) -> str:
    """Vega-Lite JSONスペックをSVG文字列に変換する"""
    try:
        import vl_convert as vlc
    except ImportError:
        print("エラー: vl-convert-python がインストールされていません。")
        print("  pip install vl-convert-python")
        sys.exit(1)
    return vlc.vegalite_to_svg(vl_spec=spec)


def print_html_snippet(svg_path: str):
    """HTMLへの埋め込みスニペットを表示する"""
    print("\n--- HTML 埋め込みスニペット ---")
    print(f'<!-- img タグ（推奨）-->')
    print(f'<img src="{svg_path}" alt="グラフ" class="chart">')
    print()
    print(f'<!-- WebSlides の2カラムレイアウトに使う場合 -->')
    print(f'<div class="grid">')
    print(f'  <div class="column"><!-- テキスト --></div>')
    print(f'  <div class="column">')
    print(f'    <img src="{svg_path}" alt="グラフ">')
    print(f'  </div>')
    print(f'</div>')


def main():
    if len(sys.argv) < 3:
        print("使い方: python make_chart.py <spec.json または -> <output.svg>")
        print("  例: python make_chart.py bar_chart.json images/result.svg")
        sys.exit(1)

    spec_path = sys.argv[1]
    output_path = sys.argv[2]

    # スペックの読み込み
    if spec_path == '-':
        spec = json.load(sys.stdin)
    else:
        with open(spec_path, encoding='utf-8') as f:
            spec = json.load(f)

    # 出力ディレクトリを自動作成
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    svg = vegalite_to_svg(spec)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg)

    print(f"SVG保存完了: {output_path}")
    print_html_snippet(output_path)


# =====================================================
# Vega-Lite スペック テンプレート集
# （html_builder.py がコンテンツに合わせて値を差し替えて使う）
# =====================================================

TEMPLATES = {

    # 棒グラフ（縦）: 群間比較・生着率など
    "bar_vertical": {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "width": 400,
        "height": 280,
        "data": {
            "values": [
                {"group": "4週後", "value": 66.7, "category": "処置群"},
                {"group": "12週後", "value": 42.9, "category": "処置群"},
                {"group": "4週後", "value": 10.0, "category": "コントロール"},
                {"group": "12週後", "value": 5.7, "category": "コントロール"}
            ]
        },
        "mark": {"type": "bar", "cornerRadiusTopLeft": 3, "cornerRadiusTopRight": 3},
        "encoding": {
            "x": {"field": "group", "type": "nominal", "title": "観察期間",
                  "axis": {"labelFontSize": 14, "titleFontSize": 14}},
            "y": {"field": "value", "type": "quantitative", "title": "割合 (%)",
                  "scale": {"domain": [0, 110]},
                  "axis": {"labelFontSize": 14, "titleFontSize": 14}},
            "color": {"field": "category", "type": "nominal",
                      "scale": {"range": ["#1a5f9c", "#e8a838"]},
                      "legend": {"labelFontSize": 13, "titleFontSize": 13}},
            "xOffset": {"field": "category", "type": "nominal"}
        },
        "config": {"font": "Noto Sans JP, Helvetica, Arial, sans-serif"}
    },

    # 折れ線グラフ: 経時変化
    "line": {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "width": 400,
        "height": 280,
        "data": {
            "values": [
                {"week": 0, "value": 0, "group": "処置群"},
                {"week": 4, "value": 67, "group": "処置群"},
                {"week": 12, "value": 43, "group": "処置群"},
                {"week": 0, "value": 0, "group": "コントロール"},
                {"week": 4, "value": 8, "group": "コントロール"},
                {"week": 12, "value": 5, "group": "コントロール"}
            ]
        },
        "mark": {"type": "line", "point": True, "strokeWidth": 2},
        "encoding": {
            "x": {"field": "week", "type": "quantitative", "title": "経過週数",
                  "axis": {"labelFontSize": 14, "titleFontSize": 14}},
            "y": {"field": "value", "type": "quantitative", "title": "評価値 (%)",
                  "scale": {"domain": [0, 110]},
                  "axis": {"labelFontSize": 14, "titleFontSize": 14}},
            "color": {"field": "group", "type": "nominal",
                      "scale": {"range": ["#1a5f9c", "#aaaaaa"]},
                      "legend": {"labelFontSize": 13}},
            "strokeDash": {"field": "group", "type": "nominal",
                           "scale": {"range": [[1, 0], [4, 4]]}}
        },
        "config": {"font": "Noto Sans JP, Helvetica, Arial, sans-serif"}
    },

    # 水平棒グラフ: 複数指標の比較
    "bar_horizontal": {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "width": 400,
        "height": 280,
        "data": {
            "values": [
                {"marker": "指標A", "value": 98},
                {"marker": "指標B", "value": 96},
                {"marker": "指標C", "value": 64},
                {"marker": "指標D", "value": 1},
                {"marker": "指標E", "value": 0}
            ]
        },
        "mark": {"type": "bar", "cornerRadiusTopRight": 3, "cornerRadiusBottomRight": 3},
        "encoding": {
            "y": {"field": "marker", "type": "nominal", "title": "",
                  "sort": "-x",
                  "axis": {"labelFontSize": 14, "titleFontSize": 14}},
            "x": {"field": "value", "type": "quantitative", "title": "陽性率 (%)",
                  "scale": {"domain": [0, 110]},
                  "axis": {"labelFontSize": 14, "titleFontSize": 14}},
            "color": {
                "condition": {"test": "datum.value > 50", "value": "#1a5f9c"},
                "value": "#cccccc"
            }
        },
        "config": {"font": "Noto Sans JP, Helvetica, Arial, sans-serif"}
    },

    # 散布図: 2変数の相関
    "scatter": {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "width": 400,
        "height": 280,
        "data": {
            "values": [
                {"x": 1.2, "y": 3.4, "group": "A群"},
                {"x": 2.1, "y": 4.8, "group": "A群"},
                {"x": 3.5, "y": 6.2, "group": "A群"},
                {"x": 1.0, "y": 1.5, "group": "B群"},
                {"x": 2.3, "y": 2.1, "group": "B群"},
                {"x": 3.8, "y": 3.0, "group": "B群"}
            ]
        },
        "mark": {"type": "point", "size": 80, "filled": True},
        "encoding": {
            "x": {"field": "x", "type": "quantitative", "title": "X軸",
                  "axis": {"labelFontSize": 14, "titleFontSize": 14}},
            "y": {"field": "y", "type": "quantitative", "title": "Y軸",
                  "axis": {"labelFontSize": 14, "titleFontSize": 14}},
            "color": {"field": "group", "type": "nominal",
                      "scale": {"range": ["#1a5f9c", "#e8a838"]},
                      "legend": {"labelFontSize": 13}}
        },
        "config": {"font": "Noto Sans JP, Helvetica, Arial, sans-serif"}
    }
}


if __name__ == "__main__":
    main()
