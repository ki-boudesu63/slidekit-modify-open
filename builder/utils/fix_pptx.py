#!/usr/bin/env python3
"""fix_pptx.py — Fix PptxGenJS v4 known issues (comprehensive)."""
import zipfile, os, shutil, re, sys, tempfile
import xml.etree.ElementTree as ET


def fix_pptx(src, dst=None):
    dst = dst or src
    tmp = os.path.join(tempfile.gettempdir(), "_pptx_fix")
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    with zipfile.ZipFile(src, "r") as z:
        z.extractall(tmp)

    fixes = {
        "phantom_overrides": 0, "rect_to_roundRect": 0,
        "bgPr_effectLst": 0, "empty_dirs": [],
        "empty_ln_fixed": 0, "misplaced_pPr": 0,
        "slideMaster_bg": 0, "sldSz_type": 0,
        "presentation_order": 0, "unused_defaults": 0,
        "empty_runs": 0, "oval_to_ellipse": 0,
        "notesMaster_theme": 0, "image_dedup": 0,
    }

    # Fix 1 & 10: [Content_Types].xml
    ct = os.path.join(tmp, "[Content_Types].xml")
    ns = "http://schemas.openxmlformats.org/package/2006/content-types"
    ET.register_namespace("", ns)
    tree = ET.parse(ct)
    root = tree.getroot()

    for ov in list(root.findall(f"{{{ns}}}Override")):
        part = ov.get("PartName")
        if not os.path.exists(os.path.join(tmp, part.lstrip("/"))):
            root.remove(ov)
            fixes["phantom_overrides"] += 1

    actual_exts = set()
    for dirpath, _, filenames in os.walk(tmp):
        for fn in filenames:
            ext = fn.rsplit(".", 1)[-1].lower() if "." in fn else ""
            if ext:
                actual_exts.add(ext)

    for default in list(root.findall(f"{{{ns}}}Default")):
        ext = default.get("Extension", "").lower()
        if ext and ext not in actual_exts:
            root.remove(default)
            fixes["unused_defaults"] += 1

    tree.write(ct, xml_declaration=True, encoding="utf-8")

    # Fix 2, 3, 5, 6, 12: Slide XML fixes
    slides_dir = os.path.join(tmp, "ppt", "slides")
    if os.path.exists(slides_dir):
        for fname in sorted(os.listdir(slides_dir)):
            if not fname.endswith(".xml"):
                continue
            fpath = os.path.join(slides_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            modified = False

            # Fix 12: oval -> ellipse
            new_content = content.replace('prst="oval"', 'prst="ellipse"')
            if new_content != content:
                fixes["oval_to_ellipse"] += content.count('prst="oval"')
                content = new_content
                modified = True

            # Fix 2: rect + adj -> roundRect
            pattern = r'(<a:prstGeom prst=")rect(">\s*<a:avLst>\s*<a:gd name="adj")'
            new_content, count = re.subn(pattern, r'\1roundRect\2', content)
            if count > 0:
                content = new_content
                modified = True
                fixes["rect_to_roundRect"] += count

            # Fix 3: Add <a:effectLst/> to <p:bgPr> if missing
            def add_effectlst(m):
                if 'a:effectLst' not in m.group(2):
                    fixes["bgPr_effectLst"] += 1
                    return m.group(1) + m.group(2) + '<a:effectLst/>' + m.group(3)
                return m.group(0)
            new_content = re.sub(
                r'(<p:bgPr>)(.*?)(</p:bgPr>)', add_effectlst,
                content, flags=re.DOTALL
            )
            if new_content != content:
                content = new_content
                modified = True

            # Fix 5: Empty <a:ln/>
            new_content = content.replace('<a:ln/>', '<a:ln><a:noFill/></a:ln>')
            if new_content != content:
                fixes["empty_ln_fixed"] += content.count('<a:ln/>')
                content = new_content
                modified = True
            new_content = content.replace('<a:ln></a:ln>', '<a:ln><a:noFill/></a:ln>')
            if new_content != content:
                fixes["empty_ln_fixed"] += content.count('<a:ln></a:ln>')
                content = new_content
                modified = True

            # Fix 6: Remove misplaced <a:pPr> between <a:r> runs
            ppr_between = re.compile(
                r'(</a:r>\s*)<a:pPr[^>]*>.*?</a:pPr>(\s*<a:r[ >])',
                re.DOTALL
            )
            new_content, count = ppr_between.subn(r'\1\2', content)
            if count > 0:
                content = new_content
                modified = True
                fixes["misplaced_pPr"] += count

            ppr_between_sc = re.compile(
                r'(</a:r>\s*)<a:pPr[^/]*/>\s*(<a:r[ >])',
                re.DOTALL
            )
            new_content, count = ppr_between_sc.subn(r'\1\2', content)
            if count > 0:
                content = new_content
                modified = True
                fixes["misplaced_pPr"] += count

            if modified:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(content)

    # Fix 7: Add <p:bg> to slideMaster1.xml if missing
    sm_path = os.path.join(tmp, "ppt", "slideMasters", "slideMaster1.xml")
    if os.path.exists(sm_path):
        with open(sm_path, "r", encoding="utf-8") as f:
            sm_content = f.read()
        if '<p:bg>' not in sm_content:
            bg_elem = (
                '<p:bg><p:bgRef idx="1001">'
                '<a:schemeClr val="bg1"/>'
                '</p:bgRef></p:bg>'
            )
            sm_new = sm_content.replace(
                '<p:cSld><p:spTree>',
                f'<p:cSld>{bg_elem}<p:spTree>'
            )
            if sm_new == sm_content:
                sm_new = re.sub(
                    r'(<p:cSld>)\s*(<p:spTree>)',
                    rf'\1{bg_elem}\2', sm_content
                )
            if sm_new != sm_content:
                with open(sm_path, "w", encoding="utf-8") as f:
                    f.write(sm_new)
                fixes["slideMaster_bg"] = 1

    # Fix 8 & 9: presentation.xml fixes
    pres_path = os.path.join(tmp, "ppt", "presentation.xml")
    if os.path.exists(pres_path):
        with open(pres_path, "r", encoding="utf-8") as f:
            pres_content = f.read()
        pres_modified = False

        sldSz_match = re.search(r'<p:sldSz[^>]*>', pres_content)
        if sldSz_match and 'type=' not in sldSz_match.group(0):
            pres_content = re.sub(
                r'(<p:sldSz\s+cx="9144000"\s+cy="5143500")\s*/>',
                r'\1 type="screen16x9"/>', pres_content
            )
            pres_content = re.sub(
                r'(<p:sldSz\s+cx="9144000"\s+cy="5143500")(\s*>)',
                r'\1 type="screen16x9"\2', pres_content
            )
            fixes["sldSz_type"] = 1
            pres_modified = True

        notes_match = re.search(
            r'(<p:notesMasterIdLst>.*?</p:notesMasterIdLst>)',
            pres_content, re.DOTALL
        )
        sld_match = re.search(r'(<p:sldIdLst>)', pres_content)
        if notes_match and sld_match and notes_match.start() > sld_match.start():
            notes_block = notes_match.group(1)
            pres_content = (
                pres_content[:notes_match.start()]
                + pres_content[notes_match.end():]
            )
            pres_content = re.sub(r'\n\s*\n', '\n', pres_content)
            sld_match2 = re.search(r'(<p:sldIdLst>)', pres_content)
            if sld_match2:
                pres_content = (
                    pres_content[:sld_match2.start()]
                    + notes_block
                    + pres_content[sld_match2.start():]
                )
            fixes["presentation_order"] = 1
            pres_modified = True

        if pres_modified:
            with open(pres_path, "w", encoding="utf-8") as f:
                f.write(pres_content)

    # Fix 11: Remove empty <a:r><a:t/></a:r> from notesSlide XML
    notes_dir = os.path.join(tmp, "ppt", "notesSlides")
    if os.path.exists(notes_dir):
        for fname in sorted(os.listdir(notes_dir)):
            if not fname.endswith(".xml"):
                continue
            fpath = os.path.join(notes_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            new_content = re.sub(
                r'\s*<a:r>\s*<a:rPr[^/]*/>\s*<a:t/?>\s*(</a:t>\s*)?</a:r>',
                '', content
            )
            if new_content != content:
                fixes["empty_runs"] += 1
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(new_content)

    # Fix 13: Create separate theme for notesMaster
    nm_rels_path = os.path.join(
        tmp, "ppt", "notesMasters", "_rels", "notesMaster1.xml.rels"
    )
    theme_dir = os.path.join(tmp, "ppt", "theme")
    theme2_path = os.path.join(theme_dir, "theme2.xml")
    if os.path.exists(nm_rels_path) and not os.path.exists(theme2_path):
        theme1_path = os.path.join(theme_dir, "theme1.xml")
        if os.path.exists(theme1_path):
            shutil.copy2(theme1_path, theme2_path)
            with open(nm_rels_path, "r", encoding="utf-8") as f:
                rels_content = f.read()
            rels_content = rels_content.replace(
                'Target="../theme/theme1.xml"',
                'Target="../theme/theme2.xml"'
            )
            with open(nm_rels_path, "w", encoding="utf-8") as f:
                f.write(rels_content)
            tree2 = ET.parse(ct)
            root2 = tree2.getroot()
            has_theme2 = any(
                ov.get("PartName") == "/ppt/theme/theme2.xml"
                for ov in root2.findall(f"{{{ns}}}Override")
            )
            if not has_theme2:
                ET.SubElement(root2, f"{{{ns}}}Override", {
                    "PartName": "/ppt/theme/theme2.xml",
                    "ContentType": "application/vnd.openxmlformats-officedocument.theme+xml"
                })
                tree2.write(ct, xml_declaration=True, encoding="utf-8")
            fixes["notesMaster_theme"] = 1

    # Fix 14: Deduplicate identical images in ppt/media/
    media_dir = os.path.join(tmp, "ppt", "media")
    if os.path.exists(media_dir):
        import hashlib
        hash_to_file = {}
        rename_map = {}
        dedup_count = 0

        for fn in sorted(os.listdir(media_dir)):
            fp = os.path.join(media_dir, fn)
            if not os.path.isfile(fp):
                continue
            with open(fp, "rb") as f:
                h = hashlib.md5(f.read()).hexdigest()
            if h in hash_to_file:
                rename_map[fn] = hash_to_file[h]
                os.remove(fp)
                dedup_count += 1
            else:
                hash_to_file[h] = fn

        if rename_map:
            rels_dirs = [
                os.path.join(tmp, "ppt", "slides", "_rels"),
                os.path.join(tmp, "ppt", "notesSlides", "_rels"),
            ]
            for rels_dir in rels_dirs:
                if not os.path.exists(rels_dir):
                    continue
                for fn in os.listdir(rels_dir):
                    if not fn.endswith(".rels"):
                        continue
                    fp = os.path.join(rels_dir, fn)
                    with open(fp, "r", encoding="utf-8") as f:
                        content = f.read()
                    modified_rels = False
                    for old_name, new_name in rename_map.items():
                        if old_name in content:
                            content = content.replace(
                                f"../media/{old_name}",
                                f"../media/{new_name}"
                            )
                            modified_rels = True
                    if modified_rels:
                        with open(fp, "w", encoding="utf-8") as f:
                            f.write(content)
        fixes["image_dedup"] = dedup_count

    # Fix 4: Remove empty directories
    for d in ["ppt/charts", "ppt/embeddings"]:
        p = os.path.join(tmp, d)
        if os.path.exists(p) and not any(f for _, _, f in os.walk(p) if f):
            shutil.rmtree(p)
            fixes["empty_dirs"].append(d)

    # Repack
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for r, _, files in os.walk(tmp):
            for f in files:
                fp = os.path.join(r, f)
                z.write(fp, os.path.relpath(fp, tmp))
    shutil.rmtree(tmp)
    return fixes

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "presentation.pptx"
    fixes = fix_pptx(path)
    print(f"Fixed: {path}")
    for k, v in fixes.items():
        if k != "empty_dirs":
            print(f"  {k}: {v}")
    if fixes["empty_dirs"]:
        print(f"  empty_dirs: {', '.join(fixes['empty_dirs'])}")
