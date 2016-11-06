# -*- coding: utf-8 -*-
###################################################################################
#
#  SheetMetalCmd.py
#  
#  Copyright 2015 Shai Seger <shaise at gmail dot com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
###################################################################################

#from FreeCAD import Gui
import FreeCAD#, FreeCADGui, Part
from SheetMetalCommon import *
from SheetMetalFeature import *
from SheetMetalViewProvider import *
from SheetMetalCommon import *



class SMBendWall(SMFeature):
  def __init__(self, obj):
    '''"Add Wall with radius bend" '''
    SMFeature.__init__(self, obj)
    
    obj.addProperty("App::PropertyLength","radius","Parameters","Bend Radius").radius = 1.0
    obj.addProperty("App::PropertyLength","length","Parameters","Length of wall").length = 10.0
    obj.addProperty("App::PropertyLength","gap1","Parameters","Gap from left side").gap1 = 0.0
    obj.addProperty("App::PropertyLength","gap2","Parameters","Gap from right side").gap2 = 0.0
    obj.addProperty("App::PropertyAngle","angle","Parameters","Bend angle").angle = 90.0
    obj.addProperty("App::PropertyLength","reliefw","Parameters","Relief width").reliefw = 0.5
    obj.addProperty("App::PropertyLength","reliefd","Parameters","Relief depth").reliefd = 1.0
    
 
  def execute(self, fp):
    '''"Print a short message when doing a recomputation, this method is mandatory" '''
    prop = SMSelProperties(fp.baseObject[0], fp.baseObject[1][0])
    s = smBend(bendR = fp.radius.Value, bendA = fp.angle.Value, extLen = fp.length.Value, 
                gap1 = fp.gap1.Value, gap2 = fp.gap2.Value, reliefW = fp.reliefw.Value, reliefD = fp.reliefd.Value,
                qs = prop)
    fp.Shape = s


class SMBendWallViewProvider(SMViewProvider):
  def getIcon(self):
    return self.getIconPath() + 'AddWall.svg'


class AddWallCommandClass():
  """Add Wall command"""

  def GetResources(self):
    return {'Pixmap'  : SMViewProvider.getIconPath() + 'AddWall.svg' , # the name of a svg file available in the resources
            'MenuText': "Make Wall" ,
            'ToolTip' : "Extends a wall from a side face of metal sheet"}
 
  def Activated(self):
    doc = FreeCAD.ActiveDocument
    doc.openTransaction("Bend")
    a = SMFeature.GetPythonObj("Bend")  
    SMBendWall(a)
    SMBendWallViewProvider(a.ViewObject)
    doc.recompute()
    doc.commitTransaction()
    return
   
  def IsActive(self):
    if len(Gui.Selection.getSelection()) != 1 or len(Gui.Selection.getSelectionEx()[0].SubElementNames) != 1:
      return False
    return SMSelProperties.checkSelection()

Gui.addCommand('SMMakeWall',AddWallCommandClass())

###########################################################################################
# Extrude
###########################################################################################



  
class SMExtrudeWall(SMFeature):
  def __init__(self, obj):
    '''"Add Wall with radius bend" '''
    SMFeature.__init__(self, obj)
    
    obj.addProperty("App::PropertyLength","length","Parameters","Length of wall").length = 10.0
    obj.addProperty("App::PropertyDistance","gap1","Parameters","Gap from left side").gap1 = 0.0
    obj.addProperty("App::PropertyDistance","gap2","Parameters","Gap from right side").gap2 = 0.0

  def execute(self, fp):
    #s = smExtrude(extLength = fp.length.Value, selFaceNames = self.selFaceNames, selObjectName = self.selObjectName)
    prop = SMSelProperties(fp.baseObject[0], fp.baseObject[1][0])
    s = smBend(bendA = 0.0,  extLen = fp.length.Value, gap1 = fp.gap1.Value, gap2 = fp.gap2.Value, reliefW = 0.0,
                qs = prop)
    fp.Shape = s
    
class SMExtrudeWallViewProvider(SMViewProvider):
  def getIcon(self):
    return self.getIconPath() + "SMExtrude.svg"
    

class SMExtrudeCommandClass():
  """Extrude face"""

  def GetResources(self):
    return {'Pixmap'  : SMViewProvider.getIconPath() + 'SMExtrude.svg', # the name of a svg file available in the resources
            'MenuText': "Extrude Face" ,
            'ToolTip' : "Extrude a face along normal"}
 
  def Activated(self):
    doc = FreeCAD.ActiveDocument
    doc.openTransaction("Extrude")
    a = SMFeature.GetPythonObj("Extrude")
    SMExtrudeWall(a)
    SMExtrudeWallViewProvider(a.ViewObject)
    doc.recompute()
    doc.commitTransaction()
    return
   
  def IsActive(self):
    if len(Gui.Selection.getSelection()) < 1 or len(Gui.Selection.getSelectionEx()[0].SubElementNames) < 1:
      return False
    return SMSelProperties.checkSelection()

Gui.addCommand('SMExtrudeFace',SMExtrudeCommandClass())
