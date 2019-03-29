import sys,os
import vtk
import numpy as np
import skimage.io
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, \
QStatusBar, QMenuBar, QFileDialog, QMessageBox, QSpacerItem,\
    QDoubleSpinBox, QGroupBox, QPushButton, QDockWidget
from QRangeSlider import QRangeSlider
import NeuroGLWidget

from PyQt5 import (QtWidgets, QtCore, QtGui)
from PyQt5.QtGui import QIcon

class SingleDockWidget(QDockWidget):
    def __init__(self, parent=None):
        super(SingleDockWidget, self).__init__(parent)
        self.CreateDockWidget()
        self.vtkWidget = None
        self.setWidget(self.dockWidget)
        self.setWindowTitle('Image Option')
        self.setObjectName("ImageOptionDock")
        self.setFeatures(self.DockWidgetFloatable | self.DockWidgetMovable)

        self.setMinimumWidth(200)

    def SetVTKWidget(self,vtk):
        self.vtkWidget = vtk

    def CreateDockWidget(self):
        self.dockWidget = QtWidgets.QWidget(self)
        self.xResSpin = QDoubleSpinBox(self.dockWidget)
        self.yResSpin = QDoubleSpinBox(self.dockWidget)
        self.zResSpin = QDoubleSpinBox(self.dockWidget)
        groupBox1 = QGroupBox('Resolution')
        verticLayout = QtWidgets.QVBoxLayout(self.dockWidget)
        verticLayout.addWidget(groupBox1)
        self.SetupGroupBox(groupBox1, self.ApplyImage)
        self.dockWidget.setLayout(verticLayout)
        self.CreateRangeSlider()
        grid = groupBox1.layout()
        grid.addWidget(self.rs, 6, 0, 2,2)
        imageNameLabel = QtWidgets.QLabel(self.dockWidget)
        imageNameLabel.setText('FileName')
        self.imageNameEdit = QtWidgets.QLineEdit(self.dockWidget)
        grid = groupBox1.layout()
        grid.addWidget(self.imageNameEdit, 4, 1,1,1)
        grid.addWidget(imageNameLabel, 4, 0,1,1)
        self.colorLineEdit = QtWidgets.QLineEdit(self.dockWidget)
        grid.addWidget(self.colorLineEdit, 5, 0,1,2)

    def CreateRangeSlider(self):
        self.rs=QRangeSlider(self.dockWidget)
        self.rs.setMax(255)
        self.rs.setMin(0)
        self.rs.setRange(0, 255)
        self.rs.setBackgroundStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #000000, stop:1 #000000);')
        self.rs.handle.setStyleSheet('background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #000000, stop:1 #DDDDDD);')
        self.rs.startValueChanged.connect(self.RangeSliderValueChange)
        self.rs.endValueChanged.connect(self.RangeSliderValueChange)

    def RangeSliderValueChange(self):
        self.vtkWidget.SetColor(self.rs.start(),self.rs.end())
        self.colorLineEdit.setText('-'.join([str(self.rs.start()),
                                             str(self.rs.end())]))

    def SetupGroupBox(self,groupBox, applyFunc):
        gridLayout = QtWidgets.QGridLayout(groupBox)
        groupBox.setLayout(gridLayout)
        self.CreateLabelForDockWidget('xRes', [0, 0], gridLayout)
        self.CreateLabelForDockWidget('yRes', [1, 0], gridLayout)
        self.CreateLabelForDockWidget('zRes', [2, 0], gridLayout)
        self.SetupDoubleSpinBoxForDockWidget(self.xResSpin, [0, 1], gridLayout)
        self.SetupDoubleSpinBoxForDockWidget(self.yResSpin, [1, 1], gridLayout)
        self.SetupDoubleSpinBoxForDockWidget(self.zResSpin, [2, 1], gridLayout)
        applyButton = QPushButton(self.dockWidget)
        applyButton.setText('apply')
        applyButton.clicked.connect(applyFunc)
        gridLayout.addWidget(applyButton, 3, 1)
        vSpacer = QtWidgets.QSpacerItem(20, 40,
                                        QtWidgets.QSizePolicy.Minimum,
                                        QtWidgets.QSizePolicy.Expanding)
        gridLayout.addItem(vSpacer, 10, 0)

    def SetupDoubleSpinBoxForDockWidget(self,spinBox,pos, grid):
        spinBox.setValue(1)
        spinBox.setSingleStep(0.5)
        grid.addWidget(spinBox, pos[0], pos[1],1,1)

    def CreateLabelForDockWidget(self,text,pos, grid):
        label = QtWidgets.QLabel(self.dockWidget)
        label.setText(text)
        grid.addWidget(label, pos[0], pos[1])

    def ApplyImage(self):
        xScale = self.xResSpin.value()
        yScale = self.yResSpin.value()
        zScale = self.zResSpin.value()
        self.vtkWidget.RescaleImage( xScale, yScale, zScale)