#!/usr/bin/python
#
# Bob Muller, 2008-11-06, version 0.01

"""
Contains:
- xpath and xml helper functions

Doctests:

>>> doc = libxml2.parseDoc("<test><a><b>test1</b><c>test2</c></a></test>")
>>> context = xpathContext(doc)
>>> a = xpathNode(context, doc, "/test/a")
>>> xpathValue(context, a, "b")
'test1'

>>> doc = libxml2.parseDoc("<test xmlns='http://defaultns'><a><b>test1</b><c>test2</c></a></test>")
>>> context = xpathContext(doc)
>>> a = xpathNode(context, doc, "/xd:test/xd:a")
>>> xpathValue(context, a, "xd:b")
'test1'

>>> doc = libxml2.parseDoc("<ns:test xmlns:ns='http://defaultns'><ns:a><ns:b>test1</ns:b><ns:c>test2</ns:c></ns:a></ns:test>")
>>> context = xpathContext(doc)
>>> a = xpathNode(context, doc, "/ns:test/ns:a")
>>> xpathValue(context, a, "ns:b")
'test1'

>>> doc1 = libxml2.parseDoc("<test xmlns='http://defaultns'><a><b>test1</b><c>test2</c></a></test>")
>>> context = xpathContext(doc1)
>>> a = xpathNode(context, doc1, "/xd:test/xd:a")
>>> a.serialize(None, 1)
'<a>\\n  <b>test1</b>\\n  <c>test2</c>\\n</a>'

>>> b = xpathNode(context, a, "xd:b")
>>> b.serialize(None, 1)
'<b>test1</b>'

>>> doc2 = libxml2.parseDoc("<test xmlns='http://defaultns'><e><f>test1</f><g>test2</g></e></test>")
>>> context = xpathContext(doc2)
>>> f = xpathNode(context, doc2, "/xd:test/xd:e/xd:f")
>>> f.serialize(None, 1)
'<f>test1</f>'

>>> b.addChild(f.copyNode(1)) #doctest: +ELLIPSIS
<xmlNode (f) object at 0x...>
>>> b.serialize(None, 1)
'<b>test1<f xmlns="http://defaultns">test1</f></b>'

"""

# Known issues:
# - none

import string, libxml2, libxslt

######################################################
# xpath and xml functions
######################################################

def toList(firstNodeOrAttribute):
  """
  Convenience function that makes a normal list out of an object that is part of a linked list.
  """
  result = []
  while firstNodeOrAttribute:
    result.append(firstNodeOrAttribute)
    firstNodeOrAttribute = firstNodeOrAttribute.next
  return result

def xpathContext(node):
  """
  Returns a xpathContext object that has the namespaces for the document already registered.
  """
  doc = node.get_doc()
  result = doc.xpathNewContext()
  result.setContextNode(node)
  result.setContextDoc(doc)

  def walkTree(node):
    for nsdef in toList(node.nsDefs()):
      if nsdef.name is None:
        result.xpathRegisterNs("xd", nsdef.content)
      else:
        result.xpathRegisterNs(nsdef.name, nsdef.content)
      #print "prefix:", nsdef.name
      #print "uri:", nsdef.content
    for child in toList(node.children):
      walkTree(child)

  walkTree(doc)
  return result
  
def xpathList(context, node, expr):
  """ 
  Returns the result of a xpathEval. If a node is given as a parameter, a context will be automatically created
  in which node will be the contextNode.
  """
  if context is None:
    raise "Context must be given!" 
  elif node is None:
    context.setContextNode(context.contextDoc().getRootElement())
    result = context.xpathEval(expr)
  else:
    context.setContextNode(node)
    result = context.xpathEval(expr)
  return result or ()

def xpathNode(context, node, expr, default=None):
  """ 
  Returns the node found by an xpath expression evaluated on a context or node. If nothing is found, or result is
  ambigious a default value is returned. If node is given as a parameter, a context will be automatically created
  in which node will be the contextNode.
  """
  result = xpathList(context, node, expr)
  if len(result) != 1:
    return default
  elif result:
    return result[0]
  return default

def xpathValue(context, node, expr, default=None):
  """ 
  Returns the value (content) of an xpath expression evaluated on a context or node. If nothing is found, or result is
  ambigious a default value is returned.
  """
  result = xpathNode(context, node, expr)
  if result:
    return result.content
  return default

def removeNamespaces(root, ignored = []):
  """
  Removes all namespaces from the dom-structure defined by root. Returns a dict of namespaces removed so that they can be
  added again later. The ignored-parameter is an optional list of strings containing namespace prefixes that will not be removed.
  """
  result = {}

  def walkTree(node):
    for nsdef in toList(node.nsDefs()):
      if nsdef.name and nsdef.name not in ignored:
        result[nsdef.name] = nsdef.content
        node.removeNsDef(nsdef.content)#.freeNsList()
    if node.ns() and node.ns().name and node.ns().name not in ignored:
      node.setNs(None)
    for child in toList(node.children):
      walkTree(child)

  walkTree(root)
  return result

def addNamespaces(root, namespaces):
  """
  Re-adds namespaces removed by removeNamespaces.
  """
  for ns in namespaces.items():
    root.newNs(ns[1], ns[0])
  return  

def formatTree(root):
  """
  Formats (part of) an xml document.
  """
  root.replaceNode(libxml2.parseDoc(root.serialize(None, 1)).getRootElement())
  return

######################################################
# Simple oo-interface
######################################################
    
class XmlCursor:
  
  def __init__(this, doc):
    """
    Constructor associates cursor with a XML-document.
    """
    this.doc = doc
    this.context = xpathContext(doc)
    this.reset()
    
  def set(this, node):
    """
    Sets the current node to something else.
    """
    this.node = node
    
  def reset(this):
    """
    Sets the current node to the root element of the document.
    """
    this.node = this.doc
    
  def go(this, expr):
    """
    Finds a node using an xpath expression and sets the current node if found.
    Returns True if node is found, None otherwise.
    """
    newNode = this.xpathNode(expr)
    if newNode:
      this.set(newNode)
      return True

  def newCursor(this, expr):
    """
    Creates a new cursor by searching an xpath expression, when a node is found
    a cursor with this position is returned, None is returned otherwise.
    """
    newNode = this.xpathNode(expr)
    if newNode:
      cursor = XmlCursor(this.doc)
      cursor.set(newNode)
      return cursor
    
  def xpathValue(this, expr, default = None):
    """
    Evaluates an xpath epxression and returns the value if found.
    """
    return xpathValue(this.context, this.node, expr, default)

  def xpathNode(this, expr, default = None):
    """
    Evaluates an xpath epxression and returns the node if found.
    """
    return xpathNode(this.context, this.node, expr, default)

  def xpathList(this, expr):
    """
    Evaluates an xpath epxression and returns a list of nodes found.
    """
    return xpathList(this.context, this.node, expr)


# This provides for buildin doctests

if __name__ == "__main__":
  import doctest
  doctest.testmod()



