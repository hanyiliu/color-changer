from io import BytesIO
from color_changer.cli import replace_colors_raster, parse_mappings, normalize_hex, main
import tempfile, os, shutil, json, pathlib
from PIL import Image

def test_hex_normalization():
    assert normalize_hex('ff00aa') == '#ff00aa'
    assert normalize_hex('#f0a') == '#ff00aa'

def test_parse_mappings():
    m = parse_mappings(['#ff00aa=>#000000'])
    assert m['#ff00aa'] == '#000000'


def test_replace_colors_raster():
    img = Image.new('RGBA', (2,2), (255,0,170,255))
    mappings = {'#ff00aa': '#000000'}
    out, counts = replace_colors_raster(img, mappings)
    assert counts['#ff00aa'] == 4
    assert out.getpixel((0,0)) == (0,0,0,255)


def test_recursive_structure():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        in_dir = root / 'in'
    (in_dir / 'a').mkdir(parents=True)
    (in_dir / 'a' / 'b').mkdir(parents=True)
    (in_dir / 'c').mkdir()
    # Create images
    img1 = Image.new('RGBA', (1,1), (255,0,170,255))
    img1.save(in_dir / 'a' / 'one.png')
    # Ensure nested directory exists (defensive)
    (in_dir / 'a' / 'b').mkdir(parents=True, exist_ok=True)
    img2 = Image.new('RGB', (1,1), (255,0,170))
    img2.save(in_dir / 'a' / 'b' / 'two.jpg')
    (in_dir / 'c').mkdir(parents=True, exist_ok=True)
    img3 = Image.new('RGBA', (1,1), (0,0,0,255))
    img3.save(in_dir / 'c' / 'three.png')
    out_dir = root / 'out'
    # Debug: ensure files exist
    assert (in_dir / 'a' / 'one.png').exists(), 'one.png missing before run'
    assert (in_dir / 'a' / 'b' / 'two.jpg').exists(), 'two.jpg missing before run'
    assert (in_dir / 'c' / 'three.png').exists(), 'three.png missing before run'
    code = main(['-i', str(in_dir), '-o', str(out_dir), '-m', '#ff00aa=>#000000'])
    assert code == 0
    # Check structure
    assert (out_dir / 'a' / 'one.png').exists()
    # two.jpg becomes png
    assert (out_dir / 'a' / 'b' / 'two.png').exists()
    assert (out_dir / 'c' / 'three.png').exists()

    from PIL import Image as PILImage
    px = PILImage.open(out_dir / 'a' / 'one.png').getpixel((0,0))
    assert px == (0,0,0,255)

if __name__ == '__main__':
    test_hex_normalization()
    test_parse_mappings()
    test_replace_colors_raster()
    test_recursive_structure()
    print('Tests passed')
