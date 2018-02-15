import unittest
from typing import List

from fourplay import FourPlay


class BreadthFirstSearchAI(FourPlay.Player):

    def play(self) -> FourPlay.Disc:
        opponent = self.fourplay.x if self == self.fourplay.o else self.fourplay.o
        result, move = self._play(opponent)
        return move

    def _play(self, opnt: FourPlay.Player, self_best_result: tuple=(-2, None),
              opnt_best_result: tuple=(+2, None), recursion_level: int=1):
        recursion_limit = 8
        for disc in self.fourplay.frontier.choices(shuffle=True):
            self.fourplay.set(disc, self)
            self_result = (self.fourplay.score(disc), disc)
            if self_result[0] is None:
                if recursion_level < recursion_limit:
                    subtree_self_best_result = (-self_best_result[0], self_best_result[1])
                    subtree_opnt_best_result = (-opnt_best_result[0], opnt_best_result[1])
                    opnt_result = BreadthFirstSearchAI._play(opnt, self, subtree_opnt_best_result,
                                                             subtree_self_best_result, recursion_level + 1)
                    self_result = (-opnt_result[0], self_result[1])
                else:
                    self_result = (-1 / recursion_limit, self_result[1])
            else:
                self_result = (self_result[0] / recursion_level, self_result[1])
            self.fourplay.unset(disc)

            if self_result[0] > self_best_result[0]:
                self_best_result = self_result
            if opnt_best_result[0] <= self_best_result[0]:
                break

        return self_best_result


class TestBreadthFirstSearchAI(unittest.TestCase):
    Situations = {
        'Finish': [
            'XXXOXX#',
            'OOOXOOO',
            'XXXOXXX',
            'OOOXOOO',
            'XXXOXXX',
            'OOOXOOO'],
        'EasyWin': [
            '-------',
            '-------',
            '-------',
            '-------',
            '-------',
            'OOO#XXX'],
        'DontScrewUp': [
            '-------',
            '-------',
            '-------',
            'X------',
            'X------',
            'OOO#---'],
        'DontMessUp': [
            '-------',
            '-------',
            '#------',
            'O------',
            'O---X--',
            'O--XX--'],
        'DontF__kUp': [
            '-------',
            '-------',
            '#------',
            'OO-----',
            'OXO----',
            'OXXOXXX']
    }

    @staticmethod
    def find(scenario: List[str], char: str) -> tuple:
        row_line_with_char = [(row, line) for row, line in enumerate(scenario) if char in line]
        assert len(row_line_with_char) == 1
        row, line = row_line_with_char[0]
        return row, line.find(char)

    def play(self, scenario: List[str]):
        ai = BreadthFirstSearchAI(None, 'X')
        fourplay = FourPlay.build(scenario, o=None, x=ai)
        move = ai.play()
        correct = self.find(scenario, '#')
        self.assertEqual((move.row, move.column), correct)

    def test_basics(self):
        self.play(self.Situations['Finish'])
        self.play(self.Situations['EasyWin'])
        self.play(self.Situations['DontScrewUp'])
        self.play(self.Situations['DontMessUp'])
        self.play(self.Situations['DontF__kUp'])

    def test_ai_vs_ai(self):
        o, x = BreadthFirstSearchAI('O'), BreadthFirstSearchAI('X')
        fourplay = FourPlay(o, x)
        while True:
            score = fourplay.round()
            if score is not None:
                break
        self.assertEqual(score, +1, "AI vs AI game must be always won by the starting player:\n" + str(fourplay))
