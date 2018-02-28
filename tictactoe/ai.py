import math
import unittest
from typing import List, Tuple

from tictactoe import TicTacToe


class BreadthFirstSearchAI(TicTacToe.Player):

    def play(self) -> TicTacToe.Tile:
        def best_move(tictactoe: TicTacToe, recursion_level: int=1) -> Tuple[int, TicTacToe.Tile]:
            best_score, best_tile = -math.inf, None

            for tile in tictactoe.choices():
                tictactoe.set(tile)
                score = tictactoe.score(tile)
                if score is None:
                    opponent_score, opponent_tile = best_move(tictactoe, recursion_level + 1)
                    score = -opponent_score
                else:
                    score /= recursion_level
                if score > best_score:
                    best_score, best_tile = score, tile
                tictactoe.unset(tile)
            return best_score, best_tile

        best_score, best_tile = best_move(self.tictactoe)
        return best_tile


class TestBreadthFirstSearchAI(unittest.TestCase):
    Situations = {
        'Finish': [
            '#OX',
            'OXX',
            'OXO'],
        'EasyWin': [
            '#X-',
            'XOO',
            'XOO'],
        'DontScrewUp': [
            'OX-',
            'OX-',
            '#OX'],
        'DontMessUp1': [
            '#-X',
            'OX-',
            'OXO'],
        'DontMessUp2': [
            '#-X',
            'O--',
            'OX-'],
        'DontF__kUp': [
            '-#-',
            '-O-',
            '-OX']
    }

    @staticmethod
    def find(scenario: List[str], char: str) -> tuple:
        row_line_with_char = [(row, line) for row, line in enumerate(scenario) if char in line]
        assert len(row_line_with_char) == 1
        row, line = row_line_with_char[0]
        return row, line.find(char)

    def play(self, scenario: List[str], x: TicTacToe.Player):
        tictactoe = TicTacToe.build(scenario, o=None, x=x)
        tile = x.play()
        correct = self.find(scenario, '#')
        self.assertEqual((tile.row, tile.column), correct)

    def test_basics(self):
        ai = BreadthFirstSearchAI(None, 'X')
        self.play(self.Situations['Finish'], x=ai)
        self.play(self.Situations['EasyWin'], x=ai)
        self.play(self.Situations['DontScrewUp'], x=ai)
        self.play(self.Situations['DontMessUp1'], x=ai)
        self.play(self.Situations['DontMessUp2'], x=ai)
        self.play(self.Situations['DontF__kUp'], x=ai)

    def test_ai_vs_ai(self):
        o, x = BreadthFirstSearchAI('O'), BreadthFirstSearchAI('X')
        tictactoe = TicTacToe(o, x)
        while True:
            score = tictactoe.round()
            if score is not None:
                break
        self.assertEqual(score, 0, "AI vs AI game must always end up in a tie:\n" + str(tictactoe))
