# Copyright (c) 2000-2007, JPackage Project
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name of the JPackage Project nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

# If you don't want to build with maven, and use straight ant instead,
# give rpmbuild option '--without maven'

%define with_maven 0

%define base_name       lang
%define short_name      commons-%{base_name}

Name:           jakarta-%{short_name}
Version:        2.4
Release:        1.1%{?dist}
Epoch:          0
Summary:        Provides a host of helper utilities for the java.lang API
License:        ASL 2.0
Group:          Development/Libraries
URL:            http://commons.apache.org/lang/
Source0:        http://archive.apache.org/dist/commons/%{base_name}/source/%{short_name}-%{version}-src.tar.gz
Source1:        pom-maven2jpp-depcat.xsl
Source2:        pom-maven2jpp-newdepmap.xsl
Source3:        pom-maven2jpp-mapdeps.xsl
Source4:        %{short_name}-%{version}-jpp-depmap.xml
Patch0:         %{name}-notarget.patch
Patch1:         %{name}-addosgimanifest.patch
Patch2:         %{name}-encoding.patch

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  jpackage-utils >= 0:1.7.2
BuildRequires:  ant
BuildRequires:  ant-junit
BuildRequires:  %{__perl}
%if %{with_maven}
BuildRequires:  maven >= 0:1.1
BuildRequires:  saxon
BuildRequires:  saxon-scripts
BuildRequires:  maven-plugin-changelog
BuildRequires:  maven-plugin-changes
BuildRequires:  maven-plugin-xdoc
%endif
Requires(post):    jpackage-utils >= 0:1.7.2
Requires(postun):  jpackage-utils >= 0:1.7.2

%description
The standard Java libraries fail to provide enough methods for
manipulation of its core classes. The Commons Lang Component provides
these extra methods.
The Commons Lang Component provides a host of helper utilities for the
java.lang API, notably String manipulation methods, basic numerical
methods, object reflection, creation and serialization, and System
properties. Additionally it contains an inheritable enum type, an
exception structure that supports multiple types of nested-Exceptions
and a series of utilities dedicated to help with building methods, such
as hashCode, toString and equals.

%package        javadoc
Summary:        Javadoc for %{name}
Group:          Documentation
BuildRequires:  java-javadoc

%description    javadoc
Javadoc for %{name}.

%if %{with_maven}
%package manual
Summary:        Documents for %{name}
Group:          Documentation

%description manual
%{summary}.
%endif

%prep
%setup -q -n %{short_name}-%{version}-src
%{__perl} -pi -e 's/\r//g' *.txt

%patch0
%patch1
%patch2

%build
%if %{with_maven}
if [ ! -f %{SOURCE4} ]; then
export DEPCAT=$(pwd)/%{short_name}-%{version}-depcat.new.xml
echo '<?xml version="1.0" standalone="yes"?>' > $DEPCAT
echo '<depset>' >> $DEPCAT
for p in $(find . -name project.xml); do
    pushd $(dirname $p)
    /usr/bin/saxon project.xml %{SOURCE1} >> $DEPCAT
    popd
done
echo >> $DEPCAT
echo '</depset>' >> $DEPCAT
/usr/bin/saxon $DEPCAT %{SOURCE2} > %{short_name}-%{version}-depmap.new.xml
fi

for p in $(find . -name project.xml); do
    pushd $(dirname $p)
    cp project.xml project.xml.orig
    /usr/bin/saxon -o project.xml project.xml.orig %{SOURCE3} map=%{SOURCE4}
    popd
done

maven \
    -Dmaven.javadoc.source=1.4 \
    -Dmaven.repo.remote=file:/usr/share/maven/repository \
    -Dmaven.home.local=$(pwd)/.maven \
    jar javadoc xdoc:transform
%else

  %ant \
    -Djunit.jar=$(find-jar junit) \
    -Dfinal.name=%{short_name} \
    -Djdk.javadoc=%{_javadocdir}/java \
    jar javadoc
#    test dist
%endif

%install
rm -rf $RPM_BUILD_ROOT
# jars
mkdir -p $RPM_BUILD_ROOT%{_javadir}
%if %{with_maven}
cp -p target/%{short_name}-%{version}.jar $RPM_BUILD_ROOT%{_javadir}/%{name}-%{version}.jar
%else
cp -p dist/%{short_name}.jar $RPM_BUILD_ROOT%{_javadir}/%{name}-%{version}.jar
%endif
(cd $RPM_BUILD_ROOT%{_javadir} && for jar in *-%{version}*; do ln -sf ${jar} `echo $jar| sed "s|jakarta-||g"`; done)
(cd $RPM_BUILD_ROOT%{_javadir} && for jar in *-%{version}*; do ln -sf ${jar} `echo $jar| sed "s|-%{version}||g"`; done)

%if %{with_maven}
%add_to_maven_depmap %{base_name} %{base_name} %{version} JPP %{name}

# pom
install -d -m 755 $RPM_BUILD_ROOT%{_datadir}/maven2/poms
install -m 644 pom.xml $RPM_BUILD_ROOT%{_datadir}/maven2/poms/JPP-%{name}.pom
%endif

# javadoc
mkdir -p $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}
%if %{with_maven}
cp -pr target/docs/apidocs/* $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}
%else
cp -pr dist/docs/api/* $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}
%endif
ln -s %{name}-%{version} $RPM_BUILD_ROOT%{_javadocdir}/%{name}

## manual
install -d -m 755 $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}
cp -p *.txt $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}
%if %{with_maven}
rm -rf target/docs/apidocs
install -d -m 755 $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}/site
cp -pr target/docs/* $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}/site
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%if %{with_maven}
%post
%update_maven_depmap

%postun
%update_maven_depmap
%endif

%files
%defattr(0644,root,root,0755)
%dir %{_docdir}/%{name}-%{version}
%doc %{_docdir}/%{name}-%{version}/*.txt
#%doc PROPOSAL.html STATUS.html LICENSE.txt NOTICE.txt RELEASE-NOTES.txt
%{_javadir}/*
%if %{with_maven}
%{_datadir}/maven2/poms/*
%{_mavendepmapfragdir}
%endif

%files javadoc
%defattr(0644,root,root,0755)
%doc %{_javadocdir}/%{name}-%{version}
%doc %{_javadocdir}/%{name}

%if %{with_maven}
%files manual
%defattr(0644,root,root,0755)
%doc %{_docdir}/%{name}-%{version}/site
%endif

%changelog
* Fri Mar 19 2010 Alexander Kurtakov <akurtako@redhat.com> 0:2.4-1.1
- RHEL rebase.

* Wed Feb  3 2010 Jerry James <loganjerry@gmail.com> - 0:2.4-1
- Update to version 2.4.
- Install the upstream POM.
- Add -encoding patch.

* Fri Jan 08 2010 Andrew Overholt <overholt@redhat.com> 0:2.3-4.6
- Remove gcj support.
- Fix Group tags.
- Add more stuff to %%{with_maven} sections

* Fri Jan 08 2010 Andrew Overholt <overholt@redhat.com> 0:2.3-4.5
- Update Source0 URL.

* Mon Nov 30 2009 Dennis Gregorovic <dgregor@redhat.com> - 0:2.3-4.4
- Rebuilt for RHEL 6

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0:2.3-4.3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0:2.3-3.3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Thu Jul 24 2008 Andrew Overholt <overholt@redhat.com> 0:2.3-2.3
- Add OSGi MANIFEST.MF

* Wed Jul  9 2008 Tom "spot" Callaway <tcallawa@redhat.com> - 0:2.3-2.2
- drop repotag
- fix license tag

* Tue Feb 19 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 0:2.3-2jpp.1
- Autorebuild for GCC 4.3

* Tue Jan 22 2008 Permaine Cheung <pcheung@redhat.com> - 0:2.3-1jpp.1
- Merge with upstream

* Mon Aug 13 2007 Ralph Apel <r.apel at r-apel.de> - 0:2.3-1jpp
- Upgrade to 2.3
- Build with maven by default
- Add pom anf depmap frag
- Make Vendor, Distribution based on macro

* Thu Mar 29 2007 Permaine Cheung <pcheung@redhat.com> - 0:2.1-6jpp.1
- Merge from upstream and rpmlint cleanup

* Thu Aug 10 2006 Deepak Bhole <dbhole@redhat.com> - 0:2.1-5jpp.1
- Added missing requirements.
- Added missing postun section for javadoc.

* Thu Aug 10 2006 Karsten Hopp <karsten@redhat.de> - 0:2.1-4jpp_3fc
- Requires(post): coreutils

* Sat Jul 22 2006 Jakub Jelinek <jakub@redhat.com> - 0:2.1-4jpp_2fc
- Rebuilt

* Wed Jul 19 2006 Deepak Bhole <dbhole@redhat.com> - 0:2.1-4jpp_1fc
- Remove name/release/version defines as applicable.

* Mon Jul 17 2006 Deepak Bhole <dbhole@redhat.com> - 0:2.1-3jpp
- Added conditional native compiling.
- By jkeating: Patched to not use taget= in build.xml

* Mon Feb 27 2006 Fernando Nasser <fnasser@redhat.com> - 0:2.1-2jpp
- First JPP 1.7 build

* Sat Aug 20 2005 Ville Skyttä <scop at jpackage.org> - 0:2.1-1jpp
- 2.1, javadoc crosslink patch applied upstream.
- Use the %%ant macro.

* Sun Aug 23 2004 Randy Watler <rwatler at finali.com> - 0:2.0-2jpp
- Rebuild with ant-1.6.2

* Sun Oct 12 2003 Ville Skyttä <ville.skytta at iki.fi> - 0:2.0-1jpp
- Update to 2.0.
- Add non-versioned javadocs dir symlink.
- Crosslink with local J2SE javadocs.
- Convert specfile to UTF-8.

* Fri Apr  4 2003 Ville Skyttä <ville.skytta at iki.fi> - 0:1.0.1-3jpp
- Rebuild for JPackage 1.5.

* Tue Mar  4 2003 Ville Skyttä <ville.skytta at iki.fi> - 1.0.1-2jpp
- Repackage to recover from earlier accidental overwrite with older version.
- No macros in URL and SourceX tags.
- Remove spurious api/ from installed javadoc path.
- Spec file cleanups.
- (from 1.0.1-1jpp) Update to 1.0.1.
- (from 1.0.1-1jpp) Run JUnit tests when building.

* Thu Feb 27 2003 Henri Gomez <hgomez@users.sourceforge.net> 1.0-3jpp
- fix ASF license and add packager tag

* Mon Oct 07 2002 Henri Gomez <hgomez@users.sourceforge.net> 1.0-2jpp
- missed to include changelog

* Mon Oct 07 2002 Henri Gomez <hgomez@users.sourceforge.net> 1.0-1jpp
- release 1.0

* Tue Aug 20 2002 Henri Gomez <hgomez@users.sourceforge.net> 1.0.b1.1-1jpp
- fist jpp release
