import argparse
import sys
import re
from pathlib import Path
from typing import Dict, Tuple, List
from PIL import Image
import shutil
import xml.etree.ElementTree as ET

HEX_COLOR_RE = re.compile(r'#([0-9a-fA-F]{3,8})')
SUPPORTED_RASTER_EXT = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
SVG_EXT = '.svg'


def parse_mappings(mapping_args: List[str]) -> Dict[str, str]:
    mappings: Dict[str, str] = {}
    for m in mapping_args:
        if '=>' in m:
            src, dst = m.split('=>', 1)
        elif ':' in m:
            src, dst = m.split(':', 1)
        else:
            raise ValueError(f"Invalid mapping '{m}'. Use format #from=>#to")
        src = normalize_hex(src)
        dst = normalize_hex(dst)
        if not (is_valid_hex(src) and is_valid_hex(dst)):
            raise ValueError(f"Invalid hex values in mapping '{m}'")
        mappings[src] = dst
    return mappings


def normalize_hex(h: str) -> str:
    h = h.strip().lower()
    if not h.startswith('#'):
        h = '#' + h
    if len(h) == 4:  # #rgb -> #rrggbb
        h = '#' + ''.join(ch*2 for ch in h[1:])
    if len(h) == 5:  # #rgba -> #rrggbbaa
        h = '#' + ''.join(ch*2 for ch in h[1:])
    return h


def is_valid_hex(h: str) -> bool:
    return bool(re.fullmatch(r'#([0-9a-f]{6}|[0-9a-f]{8})', h))


def load_image(path: Path) -> Image.Image:
    return Image.open(path).convert('RGBA')


def replace_colors_raster(img: Image.Image, mappings: Dict[str, str]) -> Tuple[Image.Image, Dict[str, int]]:
    pixels = img.load()
    width, height = img.size
    counts = {src: 0 for src in mappings}
    reverse_map: Dict[Tuple[int, int, int, int], Tuple[int, int, int, int]] = {}

    # Precompute RGBA tuples
    for src, dst in mappings.items():
        src_rgba = hex_to_rgba(src)
        dst_rgba = hex_to_rgba(dst)
        reverse_map[src_rgba] = dst_rgba

    for y in range(height):
        for x in range(width):
            current = pixels[x, y]
            if current in reverse_map:
                pixels[x, y] = reverse_map[current]
                src_hex = rgba_to_hex(current)
                if src_hex in counts:
                    counts[src_hex] += 1
    return img, counts


def hex_to_rgba(h: str) -> Tuple[int, int, int, int]:
    h = h.lstrip('#')
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return r, g, b, 255
    elif len(h) == 8:
        r, g, b, a = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16)
        return r, g, b, a
    else:
        raise ValueError(f"Unexpected hex length for {h}")


def rgba_to_hex(rgba: Tuple[int, int, int, int]) -> str:
    r, g, b, a = rgba
    if a == 255:
        return f"#{r:02x}{g:02x}{b:02x}"
    return f"#{r:02x}{g:02x}{b:02x}{a:02x}"


def process_svg(path: Path, mappings: Dict[str, str]) -> Tuple[str, Dict[str, int]]:
    text = path.read_text(encoding='utf-8')
    counts = {src: 0 for src in mappings}

    def repl(match: re.Match) -> str:
        original = normalize_hex(match.group(0))
        if original in mappings:
            counts[original] += 1
            return mappings[original]
        return original

    new_text = re.sub(r'#[0-9a-fA-F]{3,8}', repl, text)
    return new_text, counts


def process_file(path: Path, out_dir: Path, mappings: Dict[str, str]) -> Tuple[int, Dict[str, int]]:
    ext = path.suffix.lower()
    if ext == SVG_EXT:
        new_text, counts = process_svg(path, mappings)
        rel = path.name
        (out_dir / rel).write_text(new_text, encoding='utf-8')
        replaced_total = sum(counts.values())
        return replaced_total, counts
    elif ext in SUPPORTED_RASTER_EXT:
        img = load_image(path)
        new_img, counts = replace_colors_raster(img, mappings)
        rel = path.with_suffix('.png').name  # output raster as PNG
        new_img.save(out_dir / rel)
        replaced_total = sum(counts.values())
        return replaced_total, counts
    else:
        # Unsupported - just copy
        shutil.copy2(path, out_dir / path.name)
        return 0, {}


def scan_input_files(in_dir: Path) -> List[Path]:
    return [p for p in in_dir.iterdir() if p.is_file()]


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Batch replace colors in images (raster + SVG).')
    parser.add_argument('-i', '--input', required=True, help='Input directory containing images')
    parser.add_argument('-o', '--output', required=True, help='Output directory for processed images')
    parser.add_argument('-m', '--mapping', nargs='*', default=[], help="Color mappings like '#ff00d9=>#0abab5' (repeatable)")
    parser.add_argument('--interactive', action='store_true', help='Prompt for mappings interactively if not provided')
    return parser.parse_args(argv)


def interactive_mappings() -> Dict[str, str]:
    print("Enter color mappings (blank line to finish). Format: #from=>#to")
    result: Dict[str, str] = {}
    while True:
        line = input('mapping> ').strip()
        if not line:
            break
        try:
            parsed = parse_mappings([line])
            result.update(parsed)
        except Exception as e:
            print(f"Error: {e}")
    return result


def main(argv: List[str] | None = None) -> int:
    ns = parse_args(argv or sys.argv[1:])
    in_dir = Path(ns.input)
    out_dir = Path(ns.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    mappings: Dict[str, str] = {}
    if ns.mapping:
        mappings.update(parse_mappings(ns.mapping))
    if ns.interactive or not mappings:
        mappings.update(interactive_mappings())

    if not mappings:
        print('No mappings provided. Exiting.')
        return 1

    files = scan_input_files(in_dir)
    print(f"Processing {len(files)} files with {len(mappings)} mappings...")

    aggregate_counts = {src: 0 for src in mappings}
    processed = 0
    for f in files:
        replaced_total, counts = process_file(f, out_dir, mappings)
        processed += 1
        if counts:
            for k, v in counts.items():
                aggregate_counts[k] += v
        print(f"{f.name}: replaced={replaced_total}")

    print('\nSummary:')
    for k, v in aggregate_counts.items():
        print(f"  {k} -> {mappings[k]}: {v}")
    print(f"Processed {processed} files. Output in {out_dir}")
    return 0

if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())
