import pytest

from src.commitments import check_opening, create_commitment


def test_original_opening_passes():
    commitment = create_commitment(1, 42)

    assert check_opening(commitment, 1, 42) is True


@pytest.mark.parametrize(
    "color, nonce",
    [
        (0, 42),
        (2, 42),
        (1, 43),
    ],
)
def test_changed_color_or_nonce_fails(color, nonce):
    commitment = create_commitment(1, 42)

    assert check_opening(commitment, color, nonce) is False


def test_invalid_color_raises_value_error():
    with pytest.raises(ValueError, match="Color must be one of 0, 1, or 2"):
        create_commitment(3, 42)
