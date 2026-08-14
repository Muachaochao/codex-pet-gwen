"""Remove detached alpha components from selected Codex pet animation rows."""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image


COLUMNS = 8
ROWS = 9


def find_components(alpha: Image.Image) -> list[list[int]]:
    width, height = alpha.size
    pixels = alpha.load()
    visited = bytearray(width * height)
    components: list[list[int]] = []

    for start in range(width * height):
        if visited[start] or pixels[start % width, start // width] == 0:
            continue

        visited[start] = 1
        queue = deque([start])
        component: list[int] = []
        while queue:
            pixel = queue.popleft()
            component.append(pixel)
            x = pixel % width
            y = pixel // width

            for neighbor in (pixel - 1, pixel + 1, pixel - width, pixel + width):
                if neighbor < 0 or neighbor >= width * height or visited[neighbor]:
                    continue
                neighbor_x = neighbor % width
                neighbor_y = neighbor // width
                if abs(neighbor_x - x) + abs(neighbor_y - y) != 1:
                    continue
                if pixels[neighbor_x, neighbor_y] == 0:
                    continue

                visited[neighbor] = 1
                queue.append(neighbor)

        components.append(component)

    return components


def clean_frame(frame: Image.Image) -> tuple[Image.Image, int, int]:
    rgba = frame.convert("RGBA")
    components = find_components(rgba.getchannel("A"))
    if len(components) <= 1:
        return rgba, 0, 0

    main_component = max(components, key=len)
    main_pixels = set(main_component)
    raw = bytearray(rgba.tobytes())
    removed_pixels = 0
    for component in components:
        if component is main_component:
            continue
        for pixel in component:
            if pixel in main_pixels:
                continue
            offset = pixel * 4
            raw[offset : offset + 4] = b"\x00\x00\x00\x00"
            removed_pixels += 1

    return Image.frombytes("RGBA", rgba.size, bytes(raw)), removed_pixels, len(components) - 1


def clean_row(sheet: Image.Image, row: int) -> tuple[Image.Image, list[tuple[int, int, int]]]:
    if row < 0 or row >= ROWS:
        raise ValueError(f"Row must be between 0 and {ROWS - 1}; got {row}.")
    if sheet.width % COLUMNS or sheet.height % ROWS:
        raise ValueError(
            f"Sheet size {sheet.size} is not divisible by {COLUMNS}x{ROWS}."
        )

    frame_width = sheet.width // COLUMNS
    frame_height = sheet.height // ROWS
    output = sheet.convert("RGBA")
    report: list[tuple[int, int, int]] = []

    for column in range(COLUMNS):
        box = (
            column * frame_width,
            row * frame_height,
            (column + 1) * frame_width,
            (row + 1) * frame_height,
        )
        cleaned, removed_pixels, removed_components = clean_frame(output.crop(box))
        output.paste(cleaned, box[:2])
        report.append((column, removed_components, removed_pixels))

    return output, report


def clear_transparent_rgb(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    raw = bytearray(rgba.tobytes())
    for offset in range(0, len(raw), 4):
        if raw[offset + 3] == 0:
            raw[offset : offset + 3] = b"\x00\x00\x00"
    return Image.frombytes("RGBA", rgba.size, bytes(raw))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--row", type=int, required=True)
    args = parser.parse_args()

    with Image.open(args.input) as image:
        cleaned, report = clean_row(image.convert("RGBA"), args.row)
    cleaned = clear_transparent_rgb(cleaned)

    destination = args.output.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f"{destination.stem}.tmp{destination.suffix}")
    cleaned.save(temporary, "WEBP", lossless=True, method=6, exact=True)
    temporary.replace(destination)

    for column, component_count, pixel_count in report:
        if pixel_count:
            print(
                f"row={args.row} column={column}: removed "
                f"{component_count} components / {pixel_count} pixels"
            )


if __name__ == "__main__":
    main()
