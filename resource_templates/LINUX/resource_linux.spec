Name:         resource_linux
Version:      1.0.0
Release:      1
Summary:      Resource script linux
Group:        Applications/System
License:      GPL
Vendor:       Platform Bouwteam
Source:       %{name}.tar.gz
BuildRoot:    %{_tmppath}/%{name}-root

%description
The scripts will:
Modify the iptables on the server and will push the
modified /etc/sysconfig/iptables to the satellite configuration channel.

%prep
%setup -q -n %{name}

%build
# Empty.

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/opt/scripts/linux
cp -R scripts/bin $RPM_BUILD_ROOT/opt/scripts/linux

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
%dir    /opt/scripts/linux/bin
/opt/scripts/linux/bin/linux.sh
/opt/scripts/linux/bin/README

%changelog
* Fri Jun 05 2015 Jurgen Ponds <jurgen.ponds1@prorail.nl> - 1.0.0-1
- Initial creation of the RPM
