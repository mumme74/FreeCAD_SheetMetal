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

class SMSelProperties:
  def __init__(self, obj, subObjectName):
    "class to find revolve axis etc from either face or edge"
    if not obj: return
    self.MainObject = obj
    self.selShape = obj.Shape.getElement(subObjectName)
    self.thickness = 999999.0          # thickness of metal sheet
    self.thicknessEdge = None          # the short edge vertical to revolveEdge 
    self.revAxisV = None               # revolve around this axis
    self.selFace = None                # the face that this attaches to
    self.thicknessDir = None           # Vector that points to short side of plate
    self.revEdge = None                # revolve around this edge
    self.initialized = False
  
    if type(self.selShape) == Part.Face:
      # user selected face
      self.selFace = self.selShape #fp.baseObject[0].Shape.getElement(fp.baseObject[1][0])
          
    elif type(self.selShape) == Part.Edge:
      # user selected edge, search for the correct face
      self.revEdge = self.selShape #fp.baseObject[0].Shape.getElement(fp.baseObject[1][0])
      v0 = self.revEdge.Vertexes[0]
      v1 = self.revEdge.Vertexes[1]
      for face in obj.Shape.Faces:
        if self._findVertexes(v0, face.Vertexes) and self._findVertexes(v1, face.Vertexes):
          if self.selFace == None or self.selFace.Area > face.Area:
            self.selFace = face # select the face with the smallest area
      
      # user picked the short, thickness side
      if self.selFace == None:
        FreeCAD.Console.PrintWarning("Can't build from selected edge")
        return
    else:
      # unsupported selection
      return
    
    # find the narrow edge
    for edge in self.selFace.Edges:
      if abs( edge.Length ) < self.thickness:
        self.thickness = abs( edge.Length )
        self.thicknessEdge = edge
        
    # may need to reverse thicknessEdge
    if (self.revEdge and 
       (self.thicknessEdge.valueAt(self.thicknessEdge.LastParameter) == 
        self.revEdge.valueAt(self.revEdge.FirstParameter))):
      e1 = self.thicknessEdge.valueAt(self.thicknessEdge.LastParameter)
      e0 = self.thicknessEdge.valueAt(self.thicknessEdge.FirstParameter)
      self.thicknessEdge = Part.Edge(Part.Line(e1, e0))
    
    
    # main corner
    p0 = self.thicknessEdge.valueAt(self.thicknessEdge.FirstParameter)
    
    # when selecting a surface
    if not self.revEdge:
      # find a length edge  =  revolve axis direction
      for lenEdge in self.selFace.Edges:
        lastp = lenEdge.LastParameter
        firstp = lenEdge.FirstParameter
        if lenEdge.isSame(self.thicknessEdge):
          continue
        # FreeCAD.Console.PrintLog("=>" + str(lastp)+", "+ str(lenEdge.valueAt(firstp)) +
        #                          ", "+ str(lenEdge.valueAt(lastp)) + ", " + str(p0) + "\n")
        if (lenEdge.valueAt(firstp) == p0 or lenEdge.valueAt(lastp) == p0):
          self.revEdge = lenEdge
          break
    

    self.thicknessDir = (self.thicknessEdge.valueAt(self.thicknessEdge.LastParameter) -
                         self.thicknessEdge.valueAt(self.thicknessEdge.FirstParameter))
                         
                         
    if (self.revEdge.valueAt(self.revEdge.FirstParameter) == p0):
      self.revAxisV = (self.revEdge.valueAt(self.revEdge.LastParameter) - 
                       self.revEdge.valueAt(self.revEdge.FirstParameter))
    else:
      self.revAxisV = (self.revEdge.valueAt(self.revEdge.FirstParameter) - 
                       self.revEdge.valueAt(self.revEdge.LastParameter))
        
    #make sure the direction vector is correct in respect to the normal
    if self.thicknessDir.cross(self.revAxisV).normalize() == self.selFace.normalAt(0,0):
      self.revAxisV *= -1
  
    self.initialized = True
  
  
  def _findVertexes(self, findV, vertexes):
    "Method helper, compares vertex aginst list of vertexes"
    for vertex in vertexes:
      if vertex.Point == findV.Point:
        return True
    return False
    
  @staticmethod
  def checkSelection():
    selShape = Gui.Selection.getSelectionEx()[0].SubObjects[0]
    if type(selShape) in [Part.Face, Part.Edge]:
      # test if we can build the feature out of this selection
      selObj = Gui.Selection.getSelectionEx()[0]
      return SMSelProperties(selObj.Object, selObj.SubElementNames[0]).initialized
    return False

# -------------- end class -------------


def smMakeFace(edge, dir, from_p, to_p):
    e1 = edge.copy()
    e1.translate(dir * from_p)
    e2 = edge.copy()
    e2.translate(dir * to_p)
    e3 = Part.Line(e1.valueAt(e1.FirstParameter), e2.valueAt(e2.FirstParameter)).toShape()
    e4 = Part.Line(e1.valueAt(e1.LastParameter), e2.valueAt(e2.LastParameter)).toShape()
    w = Part.Wire([e1,e3,e2,e4])
    return Part.Face(w)


def smBend(bendR = 1.0, bendA = 90.0, flipped = False, extLen = 10.0, gap1 = 0.0, gap2 = 0.0, 
            reliefW = 0.5, reliefD = 1.0, qs = SMSelProperties(None,'')):
  
  resultSolid = qs.MainObject.Shape
     
  # narrow the wall if we have gaps
  revDir = qs.revAxisV.normalize()
  lgap2 = qs.revEdge.Length - gap2
  if gap1 == 0 and gap2 == 0:
    revFace = qs.selFace
  else:
    revFace = smMakeFace(qs.thicknessEdge, revDir, gap1, lgap2)
    if (revFace.normalAt(0,0) != qs.selFace.normalAt(0,0)):
      revFace.reverse()
    
  # remove relief if needed
  if reliefW > 0 and reliefD > 0 and (gap1 > 0 or gap2 > 0) :
    thicknessEdgeW = Part.Line(qs.thicknessEdge.valueAt(qs.thicknessEdge.FirstParameter-0.1), 
                               qs.thicknessEdge.valueAt(qs.thicknessEdge.LastParameter+0.1)).toShape()
    reliefFace = smMakeFace(thicknessEdgeW, revDir, gap1 - reliefW, gap1)
    reliefFace = reliefFace.fuse(smMakeFace(thicknessEdgeW, revDir, lgap2, lgap2 + reliefW))
    reliefSolid = reliefFace.extrude(qs.selFace.normalAt(0,0) * reliefD * -1)
    #Part.show(reliefSolid)
    resultSolid = resultSolid.cut(reliefSolid)

  #find revolve point
  if bendA >= 0: # not(flipped):
    revAxisP = qs.thicknessEdge.valueAt(qs.thicknessEdge.LastParameter + bendR)
    qs.revAxisV = qs.revAxisV * -1
  else:
    bendA = bendA * -1
    revAxisP = qs.thicknessEdge.valueAt(qs.thicknessEdge.FirstParameter - bendR)  

  # create bend
  wallFace = revFace
  if bendA > 0 :
    bendSolid = revFace.revolve(revAxisP, qs.revAxisV, bendA)
    #Part.show(bendSolid)
    resultSolid = resultSolid.fuse(bendSolid)
    wallFace = revFace.copy()
    wallFace.rotate(revAxisP, qs.revAxisV, bendA)
    
  # create wall
  if extLen > 0 :
    wallSolid = wallFace.extrude(wallFace.normalAt(0,0) * extLen)
    resultSolid = resultSolid.fuse(wallSolid)
      
  Gui.ActiveDocument.getObject(qs.MainObject.Name).Visibility = False
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

