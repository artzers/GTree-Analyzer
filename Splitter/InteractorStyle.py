import vtk

class MyInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, parent=None):
        self.AddObserver("MiddleButtonPressEvent", self.middle_button_press_event)
        self.AddObserver("MiddleButtonReleaseEvent", self.middle_button_release_event)
        self.AddObserver("LeftButtonPressEvent", self.left_button_press_event)
        self.AddObserver("LeftButtonReleaseEvent", self.left_button_release_event)
        self.AddObserver("RightButtonPressEvent", self.right_button_press_event)
        self.AddObserver("RightButtonReleaseEvent", self.right_button_release_event)
        self.AddObserver("MouseMoveEvent",self.mouse_move_event)
        self.AddObserver("CharEvent", self.key_press_event)
        self.doubleClick = 0
        self.drawMode = False

    def SetInteractor(self,iren):
        self.iren = iren

    def SetRenderers(self,renderers):
        self.renderers = renderers

    def key_press_event(self, obj, event):
        #key = self.iren.GetKeySym()
        #print(key, 'was pressed')
        [x,y] = self.iren.GetEventPosition()
        renderer = self.FindPokedRenderer(x,y)
        # if key == 'r':
        #     renderer.ResetCamera()
        # renderer.GetRenderWindow().Render()
        self.OnChar()

    def mouse_move_event(self, obj, event):
        if self.doubleClick != 0:
            self.doubleClick = 0
        self.OnMouseMove()

    def middle_button_press_event(self, obj, event):
        self.OnMiddleButtonDown()
        #return

    def middle_button_release_event(self, obj, event):
        #print("Middle Button released")
        self.OnMiddleButtonUp()
        #return

    def left_button_press_event(self, obj, event):
        self.doubleClick += 1
        self.OnLeftButtonDown()
        #return

    def left_button_release_event(self, obj, event):
        if self.doubleClick == 2:
            print('double click')
            self.doubleClick = 0
        self.OnLeftButtonUp()
        #return

    def right_button_press_event(self, obj, event):
        #print("right Button pressed")
        self.OnRightButtonDown()
        #return

    def right_button_release_event(self, obj, event):
        #print("right Button released")
        self.OnLeftButtonUp()
        #return

