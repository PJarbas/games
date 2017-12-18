from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QMessageBox, QSizePolicy, QVBoxLayout, QComboBox
from PyQt5.QtCore import Qt, QSize
import unittest
import random
import math
import sys


class TicTacToe:
    class Tile:
        def __init__(self, row, column, player=None):
            self.row, self.column = row, column
            self.player = player
            self.delegate = None

        def __repr__(self):
            base = [[" "] * 3] * 3
            base[self.row][self.column] = str(self.player) if self.player is not None else "☐"
            return "\n".join(["".join(line) for line in base])

        def __str__(self):
            return str(self.player) if self.player is not None else "☐"

        def completeRow(self, ticTacToe):
            row, player = self.row, self.player
            return player == ticTacToe[row, 0].player == ticTacToe[row, 1].player == ticTacToe[row, 2].player

        def completeColumn(self, ticTacToe):
            column, player = self.column, self.player
            return player == ticTacToe[0, column].player == ticTacToe[1, column].player == ticTacToe[2, column].player

        def completeDiagonal(self, ticTacToe):
            row, column, player = self.row, self.column, self.player
            if column - row == 0:
                return player == ticTacToe[0, 0].player == ticTacToe[1, 1].player == ticTacToe[2, 2].player
            if column + row == 2:
                return player == ticTacToe[0, 2].player == ticTacToe[1, 1].player == ticTacToe[2, 0].player

        def notify(self):
            if self.delegate is not None:
                self.delegate.updateEvent(self)

    class Player:
        def __init__(self, symbol):
            self.symbol = symbol

        def __repr__(self):
            return self.symbol

        def reset(self):
            pass

    class BreadthFirstSearchAI(Player):
        def __init__(self, symbol):
            super().__init__(symbol)

        def play(self, ticTacToe, recursionLevel=1):
            bestScore, bestTile = -math.inf, None

            for tile in ticTacToe.choices():
                ticTacToe.set(tile)
                score = ticTacToe.score(tile)
                if score is None:
                    opponentScore, opponentTile = self.play(ticTacToe, recursionLevel + 1)
                    score = -opponentScore
                else:
                    score /= recursionLevel
                if score > bestScore:
                    bestScore, bestTile = score, tile
                ticTacToe.clear(tile)

            return bestScore, bestTile

    class MonteCarloSearchAI(Player):
        def __init__(self, symbol):
            super().__init__(symbol)
            self.scores = {}

        def play(self, ticTacToe):

            def unvisitedTiles(ticTacToe):
                retval = []
                for tile in ticTacToe.choices():
                    ticTacToe.set(tile)
                    if str(ticTacToe) not in self.scores:
                        retval.append(tile)
                    ticTacToe.clear(tile)
                return retval

            def optimalTile(ticTacToe, criterium):
                bestCriterium, bestTile = None, None
                for tile in ticTacToe.choices():
                    ticTacToe.set(tile)
                    if str(ticTacToe) in self.scores:
                        (wins, visits, _) = self.scores[str(ticTacToe)]
                        if bestCriterium is None or bestCriterium <= criterium(wins, visits):
                            bestCriterium, bestTile = criterium(wins, visits), tile
                    ticTacToe.clear(tile)
                return bestTile

            def select(ticTacToe):
                (parentWins, parentVisits, parentTile) = self.scores[str(ticTacToe)]
                scoreULP = lambda wins, visits: (wins / visits) + 1.0 * math.sqrt(math.log(parentVisits) / visits)

                unvisited = unvisitedTiles(ticTacToe)
                if not unvisited:
                    bestTile = optimalTile(ticTacToe, criterium=lambda *args: + scoreULP(*args))
                    ticTacToe.set(bestTile)
                    score = ticTacToe.score(bestTile)
                    if score is None:
                        return select(ticTacToe)
                    else:
                        return ticTacToe.previousPlayer, score
                else:
                    expandTile = random.choice(unvisited)
                    expandTile = unvisited[0]
                    ticTacToe.set(expandTile)
                    if str(ticTacToe) in self.scores:
                        (wins, visits, tiles) = self.scores[str(ticTacToe)]
                        tiles.append(expandTile)
                    else:
                        self.scores[str(ticTacToe)] = (0, 0, [expandTile])
                    winner = ticTacToe.previousPlayer
                    score = ticTacToe.score(expandTile)
                    if score is None:
                        winner, score = playout(ticTacToe)
                    return winner, score

            def playout(ticTacToe):
                tile = random.choice(ticTacToe.choices())
                ticTacToe.set(tile)
                winner = ticTacToe.previousPlayer
                score = ticTacToe.score(tile)
                if score is None:
                    winner = playout(ticTacToe)
                ticTacToe.clear(tile)
                return winner, score

            def backpropagate(ticTacToe, winner, score):
                (wins, visits, tiles) = self.scores[str(ticTacToe)]
                wins = wins + score if winner == ticTacToe.previousPlayer else wins
                self.scores[str(ticTacToe)] = (wins, visits + 1, tiles)
                if tiles:
                    for tile in tiles:
                        ticTacToe.clear(tile)
                        backpropagate(ticTacToe, winner, score)
                        ticTacToe.set(tile)
                    ticTacToe.clear(tiles[0])

            (wins, visits, tile) = self.scores.get(str(ticTacToe), (0, 0, None))
            self.scores[str(ticTacToe)] = (wins, visits, None)

            repeat = 1000
            while repeat > 0:
                winner, score = select(ticTacToe)
                backpropagate(ticTacToe, winner, score)
                repeat -= 1

            graph = self.visualize(ticTacToe)
            graph.draw("graph.png", prog="dot")
            return 0, optimalTile(ticTacToe, criterium=lambda wins, visits: visits)

        def visualize(self, ticTacToe):
            from pygraphviz import AGraph
            graph = AGraph(name='Tic-Tac-Toe', directed=True)
            graph.graph_attr['label'] = 'Tic-Tac-Toe'
            graph.node_attr['style'] = 'filled'

            def traverse(ticTacToe):
                for choice in ticTacToe.choices():
                    ticTacToe.set(choice)
                    if str(ticTacToe) in self.scores:
                        strCurrent = str(ticTacToe)
                        (currentWins, currentVisits, currentTiles) = self.scores[str(ticTacToe)]
                        if currentTiles:
                            for tile in currentTiles:
                                ticTacToe.clear(tile)
                                (_, visits, _) = self.scores[str(ticTacToe)]
                                graph.add_edge(str(ticTacToe), strCurrent, label=tile, weight=visits)
                                if ticTacToe.previousPlayer == self:
                                    graph.get_node(str(ticTacToe)).attr['fillcolor'] = 'gray'
                                    graph.get_node(strCurrent).attr['fillcolor'] = 'white'

                                else:
                                    graph.get_node(str(ticTacToe)).attr['fillcolor'] = 'white'
                                    graph.get_node(strCurrent).attr['fillcolor'] = 'gray'
                                ticTacToe.set(tile)
                            traverse(ticTacToe)
                    ticTacToe.clear(choice)

            for strTicTacToe, (wins, visits, tiles) in self.scores.items():
                graph.add_node(strTicTacToe, label="{:s}{:d}|{:d}".format(strTicTacToe, wins, visits))
            traverse(ticTacToe)
            return graph

        def reset(self):
            self.scores.clear()

    def __init__(self, player, ai):
        super().__init__()
        self.size = 3
        self.ai = ai
        self.player = player
        self.nextPlayer = self.player
        self.previousPlayer = self.ai
        self.tiles = {}
        for row in range(self.size):
            for column in range(self.size):
                self.tiles[row, column] = TicTacToe.Tile(row, column)

    def __getitem__(self, item):
        return self.tiles[item]

    def __iter__(self):
        return iter(self.tiles.values())

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)

    def __repr__(self):
        string = ""
        for row in range(self.size):
            for column in range(self.size):
                string += str(self[row, column])
            string += "\n"
        return string

    def build(self, symbols, nextPlayer):
        self.reset()
        for row, symbols_row in enumerate(symbols):
            for column, symbol in enumerate(symbols_row):
                tile = self[row, column]
                if symbol == self.player.symbol:
                    tile.player = self.player
                elif symbol == self.ai.symbol:
                    tile.player = self.ai
                else:
                    tile.player = None
        self.nextPlayer = nextPlayer
        self.previousPlayer = self.player if self.previousPlayer == self.ai else self.ai

    def set(self, tile, notify=False):
        if tile.player is not None:
            raise RuntimeError("Inconsistent TicTacToe state")
        tile.player = self.nextPlayer
        self.nextPlayer = self.player if self.nextPlayer == self.ai else self.ai
        self.previousPlayer = self.player if self.previousPlayer == self.ai else self.ai
        if notify is True:
            tile.notify()

    def clear(self, tile, notify=False):
        if tile.player is None:
            raise RuntimeError("Inconsistent TicTacToe state")
        tile.player = None
        self.nextPlayer = self.player if self.nextPlayer == self.ai else self.ai
        self.previousPlayer = self.player if self.previousPlayer == self.ai else self.ai
        if notify is True:
            tile.notify()

    def score(self, tile, player=None):
        def complete(ticTacToe):
            for tile in ticTacToe:
                if tile.player is None:
                    return False
            return True

        if tile.player is None:
            return None
        if player is None:
            player = tile.player
        if tile.completeRow(self):
            return +1 if tile.player == player else -1
        if tile.completeColumn(self):
            return +1 if tile.player == player else -1
        if tile.completeDiagonal(self):
            return +1 if tile.player == player else -1
        if complete(self):
            return 0
        return None

    def choices(self):
        return list(filter(lambda tile: tile.player is None, self))

    def round(self, playerTile):
        self.set(playerTile, True)
        playerScore = self.score(playerTile)
        if playerScore is not None:
            return playerScore

        _, aiTile = self.ai.play(self)
        self.set(aiTile, True)
        aiScore = self.score(aiTile)
        if aiScore is not None:
            return -aiScore
        return None

    def reset(self, notify=False):
        for tile in self:
            tile.player = None
            if notify is True:
                tile.notify()
        self.player.reset()
        self.nextPlayer = self.player
        self.ai.reset()
        self.previousPlayer = self.ai


class QTicTacToe(QWidget):
    class QTileButton(QPushButton):
        SymbolMap = {type(None): " ",
                     TicTacToe.Player: "◯",
                     TicTacToe.BreadthFirstSearchAI: "☓",
                     TicTacToe.MonteCarloSearchAI: "☩"}

        def __init__(self, parent):
            super(QTicTacToe.QTileButton, self).__init__(parent)
            self.setFocusPolicy(Qt.NoFocus)
            self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.setContextMenuPolicy(Qt.CustomContextMenu)

        def clickEvent(self, tile):
            self.parent().playRound(tile)

        def updateEvent(self, tile):
            self.setEnabled(tile.player is None)
            self.setText(self.SymbolMap[type(tile.player)])
            self.update()

        def resizeEvent(self, resizeEvent):
            font = self.font()
            font.setBold(True)
            font.setPixelSize(round(0.50 * min(self.width(), self.height())))
            self.setFont(font)

        def sizeHint(self):
            return QSize(40, 40)

    AIs = [("Breadth First Search AI", TicTacToe.BreadthFirstSearchAI),
           ("Monte Carlo Search AI", TicTacToe.MonteCarloSearchAI)]

    def __init__(self):
        super(QTicTacToe, self).__init__()
        player = TicTacToe.Player(self.QTileButton.SymbolMap[TicTacToe.Player])
        ai = TicTacToe.BreadthFirstSearchAI(self.QTileButton.SymbolMap[TicTacToe.BreadthFirstSearchAI])
        self.ticTacToe = TicTacToe(player, ai)
        self.initUI()
        self.show()

    def initUI(self):
        self.setWindowTitle(self.tr("Tic-Tac-Toe"))
        layout = QVBoxLayout()
        self.setLayout(layout)
        aiComboBox = QComboBox(self)
        aiComboBox.addItems([self.tr(ai[0]) for ai in self.AIs])
        aiComboBox.currentIndexChanged.connect(self.selectAIEvent)
        ticTaclayout = QGridLayout()
        ticTaclayout.setSpacing(3)
        layout.addWidget(aiComboBox)
        layout.addLayout(ticTaclayout)
        self.setLayout(layout)
        for tile in self.ticTacToe:
            button = QTicTacToe.QTileButton(self)
            ticTaclayout.addWidget(button, tile.row, tile.column)
            button.clicked.connect(lambda _, button=button, tile=tile: button.clickEvent(tile))
            tile.delegate = button

    def playRound(self, tile):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        gameScore = self.ticTacToe.round(tile)
        QApplication.restoreOverrideCursor()
        if gameScore is not None:
            if gameScore == +1:
                QMessageBox.information(self, self.tr("Victory!"), self.tr("You won :)"), QMessageBox.Ok)
            if gameScore == 0:
                QMessageBox.warning(self, self.tr("Tie!"), self.tr("You tied :|"), QMessageBox.Ok)
            if gameScore == -1:
                QMessageBox.critical(self, self.tr("Defeat!"), self.tr("You lost :("), QMessageBox.Ok)
            self.ticTacToe.reset(True)

    def selectAIEvent(self, index):
        self.ticTacToe.ai = self.AIs[index][1](self.ticTacToe.ai.symbol)

    def sizeHint(self):
        return QSize(180, 220)


class TestTicTacToe(unittest.TestCase):
    def testBreadthFirstSearchAIBasics(self):
        self.basicAI(TicTacToe.BreadthFirstSearchAI)

    def testMonteCarloSearchAIBasics(self):
        self.basicAI(TicTacToe.MonteCarloSearchAI)

    def basicAI(self, AI):
        ai = AI('☓')
        player = TicTacToe.Player('◯')
        ticTacToe = TicTacToe(player, ai)

        ticTacToe.build(["☐◯☓",
                         "◯☓☓",
                         "◯☓◯"], nextPlayer=ticTacToe.ai)
        #score, tile = ticTacToe.ai.play(ticTacToe)
        #self.assertEqual((tile.row, tile.column), (0, 0))

        ticTacToe.build(["☐☓☐",
                         "☓◯◯",
                         "☓◯◯"], nextPlayer=ticTacToe.ai)
        #score, tile = ticTacToe.ai.play(ticTacToe)
        #self.assertEqual((tile.row, tile.column), (0, 0))

        ticTacToe.build(["◯☓☐",
                         "◯☓☐",
                         "☐◯☓"], nextPlayer=ticTacToe.ai)
        score, tile = ticTacToe.ai.play(ticTacToe)
        self.assertEqual((tile.row, tile.column), (2, 0))

        ticTacToe.build(["☐☐☓",
                         "◯☓☐",
                         "◯☓◯"], nextPlayer=ticTacToe.ai)
        score, tile = ticTacToe.ai.play(ticTacToe)
        self.assertEqual((tile.row, tile.column), (0, 0))

        ticTacToe.build(["☐☐☓",
                         "◯☐☐",
                         "◯☓☐"], nextPlayer=ticTacToe.ai)
        score, tile = ticTacToe.ai.play(ticTacToe)
        self.assertEqual((tile.row, tile.column), (0, 0))

        ticTacToe.build(["☓☓◯",
                         "☐◯☐",
                         "☐◯☓"], nextPlayer=ticTacToe.ai)
        score, tile = ticTacToe.ai.play(ticTacToe)
        self.assertEqual((tile.row, tile.column), (2, 0))

        ticTacToe.build(["☐☐☐",
                         "☐◯☐",
                         "☐◯☓"], nextPlayer=ticTacToe.ai)
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


if __name__ == "__main__":
    application = QApplication(sys.argv)
    qTicTacToe = QTicTacToe()
    sys.exit(application.exec_())
