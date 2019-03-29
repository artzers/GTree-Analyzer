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
from scipy.ndimage.filters import convolve as convolveim
from scipy.ndimage import zoom
from PyQt5 import (QtWidgets, QtCore, QtGui)
from PyQt5.QtGui import QIcon
from DeepLearning import SuperResolutionGenerator
import InteractorStyle


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle('GTree Image Compare')
        self.setWindowIcon(QIcon('./windows.png'))
        self.setAcceptDrops(True)
        self.setupUi()
        self.CreateDockWidget()
        self.CreateLeftDock()
        self.CreateToolBar()
        self.origImg = [np.zeros((1,1)) for i in range(2)]
        self.srNet = None

    def setupUi(self):
        self.setObjectName("MainWindow")
        self.resize(1000, 640)
        self.CreateVTK()
        self.CreateMenuBar()
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('GTree Analyzer created by zhouhang', 3000)

    def CreateToolBar(self):
        self.toolBar = QtWidgets.QToolBar(self)
        self.addToolBar(self.toolBar)
        self.toolBar.addAction(self.openAction1)
        self.toolBar.addAction(self.openAction2)
        self.toolBar.addAction(self.convAction)
        self.downsampleAction = QtWidgets.QAction('&DownSample', self)
        self.downsampleAction.triggered.connect(self.DownSampling)
        self.toolBar.addAction(self.downsampleAction)
        self.exchangeAction = QtWidgets.QAction('&Exchange',self)
        self.exchangeAction.triggered.connect(self.ExchangeImage)
        self.toolBar.addAction(self.exchangeAction)
        self.dpAction = QtWidgets.QAction('&SR', self)
        self.dpAction.triggered.connect(self.SRGenerate)
        self.toolBar.addAction(self.dpAction)

    def SRGenerate(self):
        if self.srNet == None:
            self.srNet = SuperResolutionGenerator()
            filePath = '20190322-2d+1d-32-2blur.pt'
            prePath = os.path.abspath('D:/Python/SR201903/20190321-3DWDSR-AllBlur/')
            filePath = os.path.join(prePath, filePath)
            self.srNet.SetTorchFilePath(filePath)
        self.srNet.SetMeanMax(4,221)
        self.origImg[1] = self.srNet.Generate(self.origImg[0])
        self._RenderImage(self.origImg[1],1)


    def CreateVTK(self):
        self.vtkWidget = NeuroGLWidget.NeuroGLWidget(self)
        self.setCentralWidget(self.vtkWidget)

    def CreateMenuBar(self):
        self.menuBar = QMenuBar()
        self.setMenuBar(self.menuBar)
        self.fileMenu = self.menuBar.addMenu('&File')
        #
        self.openAction1 = QAction('&OpenImage1', self)
        #openAction.setShortcut('Ctrl+O')
        self.openAction1.triggered.connect(self.OpenImage1)
        self.fileMenu.addAction(self.openAction1)
        self.openAction2 = QAction('&OpenImage2', self)
        self.openAction2.triggered.connect(self.OpenImage2)
        self.fileMenu.addAction(self.openAction2)
        self.fileMenu.addAction(self.openAction2)
        self.convAction = QAction('&Conv3D', self)
        self.convAction.triggered.connect(self.Conv3d)
        self.fileMenu.addAction(self.convAction)
        exitAction = QAction(QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)
        self.fileMenu.addAction(exitAction)

    def CreateDockWidget(self):
        self.xResSpin = []
        self.yResSpin = []
        self.zResSpin = []
        for i in range(2):
            self.xResSpin.append(QDoubleSpinBox(self))
            self.yResSpin.append(QDoubleSpinBox(self))
            self.zResSpin.append(QDoubleSpinBox(self))
        self.dockWidget = QtWidgets.QWidget(self)
        groupBox1 = QGroupBox('Option for Image1')
        groupBox2 = QGroupBox('Option for Image2')
        verticLayout = QtWidgets.QVBoxLayout(self.dockWidget)
        verticLayout.addWidget(groupBox1)
        verticLayout.addWidget(groupBox2)
        self.SetupGroupBox(groupBox1,0, self.ApplyImage1)
        self.SetupGroupBox(groupBox2, 1,self.ApplyImage2)
        self.dockWidget.setLayout(verticLayout)
        image2PrefixPathLabel = QtWidgets.QLabel(self.dockWidget)
        image2PrefixPathLabel.setText('Prefix Dir')
        self.image2PrefixPathEdit = QtWidgets.QLineEdit(self.dockWidget)
        grid = groupBox2.layout()
        grid.addWidget(image2PrefixPathLabel, 4, 0)
        grid.addWidget(self.image2PrefixPathEdit,4,1)
        self.autoReadCheckBox = QtWidgets.QCheckBox(self.dockWidget)
        self.autoReadCheckBox.setText('auto read')
        grid.addWidget(self.autoReadCheckBox, 5, 1)
        #
        image1NameLabel = QtWidgets.QLabel(self.dockWidget)
        image1NameLabel.setText('FileName')
        self.image1NameEdit = QtWidgets.QLineEdit(self.dockWidget)
        grid = groupBox1.layout()
        grid.addWidget(self.image1NameEdit,4,1)
        grid.addWidget(image1NameLabel,4,0)
        self.CreateRangeSlider()
        grid = groupBox1.layout()
        grid.addWidget(self.rs[0],6,0,1,2)
        conv3dLabel = QtWidgets.QLabel(self.dockWidget)
        conv3dLabel.setText('conv param')
        self.conv3dLineEdit = QtWidgets.QLineEdit(self.dockWidget)
        self.conv3dLineEdit.setText('21,21,11,32,2')
        grid.addWidget(conv3dLabel, 7, 0, 1, 1)
        grid.addWidget(self.conv3dLineEdit, 7, 1, 1, 1)
        imadjustButton1 = QtWidgets.QPushButton(self.dockWidget)
        imadjustButton1.setText('imadjust')
        imadjustButton1.clicked.connect(self.Adjust1)
        grid.addWidget(imadjustButton1,8,0,1,1)
        grid = groupBox2.layout()
        grid.addWidget(self.rs[1], 6, 0,1,2)
        imadjustButton2 = QtWidgets.QPushButton(self.dockWidget)
        imadjustButton2.setText('imadjust')
        imadjustButton2.clicked.connect(self.Adjust2)
        grid.addWidget(imadjustButton2, 7, 0, 1, 1)

    def Adjust1(self):
        low_out = 0
        high_out = 0
        low_in = self.rs[0].start()
        high_in = self.rs[0].end()
        if self.origImg[0].dtype == np.uint8:
            high_out = 255
        else:
            QMessageBox.warning(self,'warning','16bit is not implemented')
            return
        img = self.origImg[0].astype(np.float)
        ratio = high_out / (high_in - low_in)
        img = np.uint8(np.clip((img-low_in)*ratio,0,255))
        self.origImg[0] = img
        self.vtkWidget.RenderImage(self.origImg[0],0)
        self.rs[0].setRange(0, 255)

    def Adjust2(self):
        low_out = 0
        high_out = 0
        low_in = self.rs[1].start()
        high_in = self.rs[1].end()
        if self.origImg[1].dtype == np.uint8:
            high_out = 255
        else:
            QMessageBox.warning(self, 'warning', '16bit is not implemented')
            return
        img = self.origImg[1].astype(np.float)  # shallow copy
        ratio = high_out / (high_in - low_in)
        img = np.uint8(np.clip((img-low_in)*ratio,0,255))
        self.origImg[1] = img
        self.vtkWidget.RenderImage(self.origImg[1], 1)
        self.rs[1].setRange(0, 255)


    def CreateRangeSlider(self):
        self.rs = []
        for i in range(2):
            self.rs.append(QRangeSlider(self.dockWidget))
            self.rs[i].setMax(1000)
            self.rs[i].setMin(0)
            self.rs[i].setRange(0, 1000)
            self.rs[i].setBackgroundStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #000000, stop:1 #000000);')
            self.rs[i].handle.setStyleSheet('background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #000000, stop:1 #DDDDDD);')
        self.rs[0].startValueChanged.connect(self.RangeSlider1ValueChange)
        self.rs[0].endValueChanged.connect(self.RangeSlider1ValueChange)
        self.rs[1].startValueChanged.connect(self.RangeSlider2ValueChange)
        self.rs[1].endValueChanged.connect(self.RangeSlider2ValueChange)

    def RangeSlider1ValueChange(self):
        self.vtkWidget.SetColor(self.rs[0].start(),self.rs[0].end(),0)

    def RangeSlider2ValueChange(self):
        self.vtkWidget.SetColor(self.rs[1].start(),self.rs[1].end(),1)

    def SetupGroupBox(self,groupBox, index, applyFunc):
        gridLayout = QtWidgets.QGridLayout(groupBox)
        groupBox.setLayout(gridLayout)
        self.CreateLabelForDockWidget('xRes', [0, 0], gridLayout)
        self.CreateLabelForDockWidget('yRes', [1, 0], gridLayout)
        self.CreateLabelForDockWidget('zRes', [2, 0], gridLayout)
        self.SetupDoubleSpinBoxForDockWidget(self.xResSpin[index], [0, 1], gridLayout)
        self.SetupDoubleSpinBoxForDockWidget(self.yResSpin[index], [1, 1], gridLayout)
        self.SetupDoubleSpinBoxForDockWidget(self.zResSpin[index], [2, 1], gridLayout)
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
        grid.addWidget(spinBox, pos[0], pos[1])

    def CreateLabelForDockWidget(self,text,pos, grid):
        label = QtWidgets.QLabel(self.dockWidget)
        label.setText(text)
        grid.addWidget(label, pos[0], pos[1])

    def CreateLeftDock(self):
        dock = QtWidgets.QDockWidget("Image Option")
        dock.setWidget(self.dockWidget)
        dock.setObjectName("ImageOptionDock")
        dock.setFeatures(dock.DockWidgetFloatable | dock.DockWidgetMovable )
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
        dock.setMinimumWidth(200)

    def ApplyImage1(self):
        xScale = self.xResSpin[0].value()
        yScale = self.yResSpin[0].value()
        zScale = self.zResSpin[0].value()
        self.vtkWidget.RescaleImage(0, xScale, yScale, zScale)

    def ApplyImage2(self):
        xScale = self.xResSpin[1].value()
        yScale = self.yResSpin[1].value()
        zScale = self.zResSpin[1].value()
        self.vtkWidget.RescaleImage(1,xScale, yScale, zScale)

    def OpenImage1(self):
        self.OpenImage(0)

    def OpenImage2(self):
        self.OpenImage(1)

    def OpenImage(self, index):
        self.vtkWidget.ren[index].RemoveVolume(self.vtkWidget.volume[index])
        openFile = QFileDialog.getOpenFileName(self, 'Open TIFF','./','TIFF (*.tif)')
        openFile = openFile[0]
        if not os.path.exists(openFile):
            QMessageBox.warning(self,'file invalid','please choose right tiff')
        #origImg = tifffile.imread(openFile)
        self._ReadImage(openFile, index)

    def _ReadImage(self, openFile, index):
        if self.origImg[index].shape[0] < 10:
            pass
        self.origImg[index] = skimage.io.imread(openFile, plugin='tifffile')
        if len(self.origImg[index].shape) < 3:
            self.origImg[index] = np.stack(
                [self.origImg[index],self.origImg[index]],axis=0)
        self._RenderImage(self.origImg[index],index)

    def _RenderImage(self,img,index):
        self.vtkWidget.RenderImage(img,index)
        if img.dtype == np.uint16:
            self.rs[index].setMax(4096)
            self.rs[index].setEnd(self.rs[index].end())
            #self.rs[index].setEnd(1000)
            self.rs[index].update()
        else:
            self.rs[index].setMax(1000)
            self.rs[index].setEnd(self.rs[index].end())
            #self.rs[index].setEnd(255)
            self.rs[index].update()
        if index == 0:
            self.ApplyImage1()
            self.RangeSlider1ValueChange()
        else:
            self.ApplyImage2()
            self.RangeSlider2ValueChange()

    def ExchangeImage(self):
        self.tmp = self.origImg[1]
        self.origImg[1] = self.origImg[0]
        self.origImg[0] = self.tmp
        for i in range(2):
            if self.origImg[i].shape[0] > 1:
                self._RenderImage(self.origImg[i],i)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, event):
        #print(event.mimeData().text())
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()
            if len(url) > 1:
                QMessageBox.warning(self, 'warning','cannot read multiple image')
            else:
                filePath = url[0].path()[1:]
                if filePath[-3:] != 'tif':
                    return
                image1Name = filePath.split('/')[-1]
                self.image1NameEdit.setText(image1Name)
                #origImg = tifffile.imread(filePath)
                # origImg = skimage.io.imread(filePath,plugin='tifffile')
                # self.vtkWidget.RenderImage(origImg, 0)
                self._ReadImage(filePath,0)
                self.vtkWidget.ren[0].GetRenderWindow().Render()
                if self.autoReadCheckBox.isChecked():
                    prefix = self.image2PrefixPathEdit.text()
                    prefix = os.path.abspath(prefix)
                    autoName = image1Name
                    if image1Name[0:5] == 'proj_':
                        autoName = image1Name[5:]
                    filePath2 = os.path.join(prefix, autoName)
                    if os.path.exists(filePath2):
                        self._ReadImage(filePath2,1)
                        self.vtkWidget.ren[1].GetRenderWindow().Render()

    def Conv3d(self):
        if self.origImg[0].shape[0] > 10:
            paramText =self.conv3dLineEdit.text()
            parameterList = paramText.split(',')
            if len(parameterList) != 5:
                QMessageBox.warning(self, 'warning','please input right parameter')
                return

            self.xBlurSize = int(parameterList[0])
            self.yBlurSize = int(parameterList[1])
            self.zBlurSize = int(parameterList[2])
            self.sigma1 = float(parameterList[3])
            self.sigma2 = float(parameterList[4])
            center = [np.round(self.zBlurSize / 2), np.round(self.yBlurSize / 2), np.round(self.xBlurSize / 2) ]
            psf = np.zeros((self.zBlurSize,self.yBlurSize,self.xBlurSize))
            for i in range(self.xBlurSize):
                for j in range(self.yBlurSize):
                    for k in range(self.zBlurSize):
                        psf[k,j,i] = np.exp(
                            -((i - center[2])**2+ (j - center[1])**2)/self.sigma1
                            -((k - center[0])**2) / self.sigma2
                        )
            psf /= np.sum(psf)
            #img = self.origImg[0].astype(np.float)
            self.origImg[1] = convolveim(self.origImg[0],psf)#  np.ones((11,1,1))/11
            #self.origImg[1] = self.origImg[1].astype(np.uint8)
            #psfImg = psf.copy()
            #psfImg /= np.max(psfImg)
            #psfImg *= 255.
            #psfImg = np.uint8(psfImg)
            self._RenderImage(self.origImg[1], 1)
        else:
            pass

    def DownSampling(self):
        if self.origImg[0].shape[0] > 10:
            self.origImg[1] = zoom(self.origImg[0],0.5)
            self._RenderImage(self.origImg[1], 1)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    main.vtkWidget.iren.Initialize()
    sys.exit(app.exec_())
