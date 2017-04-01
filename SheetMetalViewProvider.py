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

import FreeCAD, os
from FreeCAD import Gui
from SheetMetalCommon import *
from SheetMetalFeature import *


class SMViewProvider(object):
  "A View provider for sheet metall workbench"
  
  def __init__(self, obj):
    obj.Proxy = self
    self.Object = obj.Object
      
  def attach(self, obj):
    self.Object = obj.Object
    return

  def updateData(self, fp, prop):
    return

  def getDisplayModes(self,obj):
    return []

  def setDisplayMode(self,mode):
    return mode

  def onChanged(self, vp, prop):
    return

  def __getstate__(self):
    return None

  def __setstate__(self,state):
    if state is not None:
      self.Object = FreeCAD.ActiveDocument().getObject(state['ObjectName'])
      
  @staticmethod
  def getIconPath():
    "subclasses must implement"
    __dir__ = os.path.dirname(__file__)
    return os.path.join( __dir__, 'Resources', 'icons' ) + os.path.sep
    
  
  
class SMViewProviderTree(SMViewProvider):
  '''A Viewprovider which builds a tree with with cmds'''
  def __init__(self, obj, icon):
    SMViewProvider.__init__(self, obj, icon)
    
  def attach(self, obj):
    self.Object = obj.Object
    return

  def updateData(self, fp, prop):
    return

  def setDisplayMode(self,mode):
    return mode

  def onChanged(self, vp, prop):
    return

  def __getstate__(self):
    #        return {'ObjectName' : self.Object.Name}
    return None

  def __setstate__(self,state):
    if state is not None:
      import FreeCAD
      doc = FreeCAD.ActiveDocument #crap
      self.Object = doc.getObject(state['ObjectName'])
      
  def claimChildren(self):
    # claim children in tree if we are not a partdesign next object
    # as partdesign next sorts everything under body
    objs = []
    if smIsPartDesign(self.Object) or hasattr(self.Object,"baseObject"):
      objs.append(self.Object.baseObject[0])
    return objs

