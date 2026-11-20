Name:		jakarta-inject-api
Version:	2.0.1
Release:	1
Summary:	Jakarta Dependency Injection API
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/jakartaee/inject
Source0:	https://github.com/jakartaee/inject/archive/refs/tags/%{version}.tar.gz#/jakarta-inject-api-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar

%description
Jakarta Dependency Injection API 2.0.1, coordinate
jakarta.inject:jakarta.inject-api. The classes live in jakarta.inject.
jakarta-inject 1.0.5 remains the javax.inject jar. The two packages
use different Maven coordinates.

%prep
%autosetup -n inject-%{version} -p1
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete
python - << 'PY'
from pathlib import Path
files = [path for path in Path("src/main/java").rglob("*.java") if path.name != "module-info.java"]
if len(files) != 7:
    raise SystemExit("inject sources " + str(len(files)))
PY

%build
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
mkdir -p classes
find src/main/java -name '*.java' ! -name module-info.java > sources.list
test "$(wc -l < sources.list)" -eq 7
javac --release 8 -encoding UTF-8 -Xlint:-options -d classes @sources.list
jar cf jakarta.inject-api.jar -C classes .
jar tf jakarta.inject-api.jar | grep -E '\.(java|jar|so|node|wasm)$' && exit 1 || true
jar tf jakarta.inject-api.jar | grep -F 'javax/inject/' && exit 1 || true
jar tf jakarta.inject-api.jar | grep -F module-info.class && exit 1 || true
javap -verbose -cp jakarta.inject-api.jar jakarta.inject.Inject | grep -F 'major version: 52'

python - << 'PY'
text = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>jakarta.inject</groupId>
  <artifactId>jakarta.inject-api</artifactId>
  <version>%{version}</version>
  <name>Jakarta Dependency Injection API</name>
  <description>Jakarta Dependency Injection API %{version}.</description>
  <url>https://github.com/jakartaee/inject</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
    </license>
  </licenses>
</project>
"""
open("jakarta.inject-api.pom", "w", encoding="utf-8").write(text)
PY

%install
sysjar install --buildroot %{buildroot} \
	--artifact jakarta.inject-api.pom:jakarta.inject-api.jar \
	--file-name jakarta.inject-api \
	--filelist .mfiles

%check
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
JAR=%{buildroot}%{_javadir}/jakarta.inject-api.jar
test -f "$JAR"
mkdir -p check
cat > check/Smoke.java << 'END'
import jakarta.inject.Inject;
import jakarta.inject.Named;
import java.lang.reflect.Field;
public class Smoke {
	@Inject @Named("mail") String value;
	public static void main(String[] args) throws Exception {
		Field field = Smoke.class.getDeclaredField("value");
		Inject inject = field.getAnnotation(Inject.class);
		Named named = field.getAnnotation(Named.class);
		if (inject == null || named == null || !"mail".equals(named.value())) {
			throw new AssertionError("missing");
		}
		System.out.println("inject_ok " + named.value());
	}
}
END
javac --release 8 -encoding UTF-8 -Xlint:-options -cp "$JAR" -d check check/Smoke.java
java -cp "check:$JAR" Smoke > check/out.txt
cat check/out.txt
grep -F -qx 'inject_ok mail' check/out.txt

%files -f .mfiles
%license LICENSE.txt
%doc NOTICE.md
