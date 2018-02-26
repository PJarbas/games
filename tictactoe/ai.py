import math
import random
import unittest
from typing import Tuple

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


class MonteCarloSearchAI(TicTacToe.Player):
    def __init__(self, *args, **kwargs):
        super(TicTacToe.Player, self).__init__(*args, **kwargs)
        self.scores = {}

    def play(self) -> TicTacToe.Tile:
        tictactoe = self.tictactoe

        def unvisited_tiles(tictactoe: TicTacToe) -> list:
            retval = []
            for tile in tictactoe.choices():
                tictactoe.set(tile)
                if str(tictactoe) not in self.scores:
                    retval.append(tile)
                tictactoe.clear(tile)
            return retval

        def optimal_tile(tictactoe: TicTacToe, criterium: object) -> TicTacToe.Tile:
            best_criterium, best_tile = None, None
            for tile in tictactoe.choices():
                tictactoe.set(tile)
                if str(tictactoe) in self.scores:
                    (wins, visits, _) = self.scores[str(tictactoe)]
                    if best_criterium is None or best_criterium <= criterium(wins, visits):
                        best_criterium, best_tile = criterium(wins, visits), tile
                tictactoe.clear(tile)
            return best_tile

        def select(tictactoe: TicTacToe) -> int:
            (parent_wins, parent_visits, parent_tile) = self.scores[str(tictactoe)]
            score_ulp = lambda wins, visits: (wins / visits) + 0.3 * math.sqrt(math.log(parent_visits) / visits)

            unvisited = unvisited_tiles(tictactoe)
            if not unvisited:
                if tictactoe.next == self:
                    best_tile = optimal_tile(tictactoe, criterium=lambda *args: + score_ulp(*args))
                else:
                    best_tile = optimal_tile(tictactoe, criterium=lambda *args: - score_ulp(*args))
                tictactoe.set(best_tile)
                score = tictactoe.score(best_tile, self)
                if score is None:
                    return select(tictactoe)
                else:
                    return score
            else:
                expand_tile = random.choice(unvisited)
                tictactoe.set(expand_tile)
                score = tictactoe.score(expand_tile, self)
                if score is None:
                    score = playout(tictactoe)
                self.scores[str(tictactoe)] = (0, 0, expand_tile)
                return score

        def playout(tictactoe: TicTacToe) -> int:
            tile = random.choice(tictactoe.choices())
            tictactoe.set(tile)
            score = tictactoe.score(tile, self)
            score = 0 if score == -1 else score
            if score is None:
                score = playout(tictactoe)
            tictactoe.clear(tile)
            return score

        def backpropagate(tictactoe: TicTacToe, score: int):
            str_tictactoe = str(tictactoe)
            (wins, visits, tile) = self.scores[str(tictactoe)]
            self.scores[str_tictactoe] = (wins + score, visits + 1, tile)
            if tile is not None:
                tictactoe.clear(tile)
                backpropagate(tictactoe, score)

        (wins, visits, tile) = self.scores.get(str(tictactoe), (0, 0, None))
        self.scores[str(tictactoe)] = (wins, visits, None)

        repeat = 1000
        while repeat > 0:
            score = select(tictactoe)
            backpropagate(tictactoe, score)
            repeat -= 1

        return optimal_tile(tictactoe, criterium=lambda wins, visits: visits)

    def reset(self):
        self.scores.clear()


class TestTicTacToe(unittest.TestCase):
    def testBreadthFirstSearchAIBasics(self):
        self.basicAI(TicTacToe.BreadthFirstSearchAI)

    def testMonteCarloSearchAIBasics(self):
        self.basicAI(TicTacToe.MonteCarloSearchAI)

    def basicAI(self, AI):
        ai = AI('☓')
        player = TicTacToe.Player('◯')
        ticTacToe = TicTacToe(player, ai)

        ticTacToe.ai = AI(ticTacToe.ai.symbol)
        ticTacToe.build(["☐◯☓",
                         "◯☓☓",
                         "◯☓◯"], next=ticTacToe.ai)
        score, tile = ticTacToe.ai.play(ticTacToe)
        self.assertEqual((tile.row, tile.column), (0, 0))

        ticTacToe.ai = AI(ticTacToe.ai.symbol)
        ticTacToe.build(["☐☓☐",
                         "☓◯◯",
                         "☓◯◯"], next=ticTacToe.ai)
        score, tile = ticTacToe.ai.play(ticTacToe)
        self.assertEqual((tile.row, tile.column), (0, 0))

        ticTacToe.build(["◯☓☐",
                         "◯☓☐",
                         "☐◯☓"], next=ticTacToe.ai)
        score, tile = ticTacToe.ai.play(ticTacToe)
        self.assertEqual((tile.row, tile.column), (2, 0))

        ticTacToe.build(["☐☐☓",
                         "◯☓☐",
                         "◯☓◯"], next=ticTacToe.ai)
        score, tile = ticTacToe.ai.play(ticTacToe)
        self.assertEqual((tile.row, tile.column), (0, 1))

        ticTacToe.build(["☐☐☓",
                         "◯☐☐",
                         "◯☓☐"], next=ticTacToe.ai)
        score, tile = ticTacToe.ai.play(ticTacToe)
        self.assertEqual((tile.row, tile.column), (0, 0))

        ticTacToe.build(["☓☓◯",
                         "☐◯☐",
                         "☐◯☓"], next=ticTacToe.ai)
        score, tile = ticTacToe.ai.play(ticTacToe)
        self.assertEqual((tile.row, tile.column), (2, 0))

        ticTacToe.build(["☐☐☐",
                         "☐◯☐",
                         "☐◯☓"], next=ticTacToe.ai)
        score, tile = ticTacToe.ai.play(ticTacToe)
        self.assertEqual((tile.row, tile.column), (0, 1))

    def testBreadthFirstSearchAIvsAI(self):
        o = TicTacToe.BreadthFirstSearchAI("◯")
        x = TicTacToe.BreadthFirstSearchAI("☓")
        self.AIvsAI(o, x)

    @unittest.skip("Broken...")
    def testMonteCarloSearchAIvsAI(self):
        o = TicTacToe.MonteCarloSearchAI("◯")
        x = TicTacToe.MonteCarloSearchAI("☓")
        self.AIvsAI(o, x)

    def testMonteCarloSearchAIvsBreadthFirstSearchAI(self):
        o = TicTacToe.MonteCarloSearchAI("◯")
        x = TicTacToe.BreadthFirstSearchAI("☓")
        self.AIvsAI(o, x)

    def AIvsAI(self, o, x):
        ticTacToe = TicTacToe(o, x)
        while True:
            _, oTile = o.play(ticTacToe)
            ticTacToe.set(oTile)
            score = ticTacToe.score(oTile)
            if score is not None:
                break
            _, xTile = x.play(ticTacToe)
            ticTacToe.set(xTile)
            score = ticTacToe.score(xTile)
            if score is not None:
                break
        self.assertEqual(0, score, "AI vs AI game must always end up in a tie:\n" + str(ticTacToe))
