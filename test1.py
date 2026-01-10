import argparse
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
from PIL import Image, ImageOps
from paddleocr import PaddleOCR

LANG_MAP: Dict[str, str] = {
    "text_simplified_chinese": "ch",
    "text_english": "en",
    "text_en_ch_mixed": "en",
}


def poly_to_bbox(poly: List[float]) -> tuple:
    """Convert OmniDocBench poly list to (L, U, R, D) bbox tuple."""
    left, top, right, bottom = poly[0], poly[1], poly[2], poly[5]
    return min(left, right), min(top, bottom), max(left, right), max(top, bottom)


def get_ocr(lang_code: str, cache: Dict[str, PaddleOCR]) -> PaddleOCR:
    """Reuse PaddleOCR instances per language to avoid repeated initialization.

    Force CPU to avoid missing CUDA/cuDNN issues on machines without the DLLs.
    """
    lang = lang_code if lang_code in ("en", "ch") else "en"
    if lang not in cache:
        cache[lang] = PaddleOCR(use_gpu=False, use_textline_orientation=True, lang=lang)
    return cache[lang]


def _run_paddle(ocr: PaddleOCR, img_array) -> List:
    """Support both new (`predict`) and old (`ocr`) PaddleOCR APIs."""
    if hasattr(ocr, "predict"):
        return ocr.predict(img_array)
    return ocr.ocr(img_array, cls=True)


def _to_text(piece) -> str:
    """Convert paddle OCR output piece to a string safely."""
    if piece is None:
        return ""
    if isinstance(piece, str):
        return piece
    if isinstance(piece, (list, tuple)):
        return " ".join([_to_text(p) for p in piece if _to_text(p)])
    return str(piece)


def predict_text(block_img: Image.Image, ocr: PaddleOCR) -> str:
    """Run OCR on a cropped block and normalize the output string."""
    bordered = ImageOps.expand(block_img, border=16, fill=(255, 255, 255))
    result = _run_paddle(ocr, np.array(bordered))

    lines: List[str] = []
    if isinstance(result, list) and result:
        first = result[0]
        if isinstance(first, dict) and "rec_texts" in first:
            # Newer PaddleOCR versions
            lines = [_to_text(t) for t in first.get("rec_texts", []) if _to_text(t)]
        else:
            # Classic PaddleOCR `ocr` output: list of [bbox, (text, score)]
            for row in result:
                if not isinstance(row, list) or len(row) < 2:
                    continue
                text_candidate = row[1][0] if isinstance(row[1], (list, tuple)) else None
                text_candidate = _to_text(text_candidate)
                if text_candidate:
                    lines.append(text_candidate)
    return "\n".join(lines).strip()


def run_ocr(samples, images_dir: Path):
    ocr_cache: Dict[str, PaddleOCR] = {}
    updated = []
    for sample in samples:
        image_name = Path(sample["page_info"]["image_path"]).name
        image_path = images_dir / image_name
        if not image_path.exists():
            print(f"Skip {image_name}: image not found at {image_path}")
            continue

        page_img = Image.open(image_path)
        for anno in sample.get("layout_dets", []):
            if not anno.get("text"):
                continue

            lang_tag = (anno.get("attribute") or {}).get("text_language")
            ocr = get_ocr(LANG_MAP.get(lang_tag, "en"), ocr_cache)

            bbox = poly_to_bbox(anno["poly"])
            cropped = page_img.crop(bbox).convert("RGB")
            anno["pred"] = predict_text(cropped, ocr)
        updated.append(sample)
    return updated


def main():
    parser = argparse.ArgumentParser(
        description="Run PaddleOCR on OmniDocBench demo text blocks and write benchmark JSON."
    )
    parser.add_argument(
        "--samples",
        default="demo_data/omnidocbench_demo/OmniDocBench_demo.json",
        help="Input OmniDocBench JSON (demo_data/omnidocbench_demo/OmniDocBench_demo.json)",
    )
    parser.add_argument(
        "--images-dir",
        default="demo_data/omnidocbench_demo/images",
        help="Folder that stores page images matching the JSON",
    )
    parser.add_argument(
        "--output",
        default="demo_data/recognition/OmniDocBench_demo_text_ocr.json",
        help="Where to write predictions with benchmark structure",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=0,
        help="Limit number of pages for quick smoke tests (0 = all)",
    )
    args = parser.parse_args()

    samples_path = Path(args.samples)
    images_dir = Path(args.images_dir)
    out_path = Path(args.output)

    if not samples_path.exists():
        raise FileNotFoundError(f"Cannot find samples file: {samples_path}")
    if not images_dir.exists():
        raise FileNotFoundError(f"Cannot find images directory: {images_dir}")

    with samples_path.open("r", encoding="utf-8") as f:
        samples = json.load(f)

    if args.max_pages:
        samples = samples[: args.max_pages]

    updated_samples = run_ocr(samples, images_dir)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(updated_samples, f, ensure_ascii=False, indent=2)

    print(f"Saved OCR predictions to {out_path}")
    print("Evaluate with: python pdf_validation.py --config configs/ocr.yaml")


if __name__ == "__main__":
    main()
