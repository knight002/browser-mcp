#!/bin/bash

# Configuration
APP_DIR="/home/m247/workspace/browser_mcp"
PYTHON_BIN="$APP_DIR/venv/bin/python"
SERVER_SCRIPT="$APP_DIR/server.py"
PID_FILE="$APP_DIR/server.pid"
LOG_FILE="$APP_DIR/server.log"

# Browser (Chromium) configuration
BROWSER_BIN="${BROWSER_BIN:-chromium}"
CDP_PORT="${CDP_PORT:-9222}"
BROWSER_PID_FILE="$APP_DIR/browser.pid"
BROWSER_LOG="$APP_DIR/browser.log"
CHROME_ARGS="${CHROME_ARGS:---remote-debugging-port=$CDP_PORT --no-first-run --no-default-browser-check}"

cdp_up() {
    curl -s --max-time 2 "http://127.0.0.1:$CDP_PORT/json/version" > /dev/null
}

browser_running() {
    [ -f "$BROWSER_PID_FILE" ] && ps -p "$(cat $BROWSER_PID_FILE)" > /dev/null 2>&1
}

browser_start() {
    if browser_running; then
        echo "Browser is already running (PID: $(cat $BROWSER_PID_FILE))"
        return 0
    fi
    if cdp_up; then
        echo "CDP is already listening on port $CDP_PORT (browser not started by this script)."
        echo "Close the existing browser first if you want this script to manage it."
        return 1
    fi

    echo "Starting Chromium with CDP on port $CDP_PORT..."
    nohup $BROWSER_BIN $CHROME_ARGS > $BROWSER_LOG 2>&1 &
    echo $! > $BROWSER_PID_FILE

    for i in $(seq 1 10); do
        if cdp_up; then
            echo "Browser ready (PID: $(cat $BROWSER_PID_FILE)), CDP on port $CDP_PORT"
            return 0
        fi
        sleep 1
    done
    echo "WARNING: CDP port $CDP_PORT not responding after 10s. Check $BROWSER_LOG"
    echo "(If another Chromium instance is already running, it may have absorbed this launch.)"
    return 1
}

browser_stop() {
    if browser_running; then
        PID=$(cat $BROWSER_PID_FILE)
        echo "Stopping Browser (PID: $PID)..."
        kill $PID 2>/dev/null
        rm -f $BROWSER_PID_FILE
        echo "Browser stopped."
    else
        echo "Browser is not running (no PID file found)."
    fi
}

browser_status() {
    if browser_running; then
        echo "Browser is running (PID: $(cat $BROWSER_PID_FILE)), CDP on port $CDP_PORT"
        return 0
    fi
    if cdp_up; then
        echo "CDP is listening on port $CDP_PORT but browser was not started by this script."
    else
        echo "Browser is stopped."
    fi
    return 1
}

start() {
    if [ -f $PID_FILE ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null; then
            echo "Server is already running (PID: $PID)"
            return 1
        fi
    fi

    browser_start || echo "WARNING: browser not ready, MCP server will connect lazily on first setup_session"

    echo "Starting Browser MCP Server..."
    nohup $PYTHON_BIN $SERVER_SCRIPT > $LOG_FILE 2>&1 &
    echo $! > $PID_FILE
    echo "Server started with PID: $(cat $PID_FILE)"
}

stop() {
    if [ -f $PID_FILE ]; then
        PID=$(cat $PID_FILE)
        echo "Stopping Server (PID: $PID)..."
        kill $PID 2>/dev/null
        rm -f $PID_FILE
        echo "Server stopped."
    else
        echo "Server is not running (no PID file found)."
    fi
    browser_stop
}

status() {
    if [ -f $PID_FILE ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null; then
            echo "Server is running (PID: $PID)"
            return 0
        else
            echo "Server is dead (PID file exists but process is gone)"
            return 1
        fi
    else
        echo "Server is stopped."
        return 1
    fi
}

restart() {
    stop
    sleep 2
    start
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status
        browser_status
        ;;
    restart)
        restart
        ;;
    browser)
        case "$2" in
            start)   browser_start ;;
            stop)    browser_stop ;;
            status)  browser_status ;;
            *)       echo "Usage: $0 browser {start|stop|status}"; exit 1 ;;
        esac
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart|browser {start|stop|status}}"
        exit 1
        ;;
esac
