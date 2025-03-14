from chess import ChessEngine
from pygame_gui import ChessGUI
from game_interface import GameInterface


def main():
    engine = ChessEngine()
    gui = ChessGUI()
    interface = GameInterface(engine, gui)

    interface.init()
    interface.run_game_loop()


if __name__ == "__main__":
    main()
