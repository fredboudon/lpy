from openalea.plantgl.gui.curve2deditor import Curve2DEditor,FuncConstraint
from curve2dmanager import displayLineAsThumbnail
class FunctionManager(AbstractPglObjectManager):
    """see the doc of the objectmanager abtsract class to undesrtand the implementation of the functions"""
    def __init__(self):
        AbstractPglObjectManager.__init__(self,"Function")
        
    def createDefaultObject(self):
        return FuncConstraint.defaultCurve()
