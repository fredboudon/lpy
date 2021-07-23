try:
    import openalea.lpy.gui.py2exe_release
    py2exe_release = True
except:
    py2exe_release = False

from copy import deepcopy
import typing
from PyQt5 import QtCore
from PyQt5.QtCore import QModelIndex, QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtWidgets import QDial, QMainWindow, QMenu, QOpenGLWidget, QWIDGETSIZE_MAX, QWidget
from .abstractobjectmanager import AbstractObjectManager

from openalea.plantgl.gui.qt.QtCore import QObject, pyqtSignal
from openalea.plantgl.gui.qt.QtWidgets import QApplication, QCheckBox, QDialog, QHBoxLayout, QLayout, QMenuBar, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout
from openalea.plantgl.gui.qt.QtCore import Qt

from openalea.plantgl.gui.qt.QtOpenGL import QGLWidget 


import typing
import sys

BASE_DIALOG_SIZE = QSize(300, 400)
CONTENT_SPACING = 2

class ObjectEditorWidget(QWidget):
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

    modelIndex: QModelIndex = None
    mainWidget: QWidget = None

    okButton: QPushButton = None
    cancelButton: QPushButton = None
    resetButton: QPushButton = None

    lpyresourceBackup: object = None

    def __init__(self, parent: typing.Optional[QWidget], manager: AbstractObjectManager) -> None:
        super(ObjectEditorWidget, self).__init__()
        ## this is used if you define this class as child of QMainWindow class.
        self.setObjectName("Main Windows Object Dialog")
        self.setBaseSize(BASE_DIALOG_SIZE)

        # hierarchy : 
        # vertical layout : 
        #   - objectView (editor), 
        #   - horizontalLayout:
        #       - autoUpdateCheckBox
        #       - okButton
        #       - screenshotButton
        #       - applyButton
        #       - cancelButton
        
        self.manager: AbstractObjectManager = manager
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

        self.resetButton = QPushButton(self)
        self.resetButton.setObjectName("resetButton")
        self.horizontalLayout.addWidget(self.resetButton)

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
        self.resetButton.setText("Reset")
      
        # button connection
        self.cancelButton.pressed.connect(self.__reject)
        self.okButton.pressed.connect(self.__ok)
        self.applyButton.pressed.connect(self.__apply)
        self.resetButton.pressed.connect(self.__reset)
        self.autoUpdateCheckBox.toggled.connect(self.setAutomaticUpdate)
        self.objectView.valueChanged.connect(self.__valueChanged)

        self.manager.fillEditorMenu(self.menubar(), self.objectView)

    def setModelIndex(self, index: QModelIndex):
        self.modelIndex = index

    def setObject(self, lpyresource: object):
        self.lpyresourceBackup = deepcopy(lpyresource)
        self.manager.setObjectToEditor(self.getEditor(), lpyresource)

    def __updateThumbail(self):
        qpixmap = self.manager.getPixmapThumbnail(self.objectView)
        self.thumbnailChanged.emit(qpixmap)
    
    def __valueChanged(self):
        if self.isAutomaticUpdate:
            self.__apply()
        else:
            self.isValueChanged = True

    def __apply(self):
        lpyresource = self.manager.retrieveObjectFromEditor(self.objectView)
        self.lpyresourceBackup = deepcopy(lpyresource)
        self.__updateThumbail()
        self.valueChanged.emit(self)
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
            self.resetButton.setEnabled(not self.isAutomaticUpdate)
            self.AutomaticUpdate.emit(value)
            if self.isAutomaticUpdate and self.isValueChanged :
                self.__apply()

        
    def menubar(self) -> QMenuBar:
        return self._menubar

    def __reset(self):
        self.manager.setObjectToEditor(self.getEditor(), self.lpyresourceBackup)
    
    def __screenshot(self):
        qpixmap = self.manager.getPixmapThumbnail(self.objectView)
        self.thumbnailChanged.emit(qpixmap)

    def getThumbnail(self) -> QPixmap:
        qpixmap = self.manager.getPixmapThumbnail(self.objectView)
        return qpixmap
    
    def getLpyResource(self) -> object:
        item = self.manager.retrieveObjectFromEditor(self.objectView)
        return item

    def getEditor(self) -> QWidget:
        return self.objectView