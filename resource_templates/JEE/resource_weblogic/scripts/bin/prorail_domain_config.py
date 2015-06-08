"""
$Id$
@author Klaas van der Ploeg, Mark Heeren, Herman Mensinga, Mario Sosic

Dit is het WLST script dat herbruikbare functies bevat voor het initieel creeren of 
later upgraden van INFOPLUS domain.
"""

from wlstModule import *
from java.util import Properties
from java.io import FileInputStream
import time

def log(message = "NULL", severity = "INFO"):
  print time.strftime("[%A %d/%m/%Y %H:%M:%S]") + " [" + severity + "] " + message
  if severity == "ERROR":
    print "Critical error occurred, Exiting now.."
    raise systemExit 

def readProperties(fileName):
  properties = Properties()
  log("Loading properties from file [" + fileName + "]")
  try:
    properties.load(FileInputStream(fileName))
  except:
    dumpStack()
    log("Error reading properties from file [" + fileName + "]", "ERROR")
  return properties

def init():
  URL = "t3://" + adminServerListenAddress + ":" + adminServerListenPort
  log("Connecting to Admin Server using URL [" + URL + "]")
  try:
    connect(userName, passWord, URL)
  except:
    dumpStack()
    log("Error connecting to URL [" + URL + "] with user [" + userName + "]", "ERROR")

def startTransaction():
  log("Starting edit session.")
  edit()
  startEdit()

def endTransaction():
  log("Starting save and activate.")  
  save()
  dumpStack()
  activate(block="true")
  dumpStack()
  log("Activation complete")

def createMachines(machineNames, fullQualifiedDomain, nodemanagerListenPort, postBindGroup, postBindUser, machineType):
  log("Creating machines.")
  domain = cd("/")
  machines = machineNames.split(",")
  if fullQualifiedDomain != "":
    log("Setting Full Qualified Domain to [." +fullQualifiedDomain + "]")  
    fullQualifiedDomain = "."+fullQualifiedDomain
  for machine in machines:
    log("INFO", "Creating machine ["+machine+"]")
    name = machine
    unixmachine = domain.createUnixMachine(machine)
    if (postBindGroup != ""):
        log("Setting post bind group to [" + postBindGroup+ "]")
        unixmachine.setPostBindGID(postBindGroup)
        log("Setting PostBindGIDEnabled to [true]")
        unixmachine.setPostBindGIDEnabled(true)
    else:
        log("No post bind group configured, clearing value.")
        unixmachine.setPostBindGID("")
        log("No post bind group configured, Setting PostBindGIDEnabled to [false]")
        unixmachine.setPostBindGIDEnabled(false)
    if (postBindUser != ""):
        log("Setting post bind user to [" + postBindUser+ "]")
        unixmachine.setPostBindUID(postBindUser)
        log("Setting PostBindUIDEnabled to [true]")
        unixmachine.setPostBindUIDEnabled(true)
    else:
        log("No post bind user configured, clearing value.")
        unixmachine.setPostBindUID("")
        log("No post bind user configured, Setting PostBindUIDEnabled to [false]")
        unixmachine.setPostBindUIDEnabled(false)
    nodemanager = cd("/Machines/" + machine + "/NodeManager/" + machine)
    log("Setting Listen Address of machine to [" + machine+fullQualifiedDomain +"]")
    nodemanager.setListenAddress(machine+fullQualifiedDomain)
    log("Setting Listen Port of machine to [" + str(nodemanagerListenPort) + "]")
    nodemanager.setListenPort(nodemanagerListenPort)
    log("Setting Type of machine to [" + machineType + "]")
    nodemanager.setNMType(machineType)

def createClusterJobScheduler(clusterName, clusterJobScheduler, clusterJobSchedulerDataSource, clusterJobSchedulerTableName):
  if clusterJobScheduler == 'true':
    try:
      cluster = cd('/Clusters/' + clusterName)
      log("Found cluster %s" % clusterName, "INFO")
    except:
      cluster = None
      log("Cluster does not exsist!", "ERROR")
    if cluster:
      cluster.setJobSchedulerTableName(clusterJobSchedulerTableName)
      log("Setting cluster Job Scheduling table name to %s" % clusterJobSchedulerTableName, "INFO")
      try:
        cluster.setDataSourceForJobScheduler(getMBean('/SystemResources/' + clusterJobSchedulerDataSource))
        log("Setting cluster Job Scheduling Data Source to %s" % clusterJobSchedulerDataSource, "INFO")
      except:
        log("Cluster Job Scheduling Data Source %s not found!" % clusterJobSchedulerDataSource, "ERROR")

def createManagedServer(serverName, listenAddress, listenPort, clusterName, machineName, machineDomain, loggingBaseDir, sslEnabled, sslPort, sslHostnameIgnored, serverArgs, javaHome, javaVendor, beaHome, stuckThreadMaxTime, classPath, redirectToLog, enableDefaultCF, enableTunneling, clusterBroadcastType, unicastListenAddress, unicastListenPort, outboundEnabled, singleServer, panicAction, failureAction):
  log("Creating managed server [" + serverName + "] on machine ["+machineName+"] in cluster: [" + clusterName+"] clusterBroadcastType ["+clusterBroadcastType+"] unicastListenAddress ["+unicastListenAddress+"] unicastListenPort ["+str(unicastListenPort)+"]")  
  domain = cd("/")
  server = None
  try:
    server = cd("/Servers/" + serverName)
    log("Server %s already exists." % serverName, "WARNING")
  except WLSTException:
    dumpStack()
    server = domain.createServer(serverName)
    log("Server %s created." % serverName)

  cd("/Servers/" + serverName)
  # assign cluster and machine
  cluster = getMBean("/Clusters/" + clusterName)
  server.setCluster(cluster)

  machine = getMBean("/Machines/" + machineName)
  server.setMachine(machine)

  # set attributes of server
  server.setListenPort(listenPort)
  server.setListenAddress(listenAddress)
  if (stuckThreadMaxTime > -1):
    log("Setting StuckThreadMaxTime to ["+str(stuckThreadMaxTime)+"]")
    server.setStuckThreadMaxTime(stuckThreadMaxTime)
  else:
    log("Setting StuckThreadMaxTime to default [600]")  
    server.setStuckThreadMaxTime(600)
   
  
  # set SSL attributes
  ssl = cd("/Servers/" + serverName + "/SSL/" + serverName)
  ssl.setEnabled(sslEnabled)
  ssl.setListenPort(sslPort)
  ssl.setHostnameVerificationIgnored(sslHostnameIgnored)
  
  health = cd("/Servers/" + serverName)
  #set("AutoRestart","true")
  #set("RestartMax","1")
  log("Server ["+serverName+"] JMSDefaultConnectionFactoriesEnabled ["+enableDefaultCF+"] TunnelingEnabled ["+enableTunneling+"]")
  #TODO
  set("JMSDefaultConnectionFactoriesEnabled",str(enableDefaultCF))
  set("TunnelingEnabled",enableTunneling)

  # set Log attributes
  setLogProperties(serverName, loggingBaseDir,redirectToLog)

  # set serverstart attributes
  start = cd("/Servers/" + serverName + "/ServerStart/" + serverName)
  if (redirectToLog):
    start.setArguments(serverArgs+" -Xverboselog:"+loggingBaseDir+"/"+serverName+"verbose-gc.log" )
  else:
    start.setArguments(serverArgs)
  start.setJavaHome(javaHome)
  start.setJavaVendor(javaVendor)
  start.setBeaHome(beaHome)
  start.setClassPath(classPath)
  
  #CCB140 - Exit on Out Of Memory Exception (OOME). Applies to all platforms.
  server.setAutoKillIfFailed(true)
  op = server.getOverloadProtection() 
  op.setFailureAction(failureAction)
  op.setPanicAction(panicAction)

  #TODO - better solution for naps, no cd from current base etc
  # check unicast messaging, create and set channel
  log("Server ["+serverName+"] in cluster ["+clusterName+"] clustercommunication ["+clusterBroadcastType+"]")
  if singleServer == 'true':
    log("singleServer = [true], no protocol creating necessary.")
    log("checking if protocols already exists, if so they will be deleted....")
    server = cd("/Servers/" + serverName)
    naps = server.getNetworkAccessPoints()
    for nap in naps:
      server.removeNetworkAccessPoint(nap)
  else:
    if clusterBroadcastType == "unicast":
      naps=cd("/Servers/" + serverName + "/NetworkAccessPoints")
      try:
        nap = cd(clusterName+'UnicastChannel')
        log("NetworkAccessPoint "+clusterName+"UnicastChannel already exist", "WARNING")
      except WLSTException:
        nap=naps.createNetworkAccessPoint(clusterName+'UnicastChannel')
        log("NetworkAccessPoint "+clusterName+"UnicastChannel created")
        nap.setHttpEnabledForThisProtocol(false)
      nap.setProtocol('cluster-broadcast')
      nap.setListenAddress(unicastListenAddress)
      nap.setPublicAddress(unicastListenAddress)
      nap.setListenPort(unicastListenPort)
      nap.setPublicPort(unicastListenPort)
      if outboundEnabled == 'true':
        nap.setOutboundEnabled(true)
        nap.setPublicPort(-1) 
        nap.setPublicAddress('')
      else:
        nap.setOutboundEnabled(false)
        nap.setPublicPort(-1) 
        nap.setPublicAddress('')
  
# Needs online!
def setLogProperties(serverName, loggingBaseDir,redirectToLog):
  # server log
  server = cd("/Servers/" + serverName + "/Log/" + serverName)
  server.setNumberOfFilesLimited(true)
  server.setFileCount(20)
  server.setFileMinSize(5000)
  server.setFileName(loggingBaseDir + "/" + serverName + ".log")
  server.setRedirectStderrToServerLogEnabled(redirectToLog)
  server.setRedirectStdoutToServerLogEnabled(redirectToLog)
  
  # webserver log
  webServerLog = cd("/Servers/" + serverName + "/WebServer/" + serverName + "/WebServerLog/" + serverName)
  webServerLog.setNumberOfFilesLimited(true)
  webServerLog.setFileCount(20)
  webServerLog.setFileMinSize(5000)
  webServerLog.setFileName(loggingBaseDir + "/" + serverName + "-access.log")


def createAndTargetJMSServer(jmsServerName, serverName, jmsFileStoreDir):
  domain = cd("/")
  filestorename = jmsServerName + "-store"
  filestore = None
  try:
    filestore = cd("/FileStores/" + filestorename)
    log("Filestore %s already exists." % filestorename, "WARNING")
  except:
    log("Creating FileStore %s." % filestorename)
    filestore = domain.createFileStore(filestorename)
  
  # set filestore directory
  filestore.setDirectory(jmsFileStoreDir)
  
  # target to server
  # @TODO: target to migrateable target
  server = getMBean("/Servers/" + serverName)
  theValue = jarray.array([server], Class.forName("weblogic.management.configuration.TargetMBean"))
  filestore.setTargets(theValue)

  # create normal and nonpersistent jms server
  pJms = None
  try:
    pJms = cd("/JMSServers/" + jmsServerName)
    log("JMS Server %s already exists." % jmsServerName, "WARNING")
  except:
    log("Creating JMS server %s" % jmsServerName)
    pJms = domain.createJMSServer(jmsServerName)
  npJms = None
  try:
    npJms = cd("/JMSServers/" + jmsServerName + "-nonpersistent")
    log("JMS Server %s-nonpersistent already exists." % jmsServerName, "WARNING")
  except:
    log("Creating JMS server %s-nonpersistent" % jmsServerName)  
    npJms = domain.createJMSServer(jmsServerName + "-nonpersistent")
  
  # nonpersistent
  # max 100M of msgs
  npJms.setBytesMaximum(100000000)
  npJms.setStoreEnabled(false)
  # persistent downgrade for backwards compatibility
  npJms.setAllowsPersistentDowngrade(true)

  
  # target to managed server
  npJms.addTarget(getMBean("/Servers/" + serverName))
  
  # persistent  
  # max 100M of msgs
  pJms.setBytesMaximum(100000000)
  
  # assign filestore
  bean = getMBean("/FileStores/" + filestorename)
  pJms.setPersistentStore(filestore)

  # target to managed server
  pJms.addTarget(getMBean("/Servers/" + serverName))

def cleaninit(adminServerListenAddress, adminServerListenPort):
  global createdAdminServer
  # start a admin server and connect
  URL = "t3://" + adminServerListenAddress + ":" + adminServerListenPort
  startServer(adminServerName, domainName, URL, userName, passWord, domainDir, overWriteRootDir='true', block='false')
  dumpStack()
  createdAdminServer=1
  connect(userName, passWord, URL)

def cleanup():
  global createdAdminServer
  # shutdown the temp server
  if createdAdminServer==1:
    shutdown(force='true', block='true')
  log("Done cleaning up..")


def createDiagnosticModule(dmName):
  try:
    dm = cd("/WLDFSystemResources/" + dmName)
    log("Diagnostic Module [" + dmName + "] already exists", "WARNING")
  except WLSTException:
    dumpStack()
    domain = cd("/")
    dm = domain.createWLDFSystemResource(dmName)
    
def createJDBCDataSource(targets, name, jndiName, useXA, emulateXA, dbHost, dbPort, dbName, dbUser, dbPassword, dbPool, serviceName, testFrequency, statementCache, retryFrequency,shrinkFrequency, reserveTimeout, extraParams, readTimeout, loggingLastResource):
  log("Creating jdbcDataSource name ["+name+"] on targets ["+targets+"] on nodes ["+dbHost+"]")
  nodes = dbHost.split(",")
  instances = dbName.split(",")
  if len(nodes) > 1:
    #create single datasource for each cluster node; create multi datasource to include these
    log("JDBCDataSource '%s' has multiple hosts; creating as MultiDataSource." % name)
    i = 1
    j = 0
    nodeDSList = ""
    for node in nodes:
      nodeDSName = name + "-node" + str(i)
      if i > 1:
        nodeDSList = nodeDSList + ","
      nodeDSList = nodeDSList + nodeDSName
      nodeDSJndiName = jndiName + "-node" + str(i)
      log("Creating JDBCDataSource '"+name+"' for node '"+node+"'")
      createJDBCDataSourceForNode(targets, nodeDSName, nodeDSJndiName, useXA, emulateXA, node, dbPort, instances[j], dbUser, dbPassword, dbPool, serviceName, testFrequency, statementCache, retryFrequency, reserveTimeout, shrinkFrequency, extraParams, readTimeout, loggingLastResource)
      i = i + 1
      j = j + 1

    #create multi datasource
    domain = cd("/")
    multiDS = None
    try:
      multiDS = cd("/JDBCSystemResources/" + name)
      log("MultiDataSource %s already exists." % name, "WARNING")
    except WLSTException:
      dumpStack()
      multiDS = domain.createJDBCSystemResource(name)
      log("MultiDataSource %s created." % name)

    #Removing targets
    currentTargets = multiDS.getTargets()
    
    for currentTarget in currentTargets:
      multiDS.removeTarget(currentTarget)
    
    #Getting targets from config
    allTargets = targets.split(",")
    
    for target in allTargets:
      try:
        cluster = cd("/Clusters/" + target)
        log("Found cluster [" + cluster.getName() + "]")
        multiDS.addTarget(cluster)
      except WLSTException:
        server = cd("/Servers/" + target)
        log("Found server [" + server.getName() + "]")
        multiDS.addTarget(server)
    
    #set name
    jdbc = cd("/JDBCSystemResources/" + name + "/JDBCResource/" + name)
    jdbc.setName(name)
  
    #set datasource attributes
    dsParams = cd("/JDBCSystemResources/" + name + "/JDBCResource/" + name + "/JDBCDataSourceParams/" +name)
    dsParams.setAlgorithmType("Load-Balancing")
    dsParams.setDataSourceList(nodeDSList)
    dsParams.setJNDINames(jarray.array([jndiName], String))

    dsParams = cd("/JDBCSystemResources/" + name + "/JDBCResource/" + name + "/JDBCConnectionPoolParams/" +name)
    dsParams.setTestFrequencySeconds(120)
  else:
    #create single datasource 
    createJDBCDataSourceForNode(targets, name, jndiName, useXA, emulateXA, dbHost, dbPort, dbName, dbUser, dbPassword, dbPool, serviceName, testFrequency, statementCache, retryFrequency, shrinkFrequency, reserveTimeout, extraParams, readTimeout, loggingLastResource)

def createJDBCDataSourceForNode(targets, name, jndiName, useXA, emulateXA, dbHost, dbPort, dbName, dbUser, dbPassword, dbPool, serviceName, testFrequency, statementCache, retryFrequency, shrinkFrequency, reserveTimeout, extraParams, readTimeout, loggingLastResource):
  domain = cd("/")
  ds = None
  try:
    ds = cd("/JDBCSystemResources/" + name)
    log("DataSource %s already exists." % name, "WARNING")
  except WLSTException:
    dumpStack()
    ds = domain.createJDBCSystemResource(name)
    log("DataSource %s is created." % name)
  
  #Removing targets
  currentTargets = ds.getTargets() 
  for currentTarget in currentTargets:
    ds.removeTarget(currentTarget)
  
  allTargets = targets.split(",")
  
  for target in allTargets:
    try:  
      cluster = cd("/Clusters/" + target)
      log("Found cluster [" + cluster.getName() + "]")
      ds.addTarget(cluster)
    except WLSTException:
      server = cd("/Servers/" + target)
      log("Found server [" + server.getName() + "]")
      ds.addTarget(server)
  
  jdbc = cd("/JDBCSystemResources/" + name + "/JDBCResource/" + name)
  jdbc.setName(name)
  
  #driver params
  params = cd("/JDBCSystemResources/" + name + "/JDBCResource/" + name + "/JDBCDriverParams/" + name)
  if (dbName != ""):
      params.setUrl("jdbc:oracle:thin:@(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCP)(HOST=" + dbHost + ")(PORT=" + str(dbPort) + ")))(CONNECT_DATA=(SERVICE_NAME=" + serviceName + ")(INSTANCE_NAME=" + dbName + ")))")
  else:    
      params.setUrl("jdbc:oracle:thin:@(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCP)(HOST=" + dbHost + ")(PORT=" + str(dbPort) + ")))(CONNECT_DATA=(SERVICE_NAME=" + serviceName + ")))")

  if useXA:
    params.setDriverName("oracle.jdbc.xa.client.OracleXADataSource")
  else:
    params.setDriverName("oracle.jdbc.OracleDriver")
  params.setPassword(dbPassword)
  props = params.getProperties()
  try:
    userProp = props.createProperty("user")
    userProp.setValue(dbUser)
  except Exception:
    dumpStack()
    log("User property already exists.", "WARNING")
  if extraParams == "true":
    try:
      userProp = props.createProperty("oracle.jdbc.ReadTimeout")
      userProp.setValue(readTimeout)
    except Exception:
      dumpStack()
      log("Property already exists.", "WARNING")
    try:
      userProp = props.createProperty("oracle.jdbc.implicitstatementcachesize")
      userProp.setValue("15")
    except Exception:
      dumpStack()
      log("Property already exists.", "WARNING")
  #else:
  #  try:
  #    userProp = props.createProperty("oracle.net.CONNECT_TIMEOUT")
  #    userProp.setValue("10000")
  #  except Exception:
  #    dumpStack()
  #    log("oracle.net.CONNECT_TIMEOUT property already exists.", "WARNING")

  #datasource params
  dsParams = cd("/JDBCSystemResources/" + name + "/JDBCResource/" + name + "/JDBCDataSourceParams/" + name)
  if useXA==false:
    dsParams.setGlobalTransactionsProtocol("None")
  if useXA:
    dsParams.setGlobalTransactionsProtocol('TwoPhaseCommit')
  if emulateXA == "True":
    if loggingLastResource == "True":
      dsParams.setGlobalTransactionsProtocol('LoggingLastResource')
    else:
      dsParams.setGlobalTransactionsProtocol('EmulateTwoPhaseCommit')


  else:
    dsParams.setGlobalTransactionsProtocol("None")
  dsParams.setJNDINames(jarray.array([jndiName], String))
  
  #connectionpool params
  poolparams = cd("/JDBCSystemResources/" + name + "/JDBCResource/" + name + "/JDBCConnectionPoolParams/" + name)
  poolparams.setTestTableName("SQL SELECT 1 FROM DUAL")
  poolparams.setTestConnectionsOnReserve(true)
  poolparams.setInitialCapacity(0)
  poolparams.setMaxCapacity(dbPool)
  poolparams.setPinnedToThread(false)
  poolparams.setStatementCacheSize(statementCache)
  poolparams.setTestFrequencySeconds(testFrequency)
  poolparams.setSecondsToTrustAnIdlePoolConnection(0)
  poolparams.setConnectionCreationRetryFrequencySeconds(retryFrequency)  
  poolparams.setShrinkFrequencySeconds(shrinkFrequency)
  poolparams.setConnectionReserveTimeoutSeconds(reserveTimeout)

  #XA params
  if useXA:
    xaparams = cd("/JDBCSystemResources/" + name + "/JDBCResource/" + name + "/JDBCXAParams/" + name)
    xaparams.setKeepXaConnTillTxComplete(true)
    xaparams.setXaRetryDurationSeconds(300)
  

def createForeignServerWithAllQueues(targetJmsModule, sourceJmsModule, factoryName):
  foreignServer = createForeignServer(targetJmsModule, sourceJmsModule, factoryName)

def addAllQueuesToForeignServer(foreignServer, sourceJmsModule):
  # create all destinations off sourceJmsModule
  jr = cd("/JMSSystemResources/" + sourceJmsModule + "/JMSResource/" + sourceJmsModule)
  queues = jr.getUniformDistributedQueues()
  for queue in queues:
    addQueueToForeignServer(foreignServer, queue.getName())

def addQueueToForeignServer(foreignServer, destinationName, remoteDestination=""):
  fsPath = getPath(foreignServer)
  foreignDestination = None
  try:
    foreignDestination = cd("/" + fsPath + "/ForeignDestinations/" + destinationName)
    log("ForeignDestination %s already exists." % destinationName, "WARNING")
  except:
    dumpStack()
    log("creating foreign destination " + destinationName + " to " + foreignServer.getName())
    foreignDestination = foreignServer.createForeignDestination(destinationName)
  foreignDestination.setLocalJNDIName(destinationName)
  if remoteDestination=="":
    remoteDestination = destinationName
  foreignDestination.setRemoteJNDIName(remoteDestination)

def addFactoryToForeignServer(foreignServer, sourceFactoryName, targetFactoryName, userName, passwd, fscf):
  fsPath = getPath(foreignServer)
  log("fsPath = " + fsPath, "DEBUG")
  foreignFactory = None
  try:
    foreignFactory = cd("/" + fsPath + "/ForeignConnectionFactories/" + fscf)
    log("ForeignConnectionFactory %s already exists." % fscf, "WARNING")
  except:
    dumpStack()
    log("add factory " + sourceFactoryName + " to " + foreignServer.getName())
    foreignFactory = foreignServer.createForeignConnectionFactory(fscf)
  foreignFactory.setLocalJNDIName(targetFactoryName)
  foreignFactory.setRemoteJNDIName(sourceFactoryName)
  if userName != '':
    foreignFactory.setUsername(userName)
  else:
    foreignFactory.setUsername('')
  if passwd != '':
    foreignFactory.setPassword(passwd)
  else:
    foreignFactory.setPassword('')  

def createForeignServerForAddress(targetJmsModule, sourceJmsModule, dataSource, contextFactory, clusterUrl, jndiProperties, jndiCredentials):
  log('prorailcreate ' + dataSource + ' ' + contextFactory)
  jr = cd("/JMSSystemResources/" + targetJmsModule + "/JMSResource/" + targetJmsModule)
  try:
    foreignServer = cd("/JMSSystemResources/" + targetJmsModule + "/JMSResource/" + targetJmsModule + "/ForeignServers/" + sourceJmsModule)
    log("Foreign Server %s already exists." % targetJmsModule, "WARNING")
  except:
    dumpStack()
    log("Creating foreign server: " + sourceJmsModule + " in " + targetJmsModule)
    foreignServer = jr.createForeignServer(sourceJmsModule)
  foreignServer.setConnectionURL(clusterUrl)
  foreignServer.setInitialContextFactory(contextFactory)
  foreignServer.setDefaultTargetingEnabled(true)

  if dataSource != "":
    try:
      props = cd("/JMSSystemResources/" + targetJmsModule + "/JMSResource/" + targetJmsModule + "/ForeignServers/" + sourceJmsModule + "/JNDIProperties/datasource")
      log("JNDI property 'datasource' already exists", "WARNING")
    except:
      dumpStack()
      log("creating JNDI property 'datasource'")
      foreignServer.createJNDIProperty('datasource')
    props = cd("/JMSSystemResources/" + targetJmsModule + "/JMSResource/" + targetJmsModule + "/ForeignServers/" + sourceJmsModule + "/JNDIProperties/datasource")
    props.setValue(dataSource)
  
  if jndiProperties == "true":
    try:
      prop = foreignServer.createJNDIProperty('java.naming.security.principal')
      prop.setValue('vos')
    except:
      log("Property already exists!", "WARNING") 
    foreignServer.setJNDIPropertiesCredential(jndiCredentials)
  elif jndiProperties == "aga":
    try:
      prop = foreignServer.createJNDIProperty('java.naming.security.principal')
      prop.setValue('aga')
    except:
      log("Property already exists!", "WARNING")
    foreignServer.setJNDIPropertiesCredential(jndiCredentials)
    try:
      prop = foreignServer.createJNDIProperty('java.naming.factory.url.pkgs')
      prop.setValue('com.tibco.tibjms.naming')
    except:
      log("Property already exists!", "WARNING")
  return foreignServer

def getClusterUrlForResource(sourceJmsModule):
  sourceModule = cd("/JMSSystemResources/" + sourceJmsModule)
  result = 't3://'
  seperator = ''
  targets = sourceModule.getTargets()
  for target in targets:
    log("target = " + target, "DEBUG")
    servers = target.getServers()
    for server in servers:
      result = result + seperator + server.getListenAddress() + ':' + str(server.getListenPort())
      seperator = ','
  log('returning result value: ' + result)
  return result

def createJmsServers(targetCluster, jmsServerName, numberOfServers, jmsFileStoreDir):
  cluster =  cd('/Clusters/' + targetCluster)
  servers = cluster.getServers()
  for server in servers:
    createAndTargetJMSServer(jmsServerName +  server.getName()[-1], server.getName(), jmsFileStoreDir)


def createJMSSystemResource(jmsSystemResourceName, theClustername, theJmsServerNamePrefix):
  domain = cd("/")
  jsr = None
  try:
    jsr = cd("/JMSSystemResources/" + jmsSystemResourceName)
    log("JMSSystemResource %s already exists." % jmsSystemResourceName)
  except:
    dumpStack()
    log("Creating JMSSystemResource %s." % jmsSystemResourceName)
    jsr = domain.createJMSSystemResource(jmsSystemResourceName)
  # @TODO: should also support servers 
  for cluster in theClustername.split(','):
   log("targeting cluster: " + cluster)
   cluster = getMBean("/Clusters/" + cluster)
   jsr.addTarget(cluster)

def createQuota(jmsSystemResourceName, jmsQuotaName, maxBytes):
  jmsResource = cd("/JMSSystemResources/" + jmsSystemResourceName + "/JMSResource/" + jmsSystemResourceName)
  try:
    quota = cd("/JMSSystemResources/" + jmsSystemResourceName + "/JMSResource/" + jmsSystemResourceName + "/Quotas/" + jmsQuotaName)
    log("Quota " + jmsQuotaName + " already exists.", "WARNING")
  except:
    quota = jmsResource.createQuota(jmsQuotaName)
  quota.setBytesMaximum(long(maxBytes))
  quota.setShared(false)

def createJmsSubDeployment(jmsModuleName, jmsSubDeploymentName, numServers, theJmsServerNamePrefix):
  module = cd('/JMSSystemResources/' + jmsModuleName)
  try:
    subDeployment = cd ("/JMSSystemResources/" + jmsModuleName + "/SubDeployments/" + jmsSubDeploymentName)
    log("SubDeployment " + jmsSubDeploymentName + " already exists.", "WARNING")
  except:
    subDeployment = module.createSubDeployment(jmsSubDeploymentName)
  for i in range(1, int(numServers) + 1):
    name = theJmsServerNamePrefix + str(i)
    if "nonpersistent" in jmsSubDeploymentName:
      subDeployment.addTarget(getMBean("/JMSServers/" + name + '-nonpersistent'))
    else:
      subDeployment.addTarget(getMBean("/JMSServers/" + name))
    
def createQueueWithErrorDestination(jmsSystemResource, queueName, quotaType, jndiName, errorDestination,subDeploymentName,ttl, forwardDelay,expirationPolicy,expirationLoggingPolicy):
  # create queue
  createQueue(jmsSystemResource, queueName, quotaType,jndiName,subDeploymentName,ttl, forwardDelay,expirationPolicy,expirationLoggingPolicy)
  udq = cd("/JMSSystemResources/" + jmsSystemResource + "/JMSResource/" + jmsSystemResource + "/UniformDistributedQueues/" + queueName + "/DeliveryFailureParams/" + queueName)
  # set error destination
  udq.setErrorDestination(getMBean("/JMSSystemResources/" + jmsSystemResource + "/JMSResource/" + jmsSystemResource + "/UniformDistributedQueues/" + errorDestination))
  udq.setExpirationPolicy('Redirect')

def createQueue(jmsSystemResource, queueName, quotaType, jndiName, subDeploymentName,ttl,forwardDelay,expirationPolicy,expirationLoggingPolicy):
  jr = cd("/JMSSystemResources/" + jmsSystemResource + "/JMSResource/" + jmsSystemResource)
  udq = None
  try:
    udq = cd("/JMSSystemResources/" + jmsSystemResource + "/JMSResource/" + jmsSystemResource + "/UniformDistributedQueues/" + queueName)
    log("Queue %s already exists." % queueName, "WARNING")
  except:
    log("Creating uniform distributed queue %s." % queueName)
    udq = jr.createUniformDistributedQueue(queueName)
  udq.setDefaultTargetingEnabled(false)
  udq.setName(queueName)
  udq.setLoadBalancingPolicy("Round-Robin")
  udq.setJNDIName(jndiName)
  udq.setForwardDelay(forwardDelay)
  #udq.setSubDeploymentName("sub-persistent")
  udq.setSubDeploymentName(subDeploymentName)
  udq.getDeliveryFailureParams().setExpirationPolicy(expirationPolicy)
  udq.getDeliveryFailureParams().setExpirationLoggingPolicy(expirationLoggingPolicy)
  overrides = cd("/JMSSystemResources/" + jmsSystemResource + "/JMSResource/" + jmsSystemResource + "/UniformDistributedQueues/" + queueName + "/DeliveryParamsOverrides/"+ queueName)
  overrides.setTimeToLive(ttl)
  # set quota
  quota = getMBean("/JMSSystemResources/" + jmsSystemResource + "/JMSResource/" + jmsSystemResource + "/Quotas/" + "quota-" + quotaType)
  udq.setQuota(quota)

def createTopic(jmsSystemResource, topicName, quotaType, ttl):
  jr = cd("/JMSSystemResources/" + jmsSystemResource + "/JMSResource/" + jmsSystemResource)
  udt = None
  try:
    udt = cd("/JMSSystemResources/" + jmsSystemResource + "/JMSResource/" + jmsSystemResource + "/UniformDistributedTopics/" + topicName)
    log("Topic %s already exists." % topicName, "WARNING")
  except:
    log("Creating uniform distributed topic %s." % topicName)
    udt = jr.createUniformDistributedTopic(topicName)
  # no default targetting for topics (nonpersistent)
  udt.setDefaultTargetingEnabled(false)
  udt.setName(topicName)
  udt.setJNDIName(topicName)
  udt.setSubDeploymentName("sub-nonpersistent")
  #set ttl for topics. default is -1
  overrides = cd("/JMSSystemResources/" + jmsSystemResource + "/JMSResource/" + jmsSystemResource + "/UniformDistributedTopics/" + topicName + "/DeliveryParamsOverrides/" + topicName)
  overrides.setTimeToLive(ttl)

def createConnectionFactory(jmsSystemResourceName, factoryName, useXA, reconnectPolicy, jndiName, serverAffinity):
  log('creating ' + factoryName + ' with jndiName '+jndiName+' on ' + jmsSystemResourceName)
  jr = cd("/JMSSystemResources/" + jmsSystemResourceName + "/JMSResource/" + jmsSystemResourceName)
  cf = None
  try:
    cf = cd("/JMSSystemResources/" + jmsSystemResourceName + "/JMSResource/" + jmsSystemResourceName + "/ConnectionFactories/" + factoryName)
    log("ConnectionFactory %s already exists." % factoryName, "WARNING")
  except:
    log("Creating ConnectionFactory %s." % factoryName)
    cf = jr.createConnectionFactory(factoryName)
  cf.setDefaultTargetingEnabled(true)
  cf.setName(factoryName)
  cf.setJNDIName(jndiName)  
  cf.getLoadBalancingParams().setServerAffinityEnabled(serverAffinity)
  if useXA:
    transparams = cd("/JMSSystemResources/" + jmsSystemResourceName + "/JMSResource/" + jmsSystemResourceName + "/ConnectionFactories/" + factoryName + "/TransactionParams/" + factoryName)
    transparams.setXAConnectionFactoryEnabled(true)
  if reconnectPolicy != "":
    connectionFactory = getMBean("/JMSSystemResources/" + jmsSystemResourceName + "/JMSResource/" + jmsSystemResourceName + "/ConnectionFactories/" + factoryName)
    log('Setting reconnect policy on ' + connectionFactory.getName() + ' to ' + reconnectPolicy)
    connectionFactory.getClientParams().setReconnectPolicy(reconnectPolicy)

def setDomainProperties(domainName, adminServerName, loggingBaseDir, notes = "1.0", productionMode = true):
  domain = cd("/")
  domain.setName(domainName)
  domain.setAdminServerName(adminServerName)
  domain.setProductionModeEnabled(productionMode)
  domain.setNotes(notes)
  setDomainLogProperties(domainName, loggingBaseDir)

# Needs online!
def setDomainLogProperties(domainName, loggingBaseDir):
  domainLog = cd("/Log/" + domainName)
  domainLog.setNumberOfFilesLimited(true)
  domainLog.setFileCount(10)
  domainLog.setFileMinSize(5000)
  domainLog.setFileName(loggingBaseDir + "/" + domainName + ".log")
  
def createSNMPAgent(domainName, snmpPort, remoteTrapDestinationName, remoteTrapDestinationHost, remoteTrapDestinationPort):
  # Enable SNMP agent
  domain = cd("/")
  agent = domain.createSNMPAgentDeployment(domainName)
  agent.setEnabled(true)
  agent.setSNMPPort(snmpPort)
  # destination
  destination = agent.createSNMPTrapDestination(remoteTrapDestinationName)
  destination.setHost(remoteTrapDestinationHost)
  destination.setPort(int(remoteTrapDestinationPort))
  # log filter
  logfilter = agent.createSNMPLogFilter("All")
  logfilter.setSeverityLevel("Notice")
  # add servers to filter
  servers = domain.getServers()
  for server in servers:
    logfilter.addEnabledServer(server)

def setAdminServerProperties(adminServerName, adminServerListenAddress, adminServerListenPort, adminMachineName, adminJVMArgs, javaHome, beaHome):
  adminServer = cd("/Servers/" + adminServerName)
  adminServer.setListenAddress(adminServerListenAddress)
  adminServer.setListenPort(adminServerListenPort)
  
  #pointing adminserver to correct machine
  adminMachine = getMBean("/Machines/" + adminMachineName)
  adminServer.setMachine(adminMachine)
  #Setting the server start parameters
  start = cd("/Servers/" + adminServerName + "/ServerStart/" + adminServerName)
  start.setArguments(adminJVMArgs + ' -Djava.security.egd=file:/dev/./urandom')
  start.setJavaHome(javaHome)
  start.setBeaHome(beaHome)
  #set("JavaVendor",javaVendor)

def enableAdminserverTunneling(adminServerName):
  adminServer = cd("/Servers/"+adminServerName)
  adminServer.setTunnelingEnabled(true)

def setQueueRedelivery(resource, queueName, redeliveryValue):
  log('Setting RedeliveryLimit on ' + queueName + ' in ' + resource + ': ' + str(redeliveryValue))
  udq = cd("/JMSSystemResources/" + resource + "/JMSResource/" + resource + "/UniformDistributedQueues/" + queueName + "/DeliveryFailureParams/" + queueName)
  udq.setRedeliveryLimit(redeliveryValue)
  
def setJDBCGlobalTransactionProtocol(datasourceName, protocolName):
  log('Setting global transaction protocol on ' + datasourceName + ' to ' + protocolName)
  jdbcParams = getMBean("/JDBCSystemResources/" + datasourceName + "/JDBCResource/" + datasourceName + "/JDBCDataSourceParams/" + datasourceName) 
  jdbcParams.setGlobalTransactionsProtocol(protocolName)

def createDefaultRealmGroup(groupName,groupDescription):
    log('Creating group '+groupName+' with description '+groupDescription)
    domain=cd("/")
    atnr=domain.getSecurityConfiguration().getDefaultRealm().lookupAuthenticationProvider('DefaultAuthenticator')
    if atnr.groupExists(groupName) == false:
        atnr.createGroup(groupName, groupDescription)
        log('Group created')
    else:
        log('Skipping, group already exists', "WARNING")
        
def createDefaultRealmUser(user, passWord, userDescription, groupName):
    log('Creating user '+user+' with description '+userDescription+' in group '+groupName)
    domain=cd("/")
    atnr=domain.getSecurityConfiguration().getDefaultRealm().lookupAuthenticationProvider('DefaultAuthenticator')
    if atnr.groupExists(groupName) == true:
        if atnr.userExists(user) == false:
            atnr.createUser(user, passWord, userDescription)
        else:
            log('Skipping, user already exists', "WARNING")
        atnr.addMemberToGroup(groupName, user)
    else:
        log('Group does not exist!', "CRITICAL")
        raise WLSTException("Group does not exist!")

def createSingletonEnvironment(serverName, channelName, listenAddress, listenPort, classpath, failureAction, panicAction):
  #specific config for SBG  
  domain = cd('/')
  server = cd('/Servers/' + serverName) 
  server_start = server.getServerStart()
  server_start.setClassPath(classpath)
  server.setAutoKillIfFailed(true)
  op = server.getOverloadProtection()
  op.setFailureAction(failureAction)
  op.setPanicAction(panicAction)
  channels = server.getNetworkAccessPoints()
  
  for channel in channels:
    server.destroyNetworkAccessPoint(channel)
  server.createNetworkAccessPoint(channelName)
  channels = server.getNetworkAccessPoints()
  for channel in channels:
    channel.setListenAddress(listenAddress)
    channel.setListenPort(listenPort)
    channel.setPublicAddress('')
    channel.setPublicPort(-1)
    channel.setOutboundEnabled(true)
    channel.setHttpEnabledForThisProtocol(true)
    # Off for now. Maybe on later..
    #channel.setProtocol('cluster-broadcast')

def createSingletonService(cluster, preferredServer, post, classname):
  domain = cd('/')
  try:
    ss = cd('/SingletonServices/SBG-' + post + '-SingletonService')
  except:
    ss = domain.createSingletonService('SBG-' + post + '-SingletonService')
  ss.setClassName(classname)
  ss.setCluster(cluster)
  server = lookup(domain.getName() + '-' + post + '-managedServer-'+ preferredServer, 'Server')
  ss.setUserPreferredServer(server) 
  cluster.setMigrationBasis('consensus')
  cluster.setClusterBroadcastChannel('Unicast-Broadcast-Channel-' + post)

def createStoreAndForwardPersistentStore(safPersistentStoreName, safPersistentStoreTarget, safPersistentStorePrefix, safPersistentStoreMultiDatasource):
  log("SAF Persistent Store : " + safPersistentStoreName)
  domain = cd('/')
  #Getting target as Server MBean.
  log("Looking for target server : " + safPersistentStoreTarget)
  try:
    safPersistentStoreTargetServer = cd ('/Servers/' + safPersistentStoreTarget)
    log("Found target server " + safPersistentStoreTarget)
  except:
    log("Cannot find target server : " + safPersistentStoreTarget + ".", "CRITICAL")
    raise SystemExit
  #Getting multi data source as Server MBean
  log("Looking for Multi Data Source : " + safPersistentStoreMultiDatasource)
  try:
    safPersistentStoreDataSource = cd('/SystemResources/' + safPersistentStoreMultiDatasource)
    log("Found Multi Data Source " + safPersistentStoreMultiDatasource)
  except:
    log("Cannot find Multi Data Source : " + safPersistentStoreMultiDatasource + ".", "CRITICAL")
    raise SystemExit
  #Creation of the persistent store itself. If it exists, getting the MBean
  try:
    safPersistentStore = cd ('/JDBCStores/' + safPersistentStoreName)
    log("Persistent Store : " + safPersistentStoreName + " already exists!", "WARNING")
  except:
    log("Persistent Store : " + safPersistentStoreName + " does not exists! Creating it now!")
    safPersistentStore = domain.createJDBCStore(safPersistentStoreName)
  #Setting specific values for the safPersistentStore
  safPersistentStore.setDataSource(safPersistentStoreDataSource)
  safPersistentStore.setPrefixName(safPersistentStorePrefix)
  safPersistentStore.addTarget(safPersistentStoreTargetServer)
  #--END

def createStoreAndForwardAgent(safAgentName, safAgentJDBCPersistentStoreName, safAgentTargetServerName):
  #Creation of the SAF Agent.
  #Persistent store and target server are required.
  log("SAF Agent : " + safAgentName)
  domain = cd("/")
  #Getting the target server MBean. The addTarget() requires Server type MBean.
  log("Looking for target server : " + safAgentTargetServerName)
  try:
    safAgentTargetServer = cd ('/Servers/' + safAgentTargetServerName)
    log("Found target server " + safAgentTargetServerName)
  except:
    log("Cannot find target server : " + safAgentTargetServerName + ". Exiting program now!", "CRITICAL")
    raise SystemExit
  #Getting the JDBC Persistent store MBean. A Persistent store is required.
  log("Looking for JDBC Persistent store : " + safAgentJDBCPersistentStoreName)
  try:
    safAgentJDBCPersistentStore = cd('/JDBCStores/' + safAgentJDBCPersistentStoreName)
    log("Found JDBC Persistent store " + safAgentJDBCPersistentStoreName)
  except:
    log("Cannot find JDBC Persistent store : " + safAgentJDBCPersistentStoreName + ".", "CRITICAL")
    raise SystemExit
  #Creation of the SAF Agent itself. If it exists, getting the MBean
  try:
    safAgent = cd ('/SAFAgents/' + safAgentName)
    log("Store and Forward Agent : " + safAgentName + " already exists!", "WARNING")
  except:
    log("Store and Forward Agent : " + safAgentName + " does not exists! Creating it now!")
    safAgent = domain.createSAFAgent(safAgentName)
  #Setting the specific values of the SAFAgent.
  #Sending-only hardcoded, this value is required. 'Both' Service type doesn't work correctly.
  safAgent.setServiceType('Sending-only')
  safAgent.setStore(safAgentJDBCPersistentStore)
  safAgent.addTarget(safAgentTargetServer)
  #--END

def safStoreAndForwardDataSourceConfig(safDataSource):
  try:
    #Data source should be available, if not then a crictical error occurs.
    cd('/')
    dataSource = lookup(safDataSource, 'JDBCSystemResource')
  except:
    log("No datasource configured for SAF. Exiting program now!", "CRITICAL")
    raise SystemExit
  try:
    #Setting the specific values of the SAFAgent.
    #AlgorithmType hardcoded, this value is set as default because of the DTO to minimise RAC communication. 
    dataSourceParameters = dataSource.getJDBCResource().getJDBCDataSourceParams()
    dataSourceParameters.setAlgorithmType('Failover')
  except:
    log("The environment is VB. No SAF configuration for SAF needed.")
  #--END

def createStoreAndForwardRemoteContext(safRemoteContext, safRemoteContextModule, safRemoteContextURL):
  #Creation of the SAF Remote Context, this context is needed for the Imported Destinations. 
  cd('/')
  #looking up the module in which the context should be created
  jms_module = lookup(safRemoteContextModule, 'JMSSystemResource')
  try:
    #Looking up Remote Context, if not exists it will create it.
    remote_context= cd('/JMSSystemResources/' + safRemoteContextModule + '/JMSResource/' + safRemoteContextModule + '/SAFRemoteContexts/' + safRemoteContext)
    log("Remote Context : " + safRemoteContext + " already exists!", "WARNING")
  except:
    #creation of the SAF context.
    log("Creating Remote Context : " + safRemoteContext)
    remote_context = jms_module.getJMSResource().createSAFRemoteContext(safRemoteContext)
  #Setting URL. This should be the URL of the receiving managed servers.
  remote_context.getSAFLoginContext().setLoginURL(safRemoteContextURL)

def createStoreAndForwardErrorHandling(safErrorHandling, safErrorHandlingModule, safErrorHandlingPolicy, safErrorHandlingLogFormat):
  #Creation of the SAF Error Handling, this Error Handling is needed for the Imported Destinations.
  cd('/')
  #looking up the module in which the context should be created
  jms_module = lookup(safErrorHandlingModule, 'JMSSystemResource')
  try:
    #Looking up Error Handling, if not exists it will create it.
    error_handling = cd('/JMSSystemResources/' + safErrorHandlingModule + '/JMSResource/' + safErrorHandlingModule + '/SAFErrorHandlings/' + safErrorHandling)
    log("Error Handling : " + safErrorHandling + " already exists!", "WARNING")
  except:
    #creation of the SAF error handling
    log("Creating Error Handling : " + safErrorHandling)
    error_handling = jms_module.getJMSResource().createSAFErrorHandling(safErrorHandling)
  #Setting specific SAF Error Handling settings. No error destination because of policy Log.
  error_handling.setPolicy(safErrorHandlingPolicy)
  error_handling.setLogFormat(safErrorHandlingLogFormat)
  error_handling.setSAFErrorDestination(None)

def createStoreAndForwardImportedDestinations(safImportedDestination, safImportedDestinationModule, safImportedDestinationTTL, safImportedDestinationEnableTTL, safImportedDestinationRemoteSAFContext, safImportedDestinationSAFErrorHandling):
  #creating the SAF imported Destinations. A remote context and a error handling is required.
  cd('/')
  #looking up the module in which the imported destinations should be created
  jms_module = lookup(safImportedDestinationModule, 'JMSSystemResource')
  try:
    #Looking up SAF imported destinations, if not exists it will create it.
    saf_imported_destination = cd('/JMSSystemResources/' + safImportedDestinationModule + '/JMSResource/' + safImportedDestinationModule + '/SAFImportedDestinations/' + safImportedDestination)
    log("SAF Imported Destination : " + safImportedDestination + " already exists!", "WARNING")
  except:
    #creating the SAF imported destinations.
    log("Creating SAF Imported Destination : " + safImportedDestination)
    saf_imported_destination = jms_module.getJMSResource().createSAFImportedDestinations(safImportedDestination)
  #Setting specific setting for the SAF imported destinations
  saf_imported_destination.setJNDIPrefix(None)
  remote_context= cd('/JMSSystemResources/' + safImportedDestinationModule + '/JMSResource/' + safImportedDestinationModule + '/SAFRemoteContexts/' + safImportedDestinationRemoteSAFContext)
  saf_imported_destination.setSAFRemoteContext(remote_context)
  error_handling = cd('/JMSSystemResources/' + safImportedDestinationModule + '/JMSResource/' + safImportedDestinationModule + '/SAFErrorHandlings/' + safImportedDestinationSAFErrorHandling)
  saf_imported_destination.setSAFErrorHandling(error_handling)
  saf_imported_destination.setTimeToLiveDefault(safImportedDestinationTTL)
  saf_imported_destination.setUseSAFTimeToLiveDefault(true)
  #string can't be parsed to boolean. 
  if safImportedDestinationEnableTTL == 'true':
    saf_imported_destination.setDefaultTargetingEnabled(true)
  else:
    saf_imported_destination.setDefaultTargetingEnabled(false)

def createStoreAndForwardQueues(safQueue, safQueueModule, safQueueImportedDestination, safQueueRemoteJNDI, safQueueLocalJNDI):
  #Creating the queues for a SAF imported destinations
  cd('/')
  #looking up the module in which the imported destinations is created
  jms_module = lookup(safQueueModule, 'JMSSystemResource')
  saf_imported_destination = cd('/JMSSystemResources/' + safQueueModule + '/JMSResource/' + safQueueModule + '/SAFImportedDestinations/' + safQueueImportedDestination)
  try:
    #Looking up the queue, if not exists it will create it.
    queue = cd('/JMSSystemResources/' + safQueueModule + '/JMSResource/' + safQueueModule + '/SAFImportedDestinations/' + safQueueImportedDestination + '/SAFQueues/' + safQueue)
  except:
    #creating the queue
    queue = saf_imported_destination.createSAFQueue(safQueue)
  #setting specific parameters for the queue
  queue.setRemoteJNDIName(safQueueRemoteJNDI)
  queue.setLocalJNDIName(safQueueLocalJNDI)
