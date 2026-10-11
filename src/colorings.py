"""Color-label helpers."""


def relabel_coloring(colors: dict, label_map: dict) -> dict:
    """Return a relabeled copy without checking graph validity."""
    labels = {0, 1, 2}
    if set(label_map) != labels or set(label_map.values()) != labels:
        raise ValueError("Label map must be a permutation of 0, 1, and 2.")

    try:
        return {node: label_map[color] for node, color in colors.items()}
    except KeyError as error:
        raise ValueError("Colors must be one of 0, 1, or 2.") from error


__all__ = ["relabel_coloring"]
