"""SHA-256 commitments for 3-coloring openings.

To use:
    commitment = create_commitment(color, nonce)
    ok = check_opening(commitment, color, nonce)

The commitment binds a single color value (0, 1, or 2) to a fresh random
128-bit nonce. The same opening reproduces the same digest; changing either
part fails verification.
"""

import hashlib
import secrets


def _encode_opening(color: int, nonce: int) -> bytes:
    """Encode the color and nonce consistently for hashing."""
    if not isinstance(color, int):
        raise TypeError("Color must be an integer.")
    if not isinstance(nonce, int):
        raise TypeError("Nonce must be an integer.")

    if color not in (0, 1, 2):
        raise ValueError("Color must be one of 0, 1, or 2.")
    if nonce < 0 or nonce >= 2**128:
        raise ValueError("Nonce must be a 128-bit integer between 0 and 2**128 - 1.")

    return bytes((color,)) + nonce.to_bytes(16, byteorder="big", signed=False)


def create_commitment(color: int, nonce: int = None) -> str:
    """Create a SHA-256 commitment for a color and fresh nonce."""
    if nonce is None:
        nonce = secrets.randbits(128)

    opening = _encode_opening(color, nonce)
    return hashlib.sha256(opening).hexdigest()


def check_opening(commitment: str, color: int, nonce: int) -> bool:
    """Return True when the supplied opening matches the commitment."""
    return commitment == create_commitment(color, nonce)


__all__ = ["create_commitment", "check_opening"]
