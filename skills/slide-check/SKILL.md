---
name: slide-check
description: "生成済み SlideKit HTML スライドを agent-browser で開き、DOM構造の確認・スクリーンショット撮影・修正指示に基づく編集・再確認を行うインタラクティブなスライド調整スキル。'スライド確認', 'スライド修正', 'slide-check', 'レイアウト修正', 'フォントを大きく', 'デザイン変更' で起動。"
---

# slide-check — SlideKit スライド確認・修正

生成済みの SlideKit HTML スライド（001.html〜NNN.html + index.html）を **agent-browser** で開き、確認 → 修正 → 再確認をインタラクティブに繰り返す。

## 前提

```bash
npm i -g agent-browser
```

---

## ステップ1: 対象フォルダの特定

**ユーザーに出力フォルダのパスを聞く。**

```
確認・修正するスライドフォルダのパスを教えてください。
（例: D:\development\slidekit\output\mizuno_20260407_2130）
```

フォルダ内に `index.html` と `001.html` があることを確認する。

---

## ステップ2: ローカルサーバー起動 + agent-browser で開く

### サーバー起動

```bash
cd "<スライドフォルダ>" && npx serve -l 3556 .
```

- `run_in_background: true` で起動
- ユーザーに `http://localhost:3556/index.html` をブラウザで開けることを伝える

### agent-browser でビューア（index.html）を開く

```bash
npx agent-browser batch \
  "open http://localhost:3556/index.html" \
  "wait 3" \
  "snapshot"
```

### 個別スライドを直接開く場合

```bash
# 特定のスライドを確認（例: 3枚目）
npx agent-browser batch \
  "open http://localhost:3556/003.html" \
  "wait 2" \
  "snapshot"
```

> SlideKit は1スライド=1ファイルなので、個別に直接開ける。ビューア経由で矢印キー操作するよりも、直接 `NNN.html` を開くほうが確実。

---

## ステップ3: 現状の報告

snapshot 結果をもとに、スライド構成を報告する：

```
スライドフォルダ: output/mizuno_20260407_2130/
全16スライド:

  001.html: タイトル — "Rat Tracheal Cartilage Regeneration..."
  002.html: テキスト — "Background"
  003.html: テキスト — "Objective"
  004.html: 区切り — "Methods"
  005.html: 2カラム — "iMSC Induction Protocol" + Figure 1
  ...

どのスライドを修正しますか？（番号で指定）
```

---

## ステップ4: 修正の実行

ユーザーの指示に基づき、個別の HTML ファイルを直接編集する。

### SlideKit 固有の注意点

SlideKit は **Tailwind CSS** でスタイリングされている。修正方法：

| 修正内容 | 方法 |
|---------|------|
| フォントサイズ変更 | Tailwind クラスを変更（`text-3xl` → `text-5xl`） |
| 色の変更 | `.bg-brand-*` / `.text-brand-*` のカスタム CSS を `<style>` 内で変更 |
| レイアウト変更 | Tailwind の flex/grid クラスを変更（`w-2/5` → `w-1/2`） |
| 余白調整 | `p-*`, `m-*`, `gap-*` クラスを変更 |
| 画像サイズ | `max-h-*` クラスまたは inline style |
| テキスト追加/変更 | `<p>`, `<h1>`, `<li>` を直接編集 |

### よくある修正パターン

#### フォントサイズ拡大

```html
<!-- 変更前 -->
<h1 class="text-5xl font-black text-brand-dark leading-tight mb-6">タイトル</h1>

<!-- 変更後 -->
<h1 class="text-6xl font-black text-brand-dark leading-tight mb-6">タイトル</h1>
```

Tailwind フォントサイズ早見表:
| クラス | サイズ |
|--------|--------|
| `text-xs` | 0.75rem (12px) |
| `text-sm` | 0.875rem (14px) |
| `text-base` | 1rem (16px) |
| `text-lg` | 1.125rem (18px) |
| `text-xl` | 1.25rem (20px) |
| `text-2xl` | 1.5rem (24px) |
| `text-3xl` | 1.875rem (30px) |
| `text-4xl` | 2.25rem (36px) |
| `text-5xl` | 3rem (48px) |
| `text-6xl` | 3.75rem (60px) |

#### 画像サイズ変更

```html
<!-- 変更前 -->
<img src="images/fig.jpeg" class="max-h-96 max-w-full object-contain" />

<!-- 変更後（大きく） -->
<img src="images/fig.jpeg" class="max-h-full max-w-full object-contain" />
```

#### 2カラム比率変更

```html
<!-- 変更前: 40:60 -->
<div class="w-2/5">テキスト</div>
<div class="w-3/5">画像</div>

<!-- 変更後: 50:50 -->
<div class="w-1/2">テキスト</div>
<div class="w-1/2">画像</div>
```

#### テーマカラー変更

各スライドの `<style>` ブロック内:

```css
/* 変更前 */
.bg-brand-accent { background-color: #2b6cb0; }

/* 変更後 */
.bg-brand-accent { background-color: #6366f1; }
```

> **注意**: SlideKit は各スライドが独立 HTML なので、テーマカラーを変える場合は**全ファイルの `<style>` を一括変更**する必要がある。以下のコマンドで一括置換：

```bash
# 全スライドのアクセントカラーを一括変更
cd "<スライドフォルダ>"
sed -i 's/#2b6cb0/#6366f1/g' 0*.html
```

### 編集時の注意

- **バックアップ**: 日本語を含むファイルの編集前にバックアップを作成（`.bak`）
- **最小限の変更**: ユーザーが指示した箇所のみ変更
- **PPTX 互換性**: テキストは `<p>` / `<h*>` に入れる。`<div>` 直打ち禁止
- **JavaScript 禁止**: スライド内に JS を追加しない

---

## ステップ5: 変更後の確認

修正後、agent-browser で該当スライドを再確認する：

```bash
# 修正したスライドを直接開いて確認
npx agent-browser batch \
  "open http://localhost:3556/005.html" \
  "wait 2" \
  "snapshot"
```

スクリーンショットが必要な場合：

```bash
mkdir -p "<スライドフォルダ>/screenshots"
npx agent-browser screenshot --screenshot-dir "<スライドフォルダ>/screenshots"
```

保存されたスクリーンショットを Read ツールで読み取り、視覚的に確認する。

---

## ステップ6: 画像マーキングによる修正指示

ユーザーがスクリーンショットにペンで書き込んで修正指示を出すことができる。

| マーク | 意味 | 操作 |
|--------|------|------|
| **スラッシュ `/`** | ここで改行 | `<br>` 挿入 |
| **波線 `〜`** | 改行しない | `&nbsp;` に置換 |
| **丸囲み `○`** | 拡大 | サイズクラスを大きく |
| **×印 `✕`** | 縮小/削除 | サイズ縮小 or 非表示 |
| **矢印 `→`** | 位置移動 | レイアウト変更 |
| **テキスト書き込み** | そのまま指示 | 内容に応じて対応 |

処理手順：
1. Read ツールでマーキング画像を読み取る
2. マークの位置を HTML 要素と照合
3. HTML を編集
4. agent-browser で再確認

---

## ステップ7: スライドの追加・削除・並び替え

### スライド追加

新しいスライドを追加する場合は `slide_plan.json` を編集して再生成するのが最も確実。

```bash
# slide_plan.json に新しいスライド定義を追加してから:
cd D:\development\slidekit
python -m builder slide_plan.json --output <同じフォルダ>
```

手動で追加する場合は、既存スライドをコピーして内容を書き換える：

```bash
cp 005.html 005b.html  # コピーして編集
```

### スライド削除

不要なスライドの HTML ファイルを削除し、残りをリネーム：

```bash
rm 008.html
# 009→008, 010→009, ... のリネームが必要
```

> **推奨**: slide_plan.json から該当スライドを削除して再生成するほうが安全。

### 並び替え

ファイルをリネームして順序を変更：

```bash
mv 005.html tmp.html
mv 006.html 005.html
mv tmp.html 006.html
```

その後 index.html を再生成する必要がある。

---

## ステップ8: PDF 保存

```
ブラウザで index.html を開き：
1. Ctrl+P → 「PDF に保存」
2. 「背景のグラフィック」を ON にする
3. 余白: なし
4. 保存
```

> SlideKit の index.html には `@media print` CSS が含まれており、全スライドが page-break で分割される。

---

## ステップ9: 繰り返し・完了

ステップ4〜7 を繰り返し、ユーザーが満足したら完了。

最後にサマリーを報告：

```
スライド調整完了:
  フォルダ: output/mizuno_20260407_2130/

  変更内容:
    - 001.html: タイトルフォントサイズ拡大（text-5xl → text-6xl）
    - 005.html: 画像を拡大（max-h-96 → max-h-full）
    - 009.html: テキスト内容を日本語に修正

  確認方法:
    http://localhost:3556/index.html をブラウザで開いて最終確認
```

---

## agent-browser コマンドリファレンス

| コマンド | 用途 |
|---------|------|
| `npx agent-browser batch "open <url>" "wait N" "snapshot"` | ページを開いて DOM 構造を取得 |
| `npx agent-browser snapshot` | 現在のページの DOM 構造を取得 |
| `npx agent-browser screenshot --screenshot-dir <dir>` | スクリーンショット保存 |
| `npx agent-browser click @eN` | 要素をクリック |
| `npx agent-browser batch "open <url>" "wait N" "screenshot"` | 開いて即スクリーンショット |

---

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `agent-browser` が見つからない | `npm i -g agent-browser` |
| snapshot が空 | `wait` を長くする（3→5） |
| CSS が効かない | インターネット接続を確認（Tailwind / Font Awesome は CDN） |
| 画像が表示されない | `images/` フォルダがスライドフォルダ直下にあるか確認 |
| テーマ変更が一部スライドに適用されない | 各 HTML の `<style>` を個別に変更する必要あり（sed で一括置換推奨） |
| サーバーが起動済みでポート重複 | `npx serve -l 3557 .` で別ポートを使う |
