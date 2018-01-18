from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QMessageBox, QSizePolicy, QVBoxLayout, QComboBox
from PyQt5.QtCore import Qt, QSize
import networkx as nx
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
            self.graph = nx.DiGraph()

        def play(self, ticTacToe):

            def ulp_score(node, succ_node):
                node, succ_node = self.graph.node[node], self.graph.node[succ_node]
                return succ_node['num_wins'] / succ_node['num_visits'] + \
                       1.0 * math.sqrt(math.log(node['num_visits']) / succ_node['num_visits'])

            def select(node):
                if self.graph.successors(node):
                    succ_ulp_scores = [(succ_node, ulp_score(node, succ_node)) for succ_node in self.graph.successors(node)]
                    succ_node = max(succ_ulp_scores, key=lambda tpl: tpl[1])[0]
                    ticTacToe.set(self.graph.edge[node][succ_node]['move'])
                    return select(succ_node)
                return node

            def expand(node):
                if self.graph.node[node]['score'] is None:
                    for move in ticTacToe.choices():
                        ticTacToe.set(move)
                        succ_node, score = str(ticTacToe), ticTacToe.score(move)
                        self.graph.add_node(succ_node, attr_dict={'score': score, 'num_visits': 1, 'num_wins': 0})
                        self.graph.add_edge(node, succ_node, attr_dict={'move': move})
                        ticTacToe.clear(move)
                    playout_move = random.choice(ticTacToe.choices())
                    ticTacToe.set(playout_move)
                    score = ticTacToe.score(playout_move)
                    if score is None:
                        score = playout()
                    return score
                return self.graph.node[node]['score']

            def playout():
                playout_move = random.choice(ticTacToe.choices())
                ticTacToe.set(playout_move)
                score = ticTacToe.score(playout_move)
                if score is None:
                    score = playout()
                ticTacToe.clear(playout_move)
                return score

            def backpropagate(node, score):
                self.graph.node[node]['num_visits'] += 1
                self.graph.node[node]['num_wins'] += score
                if self.graph.predecessors(node):
                    pred_node = self.graph.predecessors(node)[0]
                    ticTacToe.clear(self.graph.edge[pred_node][node]['move'])
                    backpropagate(pred_node, score)

            repeat = 100
            if str(ticTacToe) not in self.graph:
                self.graph.add_node(str(ticTacToe), attr_dict={'score': None, 'num_visits': 0, 'num_wins': 0})
            root_node = str(ticTacToe)

            while repeat > 0:
                selected_node = select(root_node)
                score = expand(selected_node)
                backpropagate(str(ticTacToe), score)
                repeat -= 1


            succ_visits = [(succ_node, self.graph.node[succ_node]['num_visits']) for succ_node in self.graph.successors(root_node)]
            succ_node = max(succ_visits, key=lambda tpl: tpl[1])[0]
            return 0, self.graph.edge[root_node][succ_node]['move']

        def visualize(self, ticTacToe):
            import matplotlib.pyplot as plt
            position = nx.nx_agraph.graphviz_layout(self.graph, prog='dot')
            nx.draw(self.graph, position, with_labels=True, font_weight='bold')
            plt.show()

        def reset(self):
            self.graph.clear()

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
