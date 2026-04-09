---
name: slidekit-build
description: "論文PDF・研究テキスト・画像・Markdownから、学会スライドまたはポスターを自動生成する。Claude が内容を読み取り、最適な構成を設計して slide_plan.json を作成し、ビルダーで HTML を生成する。'スライドを作って', '論文からスライド', 'ポスター作って', 'slidekit build', 'プレゼン作成' で起動。"
---

# SlideKit Build — 論文→スライド/ポスター自動生成

---

## 出力モード

ユーザーの依頼に応じて2つの出力モードがある。**最初に必ずどちらかを確認する。**

| モード | 出力 | コマンド |
|--------|------|---------|
| **スライド** | 001.html〜NNN.html + index.html（矢印キー操作） | `python -m builder slide_plan.json` |
| **ポスター** | poster.html 1枚（A0 or A1、印刷用） | `python -m builder slide_plan.json --poster` |

```
ユーザーに聞く:
  スライドとポスターのどちらを作成しますか？
  1. スライド（学会口演・ゼミ発表）
  2. ポスター（学会ポスター発表、A0/A1）
```

ユーザーが「スライド作って」「ポスター作って」と明示していればスキップしてよい。

---

## 入力パターン

ユーザーが提供する可能性がある入力形式は以下の通り。**どの形式でも同じワークフローで対応できる。**

| 入力 | 説明 | Claude がやること |
|------|------|-----------------|
| **PDF** | 論文 PDF | テキストを Read で読む。画像を `extract_images.py` で抽出 |
| **テキストファイル** (.txt / .md) | 研究ノートやドラフト | 内容を Read で読んでセクション構造を把握 |
| **画像付き Markdown** (.md) | 本文 + `![caption](path)` で画像埋め込み | 内容を Read で読む。画像パスを slide_plan.json に転記 |
| **フォルダ** | meta.json + テキスト + 画像 + CSV/Excel | フォルダ内容を確認してメタ情報と素材を把握 |
| **画像のみ** | 実験結果の写真やグラフ | 画像パスを把握。テキストはユーザーに聞く or 生成 |
| **口頭説明** | チャットで内容を直接説明 | テキストとして整理して slide_plan.json を設計 |

### 画像の扱い

- **PDF の場合**: まず画像を抽出する
  ```bash
  cd /path/to/slidekit
  python builder/extract_images.py input.pdf output_dir/images/
  cat output_dir/images/images_index.json
  ```
- **フォルダ / Markdown の場合**: ユーザーが指定したパスをそのまま使用
- **slide_plan.json での画像参照**: `"image": "images/fig_p003_01.jpeg"` のように相対パスで指定

---

## ワークフロー

```
入力（PDF / テキスト / Markdown / フォルダ / 口頭）
    ↓
Phase 1: 内容読み取り
    ↓
Phase 1.5: 出力モード確認（スライド or ポスター）+ 言語確認（日本語 or 英語）
    ↓
Phase 2: 構成設計（slide_plan.json + slide_content.json 作成）
    ↓
Phase 2.5: レビュー（任意 — slide_reviewer.html で確認・編集）
    ↓
Phase 3: HTML 生成
    ↓
Phase 4: 確認・修正（/slide-check）
```

### Phase 1: 内容読み取り

**PDF の場合:**
1. Read ツールで PDF を読む（テキスト抽出）
2. 図版を `extract_images.py` で抽出
3. 論文の構造を理解（Abstract / Introduction / Methods / Results / Discussion / Conclusion）

**テキスト / Markdown の場合:**
1. Read ツールで内容を読む
2. Markdown 内の画像参照（`![caption](path)`）があればパスを記録
3. セクション構造を把握

**フォルダの場合:**
1. `ls` でファイル一覧を確認
2. `meta.json` があれば読む（タイトル・著者・所属）
3. テキスト・画像・表データの内容を把握

**画像のみ / 口頭説明の場合:**
1. 画像があれば Read で内容を確認
2. ユーザーに研究の内容（背景・方法・結果・結論）を聞く

### Phase 1.5: モード確認 + 言語確認

**出力モード確認**（ユーザーが未指定の場合）:
```
スライドとポスターのどちらを作成しますか？
1. スライド（学会口演・ゼミ発表）
2. ポスター（学会ポスター発表、A0/A1）
```

ポスターの場合、さらにサイズを確認:
```
ポスターサイズはどちらにしますか？
1. A0（841×1189mm、3カラム）— 標準
2. A1（594×841mm、2カラム）
```

**言語確認**（ユーザーが未指定の場合）:
```
スライドの言語はどちらにしますか？
1. 日本語（見出し・本文を日本語に翻訳）
2. 英語（原文のまま）
```

- 日本語の場合: 専門用語はカッコ書きで英語併記（例: 間葉系幹細胞（MSC））
- ユーザーが先に「日本語で」「英語で」と指定していればスキップ

### Phase 2: 構成設計

#### スライドモードの場合

slide_plan.json を設計する。

**設計の原則:**
1. 1スライド = 1メッセージ
2. テキストは箇条書き3〜5項目、本文は4段落以内
3. 図表を積極的に活用
4. 背景→目的→方法→結果→考察→結論のストーリーフロー
5. 10分発表 → 10〜15枚、20分発表 → 15〜20枚

**スライド構成テンプレート（基礎研究 15枚）:**

| # | type | 内容 |
|---|------|------|
| 1 | title | タイトル・著者・所属 |
| 2 | text-only | 背景・問題提起 |
| 3 | text-only | 研究目的・仮説 |
| 4 | section-break | 方法 |
| 5 | two-column | 実験材料（テキスト+図） |
| 6 | two-column | プロトコル（テキスト+フロー図） |
| 7 | section-break | 結果 |
| 8 | figure-focus | 結果1（組織学的所見） |
| 9 | two-column | 結果2（定量データ+グラフ） |
| 10 | figure-focus | 結果3（追加データ） |
| 11 | section-break | 考察 |
| 12 | text-only | 考察（解釈・比較） |
| 13 | text-only | 限界・今後の課題 |
| 14 | text-only | 結論 |
| 15 | conclusion | 謝辞 |

**臨床研究（12枚）:**

| # | type | 内容 |
|---|------|------|
| 1 | title | タイトル |
| 2 | text-only | 背景・臨床的意義 |
| 3 | text-only | 目的 |
| 4 | section-break | 方法 |
| 5 | two-column | 対象・選択基準 |
| 6 | data-table | 患者背景 |
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
| 2 | text-only | 導入 |
| 3 | text-only | 背景 |
| 4 | two-column | 方法 |
| 5 | figure-focus | 結果1 |
| 6 | figure-focus | 結果2 |
| 7 | text-only | 考察 |
| 8 | text-only | 限界 |
| 9 | text-only | Take-home message |
| 10 | conclusion | 謝辞 |

#### ポスターモードの場合

同じ slide_plan.json を使うが、**セクション区切り（section-break）は不要**。ビルダーが title / conclusion を除くスライド定義をセクションとしてカラムに均等振り分けする。

**ポスター用の構成テンプレート（8〜12セクション）:**

| # | type | 内容 |
|---|------|------|
| 1 | title | タイトル（自動でヘッダーに配置） |
| 2 | text-only | 背景・目的 |
| 3 | text-only | 仮説 |
| 4 | two-column | 方法（テキスト+実験スキーム図） |
| 5 | figure-focus | 結果1（主要な図） |
| 6 | figure-focus | 結果2 |
| 7 | two-column | 結果3（定量データ+グラフ） |
| 8 | text-only | 考察 |
| 9 | text-only | 結論 |
| 10 | conclusion | 謝辞（自動でフッターに配置） |

**ポスター生成時の注意:**
- A0（3カラム）: セクションが3カラムに均等に配置される
- A1（2カラム）: セクションが2カラムに均等に配置される
- 図は各セクション内に表示される（スライドとは異なり横並びではない）
- テキスト量は多めでOK（ポスターは読むもの）

### Phase 2.5: レビュー（任意）

Phase 2 で作成した slide_plan.json と slide_content.json を出力ディレクトリに保存したら、ユーザーに以下を伝える:

> 「slide_plan.json と slide_content.json を保存しました。」
>
> 1. **このまま生成する** — Phase 3 に進む
> 2. **レビューアプリで確認・編集する** — `slide_reviewer.html` をブラウザで開いて JSON を読み込み、内容や画像を編集してから再度このチャットに渡してください

- **1** → Phase 3 に進む
- **2** → ユーザーが編集済み JSON を渡すまで待機。渡された JSON を読み込み直して Phase 3 に進む
- ユーザーが「そのまま」「OK」「進めて」等と言った場合も Phase 3 に進む

**slide_content.json** は slidekit-create 用の素材データ（type なし）。ユーザーがレビューアプリの素材モードで編集し、`/slidekit-create` に渡して別デザインで作り直す場合に使う。

### Phase 3: HTML 生成

slide_plan.json を出力ディレクトリに保存し、ビルダーを実行する。

**スライドの場合:**
```bash
cd /path/to/slidekit
python -m builder slide_plan.json
# → output/<名前>_日時/001.html〜NNN.html + index.html
```

**ポスターの場合:**
```bash
cd /path/to/slidekit
python -m builder slide_plan.json --poster
# → output/<名前>_日時/poster.html

# A1 の場合
python -m builder slide_plan.json --poster --size a1
```

**テーマ指定:**
```bash
python -m builder slide_plan.json --theme medical-teal
```

**重要: 画像ファイルの配置**

slide_plan.json で `"image": "images/fig_xxx.jpeg"` と指定した場合、出力ディレクトリの `images/` に該当ファイルが必要。PDF から抽出した場合は自動でコピーされる。ユーザーが画像を直接指定した場合は手動でコピーする:

```bash
mkdir -p output/<名前>/images/
cp /path/to/fig01.png output/<名前>/images/
```

### Phase 4: 確認・修正

**スライドの場合:**
```bash
start output/<名前>/index.html
# → / Space: 次、←: 前、F: 全画面、PDF ボタン: PDF保存
```

**ポスターの場合:**
```bash
start output/<名前>/poster.html
# Ctrl+P → A0/A1 サイズで PDF 保存（「背景のグラフィック」ON）
```

修正が必要な場合:
1. slide_plan.json を編集して再生成
2. または `/slide-check` で個別 HTML を対話的に調整

---

## slide_plan.json スキーマ

スライドモード・ポスターモード共通で使用する。

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
    { "type": "title" },
    { "type": "text-only", "heading": "背景", "body": "テキスト..." },
    { "type": "two-column", "heading": "方法", "body": "...", "image": "images/fig01.jpeg", "image_caption": "Figure 1" },
    { "type": "figure-focus", "heading": "結果", "image": "images/fig02.jpeg", "image_caption": "Figure 2", "body": "所見..." },
    { "type": "data-table", "heading": "データ", "body": "...", "table_html": "<table>...</table>", "table_caption": "Table 1" },
    { "type": "section-break", "heading": "考察" },
    { "type": "conclusion" }
  ]
}
```

### スライドタイプ

| type | 説明 | 必須 | オプション |
|------|------|------|----------|
| `title` | タイトル（meta から自動生成） | — | — |
| `conclusion` | 謝辞（meta から自動生成） | — | — |
| `section-break` | セクション区切り（スライドのみ、ポスターでは無視） | `heading` | — |
| `text-only` | テキストのみ | `heading`, `body` | — |
| `two-column` | テキスト＋画像 | `heading`, `body`, `image`, `image_caption` | — |
| `figure-focus` | 図メイン | `heading`, `image`, `image_caption` | `body` |
| `data-table` | テーブル | `heading`, `table_html`, `table_caption` | `body` |

---

## slide_content.json スキーマ（slidekit-create 用）

slide_plan.json と同時に出力する。**type フィールドを含まない**素材データ。slidekit-create がレイアウトを自由に決定するための入力形式。

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
  "mode": "content",
  "slides": [
    {
      "heading": "背景",
      "body": "・高齢化に伴い救急外来の患者数が増加\n・トリアージの精度にばらつきがある",
      "images": []
    },
    {
      "heading": "方法",
      "body": "・単施設・前後比較研究\n・AI導入前後で比較",
      "images": [
        { "path": "images/fig01.jpeg", "caption": "Figure 1. 研究デザイン" }
      ]
    },
    {
      "heading": "結果",
      "body": "・待ち時間が26%短縮\n・トリアージ精度が78%→89%に向上",
      "images": [
        { "path": "images/fig02.jpeg", "caption": "Figure 2. 待ち時間の比較" },
        { "path": "images/fig03.jpeg", "caption": "Figure 3. 精度比較" }
      ]
    }
  ]
}
```

### slide_plan.json との違い

| | slide_plan.json | slide_content.json |
|---|---|---|
| `mode` | `"plan"` | `"content"` |
| `type` フィールド | あり（title, text-only, two-column 等） | **なし** |
| title / conclusion スライド | 含む | **含まない**（meta から自動生成） |
| section-break | 含む | **含まない** |
| 画像 | `image` + `image_caption`（1枚） | `images` 配列（**複数可**） |
| 用途 | builder CLI でそのまま HTML 生成 | slidekit-create に素材として渡す |

### Phase 2 での両ファイル生成手順

1. Phase 2 で slide_plan.json を設計する（従来通り）
2. slide_plan.json を出力ディレクトリに保存する
3. slide_plan.json から slide_content.json を生成して同じディレクトリに保存する:
   - `type` フィールドを除去
   - `title` / `conclusion` / `section-break` スライドを除去
   - `image` + `image_caption` → `images` 配列に変換
   - `"mode": "content"` を追加

---

### body テキストの書き方

- `\n\n` で段落区切り
- `・` / `- ` / `* ` で始まる行 → 箇条書き（自動検出）
- `1. ` / `1) ` で始まる行 → 番号付きリスト（自動検出）
- スライド: 4段落以内 / ポスター: 制限なし

### テーマ

| テーマ名 | 特徴 | 推奨用途 |
|---------|------|---------|
| `academic-blue` | 青基調 | 学会発表（デフォルト） |
| `medical-teal` | ティール | 医療系学会 |
| `modern-minimal` | インディゴ | ゼミ・勉強会 |

---

## 高品質モード: slidekit-create 連携

デザインの自由度を最大化したい場合（43パターン + 5スタイル × 5テーマ）。

```bash
# 1. PDF → Markdown + 両JSON + 画像を書き出す
python -m builder paper.pdf --export-md
# → content.md, slide_plan.json, slide_content.json が出力される

# 2. /slidekit-create で slide_content.json を参考ファイルとして渡す
#    （slide_content.json 優先。content.md は JSON がない場合のフォールバック）
```

- PDF からの自動抽出ではメタ情報がずれる場合がある → Claude が修正
- 画像は `output/<名前>/images/` に抽出済み → 同じフォルダを指定すれば参照可能
- レビューアプリ（`slide_reviewer.html`）で素材モードで編集してから create に渡すこともできる

---

## 使い方の例

### 例1: 論文 PDF → スライド

```
ユーザー: この論文から学会発表スライドを日本語で作って
         PDF/paper.pdf

Claude:
  1. PDF を読み取り → 構造把握
  2. 画像抽出: python builder/extract_images.py paper.pdf output/images/
  3. slide_plan.json を設計（日本語、15枚）
  4. python -m builder slide_plan.json
  5. ブラウザで確認 → 修正あれば /slide-check
```

### 例2: 論文 PDF → ポスター

```
ユーザー: この論文でA0ポスターを作って
         PDF/paper.pdf

Claude:
  1. PDF を読み取り → 構造把握
  2. 画像抽出: python builder/extract_images.py paper.pdf output/images/
  3. slide_plan.json を設計（ポスター用、10セクション）
  4. python -m builder slide_plan.json --poster
  5. ブラウザで poster.html を確認
  6. Ctrl+P → A0 で PDF 保存
```

### 例3: 研究データ（フォルダ）→ スライド

```
ユーザー: このフォルダの研究データからスライドを作って
         input_folder/ (テキスト + 画像)

Claude:
  1. フォルダ内容を確認（meta.json, テキスト, 画像一覧）
  2. slide_plan.json を設計
  3. python -m builder slide_plan.json --output input_folder/output/
  4. 確認
```

### 例4: 画像付き Markdown → スライド

```
ユーザー: この Markdown からスライドを作って
         research_notes.md (本文 + ![fig](path/to/img.png))

Claude:
  1. Markdown を読み取り → セクション・画像パスを把握
  2. slide_plan.json を設計（画像パスはそのまま転記）
  3. 画像を出力先にコピー
  4. python -m builder slide_plan.json
  5. 確認
```

### 例5: 口頭説明 → スライド

```
ユーザー: iPS細胞からMSCを作って気管軟骨を再生する研究について
         ゼミ発表用のスライドを10枚で作って

Claude:
  1. ユーザーの説明をもとにコンテンツを整理
  2. slide_plan.json を設計（ゼミ10枚テンプレート）
  3. python -m builder slide_plan.json
  4. 確認
```

---

## チェックリスト（Phase 4 で確認）

### スライド共通
- [ ] タイトル・著者・所属が正しい
- [ ] セクション区切りの位置が適切
- [ ] 図がキャプション付きで正しく表示されている
- [ ] テキストがスライドからはみ出していない
- [ ] ストーリーの流れが自然
- [ ] 枚数が発表時間に対して適切

### ポスター固有
- [ ] 3カラム（A0）/ 2カラム（A1）のバランスが良い
- [ ] 各セクションの文章量が適切（読める量）
- [ ] 図のサイズが十分大きい
- [ ] フッター（参考文献・連絡先）の内容が正しい
- [ ] Ctrl+P で印刷プレビューが正常（背景色・レイアウト）
