#!/bin/bash
# BurpSuite MCP Full Control - Linux/macOS Build Script
# Requires: JDK 21+, curl

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Auto-detect JAVA_HOME
if [ -z "$JAVA_HOME" ]; then
    if [ -x "/usr/libexec/java_home" ]; then
        JAVA_HOME=$(/usr/libexec/java_home -v 21 2>/dev/null || /usr/libexec/java_home)
    elif [ -d "/usr/lib/jvm/java-21-openjdk" ]; then
        JAVA_HOME="/usr/lib/jvm/java-21-openjdk"
    elif [ -d "/usr/lib/jvm/java-21-openjdk-amd64" ]; then
        JAVA_HOME="/usr/lib/jvm/java-21-openjdk-amd64"
    fi
fi

if [ -z "$JAVA_HOME" ]; then
    echo "JAVA_HOME not set and could not auto-detect JDK 21+."
    echo "Set JAVA_HOME to your JDK installation directory."
    exit 1
fi

JAVAC="$JAVA_HOME/bin/javac"
JAR="$JAVA_HOME/bin/jar"
SRC="src/main/java/com/burpmcp"
LIB="lib"
OUT="build/classes"
DIST="build/libs"

echo "[1/4] Downloading dependencies..."
mkdir -p "$LIB"

if [ ! -f "$LIB/montoya-api.jar" ]; then
    echo "Downloading Montoya API..."
    curl -sL -o "$LIB/montoya-api.jar" "https://repo1.maven.org/maven2/net/portswigger/burp/extensions/montoya-api/2025.5/montoya-api-2025.5.jar"
fi
if [ ! -f "$LIB/gson.jar" ]; then
    echo "Downloading Gson..."
    curl -sL -o "$LIB/gson.jar" "https://repo1.maven.org/maven2/com/google/code/gson/gson/2.11.0/gson-2.11.0.jar"
fi
if [ ! -f "$LIB/nanohttpd.jar" ]; then
    echo "Downloading NanoHTTPD..."
    curl -sL -o "$LIB/nanohttpd.jar" "https://repo1.maven.org/maven2/org/nanohttpd/nanohttpd/2.3.1/nanohttpd-2.3.1.jar"
fi

echo "[2/4] Compiling..."
mkdir -p "$OUT"
"$JAVAC" -cp "$LIB/montoya-api.jar:$LIB/gson.jar:$LIB/nanohttpd.jar" -d "$OUT" "$SRC"/*.java

echo "[3/4] Packaging fat jar..."
mkdir -p "$DIST"

cd "$OUT"
"$JAR" xf "../../$LIB/gson.jar" com
"$JAR" xf "../../$LIB/nanohttpd.jar" fi
cd "$SCRIPT_DIR"

"$JAR" cf "$DIST/burp-mcp-full.jar" -C "$OUT" .

echo "[4/4] Done!"
echo "Output: $DIST/burp-mcp-full.jar"
echo ""
echo "Install: Burp Suite -> Extensions -> Add -> Java -> Select $DIST/burp-mcp-full.jar"
