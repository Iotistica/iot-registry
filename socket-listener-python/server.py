import os
import sys
import json
import signal
import socket
import threading

SOCKET_PATH = os.environ.get("AGENT_IPC_SOCKET", "/run/agent-ipc/app.sock")


def handle_connection(conn, addr):
    remote = addr or "agent"
    print(f"[connect] {remote}", flush=True)
    buf = ""
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            buf += data.decode()
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    payload = msg.get("data", "")
                    if not isinstance(payload, str):
                        payload = json.dumps(payload)
                    print(f"[msg] topic={msg.get('topic')} ts={msg.get('ts')} data={payload}", flush=True)
                except json.JSONDecodeError:
                    print(f"[raw] {line[:200]}", flush=True)
    except Exception as e:
        print(f"[error] {e}", flush=True)
    finally:
        conn.close()
        print(f"[disconnect] {remote}", flush=True)


def main():
    try:
        os.unlink(SOCKET_PATH)
    except FileNotFoundError:
        pass

    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(SOCKET_PATH)
    os.chmod(SOCKET_PATH, 0o666)
    srv.listen(5)

    print(f"Socket listener ready at {SOCKET_PATH}", flush=True)
    print("Waiting for agent to publish data...", flush=True)

    def shutdown(signum, frame):
        srv.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    while True:
        conn, addr = srv.accept()
        t = threading.Thread(target=handle_connection, args=(conn, addr), daemon=True)
        t.start()


if __name__ == "__main__":
    main()
