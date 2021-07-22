from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QDialog, QSplitter, QTreeWidget
from openalea.plantgl.all import *
from openalea.plantgl.gui import qt
from OpenGL.GL import *
from OpenGL.GLU import *
import sys, traceback, os
from math import sin, pi

from openalea.lpy.gui.treecontroller import TreeController

from .abstractobjectmanager import AbstractObjectManager

from .objectmanagers import get_managers
from openalea.plantgl.gui.qt import QtCore, QtGui, QtWidgets
from openalea.plantgl.gui.qt.QtCore import QObject, QPoint, Qt, pyqtSignal, pyqtSlot, QT_VERSION_STR
from openalea.plantgl.gui.qt.QtGui import QFont, QFontMetrics, QImageWriter, QColor, QPainter, QPixmap
from openalea.plantgl.gui.qt.QtWidgets import QAbstractItemView, QAction, QApplication, QDockWidget, QFileDialog, QLineEdit, QMenu, QMessageBox, QScrollArea, QVBoxLayout, QWidget, QLabel, QListView, QListWidget, QListWidgetItem, QSizePolicy

SCROLL_SINGLE_STEP = 5

from .objectpanelcommon import TriggerParamFunc, retrieveidinname, retrievemaxidname, retrievebasename

        
from .objectdialog import ObjectDialog

class ManagerDialogContainer (QObject):
    def __init__(self,panel,manager):
        QObject.__init__(self)
        self.panel = panel
        self.manager = manager
        self.editor   =  None
        self.editorDialog   =  None
        self.editedobjectid = None

    def __transmit_valueChanged__(self):
        self.panel.retrieveObject(self)
        
    def __transmit_autoUpdate__(self,enabled):
        self.panel.transmit_autoUpdate(enabled)
        
    def init(self):
        if not self.editor:
            self.editorDialog = ObjectDialog(self.panel)
            self.editor = self.manager.getEditor(self.editorDialog)
            if not self.editor: return
            self.editorDialog.setupUi(self.editor, self.manager)
            self.editorDialog.setWindowTitle(self.manager.typename+' Editor')
            self.manager.fillEditorMenu(self.editorDialog.menu(),self.editor)
            self.editorDialog.valueChanged.connect(self.__transmit_valueChanged__)
            self.editorDialog.hidden.connect(self.endEditionEvent)
            self.editorDialog.AutomaticUpdate.connect(self.__transmit_autoUpdate__)
            
    def startObjectEdition(self,obj,id):
        """ used by panel. ask for object edition to start. Use getEditor and  setObjectToEditor """
        self.editedobjectid = id
        if not self.editor:
            self.init()
            if not self.editor:
                QMessageBox.warning(self.panel,"Cannot edit","Cannot edit object ! Python module (PyQGLViewer) is certainly missing!")
                return
        self.manager.setObjectToEditor(self.editor,obj)
        self.editorDialog.setWindowTitle(self.manager.typename+' Editor - '+self.manager.getName(obj))
        self.editorDialog.hasChanged = False
        self.editorDialog.show()
        self.editorDialog.activateWindow()
        self.editorDialog.raise_()


    def endObjectEdition(self):
        if self.editor:
            self.editorDialog.hide()
        
    def getEditedObject(self):
        """ used by panel. ask for object edition to start. Use getEditor and  setObjectToEditor """
        if not self.editedobjectid is None:
            return self.manager.retrieveObjectFromEditor(self.editor),self.editedobjectid
        else:
            return None, None

    def endEditionEvent(self):
        """ called when closing editor. """
        self.editedobjectid = None
    
    def isVisible(self):
        """ Tell whether editor is visible """
        return (not (self.editorDialog is None)) and self.editorDialog.isVisible()


class DockerMover:
    def __init__(self, mainwindow, position, panel):
        self.mainwindow = mainwindow
        self.panel = panel
        self.position = position
    def __call__(self):
        if self.position == 'Floating':
            if not self.panel.isFloating():
                self.panel.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable)
                self.panel.setFloating(True)
        else:
            self.panel.setFeatures(QDockWidget.DockWidgetClosable)
            self.panel.setFloating(False)
            if self.mainwindow.dockWidgetArea(self.panel) != self.position:
                visibilitycheck = self.mainwindow.isVisible()
                parentdock = [dock for dock in self.mainwindow.findChildren(QDockWidget) if dock != self.panel and (not visibilitycheck or not dock.isHidden()) and self.mainwindow.dockWidgetArea(dock) == self.position]
                self.mainwindow.addDockWidget(self.position, self.panel)
                #print([p.windowTitle() for p in parentdock])
                if len(parentdock) > 0:
                    self.mainwindow.tabifyDockWidget(parentdock[0], self.panel)

# the Manager stores all Object Panels and clipboard
class ObjectPanelManager(QObject):
    def __init__(self,parent):
        QObject.__init__(self,parent)
        self.parent = parent
        self.vparameterView = self.parent.vparameterView        
        self.panels  = []
        self.unusedpanels = []
        self.vparameterView.addAction("New Panel",self.createNewPanel)
        self.vparameterView.addSeparator()
        self.clipboard = None
    def setClipboard(self,obj):
        self.clipboard = obj
    def getClipboard(self):
        obj = self.clipboard
        self.clipboard = None
        return obj
    def hasClipboard(self):
        return not self.clipboard is None
    def getObjectPanels(self):
        return self.panels
    def getMaxObjectPanelNb(self):
        return len(self.panels)+len(self.unusedpanels)
    def setObjectPanelNb(self,nb, new_visible = True):
        nbpanel = len(self.panels)
        if nb < nbpanel:
            newunusedpanels = self.panels[nb:]
            self.unusedpanels = [(panel,panel.isVisible()) for panel in newunusedpanels]+self.unusedpanels
            self.panels = self.panels[:nb]
            for panel in newunusedpanels:
                panel.hide()
                self.vparameterView.removeAction(panel.toggleViewAction())
        else:
            nbtoadd = nb - nbpanel
            nbunusedpanels = len(self.unusedpanels)
            nbreused = min(nbtoadd,nbunusedpanels)
            if nbreused > 0:
                for i in range(nbreused):
                    npanel,visible = self.unusedpanels.pop(0)
                    self.panels.append(npanel)
                    if visible:
                        npanel.show()
                    self.vparameterView.addAction(npanel.toggleViewAction())
            if nbtoadd-nbunusedpanels > 0:
                for i in range(nbtoadd-nbunusedpanels):
                    npanel = LpyObjectPanelDock(self.parent,"Panel "+str(i+nbpanel+nbunusedpanels),self)
                    npanel.setStatusBar(self.parent.statusBar())
                    npanel.valueChanged.connect(self.parent.projectEdited)
                    npanel.valueChanged.connect(self.parent.projectParameterEdited)
                    npanel.AutomaticUpdate.connect(self.parent.projectAutoRun)
                    npanel.setFeatures(QDockWidget.DockWidgetClosable)
                    self.panels.append(npanel)
                    DockerMover(self.parent, Qt.BottomDockWidgetArea, npanel)()
                    #self.parent.addDockWidget(Qt.BottomDockWidgetArea,npanel)
                    self.vparameterView.addAction(npanel.toggleViewAction())
                    if new_visible:
                        npanel.show()
                    #self.restoreDockWidget(npanel)
    def completeMenu(self,menu,panel):
        panelmenu = QMenu("Panel",menu)
        menu.addSeparator()
        menu.addMenu(panelmenu)
        panelAction = QAction('Rename',panelmenu)
        panelAction.triggered.connect(panel.rename)
        panelmenu.addAction(panelAction)
        panelAction = QAction('Delete',panelmenu)
        panelAction.triggered.connect(TriggerParamFunc(self.deletePanel,panel))
        panelmenu.addAction(panelAction)
        panelAction = QAction('New',panelmenu)
        panelAction.triggered.connect(TriggerParamFunc(self.createNewPanel,panel))
        panelmenu.addAction(panelAction)
        panelAction = QAction('Duplicate',panelmenu)
        panelAction.triggered.connect(TriggerParamFunc(self.duplicatePanel,panel))
        panelmenu.addAction(panelAction)
        panelAction = QAction('Disable' if panel.view.isActive() else 'Enable',panelmenu)
        panelAction.triggered.connect(TriggerParamFunc(panel.view.setActive,not panel.view.isActive()))
        panelmenu.addAction(panelAction)

        subpanelmenu = QMenu("Theme",menu)
        panelmenu.addSeparator()
        panelmenu.addMenu(subpanelmenu)

        # disable themes
        """"
        for themename,value in ObjectListDisplay.THEMES.items():
            panelAction = QAction(themename,subpanelmenu)
            panelAction.triggered.connect(TriggerParamFunc(panel.view.applyTheme,value))
            subpanelmenu.addAction(panelAction)
        """

        subpanelmenu = QMenu("Move To",menu)
        panelmenu.addSeparator()
        panelmenu.addMenu(subpanelmenu)

        for position, flag in [('Bottom', Qt.BottomDockWidgetArea), ('Left', Qt.LeftDockWidgetArea), ('Right', Qt.RightDockWidgetArea), ('Top', Qt.TopDockWidgetArea), ('Floating', 'Floating')]:
            panelAction = QAction(position,subpanelmenu)
            panelAction.triggered.connect(DockerMover(self.parent.window(),flag, panel))
            subpanelmenu.addAction(panelAction)
            
        return panelmenu
    def createNewPanel(self,above = None):
        nb = len(self.panels)+1
        self.setObjectPanelNb(nb)
        npanel = self.panels[-1]
        npanel.setObjects([])
        npanel.show()
        npanel.setName(self.computeNewPanelName('Panel'))
        if not above is None:
            self.parent.tabifyDockWidget(above,npanel)

    def duplicatePanel(self,source):
        nb = len(self.panels)+1
        self.setObjectPanelNb(nb)
        npanel = self.panels[-1]
        npanel.setObjects(source.getObjectsCopy())
        npanel.show()
        npanel.setName(self.computeNewPanelName(source.name))
        self.parent.tabifyDockWidget(source,npanel)
        source.setActive(False)
    def getPanel(self,panelname):
        for panel in self.panels:
            if panel.name == panelname:
                return panel
    def deletePanel(self,panel):
        self.panels.pop( self.panels.index(panel) )
        panel.hide()
        self.vparameterView.removeAction(panel.toggleViewAction())
        self.parent.projectEdited()
    def computeNewPanelName(self,basename):
        bn = retrievebasename(basename)
        mid = retrievemaxidname([panel.name for panel in self.panels],bn)
        if not mid is None:
            return bn+' '+str(mid+1)
        return bn

from .treeview import TreeView
from .listview import ListView

class LpyObjectPanelDock (QDockWidget):
    valueChanged = pyqtSignal(bool)
    AutomaticUpdate = pyqtSignal()
    model: QStandardItemModel = None

    def __init__(self,parent,name,panelmanager = None):    
        QDockWidget.__init__(self,parent)
        self.panelmanager = panelmanager
        self.setObjectName(name.replace(' ','_'))
        self.setName(name)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(name+"DockWidgetContents")
        self.verticalLayout = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName(name+"verticalLayout")
        
        self.objectpanel = QScrollArea(self.dockWidgetContents)
        self.splitter: QSplitter = QSplitter(self)

        self.model: QStandardItemModel = QStandardItemModel( 0, 1, self)
        self.store: dict[object] = {}
        self.controller = TreeController(model=self.model, store=self.store)
        self.treeView = TreeView(self, panelmanager, self.controller)
        self.listView = ListView(self, panelmanager, self.controller)
        
        self.treeView.selectedIndexChanged.connect(self.listView.setRootIndex)


        self.splitter.dock = self

        self.splitter.addWidget(self.treeView)
        self.splitter.addWidget(self.listView)

        self.objectpanel.setWidget(self.splitter)
        self.objectpanel.setWidgetResizable(True)
        self.objectpanel.setObjectName(name+"panelarea")
        
        self.verticalLayout.addWidget(self.objectpanel)
        self.objectNameEdit = QLineEdit(self.dockWidgetContents)
        self.objectNameEdit.setObjectName(name+"NameEdit")
        self.verticalLayout.addWidget(self.objectNameEdit)        
        self.objectNameEdit.hide()
        self.setWidget(self.dockWidgetContents)
        
        self.treeView.valueChanged.connect(self.__updateStatus)
        self.treeView.AutomaticUpdate.connect(self.__transmit_autoupdate)
        # self.treeView.itemSelectionChanged.connect(self.endNameEditing)
        self.treeView.renameRequest.connect(self.displayName)

        self.objectNameEdit.editingFinished.connect(self.updateName)
        self.dockNameEdition = False
        self.nameEditorAutoHide = True
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self,event):
        event.acceptProposedAction()

    def dropEvent(self,event):
        if event.mimeData().hasUrls() :
            self.fileDropEvent(str(event.mimeData().urls()[0].toLocalFile()))

    def fileDropEvent(self,fname):
        for manager in self.treeView.managers.values():
            if manager.canImportData(fname):
                objects = manager.importData(fname)
                self.treeView.appendObjects([(manager,i) for i in objects])    
                self.showMessage('import '+str(len(objects))+" object(s) from '"+fname+"'.",5000)
                return

    def endNameEditing(self,id):
        if id != -1 and self.objectNameEdit.isVisible():
            self.displayName(-1)
    
    def displayName(self,id):
        if id == -1:
            self.objectNameEdit.clear()
            if self.nameEditorAutoHide : 
                self.objectNameEdit.hide()
        else:
            if self.nameEditorAutoHide : 
                self.objectNameEdit.show()
            self.objectNameEdit.setText(self.treeView.getSelectedObjectName())
            self.objectNameEdit.setFocus()

    def updateName(self):
        if not self.dockNameEdition :
            if self.treeView.hasSelection():
                self.treeView.setSelectedObjectName(str(self.objectNameEdit.text()))
                self.treeView.doUpdate()
                if self.nameEditorAutoHide : 
                    self.objectNameEdit.hide()
        else :
            self.setName(self.objectNameEdit.text())
            if self.nameEditorAutoHide : 
                self.objectNameEdit.hide()            
            self.dockNameEdition = False
        
    def setObjects(self,objects) -> None:
        self.treeView.setObjects(objects)

    def appendObjects(self,objects) -> None:
        self.treeView.appendObjects(objects)

    def getObjects(self) -> list:
        return self.treeView.getObjects()

    def getObjectsCopy(self) -> list:
        return self.treeView.getObjectsCopy()

    def setStatusBar(self,st):
        self.objectpanel.statusBar = st
        self.splitter.statusBar = st

    def showMessage(self,msg,timeout):
        if hasattr(self,'statusBar'):
            self.statusBar.showMessage(msg,timeout)
        else:
            print(msg)    
    def __updateStatus(self, i=None):

        if not i is None and 0 <= i < self.treeView.count() and self.treeView.item(i).getManager().managePrimitive():
            self.valueChanged.emit(True)
        else:
            self.valueChanged.emit(False)

    def __transmit_autoupdate(self):
        self.AutomaticUpdate.emit()
        
    def setName(self,name):
        self.name = name
        self.setWindowTitle(name)
        
    def rename(self):
        self.dockNameEdition = True
        if self.nameEditorAutoHide : 
            self.objectNameEdit.show()
        self.objectNameEdit.setText(self.name)
        self.objectNameEdit.setFocus()
    
    def getInfo(self):
        visibility = True
        if not self.isVisible() :
            if self.parent().isVisible() :
                visibility = False
            else:
                visibility = getattr(self,'previousVisibility',True)
        return {'name':str(self.name),'active':bool(self.splitter.isActive()),'visible':visibility }
        
    def setInfo(self,info):
        self.setName(info['name'])
        if 'active' in info:
            self.treeView.setActive(info['active'])        
        if 'visible' in info:
            self.previousVisibility = info['visible']
            self.setVisible(info['visible'])

def main():
    import pprint
    qapp = QApplication([])
    m = LpyObjectPanelDock(None,'TestPanel')
    m.controller.createExampleObjects()
    # pp = pprint.PrettyPrinter(indent=2)
    # pp.pprint(m.objectpanel.getObjects())
    m.show()
    qapp.exec_()

if __name__ == '__main__':
    main()
