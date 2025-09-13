# color-changer

Batch replace chosen colors across mixed image formats (SVG + raster) via a simple CLI.

## Features
- Supports SVG, PNG, JPEG, GIF, BMP (others copied unchanged)
- Multiple color mappings in one run (e.g. `#ff00d9=>#0abab5 #fb8deb=>#77e6e2`)
- Hex normalization: accepts #rgb, #rgba, #rrggbb, #rrggbbaa
- Outputs all raster images as PNG (lossless) into output folder
- Logs per-file replacement counts + summary
- Interactive mode for ad‑hoc mappings
- Recursive: processes all files under the input directory tree and preserves subdirectory structure in the output.

## Setup & Installation

Create and activate a virtual environment (recommended):
```bash
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
# On Windows (PowerShell): .venv\\Scripts\\Activate.ps1
```

Upgrade packaging tools (optional but helps avoid quirks):
```bash
pip install --upgrade pip setuptools wheel
```

Install in editable/development mode:
```bash
pip install -e .
```

Tip: Keep your virtual environment inside a hidden directory like `.venv` (already in `.gitignore`). Avoid naming it something that looks like a top-level Python package (e.g. `myVenv`) to prevent setuptools from trying to include it during package discovery.

Verify install (one of these should work):
```bash
color-changer -h
python -m color_changer -h
```

If `color-changer` says "command not found":
- Ensure the virtualenv is activated.
- Check that the venv's `bin` directory is in `PATH`:
	```bash
	echo $PATH | tr ':' '\n' | grep "/.venv/bin" || echo "venv bin missing from PATH"
	```
- Reinstall console script:
	```bash
	pip install -e . --force-reinstall
	```
- Fallback always works:
	```bash
	python -m color_changer -i input -o output -m '#ff00d9=>#0abab5'
	```

## Usage
CLI (installed entry point):
```bash
color-changer -i path/to/input -o processed_output -m '#ff00d9=>#0abab5' '#fb8deb=>#77e6e2'
```
Module form (always available):
```bash
python -m color_changer -i path/to/input -o processed_output -m '#ff00d9=>#0abab5' '#fb8deb=>#77e6e2'
```
Interactive mapping prompt:
```bash
color-changer -i path/to/input -o processed_output --interactive
```
Enter mappings line by line, blank line to finish.

## Mapping Formats Accepted
- `#ff00d9=>#0abab5`
- `ff00d9:0abab5`

Short forms like `#f0d` expand to full 6-digit. Alpha supported (#rrggbbaa) for exact RGBA matching in raster images.

## Notes
- Raster replacement matches exact RGBA tuples after converting image to RGBA. Near-color / fuzzy matching is not implemented (future enhancement: delta-E threshold).
- SVG replacement finds literal hex codes in element attributes and inline styles. Does not parse functional color notations (e.g. `rgb(255,0,0)`), gradients, or CSS external stylesheets yet.
- Output directory mirrors the input tree; raster outputs always use `.png` extension even if source was jpeg/gif/etc.

## Planned Enhancements
- Optional fuzzy color distance tolerance
- Recursive directory traversal
- Support for css `rgb()` / `hsl()` notations in SVG
- Parallel processing for large batches

## License
MIT
