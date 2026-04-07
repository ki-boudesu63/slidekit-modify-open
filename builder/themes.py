"""
テーマ定義（Tailwind カスタムカラークラス）

各テーマは <style> ブロックとして全スライドに埋め込まれる。
"""

from __future__ import annotations

THEMES: dict[str, dict[str, str]] = {
    "academic-blue": {
        "brand_dark":    "#1a365d",
        "brand_accent":  "#2b6cb0",
        "brand_warm":    "#ebf8ff",
        "font_primary":  "Noto Sans JP",
        "font_accent":   "Lato",
        "brand_icon":    "fa-microscope",
    },
    "medical-teal": {
        "brand_dark":    "#065f46",
        "brand_accent":  "#10b981",
        "brand_warm":    "#ecfdf5",
        "font_primary":  "Noto Sans JP",
        "font_accent":   "Inter",
        "brand_icon":    "fa-stethoscope",
    },
    "modern-minimal": {
        "brand_dark":    "#1f2937",
        "brand_accent":  "#6366f1",
        "brand_warm":    "#eef2ff",
        "font_primary":  "Noto Sans JP",
        "font_accent":   "Inter",
        "brand_icon":    "fa-lightbulb",
    },
}


def get_theme(name: str) -> dict[str, str]:
    """テーマ辞書を返す。未知のテーマ名なら academic-blue にフォールバック。"""
    return THEMES.get(name, THEMES["academic-blue"])


def get_theme_css(name: str) -> str:
    """<style> ブロック内に埋め込む CSS 文字列を返す。"""
    t = get_theme(name)
    return f"""body {{ margin: 0; padding: 0; font-family: '{t["font_primary"]}', sans-serif; overflow: hidden; }}
.font-accent {{ font-family: '{t["font_accent"]}', sans-serif; }}
.slide {{ width: 1280px; height: 720px; position: relative; overflow: hidden; }}
.bg-brand-dark {{ background-color: {t["brand_dark"]}; }}
.text-brand-dark {{ color: {t["brand_dark"]}; }}
.bg-brand-accent {{ background-color: {t["brand_accent"]}; }}
.text-brand-accent {{ color: {t["brand_accent"]}; }}
.border-brand-accent {{ border-color: {t["brand_accent"]}; }}
.bg-brand-warm {{ background-color: {t["brand_warm"]}; }}
.text-brand-warm {{ color: {t["brand_warm"]}; }}"""


def get_google_fonts_url(name: str) -> str:
    """Google Fonts の CSS URL を返す。"""
    t = get_theme(name)
    primary = t["font_primary"].replace(" ", "+")
    accent = t["font_accent"].replace(" ", "+")
    return (
        f"https://fonts.googleapis.com/css2?"
        f"family={primary}:wght@300;400;500;700;900"
        f"&family={accent}:wght@400;600;700"
        f"&display=swap"
    )
