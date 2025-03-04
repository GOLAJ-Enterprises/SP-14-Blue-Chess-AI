from functools import wraps


def validate_positions(*arg_indices: int):
    """A decorator that validates that the positional arguments at the given
    indices are valid chessboard positions using `is_valid_pos`. If the
    validation fails, it returns False instead of calling the decorated function.

    Args:
        *arg_indices (int): Indices in the args tuple that should be valid positions.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gather positions from the specified indices
            try:
                positions = [args[i] for i in arg_indices]
            except IndexError:
                # Not enough positional arguments were passed
                return False

            if not is_valid_pos(*positions):
                return False

            return func(*args, **kwargs)

        return wrapper

    return decorator


def is_valid_pos(*positions: tuple[int, int]) -> bool:
    """
    Returns True if all positions given are valid chessboard positions.

    Args:
        *positions (tuple[int, int]): the tuple containing the positions to verify.

    Returns:
        bool: True if all positions checked are valid.
    """
    for pos in positions:
        if not (
            isinstance(pos, tuple)
            and len(pos) == 2
            and all(isinstance(i, int) and 0 <= i < 8 for i in pos)
        ):
            return False

    return True
