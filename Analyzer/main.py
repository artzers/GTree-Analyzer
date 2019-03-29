import sys,os
import vtk
import numpy as np
import skimage.io
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, \
QStatusBar, QMenuBar, QFileDialog, QMessageBox, QSpacerItem,\
    QDoubleSpinBox, QGroupBox, QPushButton
from QRangeSlider import QRangeSlider
import NeuroGLWidget
from TDATAReader import TDATAReader
from PyQt5 import (QtWidgets, QtCore, QtGui)
from PyQt5.QtGui import QIcon
from SingleDockWidget import SingleDockWidget
from TDATADockWidget import TDATADockWidget
import InteractorStyle
from GDataManager import GDataManager

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle('GTree Analyzer')
        self.setWindowIcon(QIcon('./windows.png'))
        self.setAcceptDrops(True)
        self.setupUi()
        self.CreateLeftDock()
        self.dataManager = GDataManager()
        self.mostdDock.SetDataManager(self.dataManager)

    def setupUi(self):
        self.setObjectName("MainWindow")
        self.resize(1000, 640)
        self.CreateVTK()
        self.CreateMenuBar()
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('GTree Analyzer created by zhouhang', 3000)

    def CreateVTK(self):
        self.vtkWidget = NeuroGLWidget.NeuroGLWidget(self)
        self.setCentralWidget(self.vtkWidget)

    def CreateMenuBar(self):
        self.menuBar = QMenuBar()
        self.setMenuBar(self.menuBar)
        self.fileMenu = self.menuBar.addMenu('&File')
        openAction = QAction('&OpenImage', self)
        openAction.setShortcut('Ctrl+O')
        self.fileMenu.addAction(openAction)
        openAction.triggered.connect(self.OpenImage)
        exitAction = QAction(QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)
        self.fileMenu.addAction(exitAction)

    def CreateLeftDock(self):
        self.singleDock = SingleDockWidget(self)
        self.singleDock.SetVTKWidget(self.vtkWidget)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.singleDock)
        self.mostdDock = TDATADockWidget(self)
        self.mostdDock.SetVTKWidget(self.vtkWidget)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.mostdDock)
        self.mostdDock.show()
        self.singleDock.hide()

    def OpenImage(self):
        openFile = QFileDialog.getOpenFileName(self, 'Open TIFF','./','TIFF (*.tif);MOSTD (*.mostd)')
        openFile = openFile[0]
        if not os.path.exists(openFile):
            QMessageBox.warning(self,'file invalid','please choose right tiff')
        if openFile[-3:]=='tif':
            self._ReadImage(openFile)
        if openFile[-5:]=='mostd':
            self._ReadMOSTD(openFile)

    def _ReadImage(self, openFile):
        self.dataManager.origImg = skimage.io.imread(openFile, plugin='tifffile')
        self.vtkWidget.RenderImage(self.dataManager.origImg)
        self.singleDock.show()
        self.mostdDock.hide()
        if self.dataManager.origImg.dtype == np.uint16:
            self.singleDock.rs.setMax(4096)
            self.singleDock.rs.setEnd(1000)
            self.singleDock.rs.update()
            self.singleDock.colorLineEdit.setText('-'.join([str(0),str(1000)]))
        else:
            self.singleDock.rs.setMax(255)
            self.singleDock.rs.setEnd(255)
            self.singleDock.rs.update()
            self.singleDock.colorLineEdit.setText('-'.join([str(0), str(255)]))
        self.singleDock.ApplyImage()
        self.singleDock.RangeSliderValueChange()

    def _ReadMOSTD(self, openFile):
        self.singleDock.hide()
        self.mostdDock.show()
        self.mostdDock.ReadMOSTD(openFile)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, event):
        print(event.mimeData().text())
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()
            if len(url) > 1:
                QMessageBox.warning(self, 'warning','cannot read multiple image')
            else:
                filePath = url[0].path()[1:]
                if filePath[-3:] == 'tif':
                    self.singleDock.imageNameEdit.setText(filePath.split('/')[-1])
                    self._ReadImage(filePath)
                    self.vtkWidget.ren[0].GetRenderWindow().Render()
                elif filePath[-5:] == 'mostd':
                    self.mostdDock.imageNameEdit.setText(filePath.split('/')[-1])
                    self._ReadMOSTD(filePath) # set dockwidget
                    self.vtkWidget.ren[0].GetRenderWindow().Render()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    main.vtkWidget.iren.Initialize()
    sys.exit(app.exec_())
