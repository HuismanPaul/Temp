from prorail_domain_config import * 

#
# Start script
#

if len(sys.argv) > 1:
  propertiesPath = sys.argv[1]
else:
  propertiesPath = "."

try:

  domainProperties = readProperties(propertiesPath + "/install-domain.properties")
  domainName = domainProperties.getProperty("domain.name", "mydomain")
  userName = domainProperties.getProperty("admin.user", "weblogic")
  passWord = domainProperties.getProperty("admin.password", "welcome1")
  dataRootDir = domainProperties.getProperty("data.root.dir", "/data")
  domainDir = dataRootDir + "/weblogic/domains/" + domainName
  adminServerName = domainName + "-adminServer"
  adminServerListenAddress = domainProperties.getProperty("admin.server.address", "localhost")
  adminServerListenPort = int(domainProperties.getProperty("admin.server.port", "7001"))
  adminUrl = "t3://" + adminServerListenAddress + ":" + str(adminServerListenPort)
  wlVersion = domainProperties.getProperty("weblogic.version", "10.3")
  wlHome = "/opt/oracle/middleware/wlserver_" + wlVersion
  nmHome = domainProperties.getProperty("weblogic.nodemanager.home", wlHome + "/common/nodemanager")
  nmPort = int(domainProperties.getProperty("weblogic.nodemanager.port", "5556"))
  nmHost = adminServerListenAddress
  sslEnabled = domainProperties.getProperty("machine.type", "SSL")

  connect(userName, passWord, adminUrl)
  print("Discovering managed servers in domain to stop.")
  domain = cd("/")
  servers = domain.getServers()
  for s in servers:
    serverName = s.getName()
    if serverName != adminServerName:
      print("Discovered server %s" % serverName)
      try:
        #machine = cd("/Machines/" + s.getMachine())
        #nm = machine.getNodeManager()
        #nmHost = s.getListenAddress()
        #nmPort = nm.getListenPort()
        nmHost = s.getMachine().getNodeManager().getListenAddress()
	nmPort = s.getMachine().getNodeManager().getListenPort()
	print 'Managed Server ['+serverName+'] has nodemanger:port ['+nmHost+':'+str(nmPort)+']'

        if sslEnabled == 'SSL':
          nmConnect(userName, passWord, nmHost, nmPort, domainName, domainDir, 'ssl')
        else:
          nmConnect(userName, passWord, nmHost, nmPort, domainName, domainDir, 'plain')
        print("Connected to nodemanager. Stopping server %s under nodemanager control." % serverName)
        nmKill(serverName)
        nmDisconnect()
      except:
        dumpStack()
        print("Cannot stop server %s; cannot determine nodemanager" % serverName)

  print("Stopping admin server under nodemanager control.")
  if sslEnabled == 'SSL':
    nmConnect(userName, passWord, nmHost, nmPort, domainName, domainDir, 'ssl')
  else:
    nmConnect(userName, passWord, nmHost, nmPort, domainName, domainDir, 'plain')
  nmKill(adminServerName)

finally:
  dumpStack()
  disconnect()
  exit()
