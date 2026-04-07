---
name: slidekit-build
description: "論文PDF・研究テキスト・フォルダからSlideKit形式のHTMLスライドを自動生成する。Claude が内容を読み取り、最適なスライド構成を設計して slide_plan.json を作成し、ビルダーで HTML を生成する。'スライドを作って', '論文からスライド', 'slidekit build', 'プレゼン作成' で起動。"
---

# SlideKit Build — 論文→スライド自動生成

論文 PDF・研究テキスト・フォルダの内容を Claude が読み取り、最適なスライド構成を設計して SlideKit 形式の HTML スライドを生成する。

## パイプライン

```
入力（PDF / フォルダ / テキスト）
    ↓
Phase 1: 内容読み取り（Claude が PDF/テキストを読む）
    ↓
Phase 1.5: 言語確認（日本語 or 英語でスライドを作るか確認）
    ↓
Phase 2: スライド構成設計（Claude が slide_plan.json を作成）
    ↓
Phase 3: HTML 生成（python -m builder slide_plan.json）
    ↓
Phase 4: 確認・修正（/slide-check）
```

## 依存

```bash
pip install pymupdf Pillow
```

---

## ワークフロー

### Phase 1: 内容読み取り

ユーザーから入力を受け取り、内容を把握する。

**PDF の場合:**
1. PDF テキストを読む（Read ツールで直接、または PyMuPDF でテキスト抽出）
2. 図版を確認（PDF 内の画像を把握）
3. 論文の構造を理解（背景・目的・方法・結果・考察・結論）

**フォルダの場合:**
1. フォルダ内のファイル一覧を確認
2. meta.json があれば読む
3. テキストファイル・画像・表・グラフを把握

**テキストの場合:**
1. テキスト内容を読む
2. セクション構造を把握

### Phase 1.5: 言語確認

**必ずユーザーに確認する。** 入力が英語論文でも、発表は日本語で行うケースが多い。

確認の仕方:
```
スライドの言語はどちらにしますか？
1. 日本語（見出し・本文を日本語に翻訳）
2. 英語（原文のまま）
```

- **日本語を選んだ場合**: slide_plan.json の `heading` と `body` をすべて日本語で記述する。meta の `language` は `"ja"`。論文の専門用語は適宜カッコ書きで英語を併記する（例: 「間葉系幹細胞（MSC）」）。
- **英語を選んだ場合**: 原文のまま使用。meta の `language` は `"en"`。
- ユーザーが先に「日本語で」「英語で」と指定していた場合はこの確認をスキップしてよい。

### Phase 2: スライド構成設計

内容に基づいて `slide_plan.json` を設計する。これが最も重要なフェーズ。

#### 設計の原則

1. **1スライド = 1メッセージ**: 各スライドに伝えたいことは1つだけ
2. **テキストは最小限**: 箇条書き3〜5項目、本文は4段落以内
3. **図表を活用**: 図や表がある場合は積極的に配置する
4. **ストーリーフロー**: 背景→目的→方法→結果→考察→結論の流れを意識
5. **スライド枚数**: 10分発表なら10〜15枚、20分なら15〜20枚が目安

#### スライド構成テンプレート

**基礎研究（15枚）:**
| # | type | 内容 |
|---|------|------|
| 1 | title | タイトル・著者・所属 |
| 2 | text-only | 背景・問題提起 |
| 3 | text-only | 研究目的・仮説 |
| 4 | section-break | 方法 |
| 5 | two-column | 実験材料・モデル（テキスト+図） |
| 6 | two-column | 実験プロトコル（テキスト+フロー図） |
| 7 | section-break | 結果 |
| 8 | figure-focus | 結果1（組織学的所見など） |
| 9 | two-column | 結果2（定量データ+グラフ） |
| 10 | figure-focus | 結果3（追加データ） |
| 11 | section-break | 考察 |
| 12 | text-only | 考察（解釈・先行研究との比較） |
| 13 | text-only | 限界・今後の課題 |
| 14 | text-only | 結論 |
| 15 | conclusion | 謝辞 |

**臨床研究（12枚）:**
| # | type | 内容 |
|---|------|------|
| 1 | title | タイトル |
| 2 | text-only | 背景・臨床的意義 |
| 3 | text-only | 目的・仮説 |
| 4 | section-break | 方法 |
| 5 | two-column | 対象・選択基準 |
| 6 | data-table | 患者背景（テーブル） |
| 7 | section-break | 結果 |
| 8 | two-column | 主要アウトカム |
| 9 | data-table | 統計結果 |
| 10 | text-only | 考察・限界 |
| 11 | text-only | 結論 |
| 12 | conclusion | 謝辞 |

**ゼミ・勉強会（10枚）:**
| # | type | 内容 |
|---|------|------|
| 1 | title | タイトル |
| 2 | text-only | 導入・論文の位置づけ |
| 3 | text-only | 背景・先行研究 |
| 4 | two-column | 方法の要点 |
| 5 | figure-focus | 主要な結果1 |
| 6 | figure-focus | 主要な結果2 |
| 7 | text-only | 考察のポイント |
| 8 | text-only | 限界・批判的考察 |
| 9 | text-only | Take-home message |
| 10 | conclusion | 謝辞 |

#### slide_plan.json のスキーマ

```json
{
  "meta": {
    "title": "研究タイトル",
    "authors": "著者名¹、共著者名²",
    "affiliation": "¹〇〇大学 △△科、²□□研究所",
    "subtitle": "第XX回〇〇学会",
    "theme": "academic-blue",
    "date": "2025年11月",
    "presentation_type": "basic-research",
    "language": "ja"
  },
  "slides": [
    {
      "type": "title"
    },
    {
      "type": "text-only",
      "heading": "背景",
      "body": "気管軟骨欠損は...\n\n・従来の治療法には限界がある\n・新しいアプローチが求められている"
    },
    {
      "type": "two-column",
      "heading": "実験方法",
      "body": "iPS細胞からMSCを誘導し...",
      "image": "images/fig_p003_01.jpeg",
      "image_caption": "Figure 1. iMSC 誘導プロトコル"
    },
    {
      "type": "figure-focus",
      "heading": "結果: 組織学的評価",
      "body": "移植12週後の組織切片では...",
      "image": "images/fig_p005_01.jpeg",
      "image_caption": "Figure 3. HE・Alcian blue 染色"
    },
    {
      "type": "data-table",
      "heading": "定量データ",
      "body": "軟骨面積は有意に増加",
      "table_html": "<table><thead><tr><th>Group</th><th>Area (mm²)</th><th>p</th></tr></thead><tbody><tr><td>iMSC</td><td>12.3±2.1</td><td>&lt;0.01</td></tr><tr><td>Control</td><td>3.1±1.4</td><td>-</td></tr></tbody></table>",
      "table_caption": "Table 1. 軟骨再生面積の比較"
    },
    {
      "type": "section-break",
      "heading": "考察"
    },
    {
      "type": "text-only",
      "heading": "結論",
      "body": "1. iPS由来MSCは気管軟骨再生に有効\n2. 12週で有意な軟骨組織形成を確認\n3. 臨床応用への可能性を示唆"
    },
    {
      "type": "conclusion"
    }
  ]
}
```

#### スライドタイプ

| type | 説明 | 必須フィールド | オプション |
|------|------|---------------|----------|
| `title` | タイトルスライド（meta から自動生成） | なし | — |
| `conclusion` | 謝辞スライド（meta から自動生成） | なし | — |
| `section-break` | セクション区切り | `heading` | — |
| `text-only` | テキストのみ | `heading`, `body` | — |
| `two-column` | テキスト＋画像 | `heading`, `body`, `image`, `image_caption` | — |
| `figure-focus` | 図を大きく表示 | `heading`, `image`, `image_caption` | `body` |
| `data-table` | テーブル表示 | `heading`, `table_html`, `table_caption` | `body` |

#### body テキストの書き方

- `\n\n` で段落区切り
- `・` / `- ` / `* ` で始まる行 → 箇条書きとして自動検出
- `1. ` / `1) ` で始まる行 → 番号付きリストとして自動検出
- 1スライドあたり4段落以内（1280×720 に収まるように）
- 箇条書きは5項目以内

#### 画像パスの指定

PDF から画像を抽出する場合:
1. まず `extract_images.py` を実行して画像を取得
2. `images_index.json` で利用可能な画像を確認
3. slide_plan.json で `images/fig_p003_01.jpeg` のように相対パスで指定

```bash
# 画像抽出
python builder/extract_images.py input.pdf output_dir/images/

# 画像一覧確認
cat output_dir/images/images_index.json
```

#### テーマの選択

| テーマ名 | 特徴 | 推奨用途 |
|---------|------|---------|
| `academic-blue` | 青基調、落ち着いた | 学会発表（デフォルト） |
| `medical-teal` | ティール基調、医療向け | 医学系学会 |
| `modern-minimal` | インディゴ基調、モダン | ゼミ・勉強会 |

### Phase 3: HTML 生成

slide_plan.json を出力ディレクトリに保存し、ビルダーを実行する。

```bash
# slide_plan.json から HTML 生成（出力先は自動で output/<名前>_日時/ に決まる）
cd D:\development\slidekit
python -m builder slide_plan.json

# テーマを指定する場合
python -m builder slide_plan.json --theme medical-teal

# 出力先を明示する場合
python -m builder slide_plan.json --output ./output/my_deck/
```

生成されるファイル:
```
D:\development\slidekit\output\
└── mizuno_20260407_2130/     ← 入力名 + タイムスタンプで自動生成
    ├── 001.html              ← タイトル
    ├── 002.html              ← 背景
    ├── ...
    ├── 015.html              ← 謝辞
    ├── index.html            ← ビューア（矢印キー操作・PDF出力）
    └── images/               ← 抽出画像
```

`--output` を省略すると `output/<入力名>_YYYYMMDD_HHMM/` に自動で分けられる。

### Phase 4: 確認・修正

ブラウザで `index.html` を開いて確認する。

```bash
# Windows
start output/index.html

# または agent-browser で確認
npx agent-browser batch "open file:///D:/development/slidekit/output/index.html" "wait 3" "snapshot"
```

**操作方法:**
- `→` / `Space`: 次のスライド
- `←`: 前のスライド
- `F`: 全画面トグル
- PDF ボタン: PDF 保存

修正が必要な場合:
1. `slide_plan.json` を編集して再生成
2. または個別の HTML ファイルを直接編集

---

## 高品質モード: slidekit-create 連携

デザインの自由度を最大化したい場合は、`--export-md` で Markdown を書き出し、`/slidekit-create` に渡す。

### フロー

```
PDF → python -m builder paper.pdf --export-md
        ↓
    output/<名前>_日時/
    ├── content.md    ← 論文内容 + 画像パス入り Markdown
    └── images/       ← 抽出画像
        ↓
    Claude が content.md を読み、必要に応じてメタ情報を修正
        ↓
    /slidekit-create で Phase 1「参考ファイル」として content.md を指定
        ↓
    43パターンから最適なレイアウトを選んで HTML 生成
```

### コマンド

```bash
cd D:\development\slidekit

# 1. Markdown + 画像を書き出す
python -m builder paper.pdf --export-md

# 2. Claude に content.md を渡して slidekit-create を起動
#    → Phase 1 で「参考ファイル」として content.md のパスを指定
#    → Phase 2 でデザイン（スタイル・テーマ・カラー）を決定
#    → Phase 3〜4 で 43 パターンからスライドを生成
```

### 注意

- PDF からの自動抽出ではメタ情報（タイトル・著者・所属）がずれる場合がある。Claude が content.md を読んだ際に正しく修正すること。
- 画像は `output/<名前>/images/` に抽出済みなので、slidekit-create の出力先を同じフォルダにすれば画像パスがそのまま使える。

---

## 使い方の例

### 例1: 論文 PDF からスライド作成

```
ユーザー: この論文からスライドを作って
         PDF/paper.pdf

Claude:
  1. PDF を読み取り
  2. 画像を抽出: python builder/extract_images.py paper.pdf output/images/
  3. slide_plan.json を設計（15枚構成）
  4. 生成: python -m builder slide_plan.json --output ./output/
  5. ブラウザで確認
```

### 例2: フォルダ入力

```
ユーザー: この研究データからスライドを作って
         input_folder/ (meta.json + テキスト + 画像)

Claude:
  1. フォルダ内容を確認
  2. meta.json からメタ情報を取得
  3. 直接ビルダーで生成（自動モード）:
     python -m builder ./input_folder/ --output ./output/
  4. またはより良い構成にしたい場合:
     slide_plan.json を手動設計 → ビルダー実行
```

### 例3: 学会ポスター作成

```
ユーザー: この論文でポスターを作って
         PDF/paper.pdf

Claude:
  1. PDF を読み取り
  2. python -m builder paper.pdf --poster
  3. ブラウザで poster.html を開いて確認
  4. Ctrl+P → A0 サイズで PDF 保存
```

A1 サイズの場合:
```bash
python -m builder paper.pdf --poster --size a1
```

### 例4: テキストからスライド作成

```
ユーザー: この内容でゼミ発表スライドを作って
         （テキストを直接入力）

Claude:
  1. テキストをファイルに保存
  2. slide_plan.json を設計（10枚構成）
  3. 生成: python -m builder slide_plan.json --output ./output/
```

---

## チェックリスト（Phase 4 で確認）

- [ ] タイトル・著者・所属が正しい
- [ ] セクション区切りの位置が適切
- [ ] 図がキャプション付きで正しく表示されている
- [ ] テキストがスライドからはみ出していない
- [ ] テーブルが読みやすい
- [ ] ストーリーの流れが自然
- [ ] 枚数が発表時間に対して適切
