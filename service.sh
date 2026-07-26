#!/bin/bash

# Configuration
APP_DIR="/workspace/browser_mcp"
PYTHON_BIN="$APP_DIR/venv/bin/python"
SERVER_SCRIPT="$APP_DIR/server.py"
PID_FILE="$APP_DIR/server.pid"
LOG_FILE="$APP_DIR/server.log"

start() {
    if [ -f $PID_FILE ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null; then
            echo "Server is already running (PID: $PID)"
            return 1
        fi
    fi

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
        ;;
    restart)
        restart
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac
