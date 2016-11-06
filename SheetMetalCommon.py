#***************************************************************************
#*                                                                         *
#    Copyright 2015 Shai Seger <shaise at gmail dot com>                   *
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

from FreeCAD import Gui
import FreeCAD, FreeCADGui, Part
  
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
    if bendA >= 0: # not(flipped):
      revAxisP = thkEdge.valueAt(thkEdge.LastParameter + bendR)
      revAxisV = revAxisV * -1
    else:
      bendA = bendA * -1
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
      wallSolid = wallFace.extrude(wallFace.normalAt(0,0) * extLen)
      resultSolid = resultSolid.fuse(wallSolid)
      
  Gui.ActiveDocument.getObject(MainObject.Name).Visibility = False
  return resultSolid
  
  
  
def smExtrude(extLength = 10.0, selFaceNames = '', selObjectName = ''):
  
#  selFace = Gui.Selection.getSelectionEx()[0].SubObjects[0]
#  selObjectName = Gui.Selection.getSelection()[0].Name
  AAD = FreeCAD.ActiveDocument
  MainObject = AAD.getObject( selObjectName )
  finalShape = MainObject.Shape
  for selFaceName in selFaceNames:
    selFace = AAD.getObject(selObjectName).Shape.getElement(selFaceName)

    # extrusion direction
    V_extDir = selFace.normalAt( 0,0 )

    # extrusion
    wallFace = selFace.extrude( V_extDir*extLength )
    finalShape = finalShape.fuse( wallFace )
  
  #finalShape = finalShape.removeSplitter()
  #finalShape = Part.Solid(finalShape.childShapes()[0])  
  Gui.ActiveDocument.getObject( selObjectName ).Visibility = False
  return finalShape

