from __future__ import annotations
from cmath import inf
from PyQt5.QtWidgets import (
    QMainWindow, QApplication,
    QLabel, QCheckBox, QComboBox, QLineEdit,
    QLineEdit, QSpinBox, QDoubleSpinBox, QSlider,
    QPushButton, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, qApp
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QTimer, pyqtProperty, 
    QPropertyAnimation, QPoint, QEasingCurve,
    QParallelAnimationGroup , QSize, QRect,
    QSequentialAnimationGroup
)
from PyQt5 import QtCore, QtGui
from PyQt5.uic import loadUi
import typing
import numpy as np 
import sys
import random
from pprint import pprint

class Cell(QWidget):
    cellMove = pyqtSignal(object,QPoint,QPoint)
    cellRelease = pyqtSignal(object)
    def __init__(self, parent=None, idx : int =None):
        super().__init__(parent)
        loadUi('elem.ui', self)
        self.parent = parent
        self.idx = idx
        self.text.setText(f'{idx}')
        # self.canonSS = self.styleSheet()
        # self.text : QLabel
        self.selectable = self.parent.selectable
        if not self.selectable:
            self.text.setStyleSheet("")
        # self.updateStyle(self.text)
        
        self.mousePos : QPoint = None
        self.coord : QPoint = None
        self.anim : QPropertyAnimation = None

    def setColor(self, s: str = None):
        if s is None:
            self.text.setStyleSheet("")
        else:
            self.text.setStyleSheet(f"background:{s};")
        self.updateStyle(self.text)

    def enterEvent(self, a0: QtCore.QEvent) -> None:
        if not self.selectable : 
            a0.ignore()
            return
        #self.setStyleSheet("background: lightblue")



    def leaveEvent(self, a0: QtCore.QEvent) -> None:
        if not self.selectable: 
            a0.ignore()
            return
        #self.setStyleSheet(self.canonSS)

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None:
        if not self.selectable: return super().mouseMoveEvent(a0)
        if self.mousePos is None:
            self.mousePos = a0.pos()
        # print("mouse move" + str(a0.windowPos()))
        self.cellMove.emit(self, a0.windowPos().toPoint(), self.mousePos)
        return super().mouseMoveEvent(a0)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        if not self.selectable: return super().mousePressEvent(a0)
        self.mousePos = a0.pos()
        return super().mousePressEvent(a0)

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        if not self.selectable: return super().mouseReleaseEvent(a0)
        self.mousePos = None
        self.cellRelease.emit(self)
        return super().mouseReleaseEvent(a0)

    def updateStyle(self, widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def on_drag_finish(self):
        self.parent.grid.addWidget(self, self.coord.y(), self.coord.x())
        # self.parent.widgetTable[self.coord.y()][self.coord.x()] = self
        # self.parent.table[self.coord.y()][self.coord.x()] = self.idx
        # print(self.parent.table)
        # pprint(self.parent.widgetTable)

class Board(QWidget):
    cols = 3
    rows = 3
    start_pos   = None if cols != 3 else np.array([[5,8,3],[4,None,2],[7,6,1]])
    end_pos     = None if cols != 3 else np.array([[1,2,3],[8,None,4],[7,6,5]])

    boardChanged = pyqtSignal(np.ndarray)

    def __init__(self, parent=None, selectable : bool =True, size: QSize = (300,300)) -> None:
        super().__init__(parent)
        self.selectable = selectable
        self.timer = QTimer()
        #loadUi("board.ui", self)

        self.resize(*size)
        #self.setGeometry(200,150,*size)

        self.widgetTable = [[None]*self.cols for _ in range(self.rows)]
        self.widgets : typing.List[Cell] = [None]*(self.cols*self.rows-1)
        self.table = np.array([*list(range(1,self.cols*self.rows)), None]).reshape((self.rows,self.cols))

        self.grid = QGridLayout()
        self.setLayout(self.grid)

        for i in range(self.cols*self.rows-1):
            e = self.widgetTable[i//self.cols][i%self.cols] = self.widgets[i] = Cell(self, i+1)
            e.coord = QPoint(i%self.cols,i//self.cols)
            self.grid.addWidget(e, i//self.cols, i%self.cols)
            e.cellMove.connect(self.dragCell)
            e.cellRelease.connect(self.releaseCell)

        for i in range(self.rows):
            self.grid.setRowStretch(i,1)
        for i in range(self.cols):
            self.grid.setColumnStretch(i,1)
        self.grid.setSpacing(3)

        # self.timer.timeout.connect(self.ChangeTo)
        self.timer.start(2000)
        self.animGroup = None

    def dragCell(self, cell: Cell, wPos: QPoint, mPos: QPoint ):
        cell.activateWindow()
        cell.raise_()
        # print(self.window().geometry())
        # print(self.geometry())
        # print(wPos-mPos)

        lt = self.mapToGlobal(QPoint(0,0)) - self.window().pos() - QPoint(1,31)
        # lt = 

        # locPos : QPoint =  (wPos-mPos) - lt 
        locPos : QPoint =  self.mapFromGlobal(self.window().mapToGlobal(wPos-mPos) )
        globPos : QPoint = self.window().mapToGlobal(wPos-mPos)
        if self.parent() is not None:
            board_geom_lt = self.mapToGlobal(self.grid.geometry().topLeft())
            board_geom_rb = self.mapToGlobal(self.grid.geometry().bottomRight())
            # board_geom_rb = board_geom_lt + QPoint(self.grid.geometry().width(), self.grid.geometry().height())
        else: 
            board_geom_lt = self.geometry().topLeft()
            board_geom_rb = self.geometry().bottomRight()

        # locPos.setX(min([max([0, locPos.x()]), self.grid.geometry().width()-cell.width()]))
        # locPos.setY(min([max([0, locPos.y()]), self.grid.geometry().height()-cell.height()]))

        globPos.setX(min([max([board_geom_lt.x(), globPos.x()]), board_geom_rb.x()-cell.width()]))
        globPos.setY(min([max([board_geom_lt.y(), globPos.y()]), board_geom_rb.y()-cell.height()]))

        # locPos = self.window().mapFromGlobal(self.mapToGlobal(locPos))
        locPos = self.mapFromGlobal(globPos)
        cell.setGeometry(QRect(locPos,cell.size()))
        coord = self.nearestCell(locPos)
        # cell.setGeometry(QRect(wPos-mPos,cell.size()))
        # coord = self.nearestCell(wPos-mPos)

        # print(globPos,'between', board_geom_lt, board_geom_rb-QPoint(cell.width(),cell.height()))

        idx = self.grid.indexOf(cell)
        if idx != -1:
            self.grid.removeItem(self.grid.itemAt(idx))
        # print(row,column)

        if cell.coord.x() != coord.x() or cell.coord.y() != coord.y():
            # pprint(vars(self))
            self.widgetTable[cell.coord.y()][cell.coord.x()] = None
            self.table[cell.coord.y()][cell.coord.x()] = None
            if self.widgetTable[coord.y()][coord.x()] is not None :
                self.moveCell(
                    self.widgetTable[coord.y()][coord.x()], 
                    self.grid.cellRect(cell.coord.y(), cell.coord.x()).topLeft(),
                    cell.coord)

            self.widgetTable[coord.y()][coord.x()] = cell
            cell.coord = coord
            self.table[cell.coord.y()][cell.coord.x()] = cell.idx
            # pprint(vars(self))

    def releaseCell(self, cell : Cell):
        # self.grid.addWidget(cell, cell.coord.y(), cell.coord.x())
        # self.widgetTable[cell.coord.y()][cell.coord.x()] = cell
        self.moveCell(cell, self.grid.cellRect(cell.coord.y(), cell.coord.x()).topLeft(), cell.coord)

    def moveCell(self, cell: Cell, pos: QPoint, coords: QPoint):
        cell.anim = QPropertyAnimation(cell, b"geometry")
        cell.anim.setStartValue(cell.geometry())
        cell.anim.setEndValue(QRect(pos, cell.size()))
        cell.anim.setDuration(200)
        cell.anim.setEasingCurve(QEasingCurve.OutCubic)
        cell.anim.finished.connect(cell.on_drag_finish)  
        self.grid.removeItem(self.grid.itemAtPosition(cell.coord.y(), cell.coord.x()))    
        # self.grid.addWidget(cell, coords.y(), coords.x())
        self.widgetTable[cell.coord.y()][cell.coord.x()] = None
        self.table[cell.coord.y()][cell.coord.x()] = None
        cell.coord = coords
        cell.anim.start()
        # self.grid.addWidget(cell, cell.coord.y(), cell.coord.x())
        self.widgetTable[coords.y()][coords.x()] = cell
        self.table[cell.coord.y()][cell.coord.x()] = cell.idx

        self.boardChanged.emit(self.table)

    def on_cell_move_finish(self, cell : Cell, coord):
        self.grid.addWidget(cell, cell.coord.y(), cell.coord.x())
        self.widgetTable[coord.y()][coord.x()] = cell
        self.table[cell.coord.y()][cell.coord.x()] = cell.idx
        # pprint(vars(self))
        pass

    def nearestCell(self, pos: QPoint) -> QPoint:
        coords = QPoint(0,0)
        min_dist : int = inf
        for i in range(self.rows):
            for j in range(self.cols):
                c = self.grid.cellRect(i,j).topLeft()
                dist = (c.x() - pos.x()) ** 2 + (c.y() - pos.y()) ** 2
                if dist < min_dist:
                    min_dist = dist
                    coords = QPoint(j,i)
        return coords

    # no anim
    def SetTo(self, table : np.array = None):
        if table is None: return
        self.table = np.copy(table)

        for i in range(self.grid.columnCount()):
            for j in range(self.grid.rowCount()):
                self.grid.removeItem( self.grid.itemAtPosition(j,i))

        for r, row in enumerate(table):
            for c, el in enumerate(row):
                if el is not None:
                    self.grid.addWidget(self.widgets[el-1], r, c)
                    self.widgetTable[r][c] = self.widgets[el-1]
                    self.widgets[el-1].coord = QPoint(c,r)
                else:
                    self.widgetTable[c][r] = None

        self.boardChanged.emit(self.table)
        # pprint(vars(self))


    def ChangeTo(self, table : np.ndarray = None,curve : QEasingCurve = QEasingCurve.InBack, time:int = 500):
        if table is None:
            table = np.array(sorted( [*list(range(1,self.cols*self.rows)), None], key=lambda k: random.random()), dtype=object).reshape((self.rows,self.cols))

        # self.table = table

        #print(self.grid.count())
        animCount = 0
        self.anims = {}

        grid = np.empty(shape=(self.rows, self.cols), dtype=object)
        #print(self.grid.rowCount(), self.grid.columnCount())
        for i in range(self.rows):
            for j in range(self.cols):
                grid[i][j] = self.grid.cellRect(i,j)
        
        for i in self.widgets:
            a = self.anims[i] = QPropertyAnimation(i, b'geometry')
            a.setStartValue(i.geometry())

        # for i in range(self.grid.columnCount()):
        #     for j in range(self.grid.rowCount()):
        #         self.grid.removeItem( self.grid.itemAtPosition(j,i))

        # if self.animGroup is not None:
        #     self.animGroup.setCurrentTime(self.animGroup.totalDuration())
        #     self.animGroup = None
        self.animGroup = QParallelAnimationGroup()
        for r, row in enumerate(table):
            for c, el in enumerate(row):
                if el is not None:
                    w : Cell = self.widgets[el-1]
                    #self.grid.addWidget(w, r, c)
                    a : QPropertyAnimation = self.anims[w]
                    a.setEndValue(grid[r][c])
                    #print(self.grid.cellRect(r,c))
                    a.setDuration(time)
                    a.setEasingCurve(curve)
                    #print(el, ' : start', a.startValue(),': end ',a.endValue())
                    self.animGroup.addAnimation(a)

                    #a.finished.connect(lambda : print(grid))
                    #a.finished.connect(lambda : self.anims.pop(self.widgets[el-1], None))
                    #a.stateChanged.connect(lambda x : print(w.pos().x(), w.pos().y()))
        self.animGroup.finished.connect(lambda : self.SetTo(table))
        self.animGroup.start()

        #while len(self.anims): pass

    # inv = inversion_count + none_row_num
    def inv_count(self):
        inv = 0
        none_row = 0
        for i in range(self.rows * self.cols):
            r = i // self.cols
            c = i % self.cols
            if self.table[r][c] is not None:
                for j in range(i+1, self.rows * self.cols):
                    if self.table[j//self.cols][j%self.cols] is None: continue
                    if self.table[j//self.cols][j%self.cols] < self.table[r][c]:
                        inv += 1
            else:
                none_row = (self.rows+1)*(r+1)

        return inv + none_row

    def sequence_anim(self, tables : typing.List[np.ndarray], curve : QEasingCurve):
        self.seq_anim = QSequentialAnimationGroup()
        self.all_anim = []

        grid = np.empty(shape=(self.rows, self.cols), dtype=object)
        for i in range(self.rows):
            for j in range(self.cols):
                grid[i][j] = self.grid.cellRect(i,j)

        for index, thing in enumerate(tables):
            if index < len(tables):
                current, next_ = thing, tables[index + 1]
                pg = QParallelAnimationGroup()
                self.all_anim.append(pg)
                for i in self.widgets:
                    a = QPropertyAnimation(i, b'geometry')
                    self.all_anim.append(a)
                    # a.setStartValue()
        for t in tables:
            for i in self.widgets:
                a = QPropertyAnimation(i, b'geometry')
                self.all_anim.append(a)
                a.setStartValue(i.geometry())
        pass

def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback) 
    sys.exit(1)

def main():
    sys._excepthook = sys.excepthook 

    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    b = Board()
    b.show()
    app.exec()



if __name__ == '__main__':
    main()
