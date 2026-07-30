"""Add a compact, readable portable keyboard to Codex work-state frames."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


FRAME_SIZE = (192, 208)
FRAME_COUNT = 6
SUPERSAMPLE = 4
CYAN = (0, 255, 255, 255)

# Small per-frame shifts keep the device connected to the existing hand motion.
DEVICE_OFFSETS = ((0, 0), (1, 1), (0, 0), (-1, 1), (1, 0), (0, 0))


def scaled_point(x: int, y: int) -> tuple[int, int]:
    return x * SUPERSAMPLE, y * SUPERSAMPLE


def scaled_box(
    left: int, top: int, right: int, bottom: int
) -> tuple[int, int, int, int]:
    return (
        left * SUPERSAMPLE,
        top * SUPERSAMPLE,
        right * SUPERSAMPLE,
        bottom * SUPERSAMPLE,
    )


def make_keyboard(frame_index: int) -> Image.Image:
    overlay = Image.new("RGBA", tuple(value * SUPERSAMPLE for value in FRAME_SIZE))
    draw = ImageDraw.Draw(overlay, "RGBA")
    dx, dy = DEVICE_OFFSETS[frame_index]

    top = [
        scaled_point(72 + dx, 66 + dy),
        scaled_point(119 + dx, 66 + dy),
        scaled_point(124 + dx, 75 + dy),
        scaled_point(67 + dx, 75 + dy),
    ]
    front = [
        scaled_point(67 + dx, 75 + dy),
        scaled_point(124 + dx, 75 + dy),
        scaled_point(120 + dx, 79 + dy),
        scaled_point(71 + dx, 79 + dy),
    ]

    draw.polygon(top, fill=(160, 169, 181, 255), outline=(43, 48, 57, 255))
    draw.line(
        top + [top[0]],
        fill=(225, 231, 238, 255),
        width=SUPERSAMPLE,
        joint="curve",
    )
    draw.polygon(front, fill=(67, 73, 84, 255), outline=(31, 35, 42, 255))

    # Blank physical keys only: no text, logos, code, or screen UI.
    for row in range(2):
        y = 68 + dy + row * 3
        for column in range(6):
            x = 75 + dx + column * 7
            draw.rounded_rectangle(
                scaled_box(x, y, x + 5, y + 1),
                radius=SUPERSAMPLE,
                fill=(72, 78, 89, 245),
            )

    draw.rounded_rectangle(
        scaled_box(89 + dx, 73 + dy, 103 + dx, 75 + dy),
        radius=SUPERSAMPLE,
        fill=(113, 122, 135, 255),
    )
    draw.line(
        [scaled_point(72 + dx, 78 + dy), scaled_point(119 + dx, 78 + dy)],
        fill=(204, 211, 220, 210),
        width=SUPERSAMPLE,
    )

    return overlay.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def enhance_frame(source: Path, destination: Path, frame_index: int) -> None:
    with Image.open(source) as image:
        frame = image.convert("RGBA")
    if frame.size != FRAME_SIZE:
        raise ValueError(f"{source} is {frame.size}; expected {FRAME_SIZE}.")
    frame.alpha_composite(make_keyboard(frame_index))
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.save(destination)


def build_strip(frames_dir: Path, destination: Path) -> None:
    strip = Image.new("RGBA", (FRAME_SIZE[0] * FRAME_COUNT, FRAME_SIZE[1]), CYAN)
    for index in range(FRAME_COUNT):
        with Image.open(frames_dir / f"{index:02d}.png") as image:
            strip.alpha_composite(image.convert("RGBA"), (FRAME_SIZE[0] * index, 0))
    destination.parent.mkdir(parents=True, exist_ok=True)
    strip.convert("RGB").save(destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--strip-output", type=Path, required=True)
    args = parser.parse_args()

    for index in range(FRAME_COUNT):
        enhance_frame(
            args.input_dir / f"{index:02d}.png",
            args.output_dir / f"{index:02d}.png",
            index,
        )
    build_strip(args.output_dir, args.strip_output)


if __name__ == "__main__":
    main()
