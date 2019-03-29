import sys,os
import vtk
import InteractorStyle
from vtk import vtkCamera
import numpy as np
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk import vtkImagePlaneWidget,vtkSliderRepresentation2D
from PyQt5 import QtGui, QtCore, QtWidgets

class SliderCallback():
    def __init__(self, planeWidget):
        self.planeWidget = planeWidget

    def __call__(self, caller, ev):
        sliderWidget = caller
        value = sliderWidget.GetRepresentation().GetValue()
        self.planeWidget.SetSliceIndex(np.int(value))

class NeuroGLWidget(QVTKRenderWindowInteractor):
    def __init__(self, parent):
        super(NeuroGLWidget,self).__init__(parent)
        xmins = [0, .5]
        xmaxs = [0.5, 1]
        ymins = [0, 0]
        ymaxs = [1, 1]
        self.ren = []
        self.iren = self.GetRenderWindow().GetInteractor()
        self.volume = []
        self.volume.append(vtk.vtkVolume())
        self.volume.append(vtk.vtkVolume())
        for i in range(2):
            self.ren.append(vtk.vtkRenderer())
            self.GetRenderWindow().AddRenderer(self.ren[i])
            self.ren[i].SetViewport(xmins[i], ymins[i], xmaxs[i], ymaxs[i])
            self.ren[i].SetBackground(i / 10, i / 10, i / 10)
            self.ren[i].GetActiveCamera().ParallelProjectionOn()
        self.style = InteractorStyle.MyInteractorStyle()
        self.style.AutoAdjustCameraClippingRangeOn()
        self.style.SetInteractor(self.iren)
        self.style.SetRenderers(self.ren)
        self.iren.SetInteractorStyle(self.style)
        self.transform = []
        self.transform.append(vtk.vtkTransform())
        self.transform[0].Identity()
        self.transform.append(vtk.vtkTransform())
        self.transform[1].Identity()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onContextMenu)
        self.volumeRes=[]
        self.volumeRes.append([1,1,1])
        self.volumeRes.append([1,1,1])
        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.005)
        self.importData = [vtk.vtkImageData() for i in range(2)]
        self.colorFunc = []
        self.planeWidgetZ = []
        self.sliderRep = []
        self.sliderWidget = []
        for i in range(2):
            self.colorFunc.append(vtk.vtkColorTransferFunction())
            self.planeWidgetZ.append(vtkImagePlaneWidget())
            self.planeWidgetZ[i].SetSliceIndex(0)
        self.planeMode = False
        self.CreateSliderWidget()

    def CreateSliderWidget(self):
        for i in range(2):
            self.sliderRep.append(vtkSliderRepresentation2D())
            self.sliderRep[i].SetMinimumValue(0)
            self.sliderRep[i].SetMaximumValue(50)
            self.sliderRep[i].SetValue(self.planeWidgetZ[i].GetSliceIndex())
            self.sliderRep[i].GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
            self.sliderRep[i].GetPoint1Coordinate().SetValue( 0.1, 0.1)
            self.sliderRep[i].GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
            self.sliderRep[i].GetPoint2Coordinate().SetValue( 0.3, 0.1)
            self.sliderWidget.append(vtk.vtkSliderWidget())
            self.sliderWidget[i].SetAnimationModeToJump()
            self.sliderWidget[i].SetInteractor(self.iren)
            self.sliderWidget[i].SetRepresentation(self.sliderRep[i])
            self.sliderWidget[i].SetCurrentRenderer(self.ren[i])
            #self.sliderWidget[i].SetAnimationModeToAnimate()
            self.sliderWidget[i].EnabledOff()
            self.sliderWidget[i].AddObserver('InteractionEvent',
                                             SliderCallback(self.planeWidgetZ[i]))


    def RenderImage(self, origImg,index):
        # create volume
        volumeImport = vtk.vtkImageImport()
        data_string = origImg.tostring()
        if origImg.dtype == np.uint16:
            volumeImport.CopyImportVoidPointer(data_string, len(data_string))
            volumeImport.SetDataScalarTypeToUnsignedShort()
        else:
            volumeImport.CopyImportVoidPointer(data_string, len(data_string))
            volumeImport.SetDataScalarTypeToUnsignedChar()
        volumeImport.SetNumberOfScalarComponents(1)
        sz = origImg.shape
        volumeImport.SetDataExtent(0, sz[2] - 1, 0, sz[1] - 1, 0, sz[0] - 1)
        volumeImport.SetWholeExtent(0, sz[2] - 1, 0, sz[1] - 1, 0, sz[0] - 1)
        volumeImport.Update()
        self.importData[index].DeepCopy(volumeImport.GetOutput())
        #
        alphaChannelFunc = vtk.vtkPiecewiseFunction()
        alphaChannelFunc.AddPoint(0, 0.0)
        alphaChannelFunc.AddPoint(10, 0.9)
        #
        self.colorFunc[index].AddRGBPoint(1, 0.0, 0.0, 0.0)
        if origImg.dtype == np.uint16:
            self.colorFunc[index].AddRGBPoint(1000, 1.0, 1.0, 1.0)
        else:
            self.colorFunc[index].AddRGBPoint(255, 1.0, 1.0, 1.0)
        #
        volumeProperty = vtk.vtkVolumeProperty()
        volumeProperty.SetColor(self.colorFunc[index])
        volumeProperty.SetScalarOpacity(alphaChannelFunc)
        volumeProperty.SetInterpolationType(3)
        #
        volumeMapper = vtk.vtkSmartVolumeMapper()
        volumeMapper.SetBlendModeToMaximumIntensity()
        # volumeMapper.SetVolumeRayCastFunction(compositeFunction)
        volumeMapper.SetInterpolationModeToCubic()
        volumeMapper.SetInputConnection(volumeImport.GetOutputPort())
        self.volume[index].SetMapper(volumeMapper)
        self.volume[index].SetProperty(volumeProperty)
        self.volume[index].SetUserTransform(self.transform[index])
        self.ren[index].AddVolume(self.volume[index])
        self.ren[index].ResetCamera()

    def RescaleImage(self,index,x,y,z):
        self.volumeRes[index] = [x,y,z]
        self.transform[index].Identity()
        self.transform[index].Scale(x,y,z)
        self.ren[index].ResetCamera()
        self.ren[index].GetRenderWindow().Render()

    def onContextMenu(self, event):
        menu = QtWidgets.QMenu(parent=self)
        actionXY = QtWidgets.QAction('XY')
        actionXY.triggered.connect(self.XYView)
        actionXZ = QtWidgets.QAction('XZ')
        actionXZ.triggered.connect(self.XZView)
        actionYZ = QtWidgets.QAction('YZ')
        actionYZ.triggered.connect(self.YZView)
        planeModeCheck = QtWidgets.QAction('PlaneMode')
        planeModeCheck.setCheckable(True)
        planeModeCheck.setChecked(self.planeMode)
        planeModeCheck.triggered.connect(self.TogglePlaneMode)
        menu.addAction(actionXY)
        menu.addAction(actionXZ)
        menu.addAction(actionYZ)
        menu.addAction(planeModeCheck)
        menu.exec_(QtGui.QCursor.pos())

    def XYView(self):
        for i in range(2):
            camera = vtk.vtkCamera()
            camera.ParallelProjectionOn()
            self.ren[i].SetActiveCamera(camera)
            self.ren[i].ResetCamera()

    def XZView(self):
        for i in range(2):
            camera = vtk.vtkCamera()
            camera.ParallelProjectionOn()
            camera.Elevation(45)
            camera.OrthogonalizeViewUp()
            camera.Elevation(45)
            self.ren[i].SetActiveCamera(camera)
            self.ren[i].ResetCamera()

    def YZView(self):
        for i in range(2):
            camera = vtk.vtkCamera()
            camera.ParallelProjectionOn()
            camera.Azimuth(90)
            self.ren[i].SetActiveCamera(camera)
            self.ren[i].ResetCamera()

    def SetColor(self,start,end,index):
        self.colorFunc[index] = vtk.vtkColorTransferFunction()
        self.colorFunc[index].AddRGBPoint(start,0,0,0)
        self.colorFunc[index].AddRGBPoint(end, 1, 1, 1)
        self.volume[index].GetProperty().SetColor(self.colorFunc[index])
        self.ren[index].GetRenderWindow().Render()

    def TogglePlaneMode(self, arg):
        self.planeMode = arg
        if arg:
            self.ren[0].RemoveVolume(self.volume[0])
            self.ren[1].RemoveVolume(self.volume[1])
            for i in range(2):
                sz = self.importData[i].GetDimensions()
                if sz[0] == 0 or sz[1] == 0 or sz[2] == 0:
                    print('empty import data')
                    continue
                self.planeWidgetZ[i].DisplayTextOn()
                #self.planeWidgetZ[i].GetTextProperty().
                self.planeWidgetZ[i].SetInputData(self.importData[i])
                self.planeWidgetZ[i].SetPlaneOrientationToZAxes()
                self.planeWidgetZ[i].RestrictPlaneToVolumeOn()
                self.planeWidgetZ[i].SetResliceInterpolateToLinear()
                self.planeWidgetZ[i].SetSliceIndex(0)
                self.planeWidgetZ[i].SetPicker(self.picker)
                self.planeWidgetZ[i].SetKeyPressActivationValue("z")
                self.planeWidgetZ[i].SetInteractor(self.GetRenderWindow().GetInteractor())
                prop2 = self.planeWidgetZ[i].GetPlaneProperty()
                prop2.SetColor(0, 0, 1)
                self.planeWidgetZ[i].SetCurrentRenderer(self.ren[i])
                self.planeWidgetZ[i].On()
                self.sliderRep[i].SetMaximumValue(sz[2])
                self.sliderWidget[i].SetCurrentRenderer(self.ren[i])
                self.sliderWidget[i].EnabledOn()
                #self.planeWidgetZ[i].SetLookupTable(planeWidgetX.GetLookupTable())
        else:
            for i in range(2):
                #self.planeWidgetZ[i].SetEnabled(False)
                sz = self.importData[i].GetDimensions()
                if sz[0] == 0 or sz[1] == 0 or sz[2] == 0:
                    pass
                else:
                    self.planeWidgetZ[i].Off()
                self.sliderWidget[i].EnabledOff()
                self.ren[i].AddVolume(self.volume[i])