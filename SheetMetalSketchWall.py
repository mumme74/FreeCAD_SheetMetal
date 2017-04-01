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

import FreeCAD, Part
from FreeCAD import Gui
from SheetMetalFeature import *
from SheetMetalViewProvider import *
from SheetMetalCommon import *

  

class SMBendWall(SMFeature):
  def __init__(self, obj):
    '''"Add Wall based on sketch with radius bend" '''
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
    wall = SMWall(bendR = fp.radius.Value, bendA = fp.angle.Value, extLen = fp.length.Value, 
               gap1 = fp.gap1.Value, gap2 = fp.gap2.Value, reliefW = fp.reliefw.Value, reliefD = fp.reliefd.Value,
               fp = fp)
    wall.hinge()
    wall.addSketchNormalToPlane()
    fp.Shape = wall.finish()


class SMSketchWallViewProvider(SMViewProvider):
  def getIcon(self):
    return self.getIconPath() + "SMAddSketchWall.svg"


class SMSketchWallCommandClass():
  """Sketch object"""

  def GetResources(self):
    __dir__ = os.path.dirname(__file__)
    iconPath = os.path.join( __dir__, 'Resources', 'icons' )
    return {'Pixmap'  : os.path.join( iconPath , 'SMAddSketchWall.svg') , # the name of a svg file available in the resources
            'MenuText': "Sketch wall" ,
            'ToolTip' : "Add sketched extrusion folded sheet metal object"}
 
  def Activated(self):
    doc = FreeCAD.ActiveDocument
    doc.openTransaction("SketchWall")
    a = SMFeature.GetPythonObj("SketchWall")
    SMBendWall(a)
    SMSketchWallViewProvider(a.ViewObject)
    doc.recompute()
    doc.commitTransaction()
    return
   
  def IsActive(self):
    if len(Gui.Selection.getSelection()) != 1 or len(Gui.Selection.getSelectionEx()[0].SubElementNames) != 1:
      return False
    return SMSelProperties.checkSelection()

Gui.addCommand('SMSketchWall',SMSketchWallCommandClass())

