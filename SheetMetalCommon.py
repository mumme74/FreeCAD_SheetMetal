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
from SheetMetalFeature import *

smEpsilon = 0.0000001


def smStrEdge(e):
    return "[" + str(e.valueAt(e.FirstParameter)) + " , " + str(e.valueAt(e.LastParameter)) + "]"
    

#import rpdb2
#rpdb2.start_embedded_debugger("freecad")

class SMSelProperties:
  def __init__(self, obj, subObjectName):
    "class to find revolve axis etc from either face or edge"
    self.initialized = False
    if not obj: return
    
    self.MainObject = obj
    self.selShape = obj.Shape.getElement(subObjectName)
    self.thickness = 999999.0          # thickness of metal sheet
    self.thicknessEdge = None          # the short edge vertical to revolveEdge 
    self.revAxisV = None               # revolve around this axis
    self.selFace = None                # the face that this attaches to
    self.thicknessDir = None           # Vector that points to short side of plate
    self.revEdge = None                # revolve around this edge
  
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
        smWarnDialog("Can't build from selected edge")
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
    #if (self.revEdge and 
    #   (self.thicknessEdge.valueAt(self.thicknessEdge.LastParameter) == 
    #    self.revEdge.valueAt(self.revEdge.FirstParameter))):
    #  e1 = self.thicknessEdge.valueAt(self.thicknessEdge.LastParameter)
    #  e0 = self.thicknessEdge.valueAt(self.thicknessEdge.FirstParameter)
    #  self.thicknessEdge = Part.Edge(Part.Line(e1, e0))
    #  print("reverse thkness", e0, e1, self.thicknessEdge.Length)
    
    
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
    if (self.thicknessDir.cross(self.revAxisV).normalize() - self.selFace.normalAt(0,0)).Length < smEpsilon:
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


class SMWall:
  def __init__(self, bendR = 1.0, bendA = 90.0, extLen = 0.0, gap1 = 0.0, gap2 = 0.0, 
               reliefW = 0.5, reliefD = 1.0, qs = SMSelProperties(None,''), fp = None):
    if not qs.initialized and not fp: return
    self.bendR = bendR          # bend radious
    self.bendA = bendA          # bend Angle
    self.extLen = extLen        # extend a square pad with this length
    self.gap1 = gap1            # hinge gap from mating edge
    self.gap2 = gap2            # same but other side
    self.reliefW = reliefW      # a relief cutout width (when using gaps)
    self.reliefD = reliefD      # a relief cutout height (when using gaps)
    self.fp = fp                # a feature python object to build from
    if not qs.initialized:
      qs = SMSelProperties(fp.baseObject[0], fp.baseObject[1][0])
    self.qs = qs
    self.Shape = self.qs.MainObject.Shape
    self.wallFace = qs.selFace


  def _makeFace(self, edge, dir, from_p, to_p):
    e1 = edge.copy()
    e1.translate(dir * from_p)
    e2 = edge.copy()
    e2.translate(dir * to_p)
    e3 = Part.Line(e1.valueAt(e1.FirstParameter), e2.valueAt(e2.FirstParameter)).toShape()
    e4 = Part.Line(e1.valueAt(e1.LastParameter), e2.valueAt(e2.LastParameter)).toShape()
    w = Part.Wire([e1,e3,e2,e4])
    return Part.Face(w)

  def hinge(self):
    "creates a hinge to extend a wall onto"
    # narrow the wall if we have gaps
    revDir = self.qs.revAxisV.normalize()
    lgap2 = self.qs.revEdge.Length - self.gap2
    if self.gap1 == 0 and self.gap2 == 0:
      revFace = self.qs.selFace
    else:
      revFace = self._makeFace(self.qs.thicknessEdge, revDir, self.gap1, lgap2)
      if (revFace.normalAt(0,0) != self.qs.selFace.normalAt(0,0)):
        revFace.reverse()
    
    # remove relief if needed
    if self.reliefW > 0 and self.reliefD > 0 and (self.gap1 > 0 or self.gap2 > 0) :
      thicknessEdgeW = Part.Line(self.qs.thicknessEdge.valueAt(self.qs.thicknessEdge.FirstParameter-0.1), 
                                 self.qs.thicknessEdge.valueAt(self.qs.thicknessEdge.LastParameter+0.1)).toShape()
      reliefFace = self._makeFace(thicknessEdgeW, revDir, self.gap1 - self.reliefW, self.gap1)
      reliefFace = reliefFace.fuse(self._makeFace(thicknessEdgeW, revDir, lgap2, lgap2 + self.reliefW))
      reliefSolid = reliefFace.extend(self.qs.selFace.normalAt(0,0) * self.reliefD * -1)
      #Part.show(reliefSolid)
      self.Shape = self.Shape.cut(reliefSolid)

    #find revolve point
    if self.bendA >= 0: # not(flipped):
      revAxisP = self.qs.thicknessEdge.valueAt(self.qs.thicknessEdge.LastParameter + self.bendR)
      self.qs.revAxisV = self.qs.revAxisV * -1
      bendA = self.bendA
    else:
      bendA = self.bendA * -1
      revAxisP = self.qs.thicknessEdge.valueAt(self.qs.thicknessEdge.FirstParameter - self.bendR)

    # create bend
    wallFace = revFace
    if bendA > 0.0 :
      bendSolid = revFace.revolve(revAxisP, self.qs.revAxisV, bendA)
      #Part.show(bendSolid)
      self.Shape = self.Shape.fuse(bendSolid)
      self.wallFace = revFace.copy()
      self.wallFace.rotate(revAxisP, self.qs.revAxisV, bendA)
  
  
  def extend(self):
    "extend a square wall from the face of our hinge"
    if self.extLen > 0.0 :
      self.wallSolid = self.wallFace.extrude(self.wallFace.normalAt(0,0) * self.extLen)
      self.Shape = self.Shape.fuse(self.wallSolid)
      
    
    
    
  def finish(self):
    Gui.ActiveDocument.getObject(self.qs.MainObject.Name).Visibility = False
    return self.Shape
    
  
  def addSketchNormalToPlane(self):
    import Sketcher
    
    doc = FreeCAD.activeDocument()

    sk = doc.addObject("Sketcher::SketchObject","WallSketch")
    
    # find wallFace edges
    longEdge = None
    for edge in self.wallFace.Edges:
      if not longEdge:
        longEdge = edge
      elif longEdge.Length < edge.Length:
        shortEdge = longEdge
        longEdge = edge
      else:
        shortEdge = edge
    halfLen = longEdge.Length / 2
    
    if hasattr(sk, 'MapMode'):
      sk.MapMode = "Translate"
    
    revAxisV = (shortEdge.valueAt(shortEdge.LastParameter) - 
                shortEdge.valueAt(shortEdge.FirstParameter))
    #App.Placement(App.Vector(1,-2,0),App.Rotation(App.Vector(0,0,1),3))
    print revAxisV
    sk.Placement = FreeCAD.Placement(longEdge.valueAt(longEdge.FirstParameter + halfLen), FreeCAD.Rotation(revAxisV,0))

    # set some constants for the constraints
    StartPoint = 1
    EndPoint = 2
    MiddlePoint = 3
        
    # add geometry to the sketch
    leftTop = FreeCAD.Vector(-(halfLen + 5),10,0)
    leftBottom = FreeCAD.Vector(-halfLen,0,0)
    rightTop = FreeCAD.Vector((halfLen + 5),12,0)
    rightBottom = FreeCAD.Vector(halfLen,0,0)

    sk.Geometry = [Part.Line(leftTop,rightTop),
                   Part.Line(rightTop,rightBottom), 
                   Part.Line(rightBottom,leftBottom),
                   Part.Line(leftBottom,leftTop)]

    # add constraint to make it a rectangle
    l = sk.Constraints
    l.append(Sketcher.Constraint('Coincident',0,EndPoint,1,StartPoint))
    l.append(Sketcher.Constraint('Coincident',1,EndPoint,2,StartPoint))
    l.append(Sketcher.Constraint('Coincident',2,EndPoint,3,StartPoint))
    l.append(Sketcher.Constraint('Coincident',3,EndPoint,0,StartPoint))
    sk.Constraints = l
    #doc.recompute()

    #face = Part.Face(sk.Shape)
    #wall = face.extend(Base.Vector(0, 0, self.qs.thickness))
    #obj = doc.getObject('SketchWall').Shape.fuse(wall)
    #sk.ViewObject.Visibility = False
    #Part.show(obj)
    #Part.show(wall)
    #doc.recompute()

