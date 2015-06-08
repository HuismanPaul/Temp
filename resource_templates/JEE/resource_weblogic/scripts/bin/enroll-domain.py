"""
$Id: enroll-domain.py,v 1.2 2011/03/10 14:40:35 KVP Exp $
@author Mark Heeren

Dit is het WLST script voor preparatie van een nieuw domain op een machine met node manager. Start dit script eenmalig op elke machine van het domain waar minimaal een server onder beheer van een nodemanager moet gaan draaien. Nota bene, de admin server dient al gestart te zijn met het start-domain script.

"""
from prorail_domain_config import *
from wlstModule import *
from java.io import File
from java.lang import RuntimeException


#
# Start script
#
if len(sys.argv) > 1:
  propertiesPath = sys.argv[1]
else:
  propertiesPath = "./"

try:

  # read properties
  domainProperties = readProperties(propertiesPath + "/install-domain.properties")
  #
  domainName = domainProperties.getProperty("domain.name", "mydomain")
  userName = domainProperties.getProperty("admin.user", "weblogic")
  passWord = domainProperties.getProperty("admin.password", "welcome1")
  adminServerListenAddress = domainProperties.getProperty("admin.server.address", "localhost")
  adminServerListenPort = int(domainProperties.getProperty("admin.server.port", "7001"))
  adminServerName = domainName + "-adminServer"
  dataRootDir = domainProperties.getProperty("data.root.dir", "/mnt/data")
  logRootDir = domainProperties.getProperty("log.root.dir", "/var/log")
  domainDir = dataRootDir + "/weblogic/domains/" + domainName
  wlVersion = domainProperties.getProperty("weblogic.version", "10.3")
  wlHome = "/opt/oracle/middleware/wlserver_" + wlVersion
  nmHome = domainProperties.getProperty("weblogic.nodemanager.home", wlHome + "/common/nodemanager")
  nmPort = domainProperties.getProperty("weblogic.nodemanager.port", "5556")
  sslEnabled = domainProperties.getProperty("machine.type", "SSL")
    
  if sslEnabled == 'SSL':
    nmConnect(userName, passWord, adminServerListenAddress,nmPort,domainName, domainDir, 'ssl')
  else:
    nmConnect(userName, passWord, adminServerListenAddress,nmPort,domainName, domainDir, 'plain')

  # start Admin Server
  nmConnect(userName,passWord,adminServerListenAddress,nmPort,domainName, domainDir, 'ssl')
  nmStart(adminServerName)

  # connect to admin server
  adminURL = "t3://" + adminServerListenAddress + ":" + str(adminServerListenPort)
  connect(userName, passWord, adminURL)

  # prepare domain servers for nodemanager startup
  nmEnroll(domainDir, nmHome)

  # prepare servers for nodemanager startup
#  nmEnroll(domainDir, nmHome)
  domain = cd("/")
  servers = domain.getServers()
  for s in servers:
    nmGenBootStartupProps(s.getName())


  nmKill(adminServerName)
  disconnect()
finally:
  dumpStack()
  exit()
