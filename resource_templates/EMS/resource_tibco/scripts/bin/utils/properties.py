#!/usr/bin/python
#
# Bob Muller, 2008-11-06, version 0.01

"""
Contains:
- functions for updating Java properties-files
"""

# Known issues:
# - none

import sys, os, os.path, string

######################################################
# functions for properties-files
######################################################

def setprop(list, key, value, wildmatch=False, separator="="):
  """
  Sets a property in a property file, whose contents are in list.
  """
  found = False
  result = {}
  for i in range(0, len(list)):
    if list[i].find(separator) >= 0:
      (lkey, lvalue) = list[i].split(separator, 1)
      if lkey.strip() == key or (wildmatch and lkey.strip().startswith(key)):
        result[lkey] = lvalue
        if value is None:
          list[i] = ""
        else:
          list[i] = key + separator + value
        found = True
  if not found and not wildmatch and value is not None:
    list.append(key + separator + value)
  return result

def readprops(file):
  """
  Reads a (standard Java) properties file. 
  Returns a list of strings. 
  """  
  if os.path.isfile(file):
    f = open(file, "r")
    result = [i.rstrip("\n") for i in f.readlines()]
    f.close()
  else:
    result = []
  return result
  
def writeprops(file, prefs):
  """
  Writes out a properties file as read by readprops. 
  prefs is a list of strings. 
  """  
  f = open(file, "w")
  f.writelines([i + "\n" for i in prefs])
  f.close()
