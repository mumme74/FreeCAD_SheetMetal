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

class SMFeature(object):
  def __init__(self, featureObj):
    featureObj.Proxy = self
    
  @staticmethod
  def GetPythonObj(name):
    '''Returns a FreeCAD PartDesign feature'''
    objType = "Part::FeaturePython" if FreeCAD.Version()[1] < 17  else "PartDesign::FeaturePython"
    obj = FreeCAD.activeDocument().addObject(objType, name)
      
    selected = Gui.Selection.getSelectionEx()
    if len(selected):
      obj.addProperty("App::PropertyLinkSub", "baseObject", "Parameters", "Base object").baseObject = (selected[0].Object, selected[0].SubElementNames)
    
      # new partdesign fix, TODO activate when API for partdesign matures, need PartDesign::FeaturePython
      if FreeCAD.Version()[1] >= 17:
        for o in selected[0].Object.InList:
          if o.TypeId == 'PartDesign::Body':
            o.addFeature(obj)
            break
 
    return obj 



