import sys,os
import vtk
import numpy as np
import skimage.io
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QFileDialog, QMessageBox, QSpacerItem,\
    QDoubleSpinBox, QGroupBox, QPushButton, QLabel, QSpinBox,QDockWidget
from QRangeSlider import QRangeSlider
import NeuroGLWidget
from TDATAReader import TDATAReader
from GDataManager import GDataManager
from PyQt5 import (QtWidgets, QtCore, QtGui)
from PyQt5.QtGui import QIcon

class TDATADockWidget(QDockWidget):
    def __init__(self, parent=None):
        super(TDATADockWidget, self).__init__(parent)
        self.CreateDockWidget()
        self.vtkWidget = None
        self.setWidget(self.dockWidget)
        self.setWindowTitle('MOSTD Option')
        self.setObjectName("MOSTDOptionDock")
        self.setFeatures(self.DockWidgetFloatable | self.DockWidgetMovable)
        self.setMinimumWidth(200)
        self.dataManager = None
        self.mostdReader = TDATAReader()

    def SetDataManager(self,manager):
        self.dataManager = manager

    def ReadMOSTD(self,mostd):
        self.mostdReader.SetInputFileName(mostd)
        if self.mostdReader.param['img_type'] == 2:
            self.rs.setMax(4096)
            self.rs.setEnd(1000)
            self.rs.update()
            self.colorLineEdit.setText('-'.join([str(0),str(1000)]))
        else:
            self.rs.setMax(255)
            self.rs.setEnd(255)
            self.rs.update()
            self.colorLineEdit.setText('-'.join([str(0), str(255)]))
        self.rangeLabelList[0].setText('X Range: %d'%(self.mostdReader.param['sz0']))
        self.rangeLabelList[1].setText('Y Range: %d' % (self.mostdReader.param['sz1']))
        self.rangeLabelList[2].setText('Z Range: %d' % (self.mostdReader.param['sz2']))
        self.levelSpinBox.setMaximum(self.mostdReader.param['level_size'])
        #self.ApplyImage()
        #self.RangeSliderValueChange()

    def ReadIOR(self):
        if not self.mostdReader.valid:
            return
        self.dataManager.origImg = self.mostdReader.SelectIOR(self.minSpinBox[0].value(),
                                             self.maxSpinBox[0].value(),
                                             self.minSpinBox[1].value(),
                                             self.maxSpinBox[1].value(),
                                             self.minSpinBox[2].value(),
                                             self.maxSpinBox[2].value(),
                                             self.levelSpinBox.value())
        self.vtkWidget.RenderImage(self.dataManager.origImg)
        self.ApplyImage()
        self.RangeSliderValueChange()

    def SetVTKWidget(self,vtk):
        self.vtkWidget = vtk

    def CreateDockWidget(self):
        self.dockWidget = QtWidgets.QWidget(self)
        verticLayout = QtWidgets.QVBoxLayout(self.dockWidget)
        self.dockWidget.setLayout(verticLayout)
        #mostd range
        groupBox1 = QGroupBox('MOSTD Range')
        verticLayout.addWidget(groupBox1)
        gridLayout = QtWidgets.QGridLayout(groupBox1)
        groupBox1.setLayout(gridLayout)
        axisLabel = ['X', 'Y', 'Z']
        self.rangeLabelList = []
        for i in range(3):
            self.rangeLabelList.append(QLabel(self.dockWidget))
            self.rangeLabelList[i].setText(axisLabel[i] + ' Range:')
            gridLayout.addWidget(self.rangeLabelList[i],i,0,1,2)
            self.rangeLabelList[i].setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.minSpinBox = []
        self.maxSpinBox = []
        for i in range(3):
            self.minSpinBox.append(QSpinBox(self.dockWidget))
            self.maxSpinBox.append(QSpinBox(self.dockWidget))
            self.minSpinBox[i].setMinimum(0)
            self.maxSpinBox[i].setMinimum(0)
            self.minSpinBox[i].setMaximum(999999)
            self.maxSpinBox[i].setMaximum(999999)
        self.levelSpinBox = QSpinBox(self.dockWidget)
        self.levelSpinBox.setMinimum(1)
        self.SetupGroupBox1(groupBox1,self.ReadIOR)
        #resolution and illusion
        groupBox2 = QGroupBox('Image')
        verticLayout.addWidget(groupBox2)
        gridLayout2 = QtWidgets.QGridLayout(groupBox2)
        groupBox2.setLayout(gridLayout2)
        self.xResSpin = QDoubleSpinBox(self.dockWidget)
        self.yResSpin = QDoubleSpinBox(self.dockWidget)
        self.zResSpin = QDoubleSpinBox(self.dockWidget)
        self.SetupGroupBox2(groupBox2, self.ApplyImage)
        self.CreateRangeSlider()
        grid = groupBox2.layout()
        grid.addWidget(self.rs, 6, 0, 2,2)
        imageNameLabel = QtWidgets.QLabel(self.dockWidget)
        imageNameLabel.setText('FileName')
        self.imageNameEdit = QtWidgets.QLineEdit(self.dockWidget)
        grid = groupBox2.layout()
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

    def SetupGroupBox1(self,groupBox, applyFunc):
        gridLayout = groupBox.layout()
        self.CreateLabelForDockWidget('XMIN:', [3, 0, 1, 1], gridLayout)
        self.CreateLabelForDockWidget('XMAX:', [4, 0, 1, 1], gridLayout)
        self.CreateLabelForDockWidget('YMIN:', [5, 0, 1, 1], gridLayout)
        self.CreateLabelForDockWidget('YMAX:', [6, 0, 1, 1], gridLayout)
        self.CreateLabelForDockWidget('ZMIN:', [7, 0, 1, 1], gridLayout)
        self.CreateLabelForDockWidget('ZMAX:', [8, 0, 1, 1], gridLayout)
        self.CreateLabelForDockWidget('LEVEL:', [9, 0, 1, 1], gridLayout)
        self.SetupSpinBoxForDockWidget(self.minSpinBox[0], [3, 1,1,1], gridLayout)
        self.SetupSpinBoxForDockWidget(self.maxSpinBox[0], [4, 1,1,1], gridLayout)
        self.SetupSpinBoxForDockWidget(self.minSpinBox[1], [5, 1, 1, 1], gridLayout)
        self.SetupSpinBoxForDockWidget(self.maxSpinBox[1], [6, 1, 1, 1], gridLayout)
        self.SetupSpinBoxForDockWidget(self.minSpinBox[2], [7, 1, 1, 1], gridLayout)
        self.SetupSpinBoxForDockWidget(self.maxSpinBox[2], [8, 1, 1, 1], gridLayout)
        self.SetupSpinBoxForDockWidget(self.levelSpinBox, [9, 1, 1, 1], gridLayout)
        readButton = QPushButton(self.dockWidget)
        readButton.setText('Read')
        readButton.clicked.connect(applyFunc)
        gridLayout.addWidget(readButton, 10, 1)
        vSpacer = QtWidgets.QSpacerItem(20, 40,
                                        QtWidgets.QSizePolicy.Minimum,
                                        QtWidgets.QSizePolicy.Expanding)
        gridLayout.addItem(vSpacer, 11, 0)

    def SetupGroupBox2(self,groupBox, applyFunc):
        gridLayout = groupBox.layout()
        self.CreateLabelForDockWidget('xRes', [0, 0,1,1], gridLayout)
        self.CreateLabelForDockWidget('yRes', [1, 0,1,1], gridLayout)
        self.CreateLabelForDockWidget('zRes', [2, 0,1,1], gridLayout)
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

    def SetupSpinBoxForDockWidget(self,spinBox,pos, grid):
        spinBox.setValue(0)
        spinBox.setSingleStep(1)
        spinBox.setMaximum(999999)
        grid.addWidget(spinBox, pos[0], pos[1],1,1)

    def SetupDoubleSpinBoxForDockWidget(self,spinBox,pos, grid):
        spinBox.setValue(1)
        spinBox.setSingleStep(0.5)
        grid.addWidget(spinBox, pos[0], pos[1],1,1)

    def CreateLabelForDockWidget(self,text,pos, grid):
        label = QtWidgets.QLabel(self.dockWidget)
        label.setText(text)
        label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        grid.addWidget(label, pos[0], pos[1],pos[2],pos[3])

    def ApplyImage(self):
        xScale = self.xResSpin.value()
        yScale = self.yResSpin.value()
        zScale = self.zResSpin.value()
        self.vtkWidget.RescaleImage( xScale, yScale, zScale)