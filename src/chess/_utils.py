def algebraic_to_coord(square: str) -> tuple[int, int]:
    file_char = square[0].lower()
    rank_char = square[1]

    col = ord(file_char) - ord("a")
    row = 8 - int(rank_char)

    return (row, col)


def coord_to_algebraic(coord: tuple[int, int]) -> str:
    row, col = coord

    file = chr(ord("a") + col)
    rank = str(8 - row)

    return f"{file}{rank}"


def is_valid_coord(coord: tuple[int, int], lower: int = 0, upper: int = 8) -> bool:
    row, col = coord
    return lower <= row < upper and lower <= col < upper


def get_coords_between(
    start: tuple[int, int], end: tuple[int, int], include_end: bool = False
) -> list[tuple[int, int]]:
    path = []

    sr, sc = start
    er, ec = end

    dr = er - sr
    dc = ec - sc

    # Ensure `end` is orthogonal or diagonal to `start`
    if sr != er and sc != ec and abs(dr) != abs(dc):
        return []

    # Determine movement direction
    row_step = 1 if dr > 0 else -1 if dr < 0 else 0
    col_step = 1 if dc > 0 else -1 if dc < 0 else 0

    # Check from first step to end
    r, c = sr, sc
    while (next_pos := (r + row_step, c + col_step)) != end:
        path.append(next_pos)
        r, c = next_pos

    if include_end:
        path.append(end)

    return path
