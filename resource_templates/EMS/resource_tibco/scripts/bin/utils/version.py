#!/usr/bin/python
#
# Bob Muller, 2008-11-11, version 0.0.1

"""
Contains:
- version compare
"""

# Known issues:
# - none

import string
import sys, os, os.path, string, tempfile, stat, re

def compareVersions(v1, v2):
  """
  Compares two version strings in the format: x.y.z where there can be any number of version components.
  The version components themselves must be valid integers however.
  
  >>> compareVersions("1.0.0", "2.0.0")
  -1

  >>> compareVersions("2.0.0", "1.0.0")
  1

  >>> compareVersions("1.2.3", "1.2.3")
  0

  >>> compareVersions("1.2.3", "1.2")
  1

  >>> compareVersions("1.2", "1.2.3.4")
  -1

  >>> compareVersions("1.2.3.2.1", "1.2.3.2.1")
  0

  >>> l = ["1.0.4", "1.0.2", "0.1", "0.1.1"]
  >>> l.sort(compareVersions)
  >>> l
  ['0.1', '0.1.1', '1.0.2', '1.0.4']

  >>> try:
  ...   compareVersions("1.2.3a", "1.2.3b")
  ... except ValueError, e:
  ...   print e
  invalid literal for int(): 3a
    
  >>> try:
  ...   compareVersions("1.2..3", "1.2.3")
  ... except ValueError, e:
  ...   print e
  invalid literal for int(): 

  However, the following example is allowed:
    
  >>> compareVersions("1.2.3", "1.2.3.")
  -1
    
  >>> compareVersions("1.2.3.a.b.c", "1.2.3")
  1
    
  """
  if type(v1) is str:
    l1 = v1.split(".")
  else:
    l1 = v1
  if type(v2) is str: 
    l2 = v2.split(".")
  else:
    l2 = v2
  for i1, i2 in zip(l1, l2):
    if i1 == None or i2 == None:
      pass # wildcard
    elif int(i1) > int(i2):
      return +1
    elif int(i1) < int(i2):
      return -1
  if len(l1) > len(l2):
    return +1
  elif len(l1) < len(l2):
    return -1
  return 0


def parseVersion(version, format = None):
  """
  The general version specification format allows for multiple appearances:

  >>> parseVersion("v1.3.6-r2002-b3")
  (1, 3, 6, 2002, 3)

  >>> parseVersion("v1.3.6-r2002")
  (1, 3, 6, 2002, None)

  >>> parseVersion("1.3")
  (1, 3, None, None, None)

  >>> parseVersion("v1")
  (1, None, None, None, None)

  >>> parseVersion("v1.3.6-r2002b3")
  (1, 3, 6, 2002, 3)

  >>> parseVersion("v1.3.6-2002b3")
  (1, 3, 6, 2002, 3)

  >>> parseVersion("v1.3.6-b3")
  (1, 3, 6, None, 3)

  However, rpm-version format is more strict:

  >>> parseVersion("1.3.6-1234b3", 'rpm')
  (1, 3, 6, 1234, 3)

  >>> parseVersion("1.3.6-1234", 'rpm')
  (1, 3, 6, 1234, None)

  >>> parseVersion("1.3.6", 'rpm')
  (1, 3, 6, None, None)

  The v-prefix is not allowed in rpm-format, so:

  >>> parseVersion("v1.3.6", 'rpm')
  Traceback (most recent call last):
    File "/usr/lib64/python2.4/doctest.py", line 1243, in __run
      compileflags, 1) in test.globs
    File "<doctest __main__.parseVersion[10]>", line 1, in ?
      parseVersion("v1.3.6", 'rpm')
    File "./version.py", line 144, in parseVersion
      raise Exception("Invalid version specification: %s" % version)
  Exception: Invalid version specification: v1.3.6

  """

  if format == 'rpm':
    m = re.compile("^(\d+)\.(\d+)\.(\d+)-(\d+)b(\d+)").match(version)
    if m: return (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))
    m = re.compile("^(\d+)\.(\d+)\.(\d+)-(\d+)").match(version)
    if m: return (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), None)
    m = re.compile("^(\d+)\.(\d+)\.(\d+)").match(version)
    if m: return (int(m.group(1)), int(m.group(2)), int(m.group(3)), None, None)
  else:
    m = re.compile("^v?(\d+)\.(\d+)\.(\d+)-r?(\d+)-?b(\d+)").match(version)
    if m: return (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))
    m = re.compile("^v?(\d+)\.(\d+)\.(\d+)-?b(\d+)").match(version)
    if m: return (int(m.group(1)), int(m.group(2)), int(m.group(3)), None, int(m.group(4)))
    m = re.compile("^v?(\d+)\.(\d+)\.(\d+)-r?(\d+)").match(version)
    if m: return (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), None)
    m = re.compile("^v?(\d+)\.(\d+)\.(\d+)").match(version)
    if m: return (int(m.group(1)), int(m.group(2)), int(m.group(3)), None, None)
    m = re.compile("^v?(\d+)\.(\d+)").match(version)
    if m: return (int(m.group(1)), int(m.group(2)), None, None, None)
    m = re.compile("^v?(\d+)").match(version)
    if m: return (int(m.group(1)), None, None, None, None)
  raise Exception("Invalid version specification: %s" % version)



def makerpmVersion(vrpm):
  """
  >>> makerpmVersion(parseVersion('1.3.6-r4534-b6'))
  '1.3.6-4534b6'

  >>> makerpmVersion(parseVersion('1.3.6-r4534'))
  '1.3.6-4534'

  >>> makerpmVersion(parseVersion('1.3.6'))
  '1.3.6'

  >>> makerpmVersion(parseVersion('1.3'))
  Traceback (most recent call last):
    File "/usr/lib64/python2.4/doctest.py", line 1243, in __run
      compileflags, 1) in test.globs
    File "<doctest __main__.makerpmVersion[3]>", line 1, in ?
      makerpmVersion(parseVersion('1.3'))
    File "./version.py", line 184, in makerpmVersion
      raise Exception("Version not convertable to rpm-version format: %s" % str(vrpm))
  Exception: Version not convertable to rpm-version format: (1, 3, None, None, None)

  >>> makerpmVersion(parseVersion('v1.3.6'))
  '1.3.6'

  """

  l = len(vrpm) - 1
  while l >= 0 and vrpm[l] == None:
    l -= 1
  if l == 4:
    return "%d.%d.%d-%db%d" % vrpm[:5]
  elif l == 3:
    return "%d.%d.%d-%d" % vrpm[:4]
  elif l == 2:
    return "%d.%d.%d" % vrpm[:3]

  raise Exception("Version not convertable to rpm-version format: %s" % str(vrpm))



def matchVersions(vmatch, vmin, vmax = None):
  """
  Compares two version strings in several different formats, examples of recognized formats:
  - v1.3.6-r2002-b3
  - 1.3.6-2002b3
  - 1.3.6
  
  When matching versions, only specified parts of a version are matched:
  - v1.3 matches 1.3.6, 1.3.7, 1.3.7-2002b3
  - 1.3.6-2002b3 matches v1.3.6-r2002-b3 but not v1.3.7
  - 1.3.7 matches 1.3.7-2002b3
  
  >>> matchVersions("v1.3.8-r2002-b3", "1.3.6")
  True

  >>> matchVersions("v1.3.6-r2002-b3", "1.3.6", "1.3.8")
  True

  >>> matchVersions("v1.3.6-r2002-b3", "1.3.6-r2000", "1.3.8")
  True

  >>> matchVersions("v1.3.8-r2002-b3", "1.3.6-r2000", "1.3.8")
  True

  >>> matchVersions("v1.3.8-r2002-b3", "1.3.6-r2000", "1.3.8-r2000-b20")
  False

  >>> matchVersions("v1.3.6-r2002-b3", "1.3.6-r2003", "1.3.8")
  False

  >>> matchVersions("v1.3.6-r2002-b3", None, "1.3.8")
  True

  >>> matchVersions("v1.3.6-r2002-b3", "1.3.6", "1.3.6")
  True

  >>> matchVersions("v1.3.6b3", "1.3.6", "1.3.6")
  True

  >>> matchVersions("v1.3.6-2002b3", "1.3.6b2", "1.3.6b4")
  True

  >>> matchVersions("v1.3.6-r2002", "1.3.6", "1.3.6")
  True

  >>> matchVersions("v1.3.6-2002b3", "1.3.6", "1.3.6")
  True

  """

  vmatch = parseVersion(vmatch)
  if vmin:
    vmin = parseVersion(vmin)
    if compareVersions(vmatch, vmin) < 0:
      return False
  if vmax: 
    vmax = parseVersion(vmax)
    if compareVersions(vmatch, vmax) > 0:
      return False
  return True
  

# This provides for buildin doctests

if __name__ == "__main__":
  import doctest
  doctest.testmod()
