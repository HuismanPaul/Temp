Name:         resource_tibco
Version:      1.0.0
Release:      1
Summary:      Resource script tibco
Group:        Applications/System
License:      GPL
Vendor:       Platform Bouwteam
Source:       %{name}.tar.gz
BuildRoot:    %{_tmppath}/%{name}-root

%description
The scripts will:
Add tibco application configuration to the tibco environment.

%prep
%setup -q -n %{name}

%build
# Empty.

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/opt/scripts/tibco
cp -R scripts/bin $RPM_BUILD_ROOT/opt/scripts/tibco

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
%dir    /opt/scripts/tibco/bin
/opt/scripts/tibco/bin/README
/opt/scripts/tibco/bin/setenv.sh
/opt/scripts/tibco/bin/tibemsadmin.sh
%dir /opt/scripts/tibco/bin/utils
/opt/scripts/tibco/bin/utils/properties.py
/opt/scripts/tibco/bin/utils/xml.py
/opt/scripts/tibco/bin/utils/version.pyc
/opt/scripts/tibco/bin/utils/xml.pyc
/opt/scripts/tibco/bin/utils/properties.pyc
/opt/scripts/tibco/bin/utils/__init__.py
/opt/scripts/tibco/bin/utils/__init__.pyc
/opt/scripts/tibco/bin/utils/version.py
/opt/scripts/tibco/bin/queue_topic_deploy.py


%changelog
* Fri Jun 05 2015 Jurgen Ponds <jurgen.ponds1@prorail.nl> - 1.0.0-1
- Initial creation of the RPM
