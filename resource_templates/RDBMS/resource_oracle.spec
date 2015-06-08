Name:         resource_oracle
Version:      1.0.0
Release:      1
Summary:      Resource script oracle
Group:        Applications/System
License:      GPL
Vendor:       Platform Bouwteam
Source:       %{name}.tar.gz
BuildRoot:    %{_tmppath}/%{name}-root

%description
The scripts will:
Add database schema's to a database. 
%prep
%setup -q -n %{name}

%build
# Empty.

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/opt/scripts/oracle/bin
cp -R scripts/bin $RPM_BUILD_ROOT/opt/scripts/oracle

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
%dir    /opt/scripts/oracle/bin
/opt/scripts/oracle/bin/install_schema.sh
/opt/scripts/oracle/bin/README

%changelog
* Fri Jun 05 2015 Jurgen Ponds <jurgen.ponds1@prorail.nl> - 1.0.0-1
- Initial creation of the RPM
