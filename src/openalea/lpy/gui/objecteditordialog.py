try:
    import openalea.lpy.gui.py2exe_release
    py2exe_release = True
except:
    py2exe_release = False

import typing
from PyQt5 import QtCore
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtWidgets import QDial, QMainWindow, QMenu, QOpenGLWidget, QWidget
from .abstractobjectmanager import AbstractObjectManager

from openalea.plantgl.gui.qt.QtCore import QObject, pyqtSignal
from openalea.plantgl.gui.qt.QtWidgets import QApplication, QCheckBox, QDialog, QHBoxLayout, QLayout, QMenuBar, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout
from openalea.plantgl.gui.qt.QtCore import Qt

from openalea.plantgl.algo._pglalgo import GLRenderer, Discretizer

from openalea.plantgl.gui.qt.QtOpenGL import QGLWidget 


import typing

BASE_DIALOG_SIZE = QSize(300, 400)
CONTENT_SPACING = 2

class ObjectEditorDialog(QDialog):
    """the class that will create dialog between the panel and the editor window"""
    valueChanged = pyqtSignal(object)
    thumbnailChanged = pyqtSignal(QPixmap)

    ## this is unused, and might not be used actually. Left for compatibility purposes
    ## (meaning: I was tired to find where this was used and remove the calls.)
    hidden = pyqtSignal()
    AutomaticUpdate = pyqtSignal(bool)

    isValueChanged: bool = False
    isAutomaticUpdate: bool = False
    _menubar: QMenuBar = None
    objectView: QGLWidget = None

    def __init__(self, parent: typing.Optional[QWidget], flags: typing.Union[QtCore.Qt.WindowFlags, QtCore.Qt.WindowType]) -> None:
        super().__init__(parent=parent, flags=flags)
        """during the init of the dialog we have to know the editor we want to open, the typ variable will allow us to know that"""

    def getEditor(self):
        return self.objectView
    
    def setupUi(self, manager: AbstractObjectManager):
        self.setObjectName("Main Windows Object Dialog")
        self.setBaseSize(BASE_DIALOG_SIZE)
        self.manager: AbstractObjectManager = manager

        # hierarchy : 
        # vertical layout : 
        #   - objectView (editor), 
        #   - horizontalLayout:
        #       - autoUpdateCheckBox
        #       - okButton
        #       - screenshotButton
        #       - applyButton
        #       - cancelButton
        
        ## this is used if you define this class as child of QMainWindow class.
        self.mainWidget = QWidget(self)
        # OpenGL object
        # self.mainWidget.discretizer = Discretizer()
        # self.mainWidget.renderer = GLRenderer(self.mainWidget.discretizer)
        # self.setCentralWidget(self.mainWidget)

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setSpacing(CONTENT_SPACING)
        self.verticalLayout.setObjectName("verticalLayout")

        self._menubar = QMenuBar(self)
        try:
            self._menubar.setNativeMenuBar(False)
        except: pass

        self.verticalLayout.setMenuBar(self._menubar)

        self.objectView = self.manager.getEditor(self) # this CREATES a new editor!!
        

        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(5)
        #sizePolicy.setHeightForWidth(self.objectView.sizePolicy().hasHeightForWidth())
        self.objectView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.objectView.setObjectName("objectView")

        self.verticalLayout.addWidget(self.objectView)


        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("the horizontal layout")
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.autoUpdateCheckBox = QCheckBox(self)
        self.autoUpdateCheckBox.setObjectName("autoUpdateCheckBox")
        self.horizontalLayout.addWidget(self.autoUpdateCheckBox)
        self.horizontalLayout.setAlignment(self.autoUpdateCheckBox, Qt.AlignLeft)

        self.okButton = QPushButton(self)
        self.okButton.setObjectName("okButton")
        self.okButton.setDefault(True)
        self.horizontalLayout.addWidget(self.okButton)
        self.horizontalLayout.setAlignment(self.okButton, Qt.AlignRight)

        self.screenshotButton = QPushButton(self)
        self.screenshotButton.setObjectName("screenshotButton")
        self.horizontalLayout.addWidget(self.screenshotButton)

        self.applyButton = QPushButton(self)
        self.applyButton.setObjectName("applyButton")
        self.horizontalLayout.addWidget(self.applyButton)

        self.cancelButton = QPushButton(self)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout.addWidget(self.cancelButton)

        
        
        # button texts
        self.setWindowTitle("ObjectDialog")
        self.autoUpdateCheckBox.setText("Auto update")
        self.okButton.setText("Ok")
        self.applyButton.setText("Apply")
        self.cancelButton.setText("Cancel")
        self.screenshotButton.setText("Screenshot")
      
        # button connection
        self.cancelButton.pressed.connect(self.__reject)
        self.okButton.pressed.connect(self.__ok)
        self.applyButton.pressed.connect(self.__apply)
        self.screenshotButton.pressed.connect(self.__screenshot)
        self.autoUpdateCheckBox.toggled.connect(self.setAutomaticUpdate)
        self.objectView.valueChanged.connect(self.__valueChanged)

        self.manager.fillEditorMenu(self.menubar(), self.objectView)

    def __updateThumbail(self):
        qpixmap = self.manager.getPixmapThumbnail(self.objectView)
        self.thumbnailChanged.emit(qpixmap)
    
    def __valueChanged(self):
        if self.isAutomaticUpdate:
            self.__apply()
        else:
            self.isValueChanged = True

    def __apply(self):
        item = self.manager.retrieveObjectFromEditor(self.objectView)
        print(item)
        self.valueChanged.emit(item)
        self.__updateThumbail()
        self.isValueChanged = False
        
    def __ok(self):
        self.__apply()
        self.close()
        self.deleteLater()

    def __reject(self):
        self.close()
        self.deleteLater()

    def setAutomaticUpdate(self,value):
        """setAutomaticUpdate: checking the autoupdate box will make the QDialog send a 'valueChanged()' signal each time it recieve the same Signal from the objectView"""
        if self.isAutomaticUpdate != value:
            self.isAutomaticUpdate = value
            self.applyButton.setEnabled(not self.isAutomaticUpdate)
            self.AutomaticUpdate.emit(value)
            if self.isAutomaticUpdate and self.isValueChanged :
                self.__apply()

        
    def menubar(self) -> QMenuBar:
        return self._menubar

    def __screenshot(self):
        qpixmap = self.manager.getPixmapThumbnail(self.objectView)
        self.thumbnailChanged.emit(qpixmap)

    def getThumbnail(self) -> QPixmap:
        qpixmap = self.manager.getPixmapThumbnail(self.objectView)
        return qpixmap
    
    def getLpyResource(self) -> object:
        item = self.manager.retrieveObjectFromEditor(self.objectView)
        return item