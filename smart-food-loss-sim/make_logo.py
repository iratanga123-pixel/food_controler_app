"""Creates assets/hunika-icon.png (browser-tab icon) from simple shapes.
Run once:  python make_logo.py     Replace the PNG with your own logo any time."""
from pathlib import Path

from PIL import Image, ImageDraw

S = 512
GREEN, PAPER = (29, 107, 82), (244, 250, 246)
k = S / 256

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle((0, 0, S - 1, S - 1), radius=int(56 * k), fill=GREEN)
shield = [(128, 36), (204, 64), (204, 126), (190, 160), (160, 195), (128, 222),
          (96, 195), (66, 160), (52, 126), (52, 64)]
d.polygon([(x * k, y * k) for x, y in shield], fill=PAPER)
d.line([(128 * k, 196 * k), (128 * k, 92 * k)], fill=GREEN, width=int(9 * k))


def grain(cx, cy, rx, ry, tilt):
    """One grain: an ellipse tilted left (-) or right (+)."""
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse(((cx - rx) * k, (cy - ry) * k, (cx + rx) * k, (cy + ry) * k), fill=GREEN)
    return layer.rotate(-tilt, center=(cx * k, cy * k), resample=Image.BICUBIC)


for cx, cy, rx, ry, tilt in [(128, 78, 11, 20, 0), (107, 100, 9, 18, -38), (149, 100, 9, 18, 38),
                             (108, 130, 9, 18, -38), (148, 130, 9, 18, 38),
                             (110, 160, 9, 17, -38), (146, 160, 9, 17, 38)]:
    img = Image.alpha_composite(img, grain(cx, cy, rx, ry, tilt))

out = Path(__file__).parent / "assets" / "hunika-icon.png"
out.parent.mkdir(exist_ok=True)
img.save(out)
print("saved", out)
