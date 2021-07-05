try:
    import openalea.lpy.gui.py2exe_release
    py2exe_release = True
except:
    py2exe_release = False

import typing
from PyQt5 import QtCore
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow, QMenu, QWidget
from .abstractobjectmanager import AbstractObjectManager

from openalea.plantgl.gui.qt.QtCore import QObject, pyqtSignal
from openalea.plantgl.gui.qt.QtWidgets import QApplication, QCheckBox, QDialog, QHBoxLayout, QLayout, QMenuBar, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout
from openalea.plantgl.gui.qt.QtCore import Qt

import typing

BASE_DIALOG_SIZE = QSize(300, 400)
CONTENT_SPACING = 2

class ObjectEditorDialog(QMainWindow):
    """the class that will create dialog between the panel and the editor window"""
    valueChanged = pyqtSignal()
    thumbnailChanged = pyqtSignal(QPixmap)

    ## this is unused, and might not be used actually. Left for compatibility purposes
    ## (meaning: I was tired to find where this was used and remove the calls.)
    hidden = pyqtSignal()
    AutomaticUpdate = pyqtSignal(bool)

    isValueChanged: bool = False
    isAutomaticUpdate: bool = False
    _menubar: QMenuBar = None
    objectView: QWidget = None

    def __init__(self, parent: typing.Optional[QWidget], flags: typing.Union[QtCore.Qt.WindowFlags, QtCore.Qt.WindowType]) -> None:
        super().__init__(parent=parent, flags=flags)

        """during the init of the dialog we have to know the editor we want to open, the typ variable will allow us to know that"""
        self.isValueChanged = False
        self.isAutomaticUpdate = False

    def setupUi(self,editor, manager: AbstractObjectManager):
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
        # 
        self.mainWidget = QWidget(self)
        self.setCentralWidget(self.mainWidget)

        self.verticalLayout = QVBoxLayout(self.mainWidget)
        self.verticalLayout.setSpacing(CONTENT_SPACING)
        # self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.verticalLayout.setObjectName("verticalLayout")

        self._menubar = QMenuBar(self)
        try:
            self._menubar.setNativeMenuBar(False)
        except: pass

        self.verticalLayout.setMenuBar(self._menubar)

        self.objectView = editor
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
      
        ## button connection
        # self.cancelButton.pressed.connect(self.reject)
        # self.okButton.pressed.connect(self.__ok)
        # self.applyButton.pressed.connect(self.__apply)
        self.screenshotButton.pressed.connect(self.__screenshot)
        # self.autoUpdateCheckBox.toggled.connect(self.setAutomaticUpdate)
        # self.objectView.valueChanged.connect(self.__valueChanged)
        
    def menubar(self) -> QMenuBar:
        return self._menubar

    def __screenshot(self):
        qpixmap = self.manager.getPixmapThumbnail(self.objectView)
        self.thumbnailChanged.emit(qpixmap)
