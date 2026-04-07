"""
SlideKit ビルダー

ContentBundle → SlideKit 形式 HTML ファイル群（001.html, 002.html, ... + index.html）
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .content_bundle import (
    ContentBundle, ImageEntry, TableEntry, ChartEntry,
    text_to_html, slug,
)
from .section_splitter import get_ordered_sections, section_to_label
from . import patterns


class SlideKitBuilder:
    """ContentBundle から SlideKit 形式の HTML スライドを生成する"""

    def build(self, bundle: ContentBundle, output_dir: Path | None = None) -> str:
        """
        スライドを生成し、出力ディレクトリパスを返す。

        1. ディレクトリ作成 + 画像コピー
        2. スライド HTML 生成
        3. 個別ファイル書き出し
        4. index.html 生成
        """
        out = Path(output_dir) if output_dir else Path(bundle.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        images_out = out / "images"
        images_out.mkdir(exist_ok=True)

        # 画像を出力ディレクトリにコピー
        self._copy_images(bundle, images_out)

        # スライド生成
        slides = self._render(bundle)

        # 個別ファイル書き出し
        for i, (_, html) in enumerate(slides):
            filename = f"{i + 1:03d}.html"
            (out / filename).write_text(html, encoding="utf-8")

        # index.html 生成
        self._write_index(out, bundle.title, len(slides))

        total = len(slides)
        print(f"生成完了: {total} スライド → {out}")
        return str(out)

    # ── レンダリング ──

    def _render(self, bundle: ContentBundle) -> list[tuple[str, str]]:
        """スライドの (タイトル, HTML) リストを返す"""
        if bundle._plan_slides:
            return self._render_plan_slides(bundle)
        return self._render_auto_slides(bundle)

    def _render_plan_slides(self, bundle: ContentBundle) -> list[tuple[str, str]]:
        """slide_plan.json のスライド定義からスライドを生成する"""
        slides: list[tuple[str, str]] = []
        plan = bundle._plan_slides
        total = len(plan)
        theme = bundle.theme

        for i, slide in enumerate(plan):
            slide_type = slide.get("type", "text-only")
            no = i + 1

            if slide_type == "title":
                html = patterns.render_cover_slide(
                    title=bundle.title,
                    authors=bundle.authors,
                    affiliation=bundle.affiliation,
                    date=bundle.date,
                    subtitle=bundle.subtitle,
                    theme_name=theme,
                )
                slides.append((bundle.title, html))

            elif slide_type == "conclusion":
                html = patterns.render_conclusion_slide(
                    title=bundle.title,
                    authors=bundle.authors,
                    affiliation=bundle.affiliation,
                    theme_name=theme,
                )
                slides.append(("謝辞", html))

            elif slide_type == "section-break":
                heading = slide.get("heading", "")
                # 章番号を推定（section-break の出現順）
                chapter = sum(1 for s in plan[:i + 1] if s.get("type") == "section-break")
                html = patterns.render_section_divider(
                    heading=heading,
                    chapter_no=chapter,
                    theme_name=theme,
                )
                slides.append((heading, html))

            elif slide_type == "text-only":
                heading = slide.get("heading", "")
                body = text_to_html(slide.get("body", ""))
                html = patterns.render_text_slide(
                    heading=heading,
                    body_html=body,
                    page_no=no,
                    total=total,
                    theme_name=theme,
                )
                slides.append((heading, html))

            elif slide_type == "two-column":
                heading = slide.get("heading", "")
                body = text_to_html(slide.get("body", ""))
                image = slide.get("image", "")
                caption = slide.get("image_caption", "")
                html = patterns.render_image_text_slide(
                    heading=heading,
                    body_html=body,
                    image_path=image,
                    caption=caption,
                    page_no=no,
                    total=total,
                    theme_name=theme,
                )
                slides.append((heading, html))

            elif slide_type == "figure-focus":
                heading = slide.get("heading", "")
                body = text_to_html(slide.get("body", ""))
                image = slide.get("image", "")
                caption = slide.get("image_caption", "")
                html = patterns.render_figure_slide(
                    heading=heading,
                    image_path=image,
                    caption=caption,
                    body_html=body,
                    page_no=no,
                    total=total,
                    theme_name=theme,
                )
                slides.append((heading, html))

            elif slide_type == "data-table":
                heading = slide.get("heading", "")
                body = text_to_html(slide.get("body", ""))
                table_html = slide.get("table_html", "<table></table>")
                caption = slide.get("table_caption", "")
                html = patterns.render_table_slide(
                    heading=heading,
                    table_html=table_html,
                    caption=caption,
                    body_html=body,
                    page_no=no,
                    total=total,
                    theme_name=theme,
                )
                slides.append((heading, html))

        return slides

    def _render_auto_slides(self, bundle: ContentBundle) -> list[tuple[str, str]]:
        """セクション内容から自動でスライドを配置する"""
        slides: list[tuple[str, str]] = []
        theme = bundle.theme
        ordered = get_ordered_sections(bundle.sections)

        # タイトルスライド
        slides.append((bundle.title, patterns.render_cover_slide(
            title=bundle.title,
            authors=bundle.authors,
            affiliation=bundle.affiliation,
            date=bundle.date,
            subtitle=bundle.subtitle,
            theme_name=theme,
        )))

        # リソースキュー
        image_queue = list(bundle.images)
        chart_queue = list(bundle.charts)
        table_queue = list(bundle.tables)

        chapter_no = 0

        for section_name, content in ordered:
            # セクション区切り（方法・結果・考察）
            if section_name in ("methods", "results", "discussion"):
                chapter_no += 1
                label = section_to_label(section_name, bundle.language)
                slides.append((label, patterns.render_section_divider(
                    heading=label,
                    chapter_no=chapter_no,
                    theme_name=theme,
                )))

            heading = section_to_label(section_name, bundle.language)
            body_html = text_to_html(content)
            no = len(slides) + 1

            # 結果セクション → 図・グラフ優先
            if section_name == "results" and (image_queue or chart_queue):
                img = image_queue.pop(0) if image_queue else None
                chart = chart_queue.pop(0) if chart_queue else None
                media = img or chart
                if media:
                    path = media.rel_path if isinstance(media, ImageEntry) else media.rel_path
                    caption = media.caption
                    slides.append((heading, patterns.render_image_text_slide(
                        heading=heading,
                        body_html=body_html,
                        image_path=path,
                        caption=caption,
                        page_no=no,
                        total=0,  # 後で更新
                        theme_name=theme,
                    )))
                else:
                    slides.append((heading, patterns.render_text_slide(
                        heading=heading,
                        body_html=body_html,
                        page_no=no,
                        total=0,
                        theme_name=theme,
                    )))

            # 方法セクション → テーブル優先
            elif section_name == "methods" and table_queue:
                table = table_queue.pop(0)
                slides.append((heading, patterns.render_table_slide(
                    heading=heading,
                    table_html=table.html,
                    caption=table.caption,
                    body_html=body_html,
                    page_no=no,
                    total=0,
                    theme_name=theme,
                )))

            # 残り画像があれば 2カラム
            elif image_queue and section_name not in ("references", "acknowledgements"):
                img = image_queue.pop(0)
                slides.append((heading, patterns.render_image_text_slide(
                    heading=heading,
                    body_html=body_html,
                    image_path=img.rel_path,
                    caption=img.caption,
                    page_no=no,
                    total=0,
                    theme_name=theme,
                )))

            # テキストのみ
            else:
                slides.append((heading, patterns.render_text_slide(
                    heading=heading,
                    body_html=body_html,
                    page_no=no,
                    total=0,
                    theme_name=theme,
                )))

        # 余ったリソースを追加スライドに
        for table in table_queue:
            no = len(slides) + 1
            slides.append((table.caption, patterns.render_table_slide(
                heading=table.caption or "Data",
                table_html=table.html,
                caption=table.caption,
                page_no=no,
                total=0,
                theme_name=theme,
            )))

        for chart in chart_queue:
            no = len(slides) + 1
            slides.append((chart.caption, patterns.render_kpi_slide(
                heading=chart.caption or "Chart",
                image_path=chart.rel_path,
                caption=chart.caption,
                page_no=no,
                total=0,
                theme_name=theme,
            )))

        for img in image_queue:
            no = len(slides) + 1
            slides.append((img.caption, patterns.render_figure_slide(
                heading=img.caption or "Figure",
                image_path=img.rel_path,
                caption=img.caption,
                page_no=no,
                total=0,
                theme_name=theme,
            )))

        # 謝辞スライド
        slides.append(("謝辞", patterns.render_conclusion_slide(
            title=bundle.title,
            authors=bundle.authors,
            affiliation=bundle.affiliation,
            theme_name=theme,
        )))

        return slides

    # ── 画像コピー ──

    def _copy_images(self, bundle: ContentBundle, images_out: Path) -> None:
        """ContentBundle 内の画像を出力ディレクトリにコピーする"""
        for img in bundle.images:
            src = Path(img.path)
            if src.exists():
                dest = images_out / img.filename
                if not dest.exists():
                    shutil.copy2(src, dest)

        for chart in bundle.charts:
            src = Path(chart.svg_path)
            if src.exists():
                dest = images_out / Path(chart.rel_path).name
                if not dest.exists():
                    shutil.copy2(src, dest)

    # ── index.html 生成 ──

    def _write_index(self, output_dir: Path, title: str, slide_count: int) -> None:
        """ビューア付き index.html を生成する"""
        # index-template.html を探す
        template_path = (
            Path(__file__).parent.parent
            / "skills" / "slidekit-create" / "references" / "index-template.html"
        )

        if template_path.exists():
            template = template_path.read_text(encoding="utf-8")
            # タイトル置換
            template = template.replace("{{TITLE}}", title)
            # スライドフレーム生成
            frames = []
            for i in range(slide_count):
                active = ' is-active' if i == 0 else ''
                frames.append(
                    f'    <div class="slide-frame{active}">'
                    f'<iframe src="{i + 1:03d}.html"></iframe></div>'
                )
            template = template.replace("<!-- {{SLIDES}} -->", "\n".join(frames))
            (output_dir / "index.html").write_text(template, encoding="utf-8")
        else:
            # テンプレートがない場合はシンプルなビューアを生成
            self._write_simple_index(output_dir, title, slide_count)

    def _write_simple_index(self, output_dir: Path, title: str, slide_count: int) -> None:
        """シンプルな iframe ビューアを生成する（テンプレート不在時のフォールバック）"""
        frames = "\n".join(
            f'    <div class="slide-frame"><iframe src="{i + 1:03d}.html"></iframe></div>'
            for i in range(slide_count)
        )

        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8" />
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #1a1a2e; display: flex; flex-direction: column; align-items: center; min-height: 100vh; }}
        .deck {{ width: 1280px; height: 720px; position: relative; margin: 40px auto; }}
        .slide-frame {{ position: absolute; inset: 0; display: none; }}
        .slide-frame.is-active {{ display: block; }}
        .slide-frame iframe {{ width: 1280px; height: 720px; border: none; }}
        .nav {{ position: fixed; bottom: 20px; right: 20px; display: flex; gap: 8px; z-index: 9999; }}
        .nav button {{ background: rgba(255,255,255,0.1); color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; }}
        .nav button:hover {{ background: rgba(255,255,255,0.2); }}
        .counter {{ position: fixed; bottom: 24px; left: 20px; color: rgba(255,255,255,0.5); font-size: 14px; font-family: monospace; }}
        @media print {{
            body {{ background: white; }}
            .slide-frame {{ position: static !important; display: block !important; page-break-after: always; }}
            .nav, .counter {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="deck">
{frames}
    </div>
    <div class="counter"><span id="current">01</span> / {slide_count:02d}</div>
    <div class="nav">
        <button onclick="go(-1)">← Prev</button>
        <button onclick="go(1)">Next →</button>
        <button onclick="window.print()">PDF</button>
    </div>
    <script>
        var idx = 0, total = {slide_count};
        var frames = document.querySelectorAll('.slide-frame');
        frames[0].classList.add('is-active');
        function go(d) {{
            frames[idx].classList.remove('is-active');
            idx = Math.max(0, Math.min(total - 1, idx + d));
            frames[idx].classList.add('is-active');
            document.getElementById('current').textContent = String(idx + 1).padStart(2, '0');
        }}
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'ArrowRight' || e.key === ' ') go(1);
            else if (e.key === 'ArrowLeft') go(-1);
            else if (e.key === 'f' || e.key === 'F') {{
                e.preventDefault();
                if (!document.fullscreenElement) document.documentElement.requestFullscreen();
                else document.exitFullscreen();
            }}
        }});
    </script>
</body>
</html>"""

        (output_dir / "index.html").write_text(html, encoding="utf-8")
