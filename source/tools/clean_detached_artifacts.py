"""Repair a directional Codex pet row by mirroring its complete counterpart."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


COLUMNS = 8
ROWS = 9


def validate_sheet(sheet: Image.Image) -> tuple[int, int]:
    if sheet.width % COLUMNS or sheet.height % ROWS:
        raise ValueError(
            f"Sheet size {sheet.size} is not divisible by {COLUMNS}x{ROWS}."
        )
    return sheet.width // COLUMNS, sheet.height // ROWS


def validate_row(row: int) -> None:
    if row < 0 or row >= ROWS:
        raise ValueError(f"Row must be between 0 and {ROWS - 1}; got {row}.")


def mirror_row(sheet: Image.Image, source_row: int, target_row: int) -> Image.Image:
    validate_row(source_row)
    validate_row(target_row)
    if source_row == target_row:
        raise ValueError("Source and target rows must be different.")

    frame_width, frame_height = validate_sheet(sheet)
    output = sheet.convert("RGBA")
    for column in range(COLUMNS):
        source_box = (
            column * frame_width,
            source_row * frame_height,
            (column + 1) * frame_width,
            (source_row + 1) * frame_height,
        )
        target_position = (column * frame_width, target_row * frame_height)
        output.paste(ImageOps.mirror(output.crop(source_box)), target_position)
    return output


def clear_transparent_rgb(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    raw = bytearray(rgba.tobytes())
    for offset in range(0, len(raw), 4):
        if raw[offset + 3] == 0:
            raw[offset : offset + 3] = b"\x00\x00\x00"
    return Image.frombytes("RGBA", rgba.size, bytes(raw))


def update_contact_sheet(sheet: Image.Image, destination: Path, row: int) -> None:
    with Image.open(destination) as image:
        contact = image.convert("RGB")

    frame_width, frame_height = validate_sheet(sheet)
    preview_width = contact.width // COLUMNS
    preview_height = frame_height // 2
    row_height = contact.height // ROWS
    image_top = row * row_height + (row_height - preview_height - 8)

    for column in range(COLUMNS):
        tile = Image.new("RGB", (preview_width, preview_height), (238, 238, 238))
        draw = ImageDraw.Draw(tile)
        checker_size = 12
        for y in range(0, preview_height, checker_size):
            for x in range(0, preview_width, checker_size):
                if (x // checker_size + y // checker_size) % 2:
                    draw.rectangle(
                        (
                            x,
                            y,
                            min(x + checker_size - 1, preview_width - 1),
                            min(y + checker_size - 1, preview_height - 1),
                        ),
                        fill=(255, 255, 255),
                    )

        frame_box = (
            column * frame_width,
            row * frame_height,
            (column + 1) * frame_width,
            (row + 1) * frame_height,
        )
        frame = sheet.crop(frame_box).resize(
            (preview_width, preview_height), Image.Resampling.LANCZOS
        )
        tile.paste(frame, (0, 0), frame)
        draw.rectangle(
            (0, 0, preview_width - 1, preview_height - 1),
            outline=(0, 150, 90),
            width=1,
        )
        contact.paste(tile, (column * preview_width, image_top))

    contact.save(destination, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-row", type=int, required=True)
    parser.add_argument("--target-row", type=int, required=True)
    parser.add_argument("--contact-sheet", type=Path)
    args = parser.parse_args()

    with Image.open(args.input) as image:
        repaired = mirror_row(
            image.convert("RGBA"),
            source_row=args.source_row,
            target_row=args.target_row,
        )
    repaired = clear_transparent_rgb(repaired)

    destination = args.output.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f"{destination.stem}.tmp{destination.suffix}")
    repaired.save(temporary, "WEBP", lossless=True, method=6, exact=True)
    temporary.replace(destination)
    if args.contact_sheet:
        update_contact_sheet(repaired, args.contact_sheet, args.target_row)
    print(
        f"Mirrored row {args.source_row} into row {args.target_row} "
        f"across {COLUMNS} complete frames."
    )


if __name__ == "__main__":
    main()
