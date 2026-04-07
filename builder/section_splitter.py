"""
テキストのセクション自動分割モジュール（html-poster-slides 用）

単一テキストファイルに背景〜結論まで含まれている場合でも
論文構造に従って自動的にセクション分割する。

分割の3段階アプローチ:
  Level 1: Markdown・番号・記号見出しで検出（高精度）
  Level 2: 「背景」「方法」「結果」等キーワード段落で検出（中精度）
  Level 3: 段落を比率（20/20/30/20/10）で配分（フォールバック）

使い方（単体）:
  from section_splitter import split_sections
  sections = split_sections("paper.txt")
  # -> {"background": "...", "methods": "...", ...}

  from section_splitter import split_text
  sections = split_text(text_string)
"""

import re
import os
from pathlib import Path


# ──────────────────────────────────────────────────
# セクション名の正規化マッピング
# 検出キーワード → 標準セクション名
# ──────────────────────────────────────────────────
SECTION_KEYWORDS: dict[str, list[str]] = {
    "background": [
        "背景", "はじめに", "序論", "緒言", "緒論", "introduction", "background",
        "はじめ", "研究背景", "研究の背景",
    ],
    "objective": [
        "目的", "研究目的", "本研究の目的", "aim", "objective", "purpose",
    ],
    "methods": [
        "方法", "材料と方法", "材料・方法", "対象と方法", "対象・方法",
        "methods", "materials", "materials and methods", "subjects", "patients",
        "study design", "methodology",
    ],
    "results": [
        "結果", "成績", "results", "findings", "outcomes",
    ],
    "discussion": [
        "考察", "discussion",
    ],
    "conclusion": [
        "結論", "まとめ", "おわりに", "総括", "conclusion", "conclusions",
        "summary", "concluding remarks",
    ],
    "references": [
        "参考文献", "文献", "引用文献", "references", "bibliography",
    ],
    "acknowledgements": [
        "謝辞", "謝辞・利益相反", "acknowledgements", "acknowledgments",
        "funding", "conflict of interest",
    ],
}

# 標準セクション名の順番（スライド生成時の配置順）
SECTION_ORDER = [
    "background",
    "objective",
    "methods",
    "results",
    "discussion",
    "conclusion",
    "references",
    "acknowledgements",
]

# フォールバック配分比率（比率の合計 = 100）
FALLBACK_RATIO = {
    "background": 20,
    "methods":    20,
    "results":    30,
    "discussion": 20,
    "conclusion": 10,
}


def split_sections(filepath: str | Path) -> dict[str, str]:
    """
    テキストファイルを読み込んでセクション辞書を返す。

    Args:
        filepath: .txt または .md ファイルのパス

    Returns:
        {"background": "...", "methods": "...", ...}
        キーが存在しない場合はそのセクションは空。
    """
    filepath = Path(filepath)
    encoding = _detect_encoding(filepath)
    text = filepath.read_text(encoding=encoding, errors="replace")
    return split_text(text)


def split_text(text: str) -> dict[str, str]:
    """
    テキスト文字列をセクション辞書に分割する。

    Level 1 → Level 2 → Level 3 の順で試みる。
    """
    text = text.strip()
    if not text:
        return {}

    # Level 1: 見出し行で分割
    result = _split_by_headings(text)
    if _is_valid_split(result):
        return _normalize_sections(result)

    # Level 2: キーワード段落で分割
    result = _split_by_keywords(text)
    if _is_valid_split(result):
        return _normalize_sections(result)

    # Level 3: 比率フォールバック
    return _split_by_ratio(text)


# ──────────────────────────────────────────────────
# Level 1: 見出し行検出
# ──────────────────────────────────────────────────

# 見出しパターン（優先順）
_HEADING_PATTERNS = [
    # Markdown: # 背景 / ## Background
    re.compile(r'^#{1,4}\s+(.+)$', re.MULTILINE),
    # 番号付き: 1. 背景 / 1） 方法 / （1）結果
    re.compile(r'^[（(]?\d+[)）.．。]\s*(.+)$', re.MULTILINE),
    # 全角番号: １．背景
    re.compile(r'^[１２３４５６７８９０]+[.．。）)]\s*(.+)$', re.MULTILINE),
    # 記号: ■ 背景 / ▶方法 / 【結果】 / ◆考察
    re.compile(r'^[■▶▷◆●○◎▼►【〔\[]\s*(.+?)[\]】〕]?\s*$', re.MULTILINE),
]


def _split_by_headings(text: str) -> dict[str, list[str]]:
    """
    見出しパターンにマッチした行を区切りとして分割する。
    戻り値: {"raw_heading_text": [content_lines, ...], ...}
    """
    for pattern in _HEADING_PATTERNS:
        matches = list(pattern.finditer(text))
        if len(matches) >= 2:
            return _extract_sections_from_matches(text, matches)
    return {}


def _extract_sections_from_matches(
    text: str, matches: list[re.Match]
) -> dict[str, list[str]]:
    """マッチ位置を区切りとしてテキストをセクションに分割する"""
    sections: dict[str, list[str]] = {}
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            sections[heading] = content
    return sections


# ──────────────────────────────────────────────────
# Level 2: キーワード段落検出
# ──────────────────────────────────────────────────

def _split_by_keywords(text: str) -> dict[str, list[str]]:
    """
    段落の先頭行がセクションキーワードと一致するか判定して分割する。
    """
    paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    if not paragraphs:
        return {}

    sections: dict[str, list[str]] = {}
    current_section: str | None = None
    current_lines: list[str] = []

    for para in paragraphs:
        first_line = para.split('\n')[0].strip()
        detected = _match_section_keyword(first_line)

        if detected:
            # 前のセクションを保存
            if current_section and current_lines:
                sections[current_section] = "\n\n".join(current_lines)
            current_section = detected
            # 見出し行を除いた残りをコンテンツとして追加
            rest = "\n".join(para.split('\n')[1:]).strip()
            current_lines = [rest] if rest else []
        else:
            if current_section is not None:
                current_lines.append(para)
            # current_section が未設定の場合はプリアンブルとして無視

    # 最後のセクションを保存
    if current_section and current_lines:
        sections[current_section] = "\n\n".join(current_lines)

    return sections


def _match_section_keyword(line: str) -> str | None:
    """
    行テキストがセクションキーワードと一致すれば標準セクション名を返す。
    一致しなければ None。
    """
    normalized = line.lower().strip().rstrip(':：。')
    # 記号・番号プレフィックスを除去
    normalized = re.sub(r'^[■▶▷◆●○◎▼►【〔\[（(]?\d*[)）.．。\]】〕]?\s*', '', normalized)

    for section_name, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            if normalized == kw.lower() or normalized.startswith(kw.lower()):
                return section_name
    return None


# ──────────────────────────────────────────────────
# Level 3: 比率フォールバック
# ──────────────────────────────────────────────────

def _split_by_ratio(text: str) -> dict[str, str]:
    """
    段落を比率に従ってセクションに割り当てる（最終手段）。
    """
    paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    if not paragraphs:
        return {"background": text}

    total = len(paragraphs)
    sections: dict[str, str] = {}
    idx = 0

    for section_name, ratio in FALLBACK_RATIO.items():
        count = max(1, round(total * ratio / 100))
        chunk = paragraphs[idx: idx + count]
        if chunk:
            sections[section_name] = "\n\n".join(chunk)
        idx += count
        if idx >= total:
            break

    # 余りがあれば最後のセクションに追加
    if idx < total:
        last_key = list(sections.keys())[-1]
        sections[last_key] += "\n\n" + "\n\n".join(paragraphs[idx:])

    return sections


# ──────────────────────────────────────────────────
# 正規化・ユーティリティ
# ──────────────────────────────────────────────────

def _normalize_sections(raw: dict[str, str | list]) -> dict[str, str]:
    """
    生のセクション辞書（キーが日本語・英語混在）を
    標準セクション名にマッピングし直す。
    """
    normalized: dict[str, str] = {}

    for raw_key, content in raw.items():
        # list の場合は結合
        if isinstance(content, list):
            content = "\n\n".join(content)

        detected = _match_section_keyword(raw_key)
        std_key = detected if detected else raw_key.lower().replace(' ', '_')

        # 同じセクションが複数あれば結合
        if std_key in normalized:
            normalized[std_key] += "\n\n" + content
        else:
            normalized[std_key] = content

    return normalized


def _is_valid_split(sections: dict) -> bool:
    """
    分割結果が有効かチェック（2セクション以上かつ中身あり）。
    """
    non_empty = {k: v for k, v in sections.items() if v and str(v).strip()}
    return len(non_empty) >= 2


def _detect_encoding(filepath: Path) -> str:
    """
    ファイルのエンコーディングを推定する。
    UTF-8 → UTF-8-BOM → Shift_JIS → Latin-1 の順で試みる。
    """
    for enc in ("utf-8-sig", "utf-8", "shift_jis", "cp932", "latin-1"):
        try:
            filepath.read_text(encoding=enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8"


def get_ordered_sections(sections: dict[str, str]) -> list[tuple[str, str]]:
    """
    セクション辞書を標準順序でソートして (section_name, content) のリストを返す。
    SECTION_ORDER にないキーは末尾に追加。
    """
    ordered = []
    seen = set()

    for key in SECTION_ORDER:
        if key in sections and sections[key].strip():
            ordered.append((key, sections[key]))
            seen.add(key)

    for key, val in sections.items():
        if key not in seen and val.strip():
            ordered.append((key, val))

    return ordered


def section_to_label(section_name: str, lang: str = "ja") -> str:
    """
    標準セクション名を表示用ラベルに変換する。
    例: "background" → "背景"（ja）または "Background"（en）
    """
    labels_ja = {
        "background":      "背景",
        "objective":       "研究目的",
        "methods":         "方法",
        "results":         "結果",
        "discussion":      "考察",
        "conclusion":      "結論",
        "references":      "参考文献",
        "acknowledgements":"謝辞",
    }
    labels_en = {
        "background":      "Background",
        "objective":       "Objective",
        "methods":         "Methods",
        "results":         "Results",
        "discussion":      "Discussion",
        "conclusion":      "Conclusion",
        "references":      "References",
        "acknowledgements":"Acknowledgements",
    }
    mapping = labels_ja if lang == "ja" else labels_en
    return mapping.get(section_name, section_name.replace("_", " ").title())


# ──────────────────────────────────────────────────
# CLI / テスト用エントリポイント
# ──────────────────────────────────────────────────

def _print_result(sections: dict[str, str], verbose: bool = False) -> None:
    """分割結果をコンソールに表示する"""
    print(f"\n分割結果: {len(sections)} セクション")
    print("=" * 50)
    for key, content in get_ordered_sections(sections):
        label = section_to_label(key)
        preview = content[:80].replace('\n', ' ') + ('...' if len(content) > 80 else '')
        print(f"  [{key}] {label}")
        if verbose:
            print(f"    {preview}")
    print("=" * 50)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("使い方: python section_splitter.py <テキストファイル> [-v]")
        print("  例: python section_splitter.py paper.txt -v")
        sys.exit(1)

    verbose = "-v" in sys.argv
    path = sys.argv[1]

    if not os.path.exists(path):
        print(f"エラー: ファイルが見つかりません: {path}")
        sys.exit(1)

    sections = split_sections(path)
    _print_result(sections, verbose=verbose)
