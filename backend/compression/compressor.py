import zstandard as zstd
import gzip
from io import BytesIO


def compress_bytes(data: bytes) -> dict[str, bytes | str | int]:
    try:
        cctx = zstd.ZstdCompressor(level=3)
        compressed = cctx.compress(data)
        return {
            "algorithm": "zstd",
            "compressed_bytes": compressed,
            "compressed_size": len(compressed),
        }
    except Exception:
        out = BytesIO()
        with gzip.GzipFile(fileobj=out, mode="wb") as gz:
            gz.write(data)
        compressed = out.getvalue()
        return {
            "algorithm": "gzip",
            "compressed_bytes": compressed,
            "compressed_size": len(compressed),
        }
