#!/usr/bin/env python3
"""Inject synthetic SSH events into the Wazuh manager queue.

Run as root on the Wazuh manager host. Sends N failed logins followed by one
successful login from the same source IP, which exercises the
100099 -> 100100 -> pb02_compromised_account chain without needing SSH
credentials on the target.

Example:
    sudo python3 tests/inject_pb02.py --src 192.168.56.145
"""

from __future__ import annotations

import argparse
import socket
import time


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject pb02 test events")
    parser.add_argument("--src", default="192.168.56.145", help="source IP")
    parser.add_argument("--user", default="labuser", help="target username")
    parser.add_argument("--agent-id", default="002", help="Wazuh agent ID")
    parser.add_argument("--agent-name", default="target-linux", help="agent name")
    parser.add_argument("--agent-ip", default="192.168.56.20", help="agent IP")
    parser.add_argument("--failures", type=int, default=7, help="failed logins")
    parser.add_argument(
        "--socket",
        default="/var/ossec/queue/sockets/queue",
        help="manager queue socket",
    )
    args = parser.parse_args()

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    base = time.time()
    for i in range(args.failures):
        stamp = time.strftime("%b %d %H:%M:%S", time.localtime(base + i))
        line = (
            f"{stamp} {args.agent_name} sshd-session[{11000 + i}]: "
            f"Failed password for {args.user} from {args.src} port {58000 + i} ssh2"
        )
        msg = (
            f"1:[{args.agent_id}] ({args.agent_name}) {args.agent_ip}"
            f"->journald:{line}\n"
        )
        sock.sendto(msg.encode(), args.socket)
        time.sleep(0.3)

    stamp = time.strftime("%b %d %H:%M:%S", time.localtime(base + args.failures + 2))
    line = (
        f"{stamp} {args.agent_name} sshd-session[11999]: "
        f"Accepted password for {args.user} from {args.src} port 59000 ssh2"
    )
    msg = (
        f"1:[{args.agent_id}] ({args.agent_name}) {args.agent_ip}"
        f"->journald:{line}\n"
    )
    sock.sendto(msg.encode(), args.socket)
    sock.close()

    print(
        f"injected {args.failures} failures + 1 success "
        f"from {args.src} for {args.user}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
