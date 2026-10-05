"""Caption-based figure candidates plus explicit page crops.

Adapted from the project's 2026-10-04 extraction script. Automatic results
are candidates requiring visual review; the layout heuristics are unchanged.
All page numbers are one-based PDF file pages. Manual boxes use PDF points.
"""

import os
import re
import sys
import pymupdf
from PIL import Image
import io

ZOOM = 3.0  # ~216 DPI baseline; rendering crop then we keep native res
PAD = 6     # pixels padding after autocrop

def page_column_x(page, caption_bbox):
    """Return (x0, x1) covering the column(s) the caption sits in."""
    pw = page.rect.width
    cx0, cy0, cx1, cy1 = caption_bbox
    cap_w = cx1 - cx0
    # detect single-column layout: any text block spanning the page center
    d = page.get_text("dict")
    for block in d.get("blocks", []):
        if block.get("type") != 0:
            continue
        b = block["bbox"]
        if b[0] < pw * 0.40 and b[2] > pw * 0.60 and (b[2] - b[0]) > pw * 0.35:
            return (36, pw - 36)  # single-column: all figures are full-width
    # full-width figure if caption is wide (>= 55% of page width)
    if cap_w >= 0.55 * pw:
        return (36, pw - 36)  # typical margins
    # otherwise single column; decide left/right by caption center
    center = (cx0 + cx1) / 2
    if center < pw / 2:
        return (36, pw / 2 - 6)
    else:
        return (pw / 2 + 6, pw - 36)

def autocrop_white(img, pad=PAD):
    """Crop white/near-white borders, keep pad pixels."""
    import numpy as np
    arr = np.array(img.convert("RGB"))
    # near-white mask
    mask = (arr < 250).any(axis=2)
    if not mask.any():
        return img
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    top, bottom = rows[0], rows[-1]
    left, right = cols[0], cols[-1]
    top = max(0, top - pad)
    bottom = min(img.height - 1, bottom + pad)
    left = max(0, left - pad)
    right = min(img.width - 1, right + pad)
    return img.crop((left, top, right + 1, bottom + 1))

def extract(pdf_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    doc = pymupdf.open(pdf_path)
    fig_re = re.compile(r"^(F\s*I\s*G\s*U\s*R\s*E|Fig)\.?\s+(\d+)\b", re.IGNORECASE)
    saved = []
    seen_fnums = set()
    for pno in range(len(doc)):
        page = doc[pno]
        d = page.get_text("dict")
        captions = []
        for block in d.get("blocks", []):
            if block.get("type") != 0:
                continue
            lines = block.get("lines", [])
            if not lines or len(lines) > 15:
                continue
            first_line = lines[0]
            text = "".join(span["text"] for span in first_line.get("spans", [])).strip()
            m = fig_re.match(text)
            if m:
                fnum = int(m.group(2))
                if fnum not in seen_fnums:
                    # use whole block bbox so multi-line captions are fully included
                    captions.append((fnum, block["bbox"], text))
        if not captions:
            continue
        captions.sort(key=lambda c: c[1][1])
        mat = pymupdf.Matrix(ZOOM, ZOOM)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        import numpy as np
        page_arr = np.array(img.convert("RGB"))
        page_white = (page_arr >= 250).all(axis=(1, 2))
        prev_bottom = 28
        for fnum, bbox, ctext in captions:
            if fnum in seen_fnums:
                continue
            x0, x1 = page_column_x(page, bbox)
            y1 = bbox[3] + 4
            # special case: caption in a narrow side column, figure sits beside it
            pw = page.rect.width
            cap_w = bbox[2] - bbox[0]
            if cap_w < 0.35 * pw:
                # find first full-width text block below the caption (body text / section heading)
                y1 = min(page.rect.height - 24, bbox[3] + 280)
                for blk in d.get("blocks", []):
                    if blk.get("type") != 0:
                        continue
                    bb = blk["bbox"]
                    if bb[1] > bbox[3] + 6 and (bb[2] - bb[0]) > 0.55 * pw:
                        y1 = min(y1, bb[1] - 4)
                        break
            # find figure top: scan upward from caption top for first large
            # white gap (separates figure from body text above it)
            cap_top_px = int(bbox[1] * ZOOM)
            scan_stop = max(0, int(prev_bottom * ZOOM))
            y0_px = scan_stop
            min_gap = 55
            state = 0  # 0: skip caption-figure gap, 1: inside figure, find top gap
            run = 0
            for y in range(cap_top_px - 1, scan_stop, -1):
                if state == 0:
                    if not page_white[y]:
                        state = 1  # entered figure content
                else:
                    if page_white[y]:
                        run += 1
                        if run >= min_gap:
                            y0_px = max(0, y - 6)
                            break
                    else:
                        run = 0
            crop = img.crop((int(x0 * ZOOM), y0_px, int(x1 * ZOOM), int(y1 * ZOOM)))
            crop = autocrop_white(crop)
            prev_bottom = bbox[3] + 10
            if crop.width < 100 or crop.height < 60:
                continue
            fname = f"figure_{fnum:02d}_p{pno+1}.png"
            fpath = os.path.join(out_dir, fname)
            crop.save(fpath, "PNG")
            seen_fnums.add(fnum)
            saved.append((fnum, pno + 1, fpath, crop.size, ctext[:70]))
    doc.close()
    return saved


def main():
    import argparse
    import hashlib
    import json
    import math
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output_dir", type=Path, help="New or empty directory")
    parser.add_argument("--page", type=int, help="Render one full PDF page instead of auto-extracting")
    parser.add_argument("--bbox", nargs=4, type=float, metavar=("X0", "Y0", "X1", "Y1"),
                        help="With --page, crop this rectangle in PDF points at 216 DPI")
    args = parser.parse_args()
    if not args.pdf.is_file():
        parser.error("Input PDF does not exist")
    if args.bbox and not args.page:
        parser.error("--bbox requires --page")
    if args.output_dir.exists() and (not args.output_dir.is_dir() or any(args.output_dir.iterdir())):
        parser.error("Output directory must be new or empty")
    items = []
    if args.page is not None:
        with pymupdf.open(args.pdf) as doc:
            if not 1 <= args.page <= len(doc):
                parser.error("Page number is outside the PDF")
            page = doc[args.page - 1]
            box = page.rect
            if args.bbox:
                if not all(math.isfinite(v) for v in args.bbox):
                    parser.error("Box coordinates must be finite")
                box = pymupdf.Rect(*args.bbox)
                if box.is_empty or not page.rect.contains(box):
                    parser.error("Box must have positive area and lie within the page")
            args.output_dir.mkdir(parents=True, exist_ok=True)
            name = f"{'crop' if args.bbox else 'page'}_p{args.page}.png"
            pix = page.get_pixmap(dpi=216, clip=box, alpha=False)
            pix.save(args.output_dir / name)
            items.append({"pdf_page": args.page, "file": name,
                          "box_pdf_points": list(box), "size_pixels": [pix.width, pix.height]})
        mode = "manual_crop" if args.bbox else "page_preview"
    else:
        for number, page, path, size, caption in extract(str(args.pdf), str(args.output_dir)):
            items.append({"figure": number, "pdf_page": page, "file": Path(path).name,
                          "size_pixels": list(size), "caption_start": caption})
        mode = "automatic_candidates"
    with args.pdf.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    manifest = {"source_pdf": args.pdf.name, "source_sha256": digest,
                "mode": mode, "dpi": 216, "visual_review_required": True, "items": items}
    with (args.output_dir / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"Saved {len(items)} image(s); inspect complete panels, axes, legends and captions.")
    if not items:
        print("No candidates found. Use --page and, if needed, --bbox for explicit rendering.")
    return 0 if items else 2


if __name__ == "__main__":
    raise SystemExit(main())
