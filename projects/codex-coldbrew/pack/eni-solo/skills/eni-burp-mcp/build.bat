@echo off
setlocal

if "%JAVA_HOME%"=="" (
    echo JAVA_HOME is not set. Set it to your JDK installation directory.
    echo Example: set JAVA_HOME=C:\Program Files\Java\jdk-21
    exit /b 1
)
set JAVAC=%JAVA_HOME%\bin\javac.exe
set JAR=%JAVA_HOME%\bin\jar.exe
set SRC=src\main\java\com\burpmcp
set LIB=lib
set OUT=build\classes
set DIST=build\libs

echo [1/4] Downloading dependencies...
if not exist %LIB% mkdir %LIB%

if not exist %LIB%\montoya-api.jar (
    echo Downloading Montoya API...
    curl -sL -o %LIB%\montoya-api.jar "https://repo1.maven.org/maven2/net/portswigger/burp/extensions/montoya-api/2025.5/montoya-api-2025.5.jar"
)
if not exist %LIB%\gson.jar (
    echo Downloading Gson...
    curl -sL -o %LIB%\gson.jar "https://repo1.maven.org/maven2/com/google/code/gson/gson/2.11.0/gson-2.11.0.jar"
)
if not exist %LIB%\nanohttpd.jar (
    echo Downloading NanoHTTPD...
    curl -sL -o %LIB%\nanohttpd.jar "https://repo1.maven.org/maven2/org/nanohttpd/nanohttpd/2.3.1/nanohttpd-2.3.1.jar"
)

echo [2/4] Compiling...
if not exist %OUT% mkdir %OUT%
"%JAVAC%" -cp "%LIB%\montoya-api.jar;%LIB%\gson.jar;%LIB%\nanohttpd.jar" -d %OUT% %SRC%\*.java
if errorlevel 1 (
    echo COMPILE FAILED
    exit /b 1
)

echo [3/4] Packaging fat jar...
if not exist %DIST% mkdir %DIST%

cd %OUT%
"%JAR%" xf ..\..\%LIB%\gson.jar com
"%JAR%" xf ..\..\%LIB%\nanohttpd.jar fi
cd ..\..

"%JAR%" cf %DIST%\burp-mcp-full.jar -C %OUT% .

echo [4/4] Done!
echo Output: %DIST%\burp-mcp-full.jar
echo.
echo Install: Burp Suite -^> Extensions -^> Add -^> Java -^> Select %DIST%\burp-mcp-full.jar
