Name:         resource_weblogic
Version:      1.0.0
Release:      1
Summary:      Resource script weblogic
Group:        Applications/System
License:      GPL
Vendor:       Platform Bouwteam
Source:       %{name}.tar.gz
BuildRoot:    %{_tmppath}/%{name}-root

%description
The scripts will:
Create a WebLogic domain conform ProRail standard.
%prep
%setup -q -n %{name}

%build
# Empty.

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/opt/scripts/weblogic/bin
cp -R scripts/bin $RPM_BUILD_ROOT/opt/scripts/weblogic

%clean
rm -rf $RPM_BUILD_ROOT

%pre
# Empty.

%post
# Empty.

%preun
# Empty.

%postun
# Empty.

%files
%defattr(0755,root,root)
%dir    /opt/scripts/weblogic/bin
/opt/scripts/weblogic/bin/weblogic.sh
/opt/scripts/weblogic/bin/clusterkey_root.sh
/opt/scripts/weblogic/bin/clusterkey_user.sh
/opt/scripts/weblogic/bin/prereq.sh
/opt/scripts/weblogic/bin/start-domain.sh
/opt/scripts/weblogic/bin/prorail_domain_config.py
/opt/scripts/weblogic/bin/common.sh
/opt/scripts/weblogic/bin/install-domain.sh
/opt/scripts/weblogic/bin/enroll-domain.sh
/opt/scripts/weblogic/bin/enroll-domain.py
/opt/scripts/weblogic/bin/configure-domain.py
/opt/scripts/weblogic/bin/start-domain.py
/opt/scripts/weblogic/bin/error.sh
/opt/scripts/weblogic/bin/configure-domain.sh
/opt/scripts/weblogic/bin/genkey.sh
/opt/scripts/weblogic/bin/install-domain.py
/opt/scripts/weblogic/bin/stop-domain.sh
/opt/scripts/weblogic/bin/stop-domain.py
/opt/scripts/weblogic/bin/README

%changelog
* Fri Jun 05 2015 Paul Huisman <paul.huisman@prorail.nl> - 1.0.0-1
- Initial creation of the RPM
