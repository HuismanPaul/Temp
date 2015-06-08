"""
$Id: install-domain.py,v 1.1 2011/03/09 10:53:32 KVP Exp $
@author Klaas van der Ploeg, Mark Heeren

Dit is het WLST script voor initiele installatie van een nieuwe domain directory.

"""
from prorail_domain_config import *
from wlstModule import *
from java.io import File
from java.lang import RuntimeException

def cleaninit(domainName, userName, passWord, domainDir, adminServerName, adminServerAddress, adminServerListenPort):
  global createdAdminServer
  # start a admin server and connect
  URL = "t3://" + adminServerAddress + ":" + str(adminServerListenPort)
  startServer(adminServerName, domainName, URL, userName, passWord, domainDir, overWriteRootDir='true', block='true',jvmArgs='-Djava.security.egd=file:/dev/./urandom')
  dumpStack()
  createdAdminServer=1
  connect(userName, passWord, URL)

def cleanup():
  global createdAdminServer
  # shutdown the temp server
  if createdAdminServer==1:
    shutdown(force='true', block='true')
  print 'done'

#
# Start script
#
if len(sys.argv) > 1:
  propertiesPath = sys.argv[1]
else:
  propertiesPath = "./"

exitonerror=false
createdAdminServer = 0

try:

  domainProperties = readProperties(propertiesPath + "/install-domain.properties")
  print('Reading properties from: ' + propertiesPath + '/install-domain.properties')
  #getProperty(<propery-to-search>, <default-property>)
  #if property not found, default property is used.
  domainName = domainProperties.getProperty("domain.name", "mydomain")
  userName = domainProperties.getProperty("admin.user", "weblogic")
  passWord = domainProperties.getProperty("admin.password", "welcome1")
  adminServerAddress = domainProperties.getProperty("admin.server.address", "localhost")
  adminServerListenAddress = domainProperties.getProperty("admin.server.listenaddress",adminServerAddress)
  adminServerListenPort = int(domainProperties.getProperty("admin.server.port", "7001"))
  nodemanagerListenPort = int(domainProperties.getProperty("weblogic.nodemanager.port", "5556"))
  print "AdminServerAddress ["+adminServerAddress+"] AdminServerListenAddress ["+adminServerListenAddress+"] AdminServerListenPort ["+str(adminServerListenPort)+"]"
  machines = domainProperties.getProperty("machines", "localhost")
  machineDomain = domainProperties.getProperty("machine.domain", "landelijk.ris")
  machineType = domainProperties.getProperty("machine.type", "SSL")
  postBindGroup = domainProperties.getProperty("machine.postbindgroup", "")
  postBindUser = domainProperties.getProperty("machine.postbinduser", "")
  adminMachineName = domainProperties.getProperty("admin.server.machine", "localhost")
  dataRootDir = domainProperties.getProperty("data.root.dir", "/mnt/data")
  logRootDir = domainProperties.getProperty("log.root.dir", "/var/log")
  domainDir = dataRootDir + "/weblogic/domains/" + domainName
  loggingBaseDir = logRootDir + "/weblogic/domains/" + domainName
  adminServerName = domainName + "-adminServer"
  snmpPort = int(domainProperties.getProperty("snmp.agent.port", "0"))
  remoteTrapDestinationName = domainProperties.getProperty("snmp.agent.trap.destination.name", "BHS")
  remoteTrapDestinationHost = domainProperties.getProperty("snmp.agent.trap.destination.host", "localhost")
  remoteTrapDestinationPort = int(domainProperties.getProperty("snmp.agent.trap.destination.port", "162"))
  wlVersion = domainProperties.getProperty("weblogic.version", "10.3")
  wlHome = "/opt/oracle/middleware/wlserver_" + wlVersion
  nmHome = domainProperties.getProperty("weblogic.nodemanager.home", wlHome + "/common/nodemanager")
  adminJVMArgs = domainProperties.getProperty("admin.server.jvmargs" , "-Xms1024m -Xmx1024m")
  javaHome = domainProperties.getProperty("admin.server.javahome", "")
  beaHome = domainProperties.getProperty("admin.server.beahome", "/opt/oracle/middleware")


  if File(domainDir).exists():
    raise RuntimeException, "Domain already exists in '" + domainDir + "'. Please install into a non-existing directory." 
  cleaninit(domainName, userName, passWord, domainDir, adminServerName, adminServerAddress, adminServerListenPort)
  startTransaction()

  # adjust domain
  setDomainProperties(domainName, adminServerName, loggingBaseDir)

  # create machines
  createMachines(machines,machineDomain,nodemanagerListenPort,postBindGroup,postBindUser,machineType)

  # adjust admin server
  setAdminServerProperties(adminServerName, adminServerListenAddress, adminServerListenPort, adminMachineName, adminJVMArgs, javaHome, beaHome)
  setLogProperties(adminServerName, loggingBaseDir,true)

  # create snmp monitoring agent
  if (snmpPort > 0):
    createSNMPAgent(domainName, snmpPort, remoteTrapDestinationName, remoteTrapDestinationHost, remoteTrapDestinationPort)

  endTransaction()

finally:
  dumpStack()
  cleanup()

