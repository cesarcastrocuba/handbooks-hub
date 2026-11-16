"""Lossless, deterministic artifact optimization for publication builds.

Recompresses staged PNG diagrams with filter 0 and zlib level 9, asserting
decoded pixel equality before replacing.
"""

from __future__ import annotations

import binascii
from pathlib import Path
import struct
import zlib

from .build_types import BuildError

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    if not data.startswith(PNG_SIGNATURE):
        raise BuildError("not a PNG file: missing PNG signature")
    position, chunks = 8, []
    while position < len(data):
        if position + 8 > len(data):
            raise BuildError("truncated PNG chunk header")
        length, kind = struct.unpack(">I4s", data[position : position + 8])
        end = position + 8 + length + 4
        if end > len(data):
            raise BuildError(f"truncated PNG chunk: expected {length} bytes for {kind!r}")
        payload = data[position + 8 : position + 8 + length]
        checksum = data[position + 8 + length : end]
        expected_crc = struct.unpack(">I", checksum)[0]
        actual_crc = binascii.crc32(kind + payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise BuildError(f"bad CRC in chunk {kind!r}: expected {expected_crc}, got {actual_crc}")
        chunks.append((kind, payload))
        position = end
    return chunks


def _chunk(kind: bytes, payload: bytes) -> bytes:
    crc = binascii.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def _ihdr(data: bytes) -> tuple[int, int, int, int, int, int, int]:
    chunks = _chunks(data)
    for kind, payload in chunks:
        if kind == b"IHDR":
            if len(payload) != 13:
                raise BuildError(f"invalid IHDR chunk length: expected 13, got {len(payload)}")
            return struct.unpack(">IIBBBBB", payload)
    raise BuildError("PNG has no IHDR chunk")


def _pixels_per_byte(color_type: int, bit_depth: int) -> int:
    channels_map = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
    if color_type not in channels_map:
        raise BuildError(f"unsupported PNG color type: {color_type}")
    channels = channels_map[color_type]
    return max(1, (channels * bit_depth + 7) // 8)


def _paeth(left: int, above: int, above_left: int) -> int:
    estimate = left + above - above_left
    left_distance, above_distance = abs(estimate - left), abs(estimate - above)
    corner_distance = abs(estimate - above_left)
    if left_distance <= above_distance and left_distance <= corner_distance:
        return left
    return above if above_distance <= corner_distance else above_left


def _unfilter(raw: bytes, width: int, height: int, color_type: int, bit_depth: int) -> bytes:
    """Undo PNG row filters and return the raw pixel bytes."""
    bpp = _pixels_per_byte(color_type, bit_depth)
    channels_map = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
    channels = channels_map[color_type]
    row_bytes = (width * channels * bit_depth + 7) // 8
    expected_len = height * (row_bytes + 1)
    if len(raw) != expected_len:
        raise BuildError(f"PNG scanline length {len(raw)} does not match IHDR expected {expected_len}")
    pixels: list[bytes] = []
    previous = bytearray(row_bytes)
    position = 0
    for _ in range(height):
        method = raw[position]
        position += 1
        row = bytearray(raw[position : position + row_bytes])
        position += row_bytes
        if method == 1:
            for index in range(bpp, row_bytes):
                row[index] = (row[index] + row[index - bpp]) & 0xFF
        elif method == 2:
            for index in range(row_bytes):
                row[index] = (row[index] + previous[index]) & 0xFF
        elif method == 3:
            for index in range(row_bytes):
                left = row[index - bpp] if index >= bpp else 0
                row[index] = (row[index] + ((left + previous[index]) >> 1)) & 0xFF
        elif method == 4:
            for index in range(row_bytes):
                left = row[index - bpp] if index >= bpp else 0
                corner = previous[index - bpp] if index >= bpp else 0
                row[index] = (row[index] + _paeth(left, previous[index], corner)) & 0xFF
        elif method != 0:
            raise BuildError(f"unsupported PNG filter method {method}")
        pixels.append(bytes(row))
        previous = row
    return b"".join(pixels)


def png_pixels(data: bytes) -> bytes:
    """Decoded (unfiltered) pixel bytes; the equivalence unit for optimization."""
    width, height, bit_depth, color_type, _, _, interlace = _ihdr(data)
    if interlace:
        return b""
    idat = b"".join(payload for kind, payload in _chunks(data) if kind == b"IDAT")
    if not idat:
        raise BuildError("PNG has no IDAT stream")
    try:
        decompressed = zlib.decompress(idat)
    except zlib.error as exc:
        raise BuildError(f"PNG IDAT decompression failed: {exc}") from exc
    return _unfilter(decompressed, width, height, color_type, bit_depth)


def png_recompress(data: bytes) -> bytes:
    """Return a smaller PNG with identical pixels, or the original bytes."""
    width, height, bit_depth, color_type, _, _, interlace = _ihdr(data)
    if interlace:
        return data
    pixels = png_pixels(data)
    channels_map = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
    channels = channels_map[color_type]
    row_bytes = (width * channels * bit_depth + 7) // 8
    filtered = b"".join(
        b"\x00" + pixels[offset : offset + row_bytes]
        for offset in range(0, len(pixels), row_bytes)
    )
    compressed = zlib.compress(filtered, 9)
    chunks = _chunks(data)
    out: list[bytes] = [PNG_SIGNATURE]
    inserted = False
    for kind, payload in chunks:
        if kind == b"IDAT":
            if not inserted:
                out.append(_chunk(b"IDAT", compressed))
                inserted = True
            continue
        out.append(_chunk(kind, payload))
    candidate = b"".join(out)
    if png_pixels(candidate) != pixels:
        raise BuildError("PNG recompression changed pixel data")
    return candidate if len(candidate) < len(data) else data


def optimize_png_file(path: Path) -> dict[str, int]:
    data = path.read_bytes()
    candidate = png_recompress(data)
    saved = len(data) - len(candidate)
    if saved > 0:
        path.write_bytes(candidate)
    return {"before": len(data), "after": len(candidate), "saved": saved}


def optimize_staged_pngs(root: Path) -> dict[str, int]:
    """Optimize all PNG images under a staged build workspace."""
    results = [optimize_png_file(path) for path in sorted(root.rglob("*.png")) if path.is_file()]
    return {
        "files": len(results),
        "before": sum(r["before"] for r in results),
        "after": sum(r["after"] for r in results),
        "saved": sum(r["saved"] for r in results),
    }
