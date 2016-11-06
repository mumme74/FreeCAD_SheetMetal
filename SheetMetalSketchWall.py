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
import FreeCAD, FreeCADGui, Part, os
__dir__ = os.path.dirname(__file__)
iconPath = os.path.join( __dir__, 'Resources', 'icons' )

  
def smMakeFace(edge, dir, from_p, to_p):
    e1 = edge.copy()
    e1.translate(dir * from_p)
    e2 = edge.copy()
    e2.translate(dir * to_p)
    e3 = Part.Line(e1.valueAt(e1.FirstParameter), e2.valueAt(e2.FirstParameter)).toShape()
    e4 = Part.Line(e1.valueAt(e1.LastParameter), e2.valueAt(e2.LastParameter)).toShape()
    w = Part.Wire([e1,e3,e2,e4])
    return Part.Face(w)


def smBend(bendR = 1.0, bendA = 90.0, flipped = False, extLen = 10.0, gap1 = 0.0, gap2 = 0.0, reliefW = 0.5, 
            reliefD = 1.0, selFaceNames = '', MainObject = None):
            
  #AAD = FreeCAD.ActiveDocument
  #MainObject = AAD.getObject( selObjectName )
  
  resultSolid = MainObject.Shape
  for selFaceName in selFaceNames:
    selFace = MainObject.Shape.getElement(selFaceName)
  
    # find the narrow edge
    thk = 999999.0
    for edge in selFace.Edges:
      if abs( edge.Length ) < thk:
        thk = abs( edge.Length )
        thkEdge = edge

    # main corner
    p0 = thkEdge.valueAt(thkEdge.FirstParameter)
    thkDir = thkEdge.valueAt(thkEdge.LastParameter) - thkEdge.valueAt(thkEdge.FirstParameter)
    
    # find a length edge  =  revolve axis direction
    for lenEdge in selFace.Edges:
      lastp = lenEdge.LastParameter
      firstp = lenEdge.FirstParameter
      len = lenEdge.Length
      if lenEdge.isSame(thkEdge):
        continue
      FreeCAD.Console.PrintLog("=>" + str(lastp)+", "+ str(lenEdge.valueAt(firstp)) +", "+ str(lenEdge.valueAt(lastp)) + ", " + str(p0) + "\n")
      if lenEdge.valueAt(firstp) == p0:
        revAxisV = lenEdge.valueAt(lastp) - lenEdge.valueAt(firstp)
        break
      if lenEdge.valueAt(lastp) == p0:
        revAxisV = lenEdge.valueAt(firstp) - lenEdge.valueAt(lastp)
        break
     
    # narrow the wall if we have gaps
    revDir = revAxisV.normalize()
    lgap2 = len - gap2
    if gap1 == 0 and gap2 == 0:
      revFace = selFace
    else:
      revFace = smMakeFace(thkEdge, revDir, gap1, lgap2)
      if (revFace.normalAt(0,0) != selFace.normalAt(0,0)):
        revFace.reverse()
    
    #make sure the direction verctor is correct in respect to the normal
    if thkDir.cross(revAxisV).normalize() == selFace.normalAt(0,0):
      revAxisV = revAxisV * -1
    
    # remove relief if needed
    if reliefW > 0 and reliefD > 0 and (gap1 > 0 or gap2 > 0) :
      thkEdgeW = Part.Line(thkEdge.valueAt(thkEdge.FirstParameter-0.1), thkEdge.valueAt(thkEdge.LastParameter+0.1)).toShape()
      reliefFace = smMakeFace(thkEdgeW, revDir, gap1 - reliefW, gap1)
      reliefFace = reliefFace.fuse(smMakeFace(thkEdgeW, revDir, lgap2, lgap2 + reliefW))
      reliefSolid = reliefFace.extrude(selFace.normalAt(0,0) * reliefD * -1)
      #Part.show(reliefSolid)
      resultSolid = resultSolid.cut(reliefSolid)
   
    #find revolve point
    if not(flipped):
      revAxisP = thkEdge.valueAt(thkEdge.LastParameter + bendR)
      revAxisV = revAxisV * -1
    else:
      revAxisP = thkEdge.valueAt(thkEdge.FirstParameter - bendR)  
    
    # create bend
    wallFace = revFace
    if bendA > 0 :
      bendSolid = revFace.revolve(revAxisP, revAxisV, bendA)
      #Part.show(bendSolid)
      resultSolid = resultSolid.fuse(bendSolid)
      wallFace = revFace.copy()
      wallFace.rotate(revAxisP, revAxisV, bendA)
    
    # create wall
    if extLen > 0 :
      #wallSolid = wallFace.extrude(wallFace.normalAt(0,0) * extLen)
      #resultSolid = resultSolid.fuse(wallSolid)
      
      #create a sketch based on these parameters
      resultSolid = resultSolid
      
  Gui.ActiveDocument.getObject(MainObject.Name).Visibility = False
  return resultSolid
  

class SMBendWall(SMFeature):
  def __init__(self, obj):
    '''"Add Wall based on sketch with radius bend" '''
    SMFeature.__init__(self, obj)
    
    obj.addProperty("App::PropertyLength","radius","Parameters","Bend Radius").radius = 1.0
    obj.addProperty("App::PropertyLength","length","Parameters","Length of wall").length = 10.0
    obj.addProperty("App::PropertyLength","gap1","Parameters","Gap from left side").gap1 = 0.0
    obj.addProperty("App::PropertyLength","gap2","Parameters","Gap from right side").gap2 = 0.0
    obj.addProperty("App::PropertyBool","invert","Parameters","Invert bend direction").invert = False
    obj.addProperty("App::PropertyAngle","angle","Parameters","Bend angle").angle = 90.0
    obj.addProperty("App::PropertyLength","reliefw","Parameters","Relief width").reliefw = 0.5
    obj.addProperty("App::PropertyLength","reliefd","Parameters","Relief depth").reliefd = 1.0
 
  def execute(self, fp):
    '''"Print a short message when doing a recomputation, this method is mandatory" '''
    s = smBend(bendR = fp.radius.Value, bendA = fp.angle.Value,  flipped = fp.invert, extLen = fp.length.Value, 
                gap1 = fp.gap1.Value, gap2 = fp.gap2.Value, reliefW = fp.reliefw.Value, reliefD = fp.reliefd.Value,
                selFaceNames = fp.baseObject[1], MainObject = fp.baseObject[0])
    fp.Shape = s


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
    selobj = Gui.Selection.getSelection()[0]
    selFace = Gui.Selection.getSelectionEx()[0].SubObjects[0]
    if type(selFace) != Part.Face:
      return False
    return True

Gui.addCommand('SMSketchWall',SMSketchWallCommandClass())


