#!/opt/bin/python3
"""Generate the NAS542 book icon (ICO + PNG) without third-party modules.

Usage: make_icon.py <output-dir>

Writes:
    favicon.ico        16/32/48 px, PNG-compressed frames
    nas542-logo.png    64 px, transparent background (header logo)
"""

import os
import struct
import sys
import zlib

BG = (31, 58, 95, 255)        # deep blue
PAGE_L = (255, 255, 255, 255)
PAGE_R = (226, 233, 243, 255)
SPINE = (217, 164, 65, 255)   # warm accent

SS = 4  # supersampling factor


def rounded_rect(x, y, w, h, r):
    def inside(px, py):
        if px < x or py < y or px > x + w or py > y + h:
            return False
        cx = min(max(px, x + r), x + w - r)
        cy = min(max(py, y + r), y + h - r)
        return (px - cx) ** 2 + (py - cy) ** 2 <= r * r
    return inside


def poly(points):
    def inside(px, py):
        res = False
        j = len(points) - 1
        for i in range(len(points)):
            xi, yi = points[i]
            xj, yj = points[j]
            if (yi > py) != (yj > py):
                xint = (xj - xi) * (py - yi) / (yj - yi) + xi
                if px < xint:
                    res = not res
            j = i
        return res
    return inside


def render(size):
    w = h = size * SS
    buf = [[(0, 0, 0, 0)] * w for _ in range(h)]

    margin = w * 0.02
    bg = rounded_rect(margin, margin, w - 2 * margin, h - 2 * margin, w * 0.22)

    left = poly([(w * 0.22, h * 0.30), (w * 0.48, h * 0.35),
                 (w * 0.48, h * 0.74), (w * 0.22, h * 0.68)])
    right = poly([(w * 0.52, h * 0.35), (w * 0.78, h * 0.30),
                  (w * 0.78, h * 0.68), (w * 0.52, h * 0.74)])
    spine = rounded_rect(w * 0.475, h * 0.35, w * 0.05, h * 0.39, w * 0.02)

    for y in range(h):
        for x in range(w):
            if not bg(x, y):
                continue
            color = BG
            if left(x, y):
                color = PAGE_L
            elif right(x, y):
                color = PAGE_R
            elif spine(x, y):
                color = SPINE
            buf[y][x] = color

    # box filter down to the target size
    out = []
    for y in range(size):
        row = []
        for x in range(size):
            r = g = b = a = 0
            for dy in range(SS):
                for dx in range(SS):
                    pr, pg, pb, pa = buf[y * SS + dy][x * SS + dx]
                    r += pr * pa
                    g += pg * pa
                    b += pb * pa
                    a += pa
            if a:
                row.append((r // a, g // a, b // a, a // (SS * SS)))
            else:
                row.append((0, 0, 0, 0))
        out.append(row)
    return out


def png_bytes(pixels):
    size = len(pixels)
    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for r, g, b, a in row:
            raw += bytes((r, g, b, a))

    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) +
            chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b''))


def ico_bytes(images):
    header = struct.pack('<HHH', 0, 1, len(images))
    entries = b''
    data = b''
    offset = 6 + 16 * len(images)
    for size, blob in images:
        entries += struct.pack('<BBBBHHII', size, size, 0, 0, 1, 32, len(blob), offset)
        offset += len(blob)
        data += blob
    return header + entries + data


def main(argv):
    outdir = argv[1] if len(argv) > 1 else '.'
    os.makedirs(outdir, exist_ok=True)

    images = [(s, png_bytes(render(s))) for s in (16, 32, 48)]
    with open(os.path.join(outdir, 'favicon.ico'), 'wb') as fh:
        fh.write(ico_bytes(images))
    with open(os.path.join(outdir, 'nas542-logo.png'), 'wb') as fh:
        fh.write(png_bytes(render(64)))
    print('icons written to %s' % outdir)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
