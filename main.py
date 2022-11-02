

from PyQt5.QtWidgets import (
    QMainWindow, QApplication,
    QLabel, QCheckBox, QComboBox, QLineEdit,
    QLineEdit, QSpinBox, QDoubleSpinBox, QSlider,
    QPushButton, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QMessageBox
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QTimer, pyqtProperty, 
    QPropertyAnimation, QPoint, QEasingCurve,
    QParallelAnimationGroup , QSize, QRunnable, QThreadPool,
    QThread
)
from PyQt5 import QtCore
from PyQt5.uic import loadUi
import typing
import numpy as np 
import sys
import random
from copy import deepcopy
from typing import Union 
import enum
from board import Board
from tree import mode
import tree

class brds(enum.Enum):
    Start   = 1
    Cur     = 2
    End     = 3



class Main(QWidget):
    
    # self.steps_lbl : QLabel
    # self.cur_step_le : QLineEdit
    # self.slider : QSlider
    # bfs_btn : QPushButton
    # ucs_btn : QPushButton
    # self.sw_shuffle_btn : QPushButton
    # self.ew_shuffle_btn : QPushButton
    # self.sw_reset_btn : QPushButton
    # self.ew_reset_btn : QPushButton
    # self.prev_btn : QPushButton
    # self.next_btn : QPushButton
    # self.memory_lbl: QLabel
    # self.time_lbl: QLabel
    # self.calc_btn : QPushButton
    
    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi('main.ui', self)
        bl = QVBoxLayout()
        self.mw.setLayout(bl)
        self.b = Board(selectable=False)
        bl.addWidget(self.b)

        bl_s = QVBoxLayout()
        self.sw.setLayout(bl_s)
        self.start_board = Board()
        bl_s.addWidget(self.start_board)

        bl_e = QVBoxLayout()
        self.ew.setLayout(bl_e)
        self.end_board = Board()
        bl_e.addWidget(self.end_board)

        self.resetTables(True)

        #self.btn.clicked.connect(lambda : self.b.ChangeTo())
        self.mode = mode.BFS

        self.pathFinder : tree.PathFinder = None

        self.curStep = 0
        self.inCalc : bool = False

        self.sw_shuffle_btn.clicked.connect(lambda _ : self.shuffleTable(brds.Start))
        self.ew_shuffle_btn.clicked.connect(lambda _ : self.shuffleTable(brds.End))
        self.sw_reset_btn.clicked.connect(lambda _ : self.resetTable(brds.Start))
        self.ew_reset_btn.clicked.connect(lambda _ : self.resetTable(brds.End))
        self.calc_btn.clicked.connect(self.calc)
        self.bfs_btn.clicked.connect(lambda : self.changeMode(mode.BFS))
        self.ucs_btn.clicked.connect(lambda : self.changeMode(mode.UCS))

        self.start_board.boardChanged.connect(self.resetCur)
        self.start_board.boardChanged.connect(self.updateInv)
        self.end_board.boardChanged.connect(self.resetCur)
        self.end_board.boardChanged.connect(self.updateInv)

        self.slider : QSlider
        self.slider.valueChanged.connect(self.on_slider_changed)
        self.cur_step_le.textEdited.connect(self.on_le_edit)

        self.prev_btn.clicked.connect(lambda: self.changeStep(self.curStep-1,-1))
        self.next_btn.clicked.connect(lambda: self.changeStep(self.curStep+1, 1))

    def updateInv(self):
        self.st_inv_lbl.setText(str(self.start_board.inv_count()))
        self.en_inv_lbl.setText(str(self.end_board.inv_count()))

    def on_slider_changed(self, value):
        if value == self.curStep: return
        
        self.skipSteps(self.curStep, value)
        self.curStep = value

    def on_le_edit(self, s: str):
        if self.pathFinder is None: return
        if self.pathFinder.no_solution: return

        if s.isnumeric() and 0 <= int(s) < self.pathFinder.depth:
            # self.changeStep(int(s))
            self.skipSteps(self.curStep, int(s))
        else:
            self.cur_step_le.setText("")

    def skipSteps(self, from_step, to_step):
        if from_step == to_step : return
        if from_step < to_step:
            for i in range(from_step, to_step+1, 1):
                self.changeStep(i, time=500/(abs(to_step-from_step)))
                while self.b.animGroup.duration() < self.b.animGroup.totalDuration(): ...
                self.curStep = i
        else:
            for i in range(from_step, to_step-1, -1):
                self.changeStep(i, time=500/(abs(to_step-from_step)))
                while self.b.animGroup.duration() < self.b.animGroup.totalDuration(): ...
                self.curStep = i
        
    def changeStep(self, step: int, change_step : int = 0, time:int = 500):
        if self.pathFinder is None: return
        if self.pathFinder.no_solution: return

        if not 0 <= step < self.pathFinder.depth: return

        node = self.pathFinder.get_node_by_step(step)
        
        for i in self.b.widgets:
            i.setColor()
        if step != 0:
            par = node.parent
            zipped = np.dstack((node.state.table, par.state.table))
            for _ in zipped:
                for cur, old in _:
                    if cur != old and cur is not None:
                        self.b.widgets[cur-1].setColor("lightgreen")
        if step != self.pathFinder.depth-1:
            ch : tree.Node = node.correct_child
            zipped = np.dstack((node.state.table, ch.state.table))
            for _ in zipped:
                for cur, nxt in _:
                    if cur != nxt and cur is not None:
                        self.b.widgets[cur-1].setColor("lightyellow")
        self.b.ChangeTo(node.state.table, curve=QEasingCurve.OutCubic, time=time)
        self.slider.blockSignals(True)
        self.slider.setValue(step)
        self.slider.blockSignals(False)
        self.cur_step_le.setText(str(step))
        self.curStep += change_step
        

    def resetInfo(self):
        self.steps_lbl.setText("---")
        self.cur_step_le.setText("")
        self.slider.setValue(0)
        self.slider.setMaximum(0)
        self.memory_lbl.setText("---")
        self.time_lbl.setText("---")
    
    def resetTable(self, board : Union[Board, brds], silent : bool = False):
        if silent:
            if board is self.start_board or board is brds.Start:
                self.start_board.SetTo(Board.start_pos)
                self.resetInfo()
            elif board is self.end_board or board is brds.End:
                self.end_board.SetTo(Board.end_pos)
                self.resetInfo()
            elif board is self.b or board is brds.Cur:
                self.b.SetTo(self.start_board.table)
                for i in self.b.widgets:
                    i.setColor()
            return

        if board is self.start_board or board is brds.Start:
            self.start_board.ChangeTo(Board.start_pos)
            self.resetInfo()
        elif board is self.end_board or board is brds.End:
            self.end_board.ChangeTo(Board.end_pos)
            self.resetInfo()
        elif board is self.b or board is brds.Cur:
            self.b.ChangeTo(self.start_board.table)
            for i in self.b.widgets:
                i.setColor()

    def resetTables(self, silent : bool = False):
        self.resetTable(brds.Start, silent)
        self.resetTable(brds.End, silent)
        self.resetTable(brds.Cur, silent)
        self.updateInv()

    def resetCur(self):
        self.resetTable(brds.Cur)
        self.resetInfo()

    def shuffleTable(self, board : Union[Board, brds]):
        if board is self.start_board or board is brds.Start:
            self.start_board.ChangeTo()
            self.resetInfo()
        elif board is self.end_board or board is brds.End:
            self.end_board.ChangeTo()
            self.resetInfo()
        elif board is self.b or board is brds.Cur:
            self.b.ChangeTo()

    def changeMode(self, mode : mode):
        if mode is mode.BFS:
            if not self.bfs_btn.isChecked():    # enable ucs
                self.ucs_btn.setChecked(True)
                self.mode = mode.UCS
            else:                               # enable bfs
                self.ucs_btn.setChecked(False)
                self.mode = mode.BFS
        elif mode is mode.UCS:  
            if not self.ucs_btn.isChecked():    # enable bfs
                self.bfs_btn.setChecked(True)
                self.mode = mode.BFS
            else:                               # enable ucs
                self.bfs_btn.setChecked(False)
                self.mode = mode.UCS
        self.resetInfo()
        self.resetTable(brds.Cur)



    def calc(self):
        if self.inCalc:
            self.pathFinder.no_abort = False

            return

        func = None
        if self.mode == mode.BFS:
            func = tree.bfs
        elif self.mode == mode.UCS:
            func = tree.ucs

        self.pathFinder = tree.PathFinder(
            tree.State(self.start_board.table),
            tree.State(self.end_board.table),
            func
        )
        self.thread = QThread()
        self.pathFinder.moveToThread(self.thread)
        
        self.thread.started.connect(self.pathFinder.makeTree)
        self.pathFinder.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.on_thread_finish)
        self.thread.finished.connect(self.thread.deleteLater)
        self.pathFinder.changeParam.connect(self.changeTreeParam)

        self.inCalc = True
        self.calc_btn.setText("Cancel")
        self.thread.start()
        # self.pathFinder.makeTree()

    def changeTreeParam(self, mem, time):
        self.memory_lbl.setText(str(mem))
        self.time_lbl.setText(str(time))
    
    def on_thread_finish(self):
        self.inCalc = False
        self.calc_btn.setText("Calc")
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setWindowTitle("Solution finder")
        if self.pathFinder.no_solution:
            msgBox.setText("No solution :(")
        else:
            msgBox.setText("Solution found")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msgBox.exec()

        self.initInfo()

    def initInfo(self):
        if self.pathFinder is None: return
        if self.pathFinder.no_solution: return

        self.curStep = 0
        self.memory_lbl.setText(str(self.pathFinder.mem))
        self.time_lbl.setText(str(self.pathFinder.time))
        self.slider.setMaximum(self.pathFinder.depth-1)
        self.slider.setMinimum(0)
        self.slider.setValue(self.curStep)
        self.steps_lbl.setText(str(self.pathFinder.depth-1))
        self.cur_step_le.setText(str(self.curStep))



def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback) 
    sys.exit(1)

def main():
    sys._excepthook = sys.excepthook 
    
    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    b = Main()
    b.show()
    app.exec()
    


if __name__ == '__main__':
    main()
