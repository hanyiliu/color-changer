from io import BytesIO
from color_changer.cli import hex_to_rgba, replace_colors_raster, parse_mappings, normalize_hex
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

if __name__ == '__main__':
    test_hex_normalization()
    test_parse_mappings()
    test_replace_colors_raster()
    print('Tests passed')
