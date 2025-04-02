import bitboarder


def print_board():
    for row in board.serialize():
        print(row)


board = bitboarder.Board()
print_board()
move = bitboarder.Move.from_uci("e2e4")
success = board.push(move)
print(success)
print_board()
