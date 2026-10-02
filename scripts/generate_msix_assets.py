from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ASSETS = {
    "StoreLogo.png": (50, 50),
    "Square44x44Logo.png": (44, 44),
    "Square150x150Logo.png": (150, 150),
    "Square310x310Logo.png": (310, 310),
    "Wide310x150Logo.png": (310, 150),
}


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int):
    for size in range(max_height, 7, -1):
        try:
            font = ImageFont.truetype("arial.ttf", size)
        except OSError:
            return ImageFont.load_default()

        box = draw.textbbox((0, 0), text, font=font)
        if box[2] - box[0] <= max_width and box[3] - box[1] <= max_height:
            return font

    return ImageFont.load_default()


def make_asset(path: Path, size: tuple[int, int]) -> None:
    width, height = size
    image = Image.new("RGBA", size, (25, 73, 135, 255))
    draw = ImageDraw.Draw(image)

    label = "Y"
    font = fit_font(draw, label, int(width * 0.65), int(height * 0.65))
    box = draw.textbbox((0, 0), label, font=font)
    x = (width - (box[2] - box[0])) / 2
    y = (height - (box[3] - box[1])) / 2 - box[1]
    draw.text((x, y), label, fill=(255, 255, 255, 255), font=font)

    image.save(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, size in ASSETS.items():
        make_asset(output_dir / filename, size)


if __name__ == "__main__":
    main()
