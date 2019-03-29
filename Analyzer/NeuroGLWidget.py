import sys,os
import vtk
import InteractorStyle
import numpy as np
from vtk import vtkRenderWindowInteractor, vtkWorldPointPicker, \
    vtkProperty, vtkRenderWindowInteractor3D
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
        self.iren = self.GetRenderWindow().GetInteractor()
        self.volume = vtk.vtkVolume()
        self.GetRenderWindow().SetNumberOfLayers(2)
        self.ren = []
        for i in range(2):
            self.ren.append(vtk.vtkRenderer())
            self.ren[i].SetLayer(i)
            self.GetRenderWindow().AddRenderer(self.ren[i])
            #self.ren[i].GetActiveCamera().ParallelProjectionOn()
        self.ren[1].SetActiveCamera(self.ren[0].GetActiveCamera())
        self.ren[0].GetActiveCamera().ParallelProjectionOn()
        self.style = InteractorStyle.MyInteractorStyle()
        self.style.SetInteractor(self.iren)
        self.style.SetRenderers(self.ren)
        #self.style.SetRendererCollection(self.GetRenderWindow().GetRenderers())
        self.style.AutoAdjustCameraClippingRangeOff()
        self.iren.SetInteractorStyle(self.style)
        self.style.SetGLWidgetHandle(self)
        self.transform = vtk.vtkTransform()
        self.transform.Identity()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onContextMenu)
        self.volumeSize = [0,0,0]#d,h,w
        self.volumeRes = [1,1,1]#d,h,w
        self.outLine = vtk.vtkActor()

        self.axes = vtk.vtkAxesActor()
        self.marker = vtk.vtkOrientationMarkerWidget()
        self.marker.SetOutlineColor(1,1,1)
        self.marker.SetOrientationMarker(self.axes)
        self.marker.SetInteractor(self.GetRenderWindow().GetInteractor())
        self.marker.SetViewport(0,0,0.1,0.1)
        self.marker.SetEnabled(True)
        self.marker.InteractiveOn()
        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.005)
        self.importData = vtk.vtkImageData()
        self.colorFunc = vtk.vtkColorTransferFunction()
        self.planeWidgetZ = vtkImagePlaneWidget()
        self.planeWidgetZ.SetSliceIndex(0)
        self.planeMode = False
        self.CreateSliderWidget()

    def CreateSliderWidget(self):
            self.sliderRep=vtkSliderRepresentation2D()
            self.sliderRep.SetMinimumValue(0)
            self.sliderRep.SetMaximumValue(50)
            self.sliderRep.SetValue(self.planeWidgetZ.GetSliceIndex())
            self.sliderRep.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
            self.sliderRep.GetPoint1Coordinate().SetValue( 0.3, 0.02)
            self.sliderRep.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
            self.sliderRep.GetPoint2Coordinate().SetValue( 0.6, 0.02)
            self.sliderWidget=vtk.vtkSliderWidget()
            self.sliderWidget.SetAnimationModeToJump()
            self.sliderWidget.SetInteractor(self.iren)
            self.sliderWidget.SetRepresentation(self.sliderRep)
            #self.sliderWidget.SetCurrentRenderer(self.ren)
            self.sliderWidget.EnabledOff()
            self.sliderWidget.AddObserver('InteractionEvent',
                                             SliderCallback(self.planeWidgetZ))


    def RenderImage(self, origImg):
        self.ren[0].RemoveVolume(self.volume)
        self.ren[0].RemoveActor(self.outLine)
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
        self.importData.DeepCopy(volumeImport.GetOutput())
        self.volumeSize = sz
        #
        alphaChannelFunc = vtk.vtkPiecewiseFunction()
        alphaChannelFunc.AddPoint(0, 0.0)
        alphaChannelFunc.AddPoint(10, 0.9)
        #
        self.colorFunc.AddRGBPoint(1, 0.0, 0.0, 0.0)
        self.colorFunc.AddRGBPoint(255, 1.0, 1.0, 1.0)
        #
        volumeProperty = vtk.vtkVolumeProperty()
        volumeProperty.SetColor(self.colorFunc)
        volumeProperty.SetScalarOpacity(alphaChannelFunc)
        volumeProperty.SetInterpolationType(3)
        #
        volumeMapper = vtk.vtkSmartVolumeMapper()
        volumeMapper.SetBlendModeToMaximumIntensity()
        # volumeMapper.SetVolumeRayCastFunction(compositeFunction)
        volumeMapper.SetInterpolationModeToCubic()
        volumeMapper.SetInputConnection(volumeImport.GetOutputPort())
        self.volume.SetMapper(volumeMapper)
        self.volume.SetProperty(volumeProperty)
        self.volume.SetUserTransform(self.transform)
        #
        outLineSource = vtk.vtkVolumeOutlineSource()
        outLineSource.SetVolumeMapper(volumeMapper)
        outLineMapper = vtk.vtkPolyDataMapper()
        outLineMapper.SetInputConnection(outLineSource.GetOutputPort())
        self.outLine.SetMapper(outLineMapper)
        self.outLine.GetProperty().SetColor(0,1,1)
        self.outLine.SetUserTransform(self.transform)
        self.ren[0].AddVolume(self.volume)
        self.ren[0].AddActor(self.outLine)
        self.ren[0].ResetCamera()

    def RescaleImage(self,x,y,z):
        self.volumeRes = [z,y,x]
        self.transform.Identity()
        self.transform.Scale(x,y,z)
        self.ren[0].ResetCamera()
        self.ren[0].GetRenderWindow().Render()

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
        camera = vtk.vtkCamera()
        camera.ParallelProjectionOn()
        self.ren[0].SetActiveCamera(camera)
        self.ren[1].SetActiveCamera(camera)
        self.ren[0].ResetCamera()

    def XZView(self):
        camera = vtk.vtkCamera()
        camera.ParallelProjectionOn()
        camera.Elevation(45)
        camera.OrthogonalizeViewUp()
        camera.Elevation(45)
        self.ren[0].SetActiveCamera(camera)
        self.ren[1].SetActiveCamera(camera)
        self.ren[0].ResetCamera()

    def YZView(self):
        camera = vtk.vtkCamera()
        camera.ParallelProjectionOn()
        camera.Azimuth(90)
        self.ren[0].SetActiveCamera(camera)
        self.ren[1].SetActiveCamera(camera)
        self.ren[0].ResetCamera()

    def SetColor(self,start,end):
        colorFunc = vtk.vtkColorTransferFunction()
        colorFunc.AddRGBPoint(start,0,0,0)
        colorFunc.AddRGBPoint(end, 1, 1, 1)
        self.volume.GetProperty().SetColor(colorFunc)
        self.ren[0].GetRenderWindow().Render()

    def TogglePlaneMode(self, arg):
        self.planeMode = arg
        if arg:
            self.ren[0].RemoveVolume(self.volume)
            sz = self.importData.GetDimensions()
            if sz[0] == 0 or sz[1] == 0 or sz[2] == 0:
                print('empty import data')
                return
            self.planeWidgetZ.DisplayTextOn()
            self.planeWidgetZ.SetInputData(self.importData)
            self.planeWidgetZ.SetPlaneOrientationToZAxes()
            self.planeWidgetZ.RestrictPlaneToVolumeOn()
            self.planeWidgetZ.SetResliceInterpolateToLinear()
            self.planeWidgetZ.SetSliceIndex(0)
            self.planeWidgetZ.SetPicker(self.picker)
            self.planeWidgetZ.SetKeyPressActivationValue("z")
            self.planeWidgetZ.SetInteractor(self.GetRenderWindow().GetInteractor())
            prop2 = self.planeWidgetZ.GetPlaneProperty()
            prop2.SetColor(0, 0, 1)
            #self.planeWidgetZ.SetCurrentRenderer(self.ren[i])
            self.planeWidgetZ.On()
            self.sliderRep.SetMaximumValue(sz[2])
            #self.sliderWidget.SetCurrentRenderer(self.ren[i])
            self.sliderWidget.EnabledOn()
        else:
            sz = self.importData.GetDimensions()
            if sz[0] == 0 or sz[1] == 0 or sz[2] == 0:
                pass
            else:
                self.planeWidgetZ.Off()
            self.sliderWidget.EnabledOff()
            self.ren[0].AddVolume(self.volume)

    def Draw3DLine(self):
        eventPos = self.iren.GetEventPosition()
        picker = vtk.vtkWorldPointPicker()
        picker.Pick(eventPos[0],eventPos[1],0,self.ren[0])
        globalPos = picker.GetPickPosition()
        coneSource = vtk.vtkConeSource()
        coneSource.SetCenter(globalPos)
        coneMapper = vtk.vtkPolyDataMapper()
        coneMapper.SetInputConnection(coneSource.GetOutputPort())
        self.testActor = vtk.vtkActor()
        self.testActor.SetMapper(coneMapper)
        self.testActor.GetProperty().SetColor(1,0,0)
        self.ren[1].AddActor(self.testActor)



