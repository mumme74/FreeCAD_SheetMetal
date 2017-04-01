#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2016 - Fredrik Johansson <mumme74@github.com>           *  
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

import FreeCAD
from FreeCAD import Gui

def smWarnDialog(msg):
    diag = QtGui.QMessageBox(QtGui.QMessageBox.Warning, 'Error in macro MessageBox', msg)
    diag.setWindowModality(QtCore.Qt.ApplicationModal)
    diag.exec_()
    
def smBelongToBody(item, body):
    if (body == None):
        return False
    for obj in body.Group:
        if obj.Name == item.Name:
            return True
    return False
    
def smIsPartDesign(obj):
    return str(obj).find("<PartDesign::") == 0
        
def smIsOperationLegal(body, selobj):
    #FreeCAD.Console.PrintLog(str(selobj) + " " + str(body) + " " + str(smBelongToBody(selobj, body)) + "\n")
    if smIsPartDesign(selobj) and not smBelongToBody(selobj, body):
        smWarnDialog("The selected geometry does not belong to the active Body.\nPlease make the container of this item active by\ndouble clicking on it.")
        return False
    return True   
    
    

class SMFeature(object):
  def __init__(self, featureObj):
    featureObj.Proxy = self
    
  @staticmethod
  def GetPythonObj(name):
    '''Returns a FreeCAD PartDesign feature'''
    view = Gui.ActiveDocument.ActiveView
    activeBody = None
    selobj = Gui.Selection.getSelectionEx()[0].Object
    if hasattr(view,'getActiveObject'):
      activeBody = view.getActiveObject('pdbody')
    if not smIsOperationLegal(activeBody, selobj):
        return
    isPartDesign = not (activeBody == None or not smIsPartDesign(selobj))
    objType = "Part::FeaturePython" if isPartDesign  else "PartDesign::FeaturePython"
    obj = FreeCAD.activeDocument().addObject(objType, name)
    if isPartDesign and activeBody != None:
      activeBody.addObject(obj)
      
    selected = Gui.Selection.getSelectionEx()
    if len(selected):
      obj.addProperty("App::PropertyLinkSub", "baseObject", "Parameters", "Base object").baseObject = (selected[0].Object, selected[0].SubElementNames)
    
#      # need PartDesign::FeaturePython
#      if isPartDesign:
#        for o in selected[0].Object.InList:
#          if o.TypeId == 'PartDesign::Body':
#            o.addFeature(obj)
#            break
 
    return obj 



