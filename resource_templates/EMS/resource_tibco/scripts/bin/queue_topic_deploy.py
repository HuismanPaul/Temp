#!/usr/bin/python -u
#
# Convenience scripts for TIBCO tools and services.
#
# Created: 2008-11-12 by Bob Muller. ProRail ICC
# Built:   2014-10-22 11:49
# Version: v1.6.2-r3540-b56.el6.el6
# Purpose:
# Deploys an .ear file (or set of .ear-files) locally or on a remote machine. 


import sys, os, os.path, string, tempfile, stat, re, base64
import platform
import optparse
import datetime, time
import libxml2
import urllib
import zipfile
import getpass
import subprocess
import utils.xml, utils.properties, utils.version
import fnmatch
import logging

logfile = None
obfuscated_strings = []
passwords = {}

def ofs(msg):
  for search in obfuscated_strings:
    msg = msg.replace(search, "???")
  return msg

# properties handling

class IllegalArgumentException(Exception):

    def __init__(self, lineno, msg):
        self.lineno = lineno
        self.msg = msg

    def __str__(self):
        s='Exception at line number %d => %s' % (self.lineno, self.msg)
        return s
                 
class Properties(object):
    """ A Python replacement for java.util.Properties """
    
    def __init__(self, props=None):

        # Note: We don't take a default properties object
        # as argument yet

        # Dictionary of properties.
        self._props = {}
        self._propkeys = [] # maintain property order
        
        self.othercharre = re.compile(r'(?<!\\)(\s*\=)|(?<!\\)(\s*\:)')
        self.othercharre2 = re.compile(r'(\s*\=)|(\s*\:)')
        self.bspacere = re.compile(r'\\(?!\s$)')
        self._storeDuplicates = False
        self._section = None
        self._sections = []
        self._format = "tra" # valid: tra, ini
        self._stat = ()
        
    def __str__(self):
        s='{'
        for key,value in self._props.items():
            s = ''.join((s,key,'=',value,', '))

        s=''.join((s[:-2],'}'))
        return s

    def __parse(self, lines):
        """ Parse a list of lines and create
        an internal property dictionary """

        # Every line in the file must consist of either a comment
        # or a key-value pair. A key-value pair is a line consisting
        # of a key which is a combination of non-white space characters
        # The separator character between key-value pairs is a '=',
        # ':' or a whitespace character not including the newline.
        # If the '=' or ':' characters are found, in the line, even
        # keys containing whitespace chars are allowed.

        # A line with only a key according to the rules above is also
        # fine. In such case, the value is considered as the empty string.
        # In order to include characters '=' or ':' in a key or value,
        # they have to be properly escaped using the backslash character.

        # Some examples of valid key-value pairs:
        #
        # key     value
        # key=value
        # key:value
        # key     value1,value2,value3
        # key     value1,value2,value3 \
        #         value4, value5
        # key
        # This key= this value
        # key = value1 value2 value3
  
        # Any line that matches [section] starts a new section. Keys 
        # will have [section] prepended internally. Sections are recreated
        # upon writing the file to disk.
        
        # Any line that starts with a '#' is considerered a comment
        # and skipped. Also any trailing or preceding whitespaces
        # are removed from the key/value.
        
        # This is a line parser. It parses the
        # contents like by line.

        lineno=0
        i = iter(lines)
        section = ""

        for line in i:
            lineno += 1
            line = line.strip()
            # Skip null lines
            if not line: continue
            # Skip lines which are comments
            if line[0] == '#': continue
            # Begin a new section
            if line[0] == '[':
              if line[-1] != ']':
                raise Exception("Parsing error, invalid section format")
              section = line
              self._sections.append(section)
              continue
            # Some flags
            escaped=False
            # Position of first separation char
            sepidx = -1
            # A flag for performing wspace re check
            flag = 0
            # Check for valid space separation
            # First obtain the max index to which we
            # can search.
            wspacere = re.compile(r'(?<![\\\=\:])(\s)')        
            m = self.othercharre.search(line)
            if m:
                first, last = m.span()
                start, end = 0, first
                flag = 1
            else:
                if self.othercharre2.search(line):
                    # Check if either '=' or ':' is present
                    # in the line. If they are then it means
                    # they are preceded by a backslash.
                    
                    # This means, we need to modify the
                    # wspacere a bit, not to look for
                    # : or = characters.
                    wspacere = re.compile(r'(?<![\\])(\s)')        
                start, end = 0, len(line)
                
            m2 = wspacere.search(line, start, end)
            if m2:
                # print 'Space match=>',line
                # Means we need to split by space.
                first, last = m2.span()
                sepidx = first
            elif m:
                # print 'Other match=>',line
                # No matching wspace char found, need
                # to split by either '=' or ':'
                first, last = m.span()
                sepidx = last - 1
                # print line[sepidx]
                
                
            # If the last character is a backslash
            # it has to be preceded by a space in which
            # case the next line is read as part of the
            # same property
            while line[-1] == '\\':
                # Read next line
                nextline = i.next()
                nextline = nextline.strip()
                lineno += 1
                # This line will become part of the value
                line = line[:-1] + nextline

            # Now split to key,value according to separation char
            if sepidx != -1:
                key, value = line[:sepidx], line[sepidx+1:]
            else:
                key,value = line,''

            oldDups = self._storeDuplicates
            self._storeDuplicates = True
            self.processPair(section + key, value)
            self._storeDuplicates = oldDups
            

    def processPair(self, key, value):
        """ Process a (key, value) pair """

        # handle section prefixes
        if key[0:1] == '[':
          section = key.split(']')[0] + ']'
          if section not in self._sections:
            self._sections.append(section)
        
        # Create key intelligently
        keyparts = self.bspacere.split(key)

        strippable = False
        lastpart = keyparts[-1]

        if lastpart.find('\\ ') != -1:
            keyparts[-1] = lastpart.replace('\\','')

        # If no backspace is found at the end, but empty
        # space is found, strip it
        elif lastpart and lastpart[-1] == ' ':
            strippable = True

        key = ''.join(keyparts)
        if strippable:
            key = key.strip()

        # handle duplicate keys
        if self._props.has_key(key):
          if self._storeDuplicates:
            # make key unique
            id = 1
            while self._props.has_key(key + ":%d" % id):
              id += 1
            key += ":%d" % id
          else:
            self.delProperty(key)

        value = self.unescape(value)
        logging.debug(ofs("Storing %s=%s" % (key, value)))
        if key not in self._propkeys:
          self._propkeys.append(key)
        self._props[key] = value.strip()

        
    def escape(self, value):

        # No escaping for ini files
        if self._format == 'ini': return value

        # Java escapes the '=' and ':' in the value
        # string with backslashes in the store method.
        # So let us do the same.
        newvalue = value.replace(':','\:').replace('=','\=')

        return newvalue

    def unescape(self, value):

        # No escaping for ini files
        if self._format == 'ini': return value

        # Reverse of escape
        newvalue = value.replace('\:',':')
        newvalue = newvalue.replace('\=','=')

        return newvalue    
        
    def load(self, stream):
        """ Load properties from an open file stream """
        
        # For the time being only accept file input streams
        if type(stream) is not file:
            raise TypeError,'Argument should be a file object!'
        # Check for the opened mode
        if stream.mode != 'r':
            raise ValueError,'Stream should be opened in read-only mode!'

        try:
            lines = stream.readlines()
            self.__parse(lines)
        except IOError, e:
            raise

    def delProperty(self, key):
        # remove existing keys
        del self._props[key]
        id = 1
        while self._props.has_key(key + ":%d" % id):
          del self._props[key + ":%d" % id]
          id += 1

    def getProperty(self, key):
        """ Return a property for the given key """
        
        return self._props.get(key,'')

    def setProperty(self, key, value):
        """ Set the property for the given key """

        if type(key) is str and type(value) is str:
            self.processPair(key, value)
        else:
            raise TypeError,'both key and value should be strings!'

    def duplicates(self, enable):
        """ Enable or disable duplicate keys """

        self._storeDuplicates = enable or False
 
    def addProperty(self, key, value):
        """ Append the property for the given key """

        if type(key) is str and type(value) is str:
            oldDups = self._storeDuplicates
            self._storeDuplicates = True
            self.processPair(key, value)
            self._storeDuplicates = oldDups
        else:
            raise TypeError,'both key and value should be strings!'

    def propertyNames(self):
        """ Return an iterator over all the keys of the property
        dictionary, i.e the names of the properties """

        return self._props.keys()

    def list(self, out=sys.stdout):
        """ Prints a listing of the properties to the
        stream 'out' which defaults to the standard output """

        out.write('-- listing properties --\n')
        for key,value in self._props.items():
            out.write(''.join((key,'=',value,'\n')))

    def store(self, out, header=""):
        """ Write the properties list to the stream 'out' along
        with the optional 'header' """

        if out.mode[0] != 'w':
            raise ValueError,'Steam should be opened in write mode!'

        try:
            # only tra-files have these Java-headers
            if self._format == 'tra': 
              out.write(''.join(('#',header,'\n')))
              # Write timestamp
              tstamp = time.strftime('%a %b %d %H:%M:%S %Z %Y', time.localtime())
              out.write(''.join(('#',tstamp,'\n')))
              # Write properties in order
              for prop in self._propkeys:
                if prop in self._props:
                  val = self._props[prop]
                  out.write(''.join((prop.split(':')[0],'=',self.escape(val),'\n')))
            elif self._format == 'ini':
              # Write properties
              for prop, val in self._props.items():
                if prop[0:1] != '[':
                  out.write(''.join((prop.split(':')[0],'=',self.escape(val),'\n')))
              for section in self._sections:
                out.write(''.join((section,'\n')))
                for prop, val in self._props.items():
                  if prop.startswith(section):
                    out.write(''.join((prop.split(']', 1)[1].split(':')[0],'=',self.escape(val),'\n')))
            else:
              raise Exception("Invalid format for properties file (only tra and ini supported)")
                
            out.close()
        except IOError, e:
            raise

    def setFormat(self, format):
        self._format = format

    def getFormat(self):
        return self._format

    def getPropertyDict(self):
        return self._props

    def __getitem__(self, name):
        """ To support direct dictionary like access """

        return self.getProperty(name)

    def __setitem__(self, name, value):
        """ To support direct dictionary like access """

        self.setProperty(name, value)
        
    def __getattr__(self, name):
        """ For attributes not found in self, redirect
        to the properties dictionary """

        try:
            return self.__dict__[name]
        except KeyError:
            if hasattr(self._props,name):
                return getattr(self._props, name)

class Permissions(object):
    """ A file permissions retainer """
    
    def __init__(self, filename=None):
        self._stat_ = 0
        if filename:
            self.getPermissions(filename)

    def getPermissions(self, filename):
        self._stat_ = os.stat(filename)
        self._filename_ = filename

    def setPermissions(self, filename=None):
        if not filename:
            filename = self._filename_
        os.chmod(filename, self._stat_.st_mode)
        os.chown(filename, self._stat_.st_uid, self._stat_.st_gid)

# remote copy

def rcopy(host, file):
  if os.path.getsize(file) < 4*1024*1024:
    logging.info("Transferring %s to %s (using scp)" % (file, host))
    lcmd("scp -q %s %s:%s" % (file, host, file), exitonerror=True)
  else:
    lmd5 = lcmd("md5sum %s" % file)[0].split(" ", 1)[0]
    rmd5 = rcmd(host, "[ -e %s ] && md5sum %s" % (file, file))[0].split(" ", 1)[0]
    if lmd5 == rmd5:
      logging.info("Same file %s already exists on %s" % (file, host))
    else:
      logging.info("Transferring %s to %s (using rsync)" % (file, host))
      lcmd("rsync %s %s:%s" % (file, host, file), exitonerror=True)

# remote delete

def rdelete(host, file):
  logging.info("Removing %s from %s" % (file, host))
  lcmd("ssh -t %s '[ -e %s ] && rm %s'" % (host, file, file), exitonerror=True)

# remote command execution

def rcmd(host, cmd, files=[]):
  if type(cmd) is list:
    cmds = ''
    for c in cmd:
      if c in (';', '>'):
        cmds += c
      else:
        cmds += '"' + c + '" '
  else:
    cmds = cmd

  if host == platform.node():
    logging.debug("Executing cmds locally")
    result = lcmd(cmds, exitonerror=True)
  else:
    cmds = '"%s"' % cmds.replace('"', '\\"').replace("'", "\\'")
    if files:
      logging.debug("Transfering temporary files")
      for file in files:
        rcopy(host, file)
      logging.debug("Executing cmds on %s" % (host))
      result = lcmd("ssh -t %s %s" % (host, cmds), exitonerror=True)
      logging.debug("Removing temporary files")
      for file in files:
        if not file.endswith(".rpm"):
          rdelete(host, file)
    else:
      logging.debug("Executing cmds on %s" % (host))
      result = lcmd("ssh -t %s %s" % (host, cmds), exitonerror=True)

  return result

# emscmd: executes EMS-commands

def emscmd(node, url, user, password, cmd):
  tmpfile = tempfile.NamedTemporaryFile(mode="wt")
  try:
    tmpfile.write("\n".join(cmd + ['commit', 'quit']))
    logging.debug(ofs("Preparing EMS-commands: %s" % "\n".join(cmd)))
    tmpfile.flush()

    if url.find(",") >= 0:
      ems1 = url.split('://')[1].split(':')[0]
      emsnode1 = url.split(',')[0]
      result = lcmd("ssh -t %s echo 'show server' | /opt/tibco/bin/tibemsadmin.sh -server %s -user %s -password %s |grep State|grep 'fault tolerant standby'" % (ems1, emsnode1, user, password), exitonerror=True,  returnexitcode=True)
      if result == 0:
        url = url.split(',')[1]+","+url.split(',')[0]

    logging.info("Committing changes to EMS server %s" % url)

    cmd = [
      scriptDir + "/tibemsadmin.sh",
      "-server " + url,
      "-user " + user,
      "-script " + tmpfile.name
    ]
    logging.debug(ofs("Executing: %s" % ' '.join(cmd)))
    if password:
      cmd.append("-password " + password)
    ems70adminexists = lcmd("ssh -t %s [ -d /opt/tibco/ems/7.0/ ]" % (machine), exitonerror=True,  returnexitcode=True)
    ems51adminexists = lcmd("ssh -t %s [ -d /opt/tibco/ems/5.1/ ]" % (machine), exitonerror=True,  returnexitcode=True)
    if ems70adminexists == 0:		 
      logging.debug("Using local emsadmin")
      return rcmd(platform.node(), cmd, files=[tmpfile.name])	  
    elif ems51adminexists == 0:
      logging.debug("Using local emsadmin")
      return rcmd(platform.node(), cmd, files=[tmpfile.name])
    else:
      return rcmd(node, cmd, files=[tmpfile.name])	  
  except:
    return

# lcmd: executes a unix-command locally and returns command output as a string or list of strings

def lcmd(cmd, exitonerror=False, returnexitcode=False, showoutput=False):
  if type(cmd) is list:
    logging.debug(ofs("Executing: " + " ".join(cmd)))
  else:
    logging.debug(ofs("Executing: " + cmd))
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=(type(cmd) is str))
  result = p.communicate()[0]
  logging.debug("Exit code was %d" % p.returncode)
  if showoutput:
    logging.info(result)
  else:
    logging.debug(result)
  if returnexitcode:
    logging.debug("About to return exit code %d" % p.returncode)
    return p.returncode
  elif p.returncode > 0:
    if exitonerror:
      if type(cmd) is list:
        cmd = " ".join(cmd)
      logging.error(ofs("Error %d executing subcommand: %s" % (p.returncode, cmd)))
      sys.exit(p.returncode)
    else:
      logging.debug("About to raise an exception, exit code was %d" % p.returncode)
      logging.error(result)
      raise OSError(p.returncode)
  else:
    logging.debug("About to return, exit code was 0")
    return result.split('\n')
	

def open_deploymentplan(deploymentplan):

  global deployplanDom
  global deployplanContext

  class ErrorHandler:

    def __init__(self):
      self.errors = []

    def handler(self, msg, data):
      self.errors.append(msg)

  # open the deployment plan  
  if deploymentplan.startswith("http://"):
    deployplanDom = libxml2.parseDoc(urllib.urlopen(deploymentplan).read())
  else:
    deployplanDom = libxml2.parseFile(deploymentplan)
  deployplanContext = utils.xml.xpathContext(deployplanDom)
  paths = [os.path.dirname(deploymentplan)]
  
  # resolve includes first
  includes = utils.xml.xpathList(deployplanContext, None, "//xd:include")
  while includes:
    for include in includes:
      filename = include.prop("file")
      if deploymentplan.startswith("http://"):

        filename = os.path.join(os.path.split(deploymentplan)[0], filename)
        logging.info("Included file %s in deployment plan" % filename)
        newDom = libxml2.parseDoc(urllib.urlopen(filename).read())
      elif filename.startswith("http://"):
        logging.info("Included file %s in deployment plan" % filename)
        newDom = libxml2.parseDoc(urllib.urlopen(filename).read())
      else:
        if os.path.dirname(filename) and os.path.exists(filename):
          # if file references existing file including path, add directory to paths 
          filename = os.path.realpath(filename)
          paths.append(os.path.dirname(filename))
        else:
          # search other paths
          found = None
          for path in paths:
            if os.path.exists(os.path.realpath(os.path.join(path, filename))):
              found = os.path.realpath(os.path.join(path, filename))
          if found:
            filename = found
          else:
            raise Exception("Include file %s not found, when processing %s" % (filename, deploymentplan))
        logging.info("Included file %s in deployment plan" % filename)
        newDom = libxml2.parseFile(filename)
      select = include.prop("select")
      if select:
        newDomContext = utils.xml.xpathContext(newDom)
        newNodes = utils.xml.xpathList(newDomContext, None, select)
        for node in newNodes:
          include.addNextSibling(node)
        include.unlinkNode()  
        include.freeNode()
      else:  
        newNode = include.replaceNode(newDom.get_children())
    deployplanXml = deployplanDom.serialize()
    deployplanDom = libxml2.parseDoc(deployplanXml)
    deployplanContext = utils.xml.xpathContext(deployplanDom)
    # determine if reprocessing is required (eg. nested includes)
    includes = utils.xml.xpathList(deployplanContext, None, "//xd:include")

  try:
    ctxt = libxml2.schemaNewParserCtxt("%s/DeploymentPlan_v1.6.2.xsd" % scriptDir)
    schema = ctxt.schemaParse()
    validationCtxt = schema.schemaNewValidCtxt()
    e = ErrorHandler()
    validationCtxt.setValidityErrorHandler(e.handler, e.handler, 'test')
    if validationCtxt.schemaValidateDoc(deployplanDom) or e.errors:
      logging.warning("Deployment plan does not validate against schema (however, this might not be a problem).")
      for msg in e.errors:
        logging.warning(ofs("-> %s" % msg.strip()))
      #sys.exit(1)
  except:
    pass    


def validate_plan(domainname):
  global deployplanDom
  global deployplanContext

  result = True

  if utils.xml.xpathNode(deployplanContext, None, "/xd:deploymentPlan/xd:credentials"):
    logging.error("<credentials> not supported anymore (use: <domain name='' user='' password=''>)")
    result = False

  if domainname:
    domain = utils.xml.xpathNode(deployplanContext, None, "/xd:deploymentPlan/xd:domain[@name='%s']" % domainname)
  if not domain:
    logging.error("No domain configuration for %s found in deployment plan" % domainname)
    result = False
  else:    
      
    cnt = len(utils.xml.xpathList(deployplanContext, domain, "xd:machines/xd:machine[@role='ems']") or [])
    if cnt not in [1, 2]:
      logging.error("Domain requires 1 or 2 EMS-nodes, %d found" % cnt)
      result = False
    elif cnt == 1:
      logging.warning("Recommended is 2 EMS-nodes per domain, only 1 is currently defined")

  return result


def getplanoption(xpath):
  global deployplanDom
  global deployplanContext

  return utils.xml.xpathValue(deployplanContext, None, xpath)


def update_conf(file, nvpairs):
  logging.info("Updating %s", file)
  if os.path.splitext(file)[1] == '.cfg':
    # Support for: .cfg-file format (used for hawkagent.cfg)
    # File-syntax:
    #   sections: -M <section>
    #   keys: -<key> <value>
    # Dictionary-syntax:
    #   keys: <section>:<key>
    #   replace: <section>:<key>=<value>
    #   remove: del:<section>:<key>
    data = {}
    section = ""
    # read data
    for line in open(file).readlines():
      line = line.strip()
      if line.startswith("-M"):
        section = line.split()[1]
      elif line.startswith("-"):
        if " " in line:
          (key, value) = line.split(" ", 1)
        else:
          (key, value) = (line, "")
        data["%s:%s" % (section, key[1:])] = value.strip()
    # create backup
    perms = Permissions(file)
    i = 1
    while os.path.exists("%s.%d" % (file, i)):
      i += 1
    os.rename(file, "%s.%d" % (file, i))
    # process changes
    for nvpair in nvpairs:
      if "=" in nvpair:
        (key, value) = [x.strip() for x in nvpair.split("=", 1)]
      else:
        (key, value) = (nvpair.strip(), "")
      if key.startswith("del:"):
        if key[4:] in data.keys():
          del data[key[4:]]
      elif ":" in key:
        data[key] = value
      else:        
        data[":%s" % key] = value
    # write data
    f = open(file, "w+")
    section = ""
    for key in sorted(data.keys()):
      (nsection, nkey) = key.split(":", 1)
      if nsection != section:
        section = nsection
        print >>f, "-M %s" % (section)
      print >>f, "-%s %s" % (nkey, data[key])
    f.close()
    perms.setPermissions(file)
  elif os.path.splitext(file)[1] == '.xml':
    # Support for: .xml-file format (used for msghma.xml)
    # Dictionary-syntax:
    #   replace: <xpath> <value>
    dom = libxml2.parseFile(file)
    # create backup
    perms = Permissions(file)
    i = 1
    while os.path.exists("%s.%d" % (file, i)):
      i += 1
    os.rename(file, "%s.%d" % (file, i))
    # process changes
    context = utils.xml.xpathContext(dom)
    while nvpairs:
      (xpath, value, nvpairs) = (nvpairs[0], nvpairs[1], nvpairs[2:])
      logging.debug(ofs("xpath=%s value=%s" % (xpath, value)))
      node = utils.xml.xpathNode(context, None, xpath)
      if node:
        logging.debug("Found %s" % xpath)
        logging.debug(ofs("Replacing %s with %s" % (node.content, value)))
        node.setContent(value)
      else:
        logging.debug("Not found %s" % xpath)
    # write data
    open(file, "w+").write(dom.serialize(None, 0))
    perms.setPermissions(file)
  else:
    # Support for: .ini-file format (used for .ini, .conf, .config files)
    # File-syntax:
    #   sections: [<section>]
    #   keys: <key>=<value>
    # Dictionary-syntax:
    #   keys: [<section>]<key>
    #   replace: [<section>]<key>=<value>
    #   remove: del:[<section>]<key>

    # Support for: .tra-file format (used for .tra, .properties, etc.)
    # File-syntax:
    #   keys: <key>=<value>
    # Dictionary-syntax:
    #   keys: <key>
    #   replace: <key>=<value>
    #   remove: del:<key>
    p = Properties()
    if os.path.splitext(file)[1] in ('.ini', '.conf', '.config'):
      p.setFormat("ini")
    else:
      p.setFormat("tra")
    # read data
    if os.path.exists(file):
      p.load(open(file))
    # create backup
    perms = Permissions(file)
    i = 1
    while os.path.exists("%s.%d" % (file, i)):
      i += 1
    os.rename(file, "%s.%d" % (file, i))
    # process changes
    for nvpair in nvpairs:
      try:
        (key, value) = [x.strip() for x in nvpair.split("=", 1)]
      except:
        (key, value) = (nvpair.strip(), "")
      if key.startswith("del:"):
        p.delProperty(key[4:])
      else:        
        p[key] = value
    # write data
    p.store(open(file, "w+"))
    perms.setPermissions(file)

	  
def substitute(arg, context):
    global deployplanDom
    global deployplanContext

    if not arg:
      arg = ""
    result = arg
    while result.find("${") >= 0:
      (part1, rest) = result.split("${", 1)
      if rest.find("}") < 0:
        raise Exception("No closing }-sign in configuration parameter substitution")
      (parameter, rest) = rest.split("}", 1)
      value = utils.xml.xpathValue(deployplanContext, context, "xd:value[@parameter='%s']" % parameter)
      if value is None:
        raise Exception("Parameter %s not found" % parameter)
      result = part1 + value + rest
      logging.debug(ofs("Substituted '%s' for '%s'" % (result, arg)))
    # support for obfuscated strings
    if re.search("^ObFuScAtEd:.*:$", result):
      #logging.debug("De-obfuscated from '%s'" % (result[11:-1]))
      result = re.sub(".(.)", "\g<1>", base64.standard_b64decode(result[11:-1]))
      obfuscated_strings.append(result);
      #logging.debug("De-obfuscated to '%s'" % (result))
    
    return result


def update_ems(machine, domainname, emsport):
  global deployplanDom
  global deployplanContext
 
  # start domain processing
  if domainname:
    domain = utils.xml.xpathNode(deployplanContext, None, "/xd:deploymentPlan/xd:domain[@name='%s']" % domainname)
  if not domain:
    logging.error("No domain %s in deployment plan found" % domainname)
    sys.exit(2)

  for emsconfig in utils.xml.xpathList(deployplanContext, domain, "xd:ems"):
    if str(emsport) == str(substitute(utils.xml.xpathValue(deployplanContext, emsconfig, "@port"), domain)):
      emsuser = substitute(utils.xml.xpathValue(deployplanContext, emsconfig, "@user"), domain)
      emspass = substitute(utils.xml.xpathValue(deployplanContext, emsconfig, "@password"), domain)
      ems = emsconfig
      
  if not emsuser:
    logging.warning("No domain/ems/@user configured for domain.")
    return

  if not emspass:
    logging.warning("No domain/ems/@password configured for domain.")
    return

  cnt = len(utils.xml.xpathList(deployplanContext, domain, "xd:machines/xd:machine[@role='ems']") or [])
  if cnt == 1:
    # single-node ems
    emsnode1 = emsnode2 = utils.xml.xpathValue(deployplanContext, domain, "xd:machines/xd:machine[@role='ems'][1]")
  else:
    # fault-tolerant ems
    emsnode1 = utils.xml.xpathValue(deployplanContext, domain, "xd:machines/xd:machine[@role='ems'][1]")
    emsnode2 = utils.xml.xpathValue(deployplanContext, domain, "xd:machines/xd:machine[@role='ems'][2]")

  emsurl = "tcp://%s:%s,tcp://%s:%s" % (emsnode1, emsport, emsnode2, emsport)

  if opts.updateems:
    topics = []
    queues = []
    factories = []
    bridgesources = []
    bridgecmds = []    
    users = []

    # step 1 - determine existing queues/topics
    mode = None
    end = 0
    for line in emscmd(machine, emsurl, emsuser, emspass, [
      "show topics",
      "show queues",
      "show users",
      "show bridges",
      "show factories",
    ]) or []:
      # command starters
      if line == "Command: show topics":
        mode = "GETTOPICSIZE"
      elif line == "Command: show queues":
        mode = "GETQUEUESIZE"
      elif line == "Command: show users":
        mode = "GETUSERSIZE"
      elif line == "Command: show bridges":
        mode = "GETBRIDGESOURCES"
      elif line == "Command: show factories":
        mode = "GETFACTORIES"		
      elif line == "Command: exit":
        mode = "EXIT"
      # topic processing
      elif line.startswith("  Topic Name") and mode == "GETTOPICSIZE":
        mode = "TOPIC"
        end = line.find(" SNFGEIBCTM ")
      elif mode == "TOPIC":
        topicname = line[2:end].rstrip()
        topics.append(topicname)
        logging.debug("Found existing topic " + topicname)
      # queue processing
      elif line.startswith("  Queue Name") and mode == "GETQUEUESIZE":
        mode = "QUEUE"
        end = line.find(" SNFGXIBCT ")
      elif mode == "QUEUE":
        queuename = line[2:end].rstrip()
        queues.append(queuename)
        logging.debug("Found existing queue " + queuename)
      # factory processing
      elif line.startswith("Factory Type") and mode == "GETFACTORIES":
        mode = "FACTORY"
        end = line.find("JNDI Names")
      elif mode == "FACTORY":
        factoryname = line[2:end].rstrip()
        factories.append(factoryname)
        logging.debug("Found existing factory " + factoryname)
      # bridge processing
      elif line.startswith("  Source Name") and mode == "GETBRIDGESOURCES":
        mode = "BRIDGESOURCE"
        end = line.find(" Queue Targets")
      elif mode == "BRIDGESOURCE":
        if not line:
          pass
        elif line[0] == 'T':
          bridgesources.append("topic " + line[2:end].rstrip())
        elif line[0] == 'Q':
          bridgesources.append("queue " + line[2:end].rstrip())
      # user processing
      elif line.startswith(" User Name") and mode == "GETUSERSIZE":
        mode = "USER"
        end = line.find(" Description")
      elif mode == "USER":
        username = line[1:end].rstrip()
        users.append(username)
        logging.debug("Found existing user " + username)

    # step 2 - get bridge details
    source = None
    end = 0
    for line in emscmd(machine, emsurl, emsuser, emspass, [
      "show bridge %s" % bridge for bridge in bridgesources
    ]) or []:
      # command starters
      if line.startswith("Command: show bridge topic"):
        source = "topic:" + line[27:]
      elif line.startswith("Command: show bridge queue"):
        source = "queue:" + line[27:]
      elif line.startswith("Command: "):
        end = 0
      # process header
      elif line.startswith(" Target Name"):
        end = line.find(" Type")
      elif end:
        target = line[1:end].rstrip()
        if line[end + 4] == 'Q':
          target = 'queue:' + target
        elif line[end + 4] == 'T':
          target = 'topic:' + target
        bridgecmds.append('create bridge source="%s" target="%s"' % (source, target))
  
    # step 3 - create new topics/queues/users and set privileges
    logging.info("Checking for new topics/queues/users")
    cmds = []
    for emsusernode in utils.xml.xpathList(deployplanContext, ems, "xd:create/xd:user"):
      usertocreate = substitute(emsusernode.prop("name"), domain)
      pwdtocreate = utils.xml.xpathValue(deployplanContext, emsusernode, "xd:password")
      if not usertocreate in users:
        cmds += ['create user "%s" password="%s"' % (usertocreate, pwdtocreate)]
        logging.info("Creating user " + usertocreate)
      else:
        logging.debug("Skipped creation of existing user " + usertocreate)

      rights = utils.xml.xpathValue(deployplanContext, emsusernode, "xd:rights")
      logging.info('Setting rights for ' + str(usertocreate) + ' to: ' + str(rights))
      if rights and usertocreate != 'admin':
        cmds += ['grant admin user="%s" %s' % (usertocreate, rights)]

    for topic in utils.xml.xpathList(deployplanContext, ems, "xd:create/xd:topic"):
      topicname = substitute(topic.prop("name"), domain)
      props = ""
      for attr in topic.get_properties() or ():
        if attr.get_type() == "attribute" and attr.name != "name":
          if props: 
            props += ','
          if attr.content == "true":
            props += '%s' % attr.name
          else:
            props += '%s=\"%s\"' % (attr.name, attr.content)
      if not topicname in topics:
        cmds += ['create topic "%s" %s' % (topicname, props)]
        if props:
          logging.info("Creating topic " + topicname + " with properties:" + props)
        else:
          logging.info("Creating topic " + topicname)
      else:
        cmds += ['setprop topic "%s" %s' % (topicname, props)]
        if props:
          logging.info("Updating topic " + topicname + " with properties:" + props)
        else:
          logging.info("Removing properties from existing topic " + topicname)
      # TODO: how to deal with durable subscribers??
      for reader in utils.xml.xpathList(deployplanContext, topic, "xd:reader"):
        if reader.content != 'admin':
          cmds += ['grant topic "%s" user="%s" subscribe,view' % (topicname, reader.content)]
      for writer in utils.xml.xpathList(deployplanContext, topic, "xd:writer"):
        if writer.content != 'admin':
          cmds += ['grant topic "%s" user="%s" publish,view' % (topicname, writer.content)]
      for admin in utils.xml.xpathList(deployplanContext, topic, "xd:admin"):
        if admin.content != 'admin':
          cmds += ['grant topic "%s" user="%s" create,view,delete,modify,purge' % (topicname, admin.content)]

    for queue in utils.xml.xpathList(deployplanContext, ems, "xd:create/xd:queue"):
      queuename = substitute(queue.prop("name"), domain)
      props = ""
      for attr in queue.get_properties() or ():
        if attr.get_type() == "attribute" and attr.name != "name":
          if props: 
            props += ','
          if attr.content == "true":
            props += '%s' % attr.name
          else:
            props += '%s=\"%s\"' % (attr.name, attr.content)
      if not queuename in queues:
        cmds += ['create queue "%s" %s' % (queuename, props)]
        if props:
          logging.info("Creating queue " + queuename + " with properties:" + props)
        else:
          logging.info("Creating queue " + queuename)
      else:
        cmds += ['setprop queue "%s" %s' % (queuename, props)]
        if props:
          logging.info("Updating queue " + queuename + " with properties:" + props)
        else:
          logging.info("Removing properties from existing queue " + queuename)
      for reader in utils.xml.xpathList(deployplanContext, queue, "xd:reader"):
        if reader.content != 'admin':
          cmds += ['grant queue "%s" user="%s" receive,view' % (queuename, reader.content)]
      for writer in utils.xml.xpathList(deployplanContext, queue, "xd:writer"):
        if writer.content != 'admin':
          cmds += ['grant queue "%s" user="%s" send,view' % (queuename, writer.content)]
      for admin in utils.xml.xpathList(deployplanContext, queue, "xd:admin"):
        if admin.content != 'admin':
          cmds += ['grant queue "%s" user="%s" create,view,delete,modify,purge,browse' % (queuename, admin.content)]
		  
    for factory in utils.xml.xpathList(deployplanContext, ems, "xd:create/xd:factory"):
      factoryname = substitute(factory.prop("name"), domain)
      factorytype = substitute(factory.prop("type"), domain)
      logging.info("factory type" + factorytype)
      props = ""
      for attr in factory.get_properties() or ():
        if attr.get_type() == "attribute" and attr.name != "name" and attr.name != "type":
          if props: 
            props += ','
          if attr.content == "true":
            props += '%s' % attr.name
          else:
            props += '%s=\"%s\"' % (attr.name, attr.content)
      if not factoryname in factories:
        cmds += ['create factory "%s" %s %s' % (factoryname, factorytype, props)]
        if props:
          logging.info("Creating factory " + factoryname + factorytype +" with properties:" + props)
        else:
          logging.info("Creating factory " + factoryname)
      else:
        cmds += ['setprop factory "%s" %s' % (factoryname, props)]
        if props:
          logging.info("Updating factory " + factoryname + " with properties:" + props)
        else:
          logging.info("Removing properties from existing factory " + factoryname)	  

    if cmds:
      emscmd(machine, emsurl, emsuser, emspass, cmds)
    else:
      logging.info("No changes have been performed on EMS server %s" % emsurl)

    # step 4 - create new bridges
    logging.info("Checking for new bridges")
    cmds = []
    for topic in utils.xml.xpathList(deployplanContext, ems, "xd:create/xd:topic"):
      topicname = substitute(topic.prop("name"), domain)
      # Topic bridges
      for target in utils.xml.xpathList(deployplanContext, topic, "xd:bridge_to/xd:queue"):
        bridgetarget = substitute(target.prop("name"), domain)
        bridgecmd = 'create bridge source="%s:%s" target="%s:%s"' % ("topic", topicname, "queue", bridgetarget)
        if not bridgecmd in bridgecmds:
          logging.info("Creating bridge from %s to %s" % (topicname, bridgetarget))
          cmds.append(bridgecmd)
      for target in utils.xml.xpathList(deployplanContext, topic, "xd:bridge_to/xd:topic"):
        bridgetarget = substitute(target.prop("name"), domain)
        bridgecmd = 'create bridge source="%s:%s" target="%s:%s"' % ("topic", topicname, "topic", bridgetarget)
        if not bridgecmd in bridgecmds:
          logging.info("Creating bridge from %s to %s" % (topicname, bridgetarget))
          cmds.append(bridgecmd)
      for source in utils.xml.xpathList(deployplanContext, topic, "xd:bridge_from/xd:queue"):
        bridgesource = substitute(source.prop("name"), domain)
        bridgecmd = 'create bridge source="%s:%s" target="%s:%s"' % ("queue", bridgesource, "topic", topicname)
        if not bridgecmd in bridgecmds:
          logging.info("Creating bridge from %s to %s" % (bridgesource, topicname))
          cmds.append(bridgecmd)
      for source in utils.xml.xpathList(deployplanContext, topic, "xd:bridge_from/xd:topic"):
        bridgesource = substitute(source.prop("name"), domain)
        bridgecmd = 'create bridge source="%s:%s" target="%s:%s"' % ("topic", bridgesource, "topic", topicname)
        if not bridgecmd in bridgecmds:
          logging.info("Creating bridge from %s to %s" % (bridgesource, topicname))
          cmds.append(bridgecmd)

    for queue in utils.xml.xpathList(deployplanContext, ems, "xd:create/xd:queue"):
      queuename = substitute(queue.prop("name"), domain)
      # Queue bridges
      for target in utils.xml.xpathList(deployplanContext, queue, "xd:bridge_to/xd:queue"):
        bridgetarget = substitute(target.prop("name"), domain)
        bridgecmd = 'create bridge source="%s:%s" target="%s:%s"' % ("queue", queuename, "queue", bridgetarget)
        if not bridgecmd in bridgecmds:
          logging.info("Creating bridge from %s to %s" % (topicname, bridgetarget))
          cmds.append(bridgecmd)
      for target in utils.xml.xpathList(deployplanContext, queue, "xd:bridge_to/xd:topic"):
        bridgetarget = substitute(target.prop("name"), domain)
        bridgecmd = 'create bridge source="%s:%s" target="%s:%s"' % ("queue", queuename, "topic", bridgetarget)
        if not bridgecmd in bridgecmds:
          logging.info("Creating bridge from %s to %s" % (topicname, bridgetarget))
          cmds.append(bridgecmd)
      for source in utils.xml.xpathList(deployplanContext, queue, "xd:bridge_from/xd:queue"):
        bridgesource = substitute(source.prop("name"), domain)
        bridgecmd = 'create bdirge source="%s:%s" target="%s:%s"' % ("queue", bridgesource, "queue", queuename)
        if not bridgecmd in bridgecmds:
          logging.info("Creating bridge from %s to %s" % (bridgesource, topicname))
          cmds.append(bridgecmd)
      for source in utils.xml.xpathList(deployplanContext, queue, "xd:bridge_from/xd:topic"):
        bridgesource = substitute(source.prop("name"), domain)
        bridgecmd = 'create bridge source="%s:%s" target="%s:%s"' % ("topic", bridgesource, "queue", queuename)
        if not bridgecmd in bridgecmds:
          logging.info("Creating bridge from %s to %s" % (bridgesource, topicname))
          cmds.append(bridgecmd)

    if cmds:
      try:
        emscmd(machine, emsurl, emsuser, emspass, cmds)
      except Exception:
        print "Error due to existing bridges, can be safely ignored\n"
    else:
      logging.info("No changes have been performed on EMS server %s" % emsurl)

 
def deploy_ems(domainname):
  global deployplanDom
  global deployplanContext

  # start domain processing
  if domainname:
    domain = utils.xml.xpathNode(deployplanContext, None, "/xd:deploymentPlan/xd:domain[@name='%s']" % domainname)
  if not domain:
    logging.error("No domain %s in deployment plan found" % domainname)
    sys.exit(2)
  emsnode = utils.xml.xpathValue(deployplanContext, domain, "xd:machines/xd:machine[@role='ems'][1]")
  if not emsnode:
    logging.error("No ems-machine configured for domain %s" % domainname)
    sys.exit(2)
 
  # deploy ems configuration items
  for emsconfig in utils.xml.xpathList(deployplanContext, domain, "xd:ems"):
    emsport = substitute(utils.xml.xpathValue(deployplanContext, emsconfig, "@port"), domain)
    update_ems(emsnode, domainname, emsport)


def deploy_plan(domainname):
  global deployplanDom
  global deployplanContext

  # start domain processing
  if domainname:
    domain = utils.xml.xpathNode(deployplanContext, None, "/xd:deploymentPlan/xd:domain[@name='%s']" % domainname)
  if not domain:
    logging.error("No domain %s in deployment plan found" % domainname)
    sys.exit(2)
  ems = utils.xml.xpathNode(deployplanContext, domain, "xd:machines/xd:machine[@role='ems'][1]")
  if not ems:
    logging.error("No ems-machine configured for domain %s" % domainname)
    sys.exit(2)

  # deploy ems configuration items
  deploy_ems(domainname)

  # finally deploy earfiles
  logging.debug("Start processing .ear-files")
#  for ear in utils.xml.xpathList(deployplanContext, domain, "xd:earfile"):
#    filespec = utils.xml.xpathValue(deployplanContext, ear, "@name")
#    earfile = newest_version(earfiles, filespec)
#    if earfile:
#      logging.debug("Earfile found: " + earfile)
#      for deployment in utils.xml.xpathList(deployplanContext, ear, "xd:deploy"):
#        try:
#          contact = deployment.prop("contact")
#        except:
#          contact = ""
#        try:
#          description = deployment.prop("description")
#        except:
#          description = ""
#        appname = utils.xml.xpathValue(deployplanContext, deployment, "@name")
#        settingsfile = "%s.%s.%s.config.xml" % (earfile[:-4],  os.path.basename(appname), domainname)
#        configfile = earfile[:-4] + ".xml"
#        if not os.path.isfile(configfile):
#          logging.error("Cannot find configfile %s" % configfile)
#          sys.exit(2)
#        logging.info("== Configuring %s" % appname)
#        logging.debug("Reading configfile: %s" % configfile)
#        # load deployment configfile        
#        currentSettingsDom = libxml2.parseFile(configfile)
#        currentSettingsContext = utils.xml.xpathContext(currentSettingsDom)
#        # apply values
#        applyconfig(currentSettingsContext, domain, domain) 
#        applyconfig(currentSettingsContext, ear, domain) 
#        applyconfig(currentSettingsContext, deployment, domain) 
#        # write settingsfile
#        logging.debug("Writing configfile: %s" % settingsfile)
#        open(settingsfile, "w+").write(currentSettingsDom.serialize(None, 0))
#        instances = []
#        for instance in utils.xml.xpathList(deployplanContext, deployment, "xd:machine"):
#          instances.append(instance.content)
#        if instances:
#          deploy(earfile, instances, appname, settingsfile, contact, description)
#        else:
#          deploy(earfile, machines, appname, settingsfile, contact, description)
#    else:
#      logging.debug("No files found matching: %s (skipped)" % filespec)
  
# monitors file or directory for changes and starts deployment using a deploymentplan when a change is detected

def auto_deploy(deploymentplan, domain, targetdir):
  last_deploy = 0
  while True:
    files = earfiles[:] # (shallow-)copy list of earfiles
    # create a list of .ear files
    for f in os.listdir(targetdir):
      if f.endswith(".ear"):
        files.append(os.path.join(targetdir, f))
    filefound = False
    maxtime = 1
    for earfile in files:
      # only if it still exists
      if os.path.isfile(earfile):
        ctime = os.stat(earfile)[stat.ST_CTIME]
        # save file date of newest file
        if ctime > maxtime:
          maxtime = ctime
        # file has been modified since last deployment
        if ctime > last_deploy and last_deploy > 0:
          configfile = earfile[:-4] + ".xml"
          if not os.path.isfile(configfile):
            logging.info("No configfile for %s, waiting for configfile to appear..." % os.path.basename(earfile))
            while not os.path.isfile(configfile):
              time.sleep(5)
          filefound = True
          if not deploymentplan:
            try:
              deploy(earfile, machines, opts.appname)
            except:
              logging.error("Could not deploy %s" % earfile)
    # show message, only when something happened
    if not filefound and not last_deploy:
      # first time
      logging.info("== Auto-deploy waiting for filechanges, press Ctl-C to quit...")
    elif filefound:
      if deploymentplan:
        deploy_plan(deploymentplan, domain)
      # file found (and deployed)
      logging.info("== Finished auto-deploying, press Ctl-C to quit...")
    # register point in time, files created after this moment will trigger the deployment process
    last_deploy = maxtime
    try:
      time.sleep(5)
    except:
      sys.exit(0)
    
#########################################

if __name__ == "__main__":
  # This provides for buildin doctests
  import doctest
  doctest.testmod()

  # Main script starts here
  tibcoHome = "/opt/tibco"
  configDir = tibcoHome + "/etc"
  scriptDir = os.path.abspath(os.path.dirname(sys.argv[0]))
  configDomainDir = configDir + "/domain"
  domainSettingsFile = "domainSettings.xml"
  machine = os.environ.get("HOSTNAME")
  contact = os.environ.get("USER")
  description = ""
  starttime = datetime.datetime.now()
  
  try:
    parser = optparse.OptionParser()
    parser.usage = """tibdeploy [<options>] <cmd>|<targetdir|earfile> [<domain> <user> [<passwd>]]
  <cmd>                 is one of the following:
                          "install-software" installs software based on roles defined in deployment plan
                          "configure-ems" configures ems either single-node or as fault-tolerant pair
                          "create-domain" creates a new domain
                          "update-ems" updates ems resources (queues, topics, users, etc.) from deployment plan
  <targetdir>           used to deploy endpoints in domain, specifies a directory containing .ear-files and config-files for ESB-endpoints
  <earfile>             specifies one or more .ear-files to be deployed (wildcards may be used)
  <user>                domain user that is used to deploy the .ear-files
  <passwd>              domain password (overrides any credentials which may be defined in the deployment plan)"""
    parser.add_option("-d", "--deployment-plan", help="specifies a different deployment plan then the default /opt/tibco/etc/deployment_plan.xml")
    parser.add_option("-c", "--clean", action="store_true", help="removes existing components before deploying")
    parser.add_option("-a", "--auto-deploy", action="store_true", help="starts deployment whenever .ear-files are changed")
    parser.add_option("", "--host", help="provide hostname to perform remote installation on, format: user@host")
    parser.add_option("", "--earfile", help="deploy only a single .ear-file")
    parser.add_option("", "--domain", help="specify the TIBCO domain to deploy on")
    parser.add_option("", "--user", help="user used to login to the domain")
    parser.add_option("", "--passwd", help="password used to login to the domain")
    parser.add_option("", "--appname", help="name of the application")
    parser.add_option("", "--machine", action="append", help="specify a machine on which to deploy a single .ear-file")
    parser.add_option("", "--description", help="specifies the description for deployed components, this is visible in TIBCO Administrator")
    parser.add_option("", "--contact", help="specifies the contact for deployed components, this is visible in TIBCO Administrator")
    parser.add_option("", "--update-ems", dest="updateems", default=True, action="store_true", help="creates EMS items as defined in the deployment plan")
    parser.add_option("", "--no-update-ems", dest="updateems", action="store_false", help="prevents any updates to EMS")
    parser.add_option("", "--remove", action="store_true", help="removes a deployed application from a domain")
    parser.add_option("", "--verbose", action="store_true", help="generates detailed output when deployment progresses")
    parser.add_option("", "--start", action="store_true", help="start the applications after deployment")
    parser.add_option("", "--all-cluster-nodes", dest="allclusternodes", default=False, action="store_true", help="in conjunction with --install-software provisions all cluster-nodes in domain")
    parser.add_option("", "--script-version", action="store_true")
    parser.add_option("", "--no-interaction", action="store_true")
    parser.add_option("", "--logfile", help="specify the name of the logfile to use")
    parser.add_option("", "--show-log", action="store_true")
    opts, args = parser.parse_args()
  except Exception:
    sys.exit(2)

  if opts.script_version:
    print scriptVersion
    sys.exit(0)

  if len(args) and args[0] == "update-conf":
    update_conf(args[1], args[2:])
    sys.exit(0)

  if opts.logfile:
    logfile = opts.logfile
  else:
    logfile = "/var/log/tibco/tibdeploy-%04d%02d%02d-%02d%02d%02d.log" % (starttime.year, starttime.month, starttime.day, starttime.hour, starttime.minute, starttime.second)
  ch = logging.StreamHandler()
  ch.setLevel(logging.INFO)
  if opts.verbose:
    ch.setLevel(logging.DEBUG)
  ch.setFormatter(logging.Formatter("%(message)s"))
  logging.getLogger().addHandler(ch)
  fh = logging.FileHandler(filename=logfile)
  fh.setLevel(logging.DEBUG)
  fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
  logging.getLogger().addHandler(fh)
  logging.getLogger().setLevel(logging.DEBUG)
  #logging.getLogger().setLevel(logging.INFO)

  logging.info("Logging to: %s" % logfile)
  logging.debug("Commandline used: " + " ".join(sys.argv))
  
  opts.verbose = True    
  earfiles = []
  targetdir = None
  deploymentplan = None
  cmd = "deploy"

  if opts.earfile:
    if os.path.isfile(opts.earfile):
      earfiles.append(opts.earfile)
    elif os.path.isfile(opts.earfile + ".ear"):
      earfiles.append(opts.earfile + ".ear")
    else:
      logging.error("Earfile not found")
      sys.exit(2)
  elif not len(args):
    logging.error("Argument cmd, targetdir, earfile or deploymentplan is required")
    sys.exit(2)
  elif args[0] == "install-software":
    print "Deploying software from deployment plan"
    cmd = args.pop(0)
  elif args[0] == "configure-ems":
    print "Configuring ems from deployment plan"
    cmd = args.pop(0)
  elif args[0] == "create-domain":
    print "Configuring domain from deployment plan"
    cmd = args.pop(0)
  elif args[0] == "update-ems":
    print "Updating ems from deployment plan"
    cmd = args.pop(0)
  else:
    source = args.pop(0)
    if os.path.isfile(source):
      if source.endswith(".xml"):
        print "Deployment plan specified: " + source
        deploymentplan = source
      elif source.endswith(".ear"):
        print "Ear-file specified: " + source
        earfiles.append(source)
        targetdir = os.path.dirname(source)
      elif source.endswith(".tgz"):
        if opts.auto_deploy:
          logging.error("Cannot use --auto-deploy when a release archive is specified")
          sys.exit(2)
        # unpack a release to tmp
        logging.info("Unpacking release to /tmp...")
        lcmd("tar -xzf %s -C /tmp" % (source))
        deploymentplan = "/tmp/Tools/etc/deployment_plan.xml"
        targetdir = source = "/tmp/Components"
        for f in os.listdir(source):
          if f.endswith(".ear"):
            earfiles.append(os.path.join(source, f))
      else:
        logging.error("Release-archive (.tgz), ear-file (.ear) or deploymentplan (.xml) expected")
        sys.exit(2)
    elif os.path.isfile(source + ".ear"):
      targetdir = os.path.dirname(source)
      earfiles.append(source + ".ear")
    elif os.path.isdir(source):
      targetdir = source
      if not opts.auto_deploy:
        # only populate when not auto-deploying since auto-deploy rescans the targetdir periodically
        for f in os.listdir(source):
          if f.endswith(".ear"):
            earfiles.append(os.path.join(source, f))

  if opts.deployment_plan:
    deploymentplan = opts.deployment_plan
  elif not deploymentplan and not opts.appname and not opts.contact and os.path.isfile("/opt/tibco/etc/deployment_plan.xml"):
    print "Default deployment plan selected"
    deploymentplan = "/opt/tibco/etc/deployment_plan.xml"
           
  if deploymentplan:
    open_deploymentplan(deploymentplan)
  elif not earfiles:
    if not opts.auto_deploy:
      logging.error("No earfiles specified or found")
      sys.exit(2)
    elif not targetdir:
      logging.error("No target-dir specified with --auto-deploy")
      sys.exit(2)

  if deploymentplan:
    print "Using deployment plan: "+ deploymentplan
  
  if opts.domain:
    domainname = opts.domain
  elif not len(args) and deploymentplan:
    domainname = getplanoption("/xd:deploymentPlan/xd:domain/@name")
  elif len(args) == 0:
    logging.error("Argument domain is required")
    sys.exit(2)
  else:
    domainname = args.pop(0)

  print "Domainname is "+ domainname
 
  if deploymentplan and domainname and not validate_plan(domainname):
    logging.error("Deployment plan does not validate correctly for domain %s" % domainname) 
    sys.exit(2)

  if not opts.host:
    if cmd != 'deploy':
      pass
    elif not os.path.isfile(tibcoHome + "/tra/domain/DomainHomes.properties"):
      if not os.path.isfile(tibcoHome + "/etc/ems/domain/%s/tibemsd.conf" % domainname):
        logging.error("Tibco Administrator not configured for this machine")
        sys.exit(2)
        sys.exit(2)
        sys.exit(2)
    elif not os.path.isdir(tibcoHome + "/tra/domain/" + domainname):
      logging.error("Domain does not exist on this machine")
      sys.exit(2)
  else:
    # check script versions
    try:
      remoteVersion = rcmd(opts.host, "/opt/tibco/bin/tibdeploy.py --script-version")[0]
      if remoteVersion == "":
        logging.error("Scripts not installed on remote host, please install first (eg. installtools.sh %s)." % opts.host)
        sys.exit(2)
      elif utils.version.compareVersions(remoteVersion, scriptVersion) < 0:
        logging.error("Scripts version on host is not up to date (%s<%s), please upgrade." % (remoteVersion, scriptVersion))
        sys.exit(2) 
      elif utils.version.compareVersions(remoteVersion, scriptVersion) < 0:
        logging.error("Scripts version on host is newer (%s>%s), please upgrade local scripts." % (remoteVersion, scriptVersion))
        sys.exit(2) 
    except:
      logging.warn("Unable to check scripts version, continueing.")

  if opts.user:
    user = opts.user
  elif not len(args) and deploymentplan:
    user = getplanoption("/xd:deploymentPlan/xd:domain[@name='%s']/@user" % domainname)
  elif not len(args):
    logging.error("Argument user is required")
    sys.exit(2)
  else:
    user = args.pop(0)
   
  passwd = None
  if opts.passwd:
    passwd = opts.passwd
  elif not len(args) and deploymentplan:
    passwd = getplanoption("/xd:deploymentPlan/xd:domain[@name='%s']/@password" % domainname)
  if not passwd:
    if not len(args):
      if opts.no_interaction:
        logging.error("Need to supply a domain-password")
        sys.exit(2)  
      passwd = getpass.getpass("Domain password: ")
    else:
      passwd = args.pop(0)

  if opts.machine:
    machines = opts.machine
  elif machine:
    machines = [machine]
  elif not deploymentplan:
    logging.error("Machine name for deployment not given.")
    sys.exit(2)

  if opts.description:
    description = opts.description
    
  if opts.contact:
    contact = opts.contact
    
  # real work starts here
  if cmd == "install-software":
    install_software(domainname)
  elif cmd == "configure-ems":
    configure_ems(domainname)
  elif cmd == "create-domain":
    create_domain(domainname)
  elif cmd == "deploy-ems":
    deploy_ems(domainname)
  elif opts.auto_deploy:
    # auto deployment
    auto_deploy(deploymentplan, domainname, targetdir)
  elif deploymentplan:
    # deploy via deployment plan
    deploy_plan(domainname)
  else:
    # simple deployment
    for earfile in earfiles:
      deploy(earfile, machines, opts.appname, None, contact, description)

  totaltime = datetime.datetime.now() - starttime
  if opts.host:
    # Batch deployment on remote host
    logging.info("Finished, entire deployment process took %d minutes and %d seconds." % (totaltime.seconds / 60, totaltime.seconds % 60))
  else:
    logging.info("Finished, deployment took %d minutes and %d seconds." % (totaltime.seconds / 60, totaltime.seconds % 60))

  print "Logfile has been created: %s\n" % logfile

  if opts.show_log:
    lcmd("cat %s" % logfile, showoutput=True)

