from prorail_domain_config import * 

#
# Start script
#

if len(sys.argv) > 1:
  propertiesPath = sys.argv[1]
else:
  propertiesPath = "."

try:

  domainProperties = readProperties(propertiesPath + "/configure-domain.properties")
  domainProperties.load(FileInputStream(propertiesPath + "/install-domain.properties"))
  domainName = domainProperties.getProperty("domain.name", "mydomain")
  userName = domainProperties.getProperty("admin.user", "weblogic")
  passWord = domainProperties.getProperty("admin.password", "welcome1")
  adminServerListenAddress = domainProperties.getProperty("admin.server.address", "localhost")
  adminServerListenPort = int(domainProperties.getProperty("admin.server.port", "7001"))
  dataRootDir = domainProperties.getProperty("data.root.dir", "/data")
  adminServerUrl = "t3://" + adminServerListenAddress + ":" + str(adminServerListenPort)
  domainDir = dataRootDir + "/weblogic/domains/" + domainName
  adminServerName = domainName + "-adminServer"
  wlVersion = domainProperties.getProperty("weblogic.version", "10.3")
  wlHome = "/opt/oracle/middleware/wlserver_" + wlVersion
  nmHome = domainProperties.getProperty("weblogic.nodemanager.home", wlHome + "/common/nodemanager")
  nmPort = int(domainProperties.getProperty("weblogic.nodemanager.port", "5556"))
  nmHost = adminServerListenAddress
  sslEnabled = domainProperties.getProperty("machine.type", "SSL")
  print 'nodemanager host ['+nmHost+'] nodemanager port ['+str(nmPort)+'] password ['+passWord+'] domainDir ['+domainDir+']'
  
  if sslEnabled == 'SSL':
    nmConnect(userName, passWord, nmHost, nmPort, domainName, domainDir, 'ssl')
  else:
    nmConnect(userName, passWord, nmHost, nmPort, domainName, domainDir, 'plain')

  print("Starting admin server under nodemanager control.")
  nmStart(adminServerName, domainDir)
  nmDisconnect()
  connect(userName, passWord, adminServerUrl) 
  print("Discovering managed servers in domain to start.")
  domain = cd("/")
  servers = domain.getServers()
  for s in servers:
    if serverName != adminServerName:
      start(s.getName(), block='false')
  disconnect()
finally:
  exit()
