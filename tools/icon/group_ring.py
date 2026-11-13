"""Build the native group ring from Blizzard's WhiteCircle-RaidBlips sprite.

Usage: python -P tools/icon/group_ring.py <World of Warcraft folder>
"""
from io import BytesIO
from pathlib import Path
import sys

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
SIZE = 64
OUTER, GAP, CENTER = 19, 15, 12
ATLAS_FILE_ID = 1523129
# WhiteCircle-RaidBlips, UiTextureAtlasMember 6220 on the 64x32 atlas 867.
SPRITE_BOX = (1, 1, 20, 19)


def layer(sprite, diameter):
    span = SIZE * diameter / OUTER
    inset = (SIZE - span) / 2
    x_scale, y_scale = sprite.width / span, sprite.height / span
    return sprite.transform(
        (SIZE, SIZE), Image.Transform.AFFINE,
        (x_scale, 0, -inset * x_scale, 0, y_scale, -inset * y_scale),
        Image.Resampling.BILINEAR,
    )


def texture(wow):
    sys.path.insert(0, str(ROOT / "tools/casc"))
    from casc import Casc

    atlas = Image.open(BytesIO(Casc(wow, "wowf").read(ATLAS_FILE_ID))).convert("RGBA")
    if atlas.size != (64, 32):
        raise ValueError("Unexpected WhiteCircle-RaidBlips atlas dimensions")
    sprite = atlas.crop(SPRITE_BOX)

    outer = layer(sprite, OUTER)
    outer = ImageChops.multiply(outer, Image.new("RGBA", outer.size, (255, 209, 0, 255)))
    gap = Image.new("RGBA", outer.size)
    gap.putalpha(layer(sprite, GAP).getchannel("A"))
    ring = Image.alpha_composite(outer, gap)

    # The native dot supplies the center of the original three-layer pin.
    center = layer(sprite, CENTER).getchannel("A")
    ring.putalpha(ImageChops.multiply(ring.getchannel("A"), ImageChops.invert(center)))
    return ring


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -P tools/icon/group_ring.py <World of Warcraft folder>")
    target = ROOT / "OpenMap/Media/Textures/GroupRing.tga"
    texture(sys.argv[1]).save(target, compression=None)
    print("wrote", target.relative_to(ROOT))
