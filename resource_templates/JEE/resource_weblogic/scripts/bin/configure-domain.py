"""
$Id: configure-domain.py,v 1.2 2011/03/10 14:41:42 KVP Exp $
@author Klaas van der Ploeg, Mark Heeren, Herman Mensinga, Mario Sosic

Dit is het WLST script voor primaire configuratie van een vers geinstalleerd domain. De configuratie is 

project-specifiek en wordt aangeleverd door een project team. Na primaire configuratie krijgt domain versie 1.1.

Vanaf versie 1.1 wordt er niets meer gewijzigd aan het configuratie-script, en verlopen wijzigingen via het upgrade 

script.

"""

from prorail_domain_config import *
from wlstModule import *
from java.io import FileInputStream

def createDefaultRealmGroupsAndUsers(domainProperties):
  print 'Creating Groups and Users'
  groups = domainProperties.getProperty("security.groups", "").split(",")
  print ' Groups found ['+str(groups)+']'
  for group in groups:
    if group == "": 
      break
    groupDescription = domainProperties.getProperty("security.group.%s.description" % group, "no description")
    createDefaultRealmGroup(group,groupDescription)
  users = domainProperties.getProperty("security.users", "").split(",")
  print ' Users found ['+str(users)+']'
  for user in users:
    if user == "":
      break
    userDescription = domainProperties.getProperty("security.user.%s.description" % user, "no description")
    userPassword = domainProperties.getProperty("security.user.%s.password" % user, "")
    userGroup = domainProperties.getProperty("security.user.%s.group" % user, "")
    createDefaultRealmUser(user, userPassword, userDescription, userGroup)

def createDiagnosticModules(domainProperties):
  diagnosticModules = domainProperties.getProperty("diagnostic.modules", "").split(",")
  for dm in diagnosticModules:
    if dm != '':
      createDiagnosticModule(dm)

def createLDAPProvider(realm, name, type, controlflag, host, principal, credential, groupbasedn, userbasedn, sslenabled, port, userobjclass, staticmemberdnattr, groupfromnamefilter, groupfrommemberfilter, userfromnamefilter, groupobjclass):
  domain = cd("/")
  try:
    realmobj = cd("/SecurityConfiguration/" + domain.getName() + "/Realms/" + realm)
    ldapprovider = cd("/SecurityConfiguration/" + domain.getName() + "/Realms/" + realm + "/AuthenticationProviders/" + name)
    print("LDAPProvider %s already exists." % name) 
  except WLSTException:
    dumpStack()
    ldapprovider = realmobj.createAuthenticationProvider(name, "weblogic.security.providers.authentication." + type)
    print("LDAPProvider %s created." % name) 
  ldapprovider.setBindAnonymouslyOnReferrals(true)
  ldapprovider.setControlFlag(controlflag)
  ldapprovider.setCredential(credential)
  ldapprovider.setGroupBaseDN(groupbasedn)
  ldapprovider.setGroupFromNameFilter(groupfromnamefilter)
  ldapprovider.setHost(host)
  ldapprovider.setPrincipal(principal)      
  ldapprovider.setPort(port)
  ldapprovider.setPropagateCauseForLoginException(true)
  ldapprovider.setSSLEnabled(false)
  ldapprovider.setStaticMemberDNAttribute(staticmemberdnattr)
  ldapprovider.setStaticGroupDNsfromMemberDNFilter(groupfrommemberfilter)
  ldapprovider.setStaticGroupObjectClass(groupobjclass)
  ldapprovider.setUserFromNameFilter(userfromnamefilter)
  ldapprovider.setUserBaseDN(userbasedn)
  ldapprovider.setUserObjectClass(userobjclass)
    
def createLDAPProviders(domainProperties):
  ldapProviders = domainProperties.getProperty("ldapproviders", "").split(",")
  defaultType = domainProperties.getProperty("ldapprovider.default.type", "OpenLDAPAuthenticator")
  defaultRealm = domainProperties.getProperty("ldapprovider.default.realm", "myrealm")
  defaultControlflag = domainProperties.getProperty("ldapprovider.default.controlflag", "OPTIONAL")
  defaultPrincipal = domainProperties.getProperty("ldapprovider.default.principal", "principal")
  defaultCredential = domainProperties.getProperty("ldapprovider.default.credential", "credential")
  defaultGroupbasedn = domainProperties.getProperty("ldapprovider.default.groupbasedn", "ou=Groups,dc=Prorail,dc=NL")
  defaultUserbasedn = domainProperties.getProperty("ldapprovider.default.userbasedn", "ou=People,dc=Prorail,dc=NL")
  defaultSslenabled = domainProperties.getProperty("ldapprovider.default.sslenabled", "false")
  defaultPort = domainProperties.getProperty("ldapprovider.default.port", "389")
  defaultUserobjclass = domainProperties.getProperty("ldapprovider.default.userobjclass", "person")
  defaultStaticmemberdnattr = domainProperties.getProperty("ldapprovider.default.staticmemberdnattr", "memberUid")
  defaultGroupfromnamefilter = domainProperties.getProperty("ldapprovider.default.groupfromnamefilter", "(&(cn=%g)(objectclass=posixgroup))")
  defaultGroupfrommemberfilter = domainProperties.getProperty("ldapprovider.default.groupfrommemberfilter", "(&(memberUid=%M)(objectclass=posixgroup))")
  defaultUserfromnamefilter = domainProperties.getProperty("ldapprovider.default.userfromnamefilter", "(&(cn=%u)(objectclass=person))")
  defaultGroupobjclass = domainProperties.getProperty("ldapprovider.default.groupobjclass", "posixgroup")

  for ldapProviderName in ldapProviders:
    name = ldapProviderName
    if name == "":
      break
    type = domainProperties.getProperty("ldapprovider.%s.type" % ldapProviderName, defaultType)
    realm = domainProperties.getProperty("ldapprovider.%s.realm" % ldapProviderName, defaultRealm)
    controlflag = domainProperties.getProperty("ldapprovider.%s.controlflag" % ldapProviderName, defaultControlflag)
    host = domainProperties.getProperty("ldapprovider.%s.host" % ldapProviderName, "localhost")
    principal = domainProperties.getProperty("ldapprovider.%s.principal" % ldapProviderName, defaultPrincipal)
    credential = domainProperties.getProperty("ldapprovider.%s.credential" % ldapProviderName, defaultCredential)
    groupbasedn = domainProperties.getProperty("ldapprovider.%s.groupbasedn" % ldapProviderName, defaultGroupbasedn)
    userbasedn = domainProperties.getProperty("ldapprovider.%s.userbasedn" % ldapProviderName, defaultUserbasedn)
    sslenabled = domainProperties.getProperty("ldapprovider.%s.sslenabled" % ldapProviderName, defaultSslenabled).upper()=='TRUE'
    port = int(domainProperties.getProperty("ldapprovider.%s.port" % ldapProviderName, defaultPort))
    userobjclass = domainProperties.getProperty("ldapprovider.%s.userobjclass" % ldapProviderName, defaultUserobjclass)
    staticmemberdnattr = domainProperties.getProperty("ldapprovider.%s.staticmemberdnattr" % ldapProviderName, defaultStaticmemberdnattr)
    groupfromnamefilter = domainProperties.getProperty("ldapprovider.%s.groupfromnamefilter" % ldapProviderName, defaultGroupfromnamefilter)
    groupfrommemberfilter = domainProperties.getProperty("ldapprovider.%s.groupfrommemberfilter" % ldapProviderName, defaultGroupfrommemberfilter)
    userfromnamefilter = domainProperties.getProperty("ldapprovider.%s.userfromnamefilter" % ldapProviderName, defaultUserfromnamefilter)
    groupobjclass = domainProperties.getProperty("ldapprovider.%s.groupobjclass" % ldapProviderName, defaultGroupobjclass)
    createLDAPProvider(realm, name, type, controlflag, host, principal, credential, groupbasedn, userbasedn, sslenabled, port, userobjclass, staticmemberdnattr, groupfromnamefilter, groupfrommemberfilter, userfromnamefilter, groupobjclass)
    
def createCluster(name, frontendHost, frontendHTTPPort, frontendHTTPSPort, clusterMulticastAddress, clusterMulticastPort, clusterAddress, clusterChannelName):
  domain = cd("/")
  clusterBroadcastType = domainProperties.getProperty("cluster.default.broadcast.type","")
  
  print('clusterBroadcastType: ' + clusterBroadcastType)

  try:
    cluster = cd("/Clusters/" + name)
    print("Cluster %s already exists." % name) 
  except WLSTException:
    dumpStack()
    cluster = domain.createCluster(name)
    print("Cluster %s created." % name) 
  cluster.setFrontendHTTPPort(frontendHTTPPort)
  cluster.setFrontendHTTPSPort(frontendHTTPSPort)
  
  if clusterBroadcastType == "unicast":
    cluster.setClusterMessagingMode("unicast")
    cluster.setClusterBroadcastChannel(clusterChannelName)
  else:
    cluster.setClusterMessagingMode("multicast")
    cluster.setMulticastAddress(clusterMulticastAddress)
    cluster.setMulticastPort(clusterMulticastPort)

  if clusterAddress != "":
    print("Cluster ["+name+"] clusteraddress ["+clusterAddress+"]")
    cluster.setClusterAddress(clusterAddress)

def createClusters(domainPropeties):
  clusterNames = domainProperties.getProperty("clusters", "").split(",")
  defaultFrontendHost = domainProperties.getProperty("cluster.default.frontend.host","")
  defaultFrontendHTTPPort = domainProperties.getProperty("cluster.default.frontend.http.port","0")
  defaultFrontendHTTPSPort = domainProperties.getProperty("cluster.default.frontend.https.port","0")
  defaultChannelName = domainProperties.getProperty("cluster.default.broadcast.channel", "UnicastChannel")
  domain = cd("/")
  for clusterName in clusterNames:
    if clusterName == "":
      break
    clusterFrontendHost = domainProperties.getProperty("cluster.%s.frontend.host" % clusterName, defaultFrontendHost)
    clusterChannelName = domainProperties.getProperty("cluster.%s.broadcast.channel" % clusterName, clusterName + "" + defaultChannelName)
    clusterFrontendHTTPPort = int(domainProperties.getProperty("cluster.%s.frontend.http.port" % clusterName, defaultFrontendHTTPPort))
    clusterFrontendHTTPSPort = int(domainProperties.getProperty("cluster.%s.frontend.https.port" % clusterName, defaultFrontendHTTPSPort))
    clusterMulticastAddress = domainProperties.getProperty("cluster.%s.multicast.address" % clusterName, "239.192.0.0")
    clusterMulticastPort = int(domainProperties.getProperty("cluster.%s.multicast.port" % clusterName, "7001"))
    clusterAddress = domainProperties.getProperty("cluster.%s.clusteraddress" % clusterName, "")

    createCluster(clusterName, clusterFrontendHost, clusterFrontendHTTPPort, clusterFrontendHTTPSPort, clusterMulticastAddress, clusterMulticastPort, clusterAddress, clusterChannelName)

def createClusterJobSchedulers(domainPropeties):
  clusterNames = domainProperties.getProperty("clusters", "").split(",")
  for clusterName in clusterNames:
    clusterJobScheduler = domainProperties.getProperty("cluster.%s.jobscheduler" % clusterName, "false")
    clusterJobSchedulerDataSource = domainProperties.getProperty("cluster.%s.jobscheduler.datasource" % clusterName, "")
    clusterJobSchedulerTableName = domainProperties.getProperty("cluster.%s.jobscheduler.tablename" % clusterName, "")
  createClusterJobScheduler(clusterName, clusterJobScheduler, clusterJobSchedulerDataSource, clusterJobSchedulerTableName)

        
def createManagedServers(domainProperties, loggingBaseDir):
  dataRootDir = domainProperties.getProperty("data.root.dir", "/data")
  domain = cd("/")
  domainDir = dataRootDir + "/weblogic/domains/" + domain.getName()

  managedServers = domainProperties.getProperty("managedservers", "").split(",")
  #
  defaultMachines = domainProperties.getProperty("managedserver.default.machines", "localhost")
  defaultMachineDomain = domainProperties.getProperty("managedserver.default.machinedomain", "")
  defaultNumServers = domainProperties.getProperty("managedserver.default.num.servers", "1")
  defaultNumServersPerMachine = domainProperties.getProperty("managedserver.default.num.servers.per.machine", "1")
  defaultPortDelta = domainProperties.getProperty("managedserver.default.port.delta", "10")
  defaultSSL = domainProperties.getProperty("managedserver.default.ssl.enabled", "true")
  defaultStuckThreadMaxTime = domainProperties.getProperty("managedserver.default.stuckthreadmaxtime","-1")
  defaultSSLHostnameIgnored = domainProperties.getProperty("managedserver.default.ssl.hostname.verification.ignored", "false")
  defaultArgs = domainProperties.getProperty("managedserver.default.jvmargs", "")
  defaultJavaHome = domainProperties.getProperty("managedserver.default.javahome", "")
  defaultJavaVendor = domainProperties.getProperty("managedserver.default.javavendor", "")
  defaultClassPath = domainProperties.getProperty("managedserver.default.classpath", "")
  defaultSingletonEnvironment = domainProperties.getProperty("managedserver.default.singleton", "false") 
  defaultFailureAction = domainProperties.getProperty("managedserver.default.failureaction", "force-shutdown")
  defaultPanicAction = domainProperties.getProperty("managedserver.default.panicaction", "system-exit")
  #defaultPersistentStores = domainProperties.getProperty("managedserver.default.persistentstores", "").split(",")
  defaultOutboundEnabled  = domainProperties.getProperty("managedserver.default.outboundenabled", "false")

  defaultBeaHome = domainProperties.getProperty("managedserver.default.beahome", "")
  defaultRedirectToLog = domainProperties.getProperty("managedserver.default.redirecttolog","true").upper()=="TRUE"
  defaultClusterBroadcastType = domainProperties.getProperty("cluster.default.broadcast.type","")
  defaultUnicastListenPortDelta = domainProperties.getProperty("managedserver.default.unicast.listenport.delta","1")
  defaultClasspath = domainProperties.getProperty("managedserver.default.classpath", "")
  #
  g = 0
  for managedServer in managedServers:
    g = g + 1
    if managedServer == "":
      break
    numServers = int(domainProperties.getProperty("managedserver.%s.num.servers" % managedServer, defaultNumServers))
    numServersPerMachine = int(domainProperties.getProperty("managedserver.%s.num.servers.per.machine" % managedServer, defaultNumServersPerMachine))
    serverMachines = domainProperties.getProperty("managedserver.%s.machines" % managedServer, defaultMachines).split(",")
    serverCluster = domainProperties.getProperty("managedserver.%s.cluster" % managedServer, "")
    serverMachineDomain = domainProperties.getProperty("managedserver.%s.machineDomain" % managedServer, defaultMachineDomain)
    serverPort =  int(domainProperties.getProperty("managedserver.%s.port" % managedServer, ""))
    serverPortBase = int(domainProperties.getProperty("managedserver.%s.port" % managedServer, str(7001 + 1000*g)))
    serverPortDelta = int(domainProperties.getProperty("managedserver.%s.port.delta" % managedServer, defaultPortDelta))
    serverSSL = domainProperties.getProperty("managedserver.%s.ssl.enabled" % managedServer, defaultSSL).upper()=='TRUE'
    serverStuckThreadMaxTime = int(domainProperties.getProperty("managedserver.%s.stuckthreadmaxtime",defaultStuckThreadMaxTime))
    serverSSLHostnameIgnored = bool(domainProperties.getProperty("managedserver.%s.ssl.hostname.verification.ignored" % managedServer, defaultSSLHostnameIgnored))
    defaultServerArgs = domainProperties.getProperty("managedserver.%s.jvmargs" % managedServer, defaultArgs)
    javaHome = domainProperties.getProperty("managedserver.%s.javahome" % managedServer, defaultJavaHome)
    javaVendor = domainProperties.getProperty("managedserver.%s.javavendor" % managedServer, defaultJavaVendor)
    beaHome = domainProperties.getProperty("managedserver.%s.beahome" % managedServer, defaultBeaHome)
    serverJmsPrefixes = domainProperties.getProperty("managedserver.%s.jms.prefix" % managedServer, "").split(",")
    serverClassPath = domainProperties.getProperty("managedserver.%s.classpath" % managedServer, defaultClassPath)
    enableDefaultCF = domainProperties.getProperty("managedserver.%s.enabledefaultcf" % managedServer, "true")
    enableTunneling = domainProperties.getProperty("managedserver.%s.enabletunneling" % managedServer, "false")
    unicastListenPortDelta =  int(domainProperties.getProperty("managedserver.%s.unicast.listenport.delta",defaultUnicastListenPortDelta))
    clusterBroadcastType = domainProperties.getProperty("cluster."+serverCluster+".broadcast.type",defaultClusterBroadcastType)
    singletonEnvironment = domainProperties.getProperty("managedserver.%s.singleton" % managedServer, defaultSingletonEnvironment)
    #serverPersistentStores = domainProperties.getProperty("managedserver.%s.persitentstores" % managedServer, defaultPersistentStores).split(",")
    singleServer = domainProperties.getProperty("environment.singleServer", "false")
 
    s = 1 
    for serverMachine in serverMachines:
      print("Creating managedServers ["+managedServer+"] on machine ["+serverMachine+"]")
      machine = cd("/Machines/" + serverMachine)
      ms = 1
      while (ms <= numServers) & (ms <= numServersPerMachine):
        print(" Creating managedServer ["+managedServer+str(ms)+"] on machine ["+serverMachine+"]")
        serverAddress = domainProperties.getProperty("managedserver."+managedServer + str(s)+".address" , machine.getNodeManager().getListenAddress())
        unicastListenAddress = domainProperties.getProperty("machine."+serverMachine+".unicast.listenaddress","")
        serverArgs = domainProperties.getProperty("managedserver."+managedServer + str(s)+".jvmargs", defaultServerArgs)
        #adding dev urandom for entropy as standaard.
        serverArgs = serverArgs + " -Djava.security.egd=file:/dev/./urandom"

        listenAddress = domainProperties.getProperty("managedserver."+managedServer + str(s)+".channel.listenaddress", "")
        channelName = domainProperties.getProperty("managedserver."+managedServer + str(s)+".channel", "")
        classpath = domainProperties.getProperty("managedserver."+managedServer + str(s)+".classpath", defaultClassPath)
        serverOutboundEnabled = domainProperties.getProperty("managedserver.%s.outboundenabled" % managedServer, defaultOutboundEnabled)
        serverPanicAction = domainProperties.getProperty("managedserver."+managedServer + str(s)+".panicaction", defaultPanicAction)
        serverFailureAction = domainProperties.getProperty("managedserver."+managedServer + str(s)+".failureaction", defaultFailureAction)
        serverSSLPort = serverPort + 50
        unicastListenPort = serverPort
        createManagedServer(managedServer + str(s), serverAddress, serverPort, serverCluster, serverMachine, serverMachineDomain, loggingBaseDir, serverSSL, serverSSLPort, serverSSLHostnameIgnored, serverArgs, javaHome, javaVendor, beaHome,serverStuckThreadMaxTime,serverClassPath,defaultRedirectToLog,enableDefaultCF,enableTunneling,clusterBroadcastType,unicastListenAddress,unicastListenPort,serverOutboundEnabled,singleServer,serverPanicAction, serverFailureAction)
        server = cd("/Servers/" + managedServer+ str(s))
        server.setAutoRestart(true)
        server.setRestartMax(1)
        
        # singleton environment for SBG++
        if singletonEnvironment == "true":
          failureAction = domainProperties.getProperty("managedserver."+managedServer + str(s)+".failureaction", defaultFailureAction)
          panicAction = domainProperties.getProperty("managedserver."+managedServer + str(s)+".panicaction", defaultPanicAction)
          createSingletonEnvironment(managedServer+ str(s), channelName, listenAddress, unicastListenPort, classpath, failureAction, panicAction)
        ms = ms + 1
        s = s + 1
    
def createJDBCServices(domainProperties):
  dataSources = domainProperties.getProperty("datasources", "").split(",")
  print 'Found datasources ['+str(dataSources)+']'
  #
  defaultUseXA = domainProperties.getProperty("datasource.default.xa","False")
  defaultEmulateXA = domainProperties.getProperty("datasource.default.emulate-xa","False")
  
  #ALLEEN ALS DIT GOEDGEKEURD WORDT!!!!
  defaultLoggingLastResource = domainProperties.getProperty("datasource.default.logginglastresource", "False")
  defaultDbPort = domainProperties.getProperty("datasource.default.db.port","1521")
  defaultDbPool = domainProperties.getProperty("datasource.default.db.pool","10")
  defaultNodes = domainProperties.getProperty("datasource.default.db.nodes","localhost")
  defaultDBName = domainProperties.getProperty("datasource.default.db.instances","")

  defaultTestFrequency = domainProperties.getProperty("datasource.default.testfrequency", "300")
  defaultStatementCache = domainProperties.getProperty("datasource.default.statementcache", "256")
  defaultShrinkFrequency = domainProperties.getProperty("datasource.default.shrinkfrequency", "900")
  defaultRetryFrequency = domainProperties.getProperty("datasource.default.retryfrequency", "10")
  defaultReserveTimeout = domainProperties.getProperty("datasource.default.reservetimeout", "10")
  defaultReadTimeout = domainProperties.getProperty("datasource.default.readtimeout", "15000")
  extraParams = domainProperties.getProperty("datasource.default.vos", "false")
  #
  for ds in dataSources:
    name = ds
    if name == "":
      break
    targets = domainProperties.getProperty("datasource.%s.targets" %ds, "myserver")
    jndiName = domainProperties.getProperty("datasource.%s.jndi.name" % ds, "jdbc/mydatasource")
    useXA = domainProperties.getProperty("datasource.%s.xa" % ds, defaultUseXA).upper()=="TRUE"
    emulateXA = domainProperties.getProperty("datasource.%s.emulate-xa" % ds, defaultEmulateXA)
    loggingLastResource = domainProperties.getProperty("datasource.%s.logginglastresource" % ds, defaultLoggingLastResource)
    dbHost = domainProperties.getProperty("datasource.%s.db.nodes" % ds, defaultNodes)
    dbPort = int(domainProperties.getProperty("datasource.%s.db.port" % ds, defaultDbPort))
    dbName = domainProperties.getProperty("datasource.%s.db.instances" %  ds, defaultDBName)
    serviceName = domainProperties.getProperty("datasource.%s.db.name" % ds, "myservice")
    dbUser = domainProperties.getProperty("datasource.%s.db.user" % ds, "scott")
    dbPassword = domainProperties.getProperty("datasource.%s.db.password" % ds, "tiger")
    dbPool = int(domainProperties.getProperty("datasource.%s.db.pool" % ds, defaultDbPool))

    #VOS CCB0181 - Data sources changes
    testFrequency = int(domainProperties.getProperty("datasource.%s.testfrequency" % ds, defaultTestFrequency))
    statementCache = int(domainProperties.getProperty("datasource.%s.statementcache" % ds, defaultStatementCache))
    shrinkFrequency = int(domainProperties.getProperty("datasource.%s.shrinkfrequency" % ds, defaultShrinkFrequency))
    retryFrequency =  int(domainProperties.getProperty("datasource.%s.retryfrequency" % ds, defaultRetryFrequency))
    reserveTimeout = int(domainProperties.getProperty("datasource.%s.reservetimeout" % ds, defaultReserveTimeout))
    readTimeout = domainProperties.getProperty("datasource.%s.readtimeout" % ds, defaultReadTimeout)

    createJDBCDataSource(targets, name, jndiName, useXA, emulateXA, dbHost, dbPort, dbName, dbUser, dbPassword, dbPool, serviceName, testFrequency, statementCache, retryFrequency,shrinkFrequency, reserveTimeout, extraParams, readTimeout, loggingLastResource)

def getNumberOfServers(target):
  numberOfServers = 0
  cluster = getMBean("/Clusters/" + target)
  if cluster != None:
    numberOfServers = len(cluster.getServers())
  else:
    server = getMBean("/Servers/" + target)
    if server != None:
      numberOfServers = 1
  return numberOfServers

def createJMSServices(domainProperties):
  domain = cd("/")
  jmsSystemResources = domainProperties.getProperty("jms.system.resources", "").split(",")
  jmsSubDeployments = domainProperties.getProperty("jms.subdeployments", "").split(",")
  jmsServers = domainProperties.getProperty("jms.jmsservers", "false")
  dataRootDir = domainProperties.getProperty("data.root.dir", "/data")

  domainDir = dataRootDir + "/weblogic/domains/" + domain.getName()
  for jsr in jmsSystemResources:
    jsrName = jsr
    if jsrName == "":
      break
    jsrTargets = domainProperties.getProperty("jms.system.resource.%s.targets" % jsr, "mycluster")
    # targets splitten ?
    jsrJmsServerPrefix = domainProperties.getProperty("jms.system.resource.%s.server.prefix" % jsr, "")
    if jmsServers == 'true':
      if jsrJmsServerPrefix != '':
        createJmsServers(jsrTargets, jsrJmsServerPrefix, getNumberOfServers(jsrTargets), domainDir)
      createJMSSystemResource(jsrName, jsrTargets, jsrJmsServerPrefix)
      quotas = domainProperties.getProperty("jms.system.resource.%s.quotas" % jsr, "").split(",")
      for quota in quotas:
        if quota == "":
          break;
        quotaMaxBytes = long(domainProperties.getProperty("jms.system.resource." + jsr + "." + quota + ".maxbytes", "50000000"))
        createQuota(jsr, quota, quotaMaxBytes)
    for jmsSubDeployment in jmsSubDeployments:
      if jmsSubDeployment == "":
        break;
      createJmsSubDeployment(jsr, jmsSubDeployment, getNumberOfServers(jsrTargets), jsrJmsServerPrefix)
  
  #
  jmsConnectionFactories = domainProperties.getProperty("jms.connection.factories", "").split(",")
  defaultUseXA = domainProperties.getProperty("jms.connection.factory.default.xa","false")
  defaultServerAffinity = domainProperties.getProperty("jms.connection.factory.default.serveraffinity", "true")
  for cf in jmsConnectionFactories:
    cfName = cf
    if cfName == "":
      break
    cfJndiName = domainProperties.getProperty("jms.connection.factory.%s.jndi" % cfName, "jms/" + cfName) 
    cfUseXA = domainProperties.getProperty("jms.connection.factory.%s.xa" % cfName, defaultUseXA).upper()=='TRUE'
    cfJmsSystemResource = domainProperties.getProperty("jms.connection.factory.%s.system.resource" % cfName, "myJMSSystemResource")
    cfReconnectPolicy = domainProperties.getProperty("jms.connection.factory.%s.reconnectpolicy" % cfName, "")
    cfServerAffinity = domainProperties.getProperty("jms.connection.factory.%s.serveraffinity" % cfName, defaultServerAffinity).upper()=='TRUE'
    createConnectionFactory(cfJmsSystemResource, cfName, cfUseXA, cfReconnectPolicy, cfJndiName, cfServerAffinity)
  #
  jmsSystemResources = domainProperties.getProperty("jms.system.resources", "").split(",")
  defaultRedelivery = domainProperties.getProperty("jms.queue.default.redelivery", "")
  defaultQueueSubDeploymentName = domainProperties.getProperty("jms.queue.default.subdeploymentname", "sub-persistent")
  for jmsSystemResource in jmsSystemResources:
    if jmsSystemResource == "":
      break
    defaultQueueQuota = domainProperties.getProperty("jms.%s.queue.default.quota" % jmsSystemResource,"s")
    defaultQueuePrefix = domainProperties.getProperty("jms.%s.queue.default.prefix" % jmsSystemResource,"")
    defaultQueuePost = domainProperties.getProperty("jms.%s.queue.default.post" % jmsSystemResource,"")
    defaultError = domainProperties.getProperty("jms.%s.queue.default.error.destination" % jmsSystemResource, "x")
    defaultQueueForwardDelay =  domainProperties.getProperty("jms.%s.queue.default.forwarddelay" % jmsSystemResource, "-1")
    defaultExpirationPolicy =  domainProperties.getProperty("jms.%s.queue.default.expirationpolicy" % jmsSystemResource, "Discard")
    defaultExpirationLoggingPolicy = domainProperties.getProperty("jms.%s.queue.default.expirationloggingpolicy" % jmsSystemResource, "") 
    jmsQueues = domainProperties.getProperty("jms.%s.queues" % jmsSystemResource, "").split(",")
    for q in jmsQueues:
      if q == "":
        break
      queuePrefix = domainProperties.getProperty("jms."+jmsSystemResource+".queue.%s.prefix" % q,defaultQueuePrefix)
      queuePost = domainProperties.getProperty("jms."+jmsSystemResource+".queue.%s.post" % q,defaultQueuePost)
      queueQuota = domainProperties.getProperty("jms."+jmsSystemResource+".queue.%s.quota" % q, defaultQueueQuota)
      qRedelivery = domainProperties.getProperty("jms."+jmsSystemResource+".queue.%s.redelivery" % q, defaultRedelivery)
      queueError = domainProperties.getProperty("jms."+jmsSystemResource+".queue.%s.error.destination" % q, defaultError)
      queueTTL = int(domainProperties.getProperty("jms."+jmsSystemResource+".queue.%s.ttl" % q, "-1"))
      queueExpirationPolicy =  domainProperties.getProperty("jms."+jmsSystemResource+".queue.%s.expirationpolicy" % q, defaultExpirationPolicy)
      queueExpirationLoggingPolicy = domainProperties.getProperty("jms."+jmsSystemResource+".queue.%s.expirationloggingpolicy" % q, defaultExpirationLoggingPolicy)

      queueName = queuePrefix + q + queuePost
      queueJndiName = domainProperties.getProperty("jms."+jmsSystemResource+".queue.%s.jndi" % q, queueName)
      print(jmsSystemResource + " " + queueName + " " + queueQuota + " " + queueError)
      queueForwardDelay = int(domainProperties.getProperty("jms."+jmsSystemResource+".queue.%s.forwarddelay" % q, defaultQueueForwardDelay))
      if queueError=="x":
        createQueue(jmsSystemResource, queueName, queueQuota,queueJndiName, defaultQueueSubDeploymentName,queueTTL,queueForwardDelay,queueExpirationPolicy,queueExpirationLoggingPolicy)
      else:
        createQueueWithErrorDestination(jmsSystemResource, queueName, queueQuota, queueJndiName, queueError, defaultQueueSubDeploymentName, queueTTL, queueForwardDelay,queueExpirationPolicy,queueExpirationLoggingPolicy)
      if qRedelivery != "":
        setQueueRedelivery(jmsSystemResource, queueName, int(qRedelivery))
    jmsTopics = domainProperties.getProperty("jms."+jmsSystemResource+".topics", "").split(",")
    defaultTopicQuota = domainProperties.getProperty("jms."+jmsSystemResource+".topic.default.quota","s")
    for topic in jmsTopics:
      topicName = topic
      if topicName == "":
        break
      topicJndiName = domainProperties.getProperty("jms."+jmsSystemResource+".topic.%s.jndi" % topicName, "jms/" + topicName)
      topicQuota = domainProperties.getProperty("jms."+jmsSystemResource+".topic.%s.quota" % topicName, defaultTopicQuota)
      topicTTL = int(domainProperties.getProperty("jms."+jmsSystemResource+".topic.%s.ttl" % topicName, "-1"))
      createTopic(jmsSystemResource, topicJndiName, topicQuota, topicTTL)
  #
  foreignServers = domainProperties.getProperty("jms.foreign.servers", "").split(",")
  for fs in foreignServers:
    fsTargetModules = domainProperties.getProperty("jms.foreign.server.%s.target.module" % fs, "").split(",")
    if fsTargetModules == "":
      break
    for fsTargetModule in fsTargetModules:
      print fsTargetModule
      fsSourceModule = fs
      if fsSourceModule == "":
        break
      print fsTargetModule
      fsClusterUrl = domainProperties.getProperty("jms.foreign.server.%s.cluster.url" % fs, "")
      fsContextFactory = domainProperties.getProperty("jms.foreign.server.%s.contextfactory" % fs, "weblogic.jndi.WLInitialContextFactory")
      fsDatasource = domainProperties.getProperty("jms.foreign.server.%s.datasource" % fs, "")
      print fsDatasource + ' ' + fsContextFactory
      jndiProperties = domainProperties.getProperty("jms.foreign.server.default.jndi.properties", "false")
      jndiCredentials = domainProperties.getProperty("jms.foreign.server.default.jndi.credentials", "")
      fserver = createForeignServerForAddress(fsTargetModule, fsSourceModule,fsDatasource,fsContextFactory,fsClusterUrl, jndiProperties, jndiCredentials)
      fsFactories = domainProperties.getProperty("jms.foreign.server.%s.connection.factories" % fs, "").split(",")
      defaultfsRemoteJNDI = domainProperties.getProperty("jms.foreign.server.%s.connection.factory.remoteJNDI" % fs, "javax.jms.QueueConnectionFactory")
      for fscf in fsFactories:
        if fscf == "":
          break
        fscfJndiName = domainProperties.getProperty("jms.foreign.server."+fs+".connection.factory." + fscf + ".jndi", "jms/" + fscf)
        fsRemoteJNDI = domainProperties.getProperty("jms.foreign.server."+fs+".connection.factory." + fscf + ".remoteJNDI", defaultfsRemoteJNDI)
        userName =  domainProperties.getProperty("jms.foreign.server."+fs+".connection.factory." + fscf + ".username", "")
        passwd = domainProperties.getProperty("jms.foreign.server."+fs+".connection.factory." + fscf + ".passwd", "") 
        print 'addFactoryToForeignServer'
        addFactoryToForeignServer(fserver, fsRemoteJNDI, fscfJndiName, userName, passwd, fscf)
      fsQueues = domainProperties.getProperty("jms.foreign.server.%s.queues" % fs, "")
      if fsQueues == "all":
        addAllQueuesToForeignServer(fserver, fsSourceModule)  
      else:
        for fsq in fsQueues.split(","):
          if fsq == "":
            break
          fsRemoteQueue = domainProperties.getProperty("jms.foreign.server."+fs+".queue."+fsq+".remote", fsq)
          print 'addQueueToForeignServer'
          addQueueToForeignServer(fserver, fsq, fsRemoteQueue)

#########################----VMB WHOLE SERVER MIGRATION----#########################




def createWholeServerMigrationCluster(name, frontendHost, frontendHTTPPort, frontendHTTPSPort, clusterChannelName, clusterMigrationBasis, clusterMigrationDatasource, primaryMachine, secondaryMachine):
  print('createCluster-clusterMigrationBasis: ' + clusterMigrationBasis)
  print('createCluster-clusterMigrationDatasource: ' + clusterMigrationDatasource)
  print('createCluster-primaryMachine: ' + str(primaryMachine))
  print('createCluster-secondaryMachine: ' + str(secondaryMachine))
  domain = cd("/")
  try:
    cluster = cd("/Clusters/" + name)
    print("Cluster %s already exists." % name) 
  except WLSTException:
    dumpStack()
    cluster = domain.createCluster(name)
    print("Cluster %s created." % name) 
  cluster.setFrontendHTTPPort(frontendHTTPPort)
  cluster.setFrontendHTTPSPort(frontendHTTPSPort)
  cluster.setClusterMessagingMode("unicast")
  cluster.setClusterBroadcastChannel(clusterChannelName)
  if cluster != "":
    print('cluster exists')
    cd("/Clusters/" + name)
    if clusterMigrationBasis == "database":
       print('clusterMigrationBasis is database')
       set('MigrationBasis', clusterMigrationBasis)
       print('DataSourceForAutomaticMigration: ' + clusterMigrationDatasource)
       cluster.setDataSourceForAutomaticMigration(getMBean('/SystemResources/'+clusterMigrationDatasource))
    print 'Set CandidateMachinesForMigratableServers'
    set('CandidateMachinesForMigratableServers',jarray.array([ObjectName('com.bea:Name=%s,Type=UnixMachine' % secondaryMachine), ObjectName('com.bea:Name=%s,Type=UnixMachine' % primaryMachine)], ObjectName))

def createWholeServerMigrationConfig(domainPropeties):
  clusterNames = domainProperties.getProperty("clusters", "").split(",")
  defaultFrontendHost = domainProperties.getProperty("cluster.default.frontend.host","")
  defaultFrontendHTTPPort = domainProperties.getProperty("cluster.default.frontend.http.port","0")
  defaultFrontendHTTPSPort = domainProperties.getProperty("cluster.default.frontend.https.port","0")
  domain = cd("/")
  for clusterName in clusterNames:
    if clusterName == "":
      break
    clusterFrontendHost = domainProperties.getProperty("cluster.%s.frontend.host" % clusterName, defaultFrontendHost)
    clusterFrontendHTTPPort = int(domainProperties.getProperty("cluster.%s.frontend.http.port" % clusterName, defaultFrontendHTTPPort))
    clusterFrontendHTTPSPort = int(domainProperties.getProperty("cluster.%s.frontend.https.port" % clusterName, defaultFrontendHTTPSPort))
    #Update version LLP 2.2, using Unicast now.
    clusterChannelName = domainProperties.getProperty("cluster.%s.unicast.channel" % clusterName, "UnicastChannel")
    clusterAddress = domainProperties.getProperty("cluster.%s.multicast.address" % clusterName, "239.192.0.0")
    clusterPort = int(domainProperties.getProperty("cluster.%s.multicast.port" % clusterName, "7001"))
    clusterMigrationBasis = domainProperties.getProperty("cluster.%s.migrationbasis" % clusterName, "consensus")
    clusterMigrationDatasource = domainProperties.getProperty("cluster.%s.migrationdatasource" % clusterName, "ds")
    clusterServers = domainProperties.getProperty("machines", "").split(",")

    print('clusterMigrationBasis ' + clusterMigrationBasis)
    print('clusterMigrationDatasource ' + clusterMigrationDatasource)
    primaryMachine=clusterServers[0] 
    print('primary ' + primaryMachine)
    secondaryMachine=clusterServers[1]
    print('secondary ' + secondaryMachine)

    createWholeServerMigrationCluster(clusterName, clusterFrontendHost, clusterFrontendHTTPPort, clusterFrontendHTTPSPort, clusterChannelName, clusterMigrationBasis, clusterMigrationDatasource, primaryMachine, secondaryMachine)

def createWholeServerMigrationServers(domainProperties, loggingBaseDir):
  dataRootDir = domainProperties.getProperty("data.root.dir", "/data")
  domain = cd("/")
  domainDir = dataRootDir + "/weblogic/domains/" + domain.getName()

  managedServers = domainProperties.getProperty("managedservers", "").split(",")
  #
  defaultMachines = domainProperties.getProperty("managedserver.default.machines", "localhost")
  defaultMachineDomain = domainProperties.getProperty("managedserver.default.machinedomain", "")
  defaultNumServers = domainProperties.getProperty("managedserver.default.num.servers", "1")
  defaultNumServersPerMachine = domainProperties.getProperty("managedserver.default.num.servers.per.machine", "1")
  defaultPortDelta = domainProperties.getProperty("managedserver.default.port.delta", "10")
  defaultSSL = domainProperties.getProperty("managedserver.default.ssl.enabled", "true")
  defaultStuckThreadMaxTime = domainProperties.getProperty("managedserver.default.stuckthreadmaxtime","-1")
  defaultSSLHostnameIgnored = domainProperties.getProperty("managedserver.default.ssl.hostname.verification.ignored", "false")
  defaultArgs = domainProperties.getProperty("managedserver.default.jvmargs", "")
  defaultClassPath = domainProperties.getProperty("managedserver.default.classpath", "")
  defaultServerJmsPrefixes = domainProperties.getProperty("managedserver.default.jms.prefix", "").split(",")
  defaultFailureAction = domainProperties.getProperty("managedserver.default.failureaction", "force-shutdown")
  defaultPanicAction = domainProperties.getProperty("managedserver.default.panicaction", "system-exit")


  defaultJavaHome = domainProperties.getProperty("managedserver.default.javahome", "")
  defaultJavaVendor = domainProperties.getProperty("managedserver.default.javavendor", "")
  defaultBeaHome = domainProperties.getProperty("managedserver.default.beahome", "")
  defaultRedirectToLog = domainProperties.getProperty("managedserver.default.redirecttolog","true").upper()=="TRUE"
 
  secondaryServer=str(managedServers[1])
 
  primaryServer=str(managedServers[0])
  print '**** primaryServer ' + primaryServer

  #
  g = 0
  for managedServer in managedServers:
    print('In de managedServer loop voor ' + managedServer)
    g = g + 1
    if managedServer == "":
      break
    numServers = int(domainProperties.getProperty("managedserver.%s.num.servers" % managedServer, defaultNumServers))
    numServersPerMachine = int(domainProperties.getProperty("managedserver.%s.num.servers.per.machine" % managedServer, defaultNumServersPerMachine))
    serverMachines = domainProperties.getProperty("machines", "").split(",")
    serverCluster = domainProperties.getProperty("managedserver.default.cluster", "")
    serverMachineDomain = domainProperties.getProperty("managedserver.%s.machineDomain" % managedServer, defaultMachineDomain)
    serverPortBase = int(domainProperties.getProperty("managedserver.%s.port" % managedServer, str(7001 + 1000*g)))
    serverPortDelta = int(domainProperties.getProperty("managedserver.%s.port.delta" % managedServer, defaultPortDelta))
    serverSSL = domainProperties.getProperty("managedserver.%s.ssl.enabled" % managedServer, defaultSSL).upper()=='TRUE'
    serverStuckThreadMaxTime = int(domainProperties.getProperty("managedserver.%s.stuckthreadmaxtime",defaultStuckThreadMaxTime))
    serverSSLHostnameIgnored = bool(domainProperties.getProperty("managedserver.%s.ssl.hostname.verification.ignored" % managedServer, defaultSSLHostnameIgnored))
    primaryServerArgs = domainProperties.getProperty("managedserver.%s.jvmargs" % primaryServer, defaultArgs)
    secondaryServerArgs = domainProperties.getProperty("managedserver.%s.jvmargs" % secondaryServer, defaultArgs)
    javaHome = domainProperties.getProperty("managedserver.%s.javahome" % managedServer, defaultJavaHome)
    javaVendor = domainProperties.getProperty("managedserver.%s.javavendor" % managedServer, defaultJavaVendor)
    serverClassPath = domainProperties.getProperty("managedserver.%s.classpath" % managedServer, defaultClassPath)
    serverPanicAction = defaultPanicAction
    serverFailureAction = defaultFailureAction
    primaryServerArgs = primaryServerArgs + " -Djava.security.egd=file:/dev/./urandom"
    secondaryServerArgs = secondaryServerArgs + " -Djava.security.egd=file:/dev/./urandom"

    beaHome = domainProperties.getProperty("managedserver.%s.beahome" % managedServer, defaultBeaHome)
    enableDefaultCF = domainProperties.getProperty("managedserver.%s.enabledefaultcf" % managedServer, "true")
    enableTunneling = domainProperties.getProperty("managedserver.%s.enabletunneling" % managedServer, "false")

    serverJmsPrefixes = domainProperties.getProperty("managedserver.%s.jms.prefix" % managedServer, "").split(',')
    primaryServerListenPort = int(domainProperties.getProperty("managedserver.%s.port" % primaryServer, ""))
    secondaryServerListenPort = int(domainProperties.getProperty("managedserver.%s.port" % secondaryServer, ""))

    primaryMachine=str(serverMachines[0])
    secondaryMachine=str(serverMachines[1])
    s = 1 
    machine = cd("/Machines/" + primaryMachine)
    primaryServerAddress = domainProperties.getProperty("managedserver.%s.address" % primaryServer, machine.getNodeManager().getListenAddress())
    primaryUnicastListenAddress = domainProperties.getProperty("machine.%s.unicast.listenaddress" % machine.getName(), "")
    machine = cd("/Machines/" + secondaryMachine)
    secondairyServerAddress = domainProperties.getProperty("managedserver.%s.address" % secondaryServer, machine.getNodeManager().getListenAddress())
    secundaryUnicastListenAddress = domainProperties.getProperty("machine.%s.unicast.listenaddress" % machine.getName(), "")
    ms = 1
    serverPort = serverPortBase + serverPortDelta * (ms - 1)
    serverSSLPort = serverPort + 50 
    createManagedServer(primaryServer, primaryServerAddress, primaryServerListenPort, serverCluster, primaryMachine, serverMachineDomain, loggingBaseDir, serverSSL, serverSSLPort, serverSSLHostnameIgnored, primaryServerArgs, javaHome, javaVendor, beaHome,serverStuckThreadMaxTime,serverClassPath,defaultRedirectToLog,enableDefaultCF,enableTunneling,"unicast",primaryUnicastListenAddress,10001,'true','false',serverPanicAction, serverFailureAction)
    createManagedServer(secondaryServer, secondairyServerAddress, secondaryServerListenPort, serverCluster, secondaryMachine, serverMachineDomain, loggingBaseDir, serverSSL, serverSSLPort, serverSSLHostnameIgnored, secondaryServerArgs, javaHome, javaVendor, beaHome,serverStuckThreadMaxTime,serverClassPath,defaultRedirectToLog,'false',enableTunneling,"unicast", secundaryUnicastListenAddress, 12001,'true','false', serverPanicAction, serverFailureAction)
    for serverJmsPrefix in serverJmsPrefixes:
      if serverJmsPrefix == '':
        break
      createAndTargetJMSServer(serverJmsPrefix + str(s), managedServer + str(s), domainDir)
    cd('/Servers/' + managedServer)
    print 'Set CandidateMachines'
    set('CandidateMachines',jarray.array([ObjectName('com.bea:Name=%s,Type=UnixMachine' % secondaryMachine), ObjectName('com.bea:Name=%s,Type=UnixMachine' % primaryMachine)], ObjectName))
    if (managedServer == primaryServer):
      set('AutoMigrationEnabled','true')
    set('HealthCheckIntervalSeconds','10')
    set('RestartDelaySeconds','5')
    set('RestartMax','2')
    set('AutoRestart','false')
    cd('/MigratableTargets/'+managedServer+' (migratable)')
    print 'Set MigrationPolicy'
    set('MigrationPolicy','failure-recovery')
    print 'Set UserPreferredServer'
    set('UserPreferredServer',getMBean('/Servers/' + managedServer))
    ms = ms + 1
    s = s + 1
  for managedServer in managedServers:
    cd('/MigratableTargets/'+managedServer+' (migratable)')
    print 'Set ConstrainedCandidateServers for ' + managedServer
    set('ConstrainedCandidateServers',jarray.array([ObjectName('com.bea:Name=%s,Type=Server' % secondaryServer), ObjectName('com.bea:Name=%s,Type=Server' % primaryServer)], ObjectName))


#########################----VMB WHOLE SERVER MIGRATION----#########################

#########################----SBG SINGLETON SERVER----#########################

def createSingletonServices(domainProperties):
  singletonClassname = domainProperties.getProperty('' ,"nl.prorail.vrijgave.cluster.singleton.weblogic.SingletonServiceImpl")
  domain = cd('/')
  clusters = domain.getClusters()
  for cluster in clusters:
    preferredServer = domainProperties.getProperty("cluster." + cluster.getName() + ".preferredserver", "")
    post = domainProperties.getProperty("cluster." + cluster.getName() + ".post", "")
    createSingletonService(cluster, preferredServer, post, singletonClassname)

#########################----SBG SINGLETON SERVER----#########################

def createStoreAndForward(domainProperties):
  #Creating SAF persistent stores. Using JDBC database persistency.
  safJDBCPersistentStores = domainProperties.getProperty("jms.saf.jdbc_persistent_stores", "").split(",")
  for safJDBCPersistentStore in safJDBCPersistentStores:
    if safJDBCPersistentStore == '':
      break;
    #safPersistentStore --> The name of the safPersistentStore. I.e. SAF_PS1
    #safPersistentStoreTarget --> The target of the persistent store. I.e. CRIS-managedServer-1.
    #safPersistentStorePrefix --> The prefix of the persistent store table in database. This value is left empty on purpose. Name of the table in database will now be the name of the persistent store.
    #safPersistentStoreDatasource --> The Multi Data Source of the persistent store used for connection to database. I.e. persistent-ds
    safPersistentStoreTarget = domainProperties.getProperty("jms.saf.jdbc_persistent_store.%s.target" % safJDBCPersistentStore, "")
    safPersistentStorePrefix = domainProperties.getProperty("jms.saf.jdbc_persistent_store.%s.prefix" % safJDBCPersistentStore, "")
    safPersistentStoreDataSource = domainProperties.getProperty("jms.saf.jdbc_persistent_store.%s.multidatasource" % safJDBCPersistentStore, "")
    #calling createSafPersistentStore() function in prorail_domain_config.py
    createStoreAndForwardPersistentStore(safJDBCPersistentStore, safPersistentStoreTarget, safPersistentStorePrefix, safPersistentStoreDataSource)

  safAgents = domainProperties.getProperty("jms.saf.agents", "").split(",")
  for safAgent in safAgents:
    if safAgent == '':
      break
    #safAgent --> The name of the safAgent. I.e. cris.safagent1
    #safAgentJDBCPersistentStore --> The persistent store used for persistency. I.e. SAF_PS_cris1
    #safAgentTargetServer --> The target server of the agent. I.e. CRIS-managedServer-1
    safAgentJDBCPersistentStore = domainProperties.getProperty("jms.saf.agent.%s.jdbc_persistent_store" % safAgent, "")
    safAgentTargetServer = domainProperties.getProperty("jms.saf.agent.%s.target" % safAgent, "")
    createStoreAndForwardAgent(safAgent, safAgentJDBCPersistentStore, safAgentTargetServer)

  safDataSources = domainProperties.getProperty("jms.saf.datasources", "").split(",")
  for safDataSource in safDataSources:
    if safDataSource == '':
      break
    #safDataSource --> The name of the Multi Data Source. I.e. SAF-ds
    safStoreAndForwardDataSourceConfig(safDataSource)

  safRemoteContexts = domainProperties.getProperty("jms.saf.remote_contexts", "").split(",")
  for safRemoteContext in safRemoteContexts:
    if safRemoteContext == '':
      break
    #safRemoteContext --> The name of the Remote Context. I.e. cris-harm-saf-context
    #safRemoteContextModule --> The name of the JMS module. I.e. cris-output
    #safRemoteContextURL --> The URL of the Remote Context. I.e. t3://oiplus22a,oiplus22b,oiplus22c,oiplus22d,oiplus22e:14001
    safRemoteContextModule = domainProperties.getProperty("jms.saf.remote_context.%s.module" % safRemoteContext, "")
    safRemoteContextURL = domainProperties.getProperty("jms.saf.remote_context.%s.URL" % safRemoteContext, "")
    createStoreAndForwardRemoteContext(safRemoteContext, safRemoteContextModule, safRemoteContextURL)

  safErrorHandlings = domainProperties.getProperty("jms.saf.error_handlings", "").split(",")
  for safErrorHandling in safErrorHandlings:
    if safErrorHandling == '':
      break
    #safErrorHandling --> The name of the Error Handling. I.e. cris-harm-saf-error-handling
    #safErrorHandlingModule --> The name of the JMS module. I.e. cris-output
    #safErrorHandlingPolicy --> The logging policy of the saf. I.e Log/Discard
    #safErrorHandlingLogFormat --> The logging format of the saf. I.e "%header%,%properties%"
    safErrorHandlingModule = domainProperties.getProperty("jms.saf.error_handling.%s.module" % safErrorHandling, "")
    safErrorHandlingPolicy = domainProperties.getProperty("jms.saf.error_handling.%s.MessageHandlingPolicy" % safErrorHandling, "")
    safErrorHandlingLogFormat = domainProperties.getProperty("jms.saf.error_handling.%s.LogFormat" % safErrorHandling, "")
    createStoreAndForwardErrorHandling(safErrorHandling, safErrorHandlingModule, safErrorHandlingPolicy, safErrorHandlingLogFormat)

  safImportedDestinations = domainProperties.getProperty("jms.saf.imported_destinations", "").split(",")
  for safImportedDestination in safImportedDestinations:
    if safImportedDestination == '':
     break;
    #safImportedDestination --> The name of the Imported Destination. I.e. cris-harm-imported-destinations
    #safImportedDestinationTTL --> The time-to-live of the Imported Destination. I.e. 14400000
    #safImportedDestinationEnableTTL --> The time-to-live enabled is effected for every queue/topic. I.e True 
    #safImportedDestinationRemoteSAFContext --> The SAF Context used for the Imported Destinations. I.e cris-harm-saf-context
    #safImportedDestinationRemoteSAFErrorHandling --> The SAF Error Handling used for the Imported Destinations. I.e cris-harm-saf-error-handling
    safImportedDestinationModule = domainProperties.getProperty("jms.saf.imported_destination.%s.module" % safImportedDestination, "")
    safImportedDestinationTTL = long(domainProperties.getProperty("jms.saf.imported_destination.%s.TTL" % safImportedDestination, "0"))
    safImportedDestinationEnableTTL = domainProperties.getProperty("jms.saf.imported_destination.%s.EnableTTL" % safImportedDestination, "")
    safImportedDestinationRemoteSAFContext = domainProperties.getProperty("jms.saf.imported_destination.%s.remote_saf_context"  % safImportedDestination, "")
    safImportedDestinationSAFErrorHandling = domainProperties.getProperty("jms.saf.imported_destination.%s.saf_error_handling" % safImportedDestination, "")
    createStoreAndForwardImportedDestinations(safImportedDestination, safImportedDestinationModule, safImportedDestinationTTL, safImportedDestinationEnableTTL,  safImportedDestinationRemoteSAFContext, safImportedDestinationSAFErrorHandling)
   
  safQueues = domainProperties.getProperty("jms.saf.queues", "").split(",")
  for safQueue in safQueues:
    #safQueue --> the name of the saf queue. I.e. saf.cris.vtg.jms.queue.output
    #safQueueModule --> The name of the module. I.e. cris-output
    #safQueueImportedDestination --> the Imported Destination where the queue needs to be created. I.e cris-harm-imported-destinations
    #safQueueRemoteJNDI --> the queue Remote JNDI name. I.e harm.vtg.jms.queue.input
    #safQueueLocalJNDI --> The local queue JNDI name. I.e cris.vtg.jms.queue.output
    safQueueModule = domainProperties.getProperty("jms.saf.queue.%s.module" % safQueue, "")
    safQueueImportedDestination = domainProperties.getProperty("jms.saf.queue.%s.importeddestination" % safQueue, "")
    safQueueRemoteJNDI = domainProperties.getProperty("jms.saf.queue.%s.remoteJNDI" % safQueue, "")
    safQueueLocalJNDI = domainProperties.getProperty("jms.saf.queue.%s.localJNDI" % safQueue, "")

    createStoreAndForwardQueues(safQueue, safQueueModule, safQueueImportedDestination, safQueueRemoteJNDI, safQueueLocalJNDI)
  safTopics = domainProperties.getProperty("jms.saf.topics", "").split(",")

          

# Start script
#
if len(sys.argv) > 1:
  propertiesPath = sys.argv[1]
else:
  propertiesPath = "./"  

exitonerror=false

try:

  domainProperties = readProperties(propertiesPath + "/configure-domain.properties")
  domainProperties.load(FileInputStream(propertiesPath + "/install-domain.properties"))
  userName = domainProperties.getProperty("admin.user", "weblogic")
  passWord = domainProperties.getProperty("admin.password", "welcome1")
  adminServerListenAddress = domainProperties.getProperty("admin.server.address", "localhost")
  adminServerListenPort = int(domainProperties.getProperty("admin.server.port", "7001"))
  dataRootDir = domainProperties.getProperty("data.root.dir", "/data")
  logRootDir = domainProperties.getProperty("log.root.dir", "/var/log")
  notes = domainProperties.getProperty("domain.notes", "Unknown")
  domainJTATimeoutSeconds = int(domainProperties.getProperty("domain.jtatimeoutseconds","30"))
  singletonEnv = domainProperties.getProperty("domain.type.singleton", "false")
  URL = "t3://" + adminServerListenAddress + ":" + str(adminServerListenPort)
  connect(userName, passWord, URL)

  domain = cd("/")
  domainName = domain.getName()
  domainDir = dataRootDir + "/weblogic/domains/" + domainName
  loggingBaseDir = logRootDir + "/weblogic/domains/" + domainName

  startTransaction()

  cd("/")
  set("Notes",notes)
  print 'Setting domain JTA Timeout seconds to ['+str(domainJTATimeoutSeconds)+']'
  cd('/JTA/'+domainName)
  set("TimeoutSeconds",domainJTATimeoutSeconds)
  
  #CCB0154 JMX available
  jmx = cd('/JMX/' + domainName)
  jmx.setPlatformMBeanServerEnabled(true)
  jmx.setPlatformMBeanServerUsed(true)

  # create clusters
  clusterType=domainProperties.getProperty("cluster.type", "cluster")
  print('clusterType: ' + clusterType)
  
  if clusterType == 'wsm':
      createJDBCServices(domainProperties)
      createWholeServerMigrationConfig(domainProperties)
  else:
      createClusters(domainProperties)
      createJDBCServices(domainProperties)
  
  # create and adjust managed servers
  
  if clusterType == 'wsm':
    createWholeServerMigrationServers(domainProperties, loggingBaseDir)
  else:
    createManagedServers(domainProperties, loggingBaseDir)
  

  # create jms servers, saf agents, foreign providers, destinations, etc.
  createJMSServices(domainProperties)
  # create ldap providers
  createLDAPProviders(domainProperties)
  # create diagnotic modules
  createDiagnosticModules(domainProperties)
  # create job schedulers
  createClusterJobSchedulers(domainProperties)
   
  #create singleton services
  if singletonEnv == 'true':
    createSingletonServices(domainProperties)

  endTransaction()
  dumpStack()
    # create users and groups
  serverConfig()
  dumpStack()
  #deployAndStartApplications(domainProperties)
  createDefaultRealmGroupsAndUsers(domainProperties)
  dumpStack()
except WLSTException,e:
  print "Exception occured "
  print e
  print dumpStack()
print("done")
