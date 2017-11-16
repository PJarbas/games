from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QComboBox, QGridLayout, QMessageBox, QSizePolicy, QVBoxLayout
from PyQt5.QtGui import QPainter, QBrush, QPen, QPalette
from PyQt5.QtCore import Qt, QPoint, QSize
import unittest
import random
import sys


class FourPlay(dict):
    class Disc:
        def __init__(self, row, column):
            self.row, self.column = row, column
            self.delegate = None
            self.player = None
            self.marked = False
            self.rank = 0

        def __eq__(self, other):
            return (self.row, self.column) == (other.row, other.column) if other is not None else False

        def __str__(self):
            return str(self.player) if self.player is not None else "☐"

        def mark(self, notify=False):
            self.marked = True
            self.notify(notify)

        def notify(self, notify=False):
            if self.delegate is not None and notify is True:
                self.delegate.updateEvent(self)

        def neighbor(self, fourPlay, location=None):
            diffRow, diffCol = location[0], location[1]
            neighborRow, neighborCol = self.row + diffRow, self.column + diffCol
            if (neighborRow, neighborCol) in fourPlay:
                return fourPlay[(neighborRow, neighborCol)]
            else:
                return None

        def crawl(self, fourPlay, direction, player, mark=False):
            if self.player == player:
                if mark is True:
                    self.mark(True)
                neighbor = self.neighbor(fourPlay, direction)
                if neighbor is not None:
                    return neighbor.crawl(fourPlay, direction, player, mark) + 1
                else:
                    return 1
            return 0

        def reset(self, notify=False):
            self.player = None
            self.marked = False
            self.rank = 0
            self.notify(notify)

    class Frontier(list):
        def __init__(self):
            super().__init__()

        def __str__(self):
            string = ""
            for disc in self:
                string += str(disc.row) if disc is not None else "_"
            return string

        def increase(self, fourPlay, column, notify=False):
            disc = self[column]
            if disc is None:
                return
            discAbove = disc.neighbor(fourPlay, (-1, 0))
            self[column] = discAbove
            if discAbove is not None:
                discAbove.notify(notify)

        def decrease(self, fourPlay, column, notify=False):
            disc = self[column]
            if disc is None:
                topRowDisc = fourPlay[0, column]
                self[column] = topRowDisc
                topRowDisc.notify(notify)
                return
            discBelow = disc.neighbor(fourPlay, (+1, 0))
            self[column] = discBelow
            if discBelow is not None:
                discBelow.notify(notify)

        def choices(self, shuffle=True):
            choices = list(filter(lambda disc: disc is not None, self))
            if shuffle is True:
                random.shuffle(choices)
            return choices

        def reset(self, fourPlay):
            self[:] = [None] * fourPlay.columns
            for column in range(fourPlay.columns):
                for row in range(fourPlay.rows):
                    disc = fourPlay[row, column]
                    if disc.player is None or row == fourPlay.rows:
                        self[column] = disc
                    else:
                        break

    class Player:
        def __init__(self, symbol):
            self.symbol = symbol

        def __str__(self):
            return str(self.symbol)

        def play(self, fourPlay, opponent, column):
            return 0, fourPlay.frontier[column]

    class BreadthFirstSearchAI(Player):
        def play(self, fourPlay, opnt, selfBestResult=(-2, None), opntBestResult=(+2, None), recursionLevel=1):
            recursionLimit = 8
            for disc in fourPlay.frontier.choices(shuffle=True):
                fourPlay.set(disc, self)
                selfResult = (fourPlay.score(disc), disc)
                if selfResult[0] is None:
                    if recursionLevel < recursionLimit:
                        subtreeSelfBestResult = (-selfBestResult[0], selfBestResult[1])
                        subtreeOpntBestResult = (-opntBestResult[0], opntBestResult[1])
                        opntResult = FourPlay.BreadthFirstSearchAI.play(opnt, fourPlay, self, subtreeOpntBestResult,
                                                      subtreeSelfBestResult, recursionLevel + 1)
                        selfResult = (-opntResult[0], selfResult[1])
                    else:
                        selfResult = (-1 / recursionLimit, selfResult[1])
                else:
                    selfResult = (selfResult[0] / recursionLevel, selfResult[1])
                fourPlay.clear(disc)

                if selfResult[0] > selfBestResult[0]:
                    selfBestResult = selfResult
                if opntBestResult[0] <= selfBestResult[0]:
                    break

            return selfBestResult

    class MonteCarloSearchAI(BreadthFirstSearchAI):
        pass

    def __init__(self, rows, columns):
        super().__init__()
        self.rows, self.columns = rows, columns
        self.ai = FourPlay.Player("☓")
        self.player = FourPlay.Player("◯")
        self.frontier = FourPlay.Frontier()
        for row in range(self.rows):
            for column in range(self.columns):
                disc = FourPlay.Disc(row, column)
                self[row, column] = disc
        self.frontier.reset(self)

    def __iter__(self):
        return iter(self.values())

    def __repr__(self):
        string = ""
        for row in range(self.rows):
            for column in range(self.columns):
                string += str(self[row, column])
            string += "\n"
        return string

    def build(self, symbols):
        for row, symbols_row in enumerate(symbols):
            for column, symbol in enumerate(symbols_row):
                disc = self[row, column]
                if symbol == self.player.symbol:
                    disc.player = self.player
                elif symbol == self.ai.symbol:
                    disc.player = self.ai
                else:
                    disc.player = None
        self.frontier.reset(self)

    def round(self, column):
        _, playerDisc = self.player.play(self, self.ai, column)
        self.set(playerDisc, self.player, True)
        playerScore = self.score(playerDisc, True)
        if playerScore is not None:
            return playerScore

        _, aiDisc = self.ai.play(self, self.player)
        self.set(aiDisc, self.ai, True)
        aiScore = self.score(aiDisc, True)
        if aiScore is not None:
            return -aiScore
        return None

    def set(self, disc, player, notify=False):
        disc.player = player
        self.frontier.increase(self, disc.column, notify)
        disc.notify(notify)

    def clear(self, disc, notify=False):
        disc.player = None
        self.frontier.decrease(self, disc.column, notify)
        disc.notify(notify)

    def score(self, disc, mark=False):
        for forward in [(+1, 0), (0, +1), (+1, +1), (+1, -1)]:
            rearward = -forward[0], -forward[1]
            connected = disc.crawl(self, forward, disc.player) + disc.crawl(self, rearward, disc.player) - 1
            if connected >= 4:
                if mark is True:
                    disc.crawl(self, forward, disc.player, True)
                    disc.crawl(self, rearward, disc.player, True)
                return 1
        if len(self.frontier.choices()) == 0:
            return 0
        return None

    def reset(self, notify=True):
        for disc in self:
            disc.reset(False)
        self.frontier.reset(self)
        for disc in self:
            disc.notify(notify)


class QFourPlay(QWidget):
    class QDiscButton(QPushButton):
        ColorMap = {type(None): (QPalette.Dark, QPalette.Background),
                    FourPlay.Player: (QPalette.Highlight, QPalette.Highlight),
                    FourPlay.BreadthFirstSearchAI: (QPalette.Dark, QPalette.Dark),
                    FourPlay.MonteCarloSearchAI: (QPalette.Light, QPalette.Light)}

        def __init__(self, qFourPlay):
            super(QFourPlay.QDiscButton, self).__init__(qFourPlay)
            self.qFourPlay = qFourPlay
            self.highlight = False
            self.playable = False
            self.marked = False
            self.color = None
            self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.setFocusPolicy(Qt.NoFocus)
            self.setMouseTracking(True)

        def updateEvent(self, disc):
            self.marked = disc.marked
            self.color = self.ColorMap[type(disc.player)]
            self.playable = disc in self.qFourPlay.fourPlay.frontier
            self.update()

        def clickEvent(self, disc):
            self.leaveEvent()
            self.qFourPlay.playRound(disc.column)
            self.enterEvent()
            return

        def enterEvent(self, *args, **kwargs):
            if self.playable is True:
                self.highlight = True
                self.update()

        def leaveEvent(self, *args, **kwargs):
            if self.playable is True:
                self.highlight = False
                self.update()

        def paintEvent(self, paintEvent):
            painter = QPainter(self)
            painter.setBackgroundMode(Qt.TransparentMode)
            painter.setRenderHint(QPainter.Antialiasing)
            brush = QBrush()
            brush.setStyle(Qt.SolidPattern)
            pen = QPen()
            pen.setJoinStyle(Qt.RoundJoin)
            pen.setCapStyle(Qt.RoundCap)

            center = QPoint(self.width() // 2, self.height() // 2)
            radius = 0.45 * min(self.width(), self.height())

            pen.setColor(self.palette().color(self.color[0]))
            brush.setColor(self.palette().color(self.color[1]))
            if self.highlight is True:
                pen.setColor(self.palette().color(QPalette.Highlight))
            pen.setWidth(round(0.15 * radius))
            painter.setBrush(brush)
            painter.setPen(pen)
            painter.drawEllipse(center, radius, radius)

            if self.marked is True:
                brush.setColor(self.palette().color(QPalette.Background))
                pen.setColor(self.palette().color(QPalette.Background))
                painter.setPen(pen)
                painter.setBrush(brush)
                painter.drawEllipse(center, 0.40 * radius, 0.40 * radius)

            del painter, brush, pen

        def sizeHint(self):
            return QSize(40, 40)

    AIs = [("Breadth First Search AI", FourPlay.BreadthFirstSearchAI),
           ("Monte Carlo Search AI", FourPlay.MonteCarloSearchAI)]

    def __init__(self):
        super(QFourPlay, self).__init__()
        self.fourPlay = None
        self.initGame()
        self.initUI()
        self.show()

    def initGame(self):
        self.fourPlay = FourPlay(6, 7)
        self.fourPlay.ai = self.AIs[0][1](self.fourPlay.ai.symbol)

    def initUI(self):
        self.setWindowTitle(self.tr("Fourplay"))
        layout = QVBoxLayout()
        self.setLayout(layout)
        discGridLayout = QGridLayout()
        discGridLayout.setSpacing(4)
        aiComboBox = QComboBox(self)
        aiComboBox.addItems([self.tr(ai[0]) for ai in self.AIs])
        aiComboBox.currentIndexChanged.connect(self.selectAIEvent)
        layout.addWidget(aiComboBox)
        layout.addLayout(discGridLayout)

        for disc in self.fourPlay:
            button = QFourPlay.QDiscButton(self)
            discGridLayout.addWidget(button, disc.row, disc.column)
            button.clicked.connect(lambda _, button=button, disc=disc: button.clickEvent(disc))
            button.updateEvent(disc)
            disc.delegate = button

    def playRound(self, column):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        score = self.fourPlay.round(column)
        QApplication.restoreOverrideCursor()
        if score is not None:
            if score == +1:
                QMessageBox.information(self, self.tr("Victory!"), self.tr("You won :)"), QMessageBox.Ok)
            if score == 0:
                QMessageBox.warning(self, self.tr("Tie!"), self.tr("You tied :|"), QMessageBox.Ok)
            if score == -1:
                QMessageBox.critical(self, self.tr("Defeat!"), self.tr("You lost :("), QMessageBox.Ok)
            self.fourPlay.reset()

    def selectAIEvent(self, index):
        self.fourPlay.ai = self.AIs[index][1](self.fourPlay.ai.symbol)

    def sizeHint(self):
        return QSize(300, 300)


class TestFourPlay(unittest.TestCase):

    def testBreadthFirstSearchAIBasics(self):
        fourPlay = FourPlay(6, 7)

        fourPlay.build(["☓☓☓◯☓☓☐",
                        "◯◯◯☓◯◯◯",
                        "☓☓☓◯☓☓☓",
                        "◯◯◯☓◯◯◯",
                        "☓☓☓◯☓☓☓",
                        "◯◯◯☓◯◯◯"])
        fourPlay.ai = FourPlay.BreadthFirstSearchAI(fourPlay.ai.symbol)
        score, disc = fourPlay.ai.play(fourPlay, fourPlay.player)
        self.assertEqual((disc.row, disc.column), (0, 6))
        self.assertEqual(score, 0.0)

        fourPlay = FourPlay(6, 7)
        fourPlay.build(["☐☐☐☐☐☐☐",
                        "☐☐☐☐☐☐☐",
                        "☐☐☐☐☐☐☐",
                        "☐☐☐☐☐☐☐",
                        "☐☐☐☐☐☐☐",
                        "◯◯◯☐☓☓☓"])
        fourPlay.ai = FourPlay.BreadthFirstSearchAI(fourPlay.ai.symbol)
        score, disc = fourPlay.ai.play(fourPlay, fourPlay.player)
        self.assertEqual((disc.row, disc.column), (5, 3))

        fourPlay.build(["☐☐☐☐☐☐☐",
                        "☐☐☐☐☐☐☐",
                        "☐☐☐☐☐☐☐",
                        "☐☐☐☐☐☐☐",
                        "☐☐☐☐☐☐☐",
                        "◯◯◯☐☓☓☐"])
        fourPlay.ai = FourPlay.BreadthFirstSearchAI(fourPlay.ai.symbol)
        score, disc = fourPlay.ai.play(fourPlay, fourPlay.player)
        self.assertEqual((disc.row, disc.column), (5, 3))

        fourPlay.build(["☐☐☐☐☐☐☐",
                        "☐☐☐☐☐☐☐",
                        "☐☐☐☐☐☐☐",
                        "◯☐☐☐☐☐☐",
                        "◯☐☐☐☓☐☐",
                        "◯☐☐☓☓☐☐"])
        fourPlay.ai = FourPlay.BreadthFirstSearchAI(fourPlay.ai.symbol)
        score, disc = fourPlay.ai.play(fourPlay, fourPlay.player)
        self.assertEqual((disc.row, disc.column), (2, 0))

        fourPlay.build(["☐☐☐☐☐☐☐",
                        "☐☐☐☐☐☐☐",
                        "☐☐☐☐☐☐☐",
                        "◯◯☐☐☐☐☐",
                        "◯☓◯☐☐☐☐",
                        "◯☓☓◯☓☓☓"])
        fourPlay.ai = FourPlay.BreadthFirstSearchAI(fourPlay.ai.symbol)
        score, disc = fourPlay.ai.play(fourPlay, fourPlay.player)
        self.assertEqual((disc.row, disc.column), (2, 0))

        fourPlay.build(["☐☐☐☐☐☐☐",
                        "☐☐☐☐☐☐☐",
                        "☐☐☐☐☐☐☐",
                        "☓☐☐☐☐☐☐",
                        "☓☐☐☐☐☐☐",
                        "◯◯◯☐☐☐☐"])
        fourPlay.ai = FourPlay.BreadthFirstSearchAI(fourPlay.ai.symbol)
        score, disc = fourPlay.ai.play(fourPlay, fourPlay.player)
        self.assertEqual((disc.row, disc.column), (5, 3))

    def testAIvsAI(self):
        fourPlay = FourPlay(6, 7)
        x = FourPlay.BreadthFirstSearchAI("☓")
        o = FourPlay.BreadthFirstSearchAI("◯")
        while True:
            _, disc = x.play(fourPlay, o)
            fourPlay.set(disc, x)
            score = fourPlay.score(disc)
            if score is not None:
                break
            _, disc = o.play(fourPlay, x)
            fourPlay.set(disc, o)
            score = fourPlay.score(disc)
            if score is not None:
                score = -score
                break
        self.assertEqual(score, 1, "AI vs AI game must be always won by the starting player:\n" + str(fourPlay))


if __name__ == "__main__":
    application = QApplication(sys.argv)
    qFourPlay = QFourPlay()
    sys.exit(application.exec_())
