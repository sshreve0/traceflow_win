import asyncio
import ipaddress
import os
from collections import defaultdict
import dns.resolver

from scapy.all import sr1
from scapy.layers.inet import IP, ICMP


def isip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except Exception:
        return False


class TraceflowWin:
    def __init__(self, destination: str, path_count: int, max_hops=30, timeout=2.0):
        self.destination = destination
        self.max_hops = max_hops
        self.timeout = timeout
        self.path_count = path_count
        self.pid = os.getpid() & 0xFFFF
        self.results = defaultdict(lambda: ["*"] * self.max_hops)
        self.stopped_paths = set()

    async def probe(self, path_id, ttl, loop):
        if path_id in self.stopped_paths:
            return

        ip_id = (path_id << 8) | ttl
        pkt = IP(dst=self.destination, ttl=ttl, id=ip_id) / ICMP(id=self.pid + path_id, seq=ttl)

        def send_and_receive():
            return sr1(pkt, timeout=self.timeout, verbose=0)

        reply = await loop.run_in_executor(None, send_and_receive)

        if reply and reply.haslayer(ICMP):
            self.results[path_id][ttl - 1] = reply.src
            if reply[ICMP].type == 0:
                self.stopped_paths.add(path_id)
        else:
            self.results[path_id][ttl - 1] = "*"

    async def run(self):
        if not isip(self.destination):
            resolved = dns.resolver.resolve(self.destination)
            resolvedip = ""
            for rdata in resolved:
                resolvedip = str(rdata)
            print(f"Resolved {self.destination} to {resolvedip}\n")
            self.destination = resolvedip
        else:
            print(f"Tracing to: {self.destination}\n")

        loop = asyncio.get_running_loop()

        for ttl in range(1, self.max_hops + 1):
            active_path_ids = [pid for pid in range(1, self.path_count + 1) if pid not in self.stopped_paths]
            if not active_path_ids:
                break  # All paths done

            tasks = [self.probe(pid, ttl, loop) for pid in active_path_ids]
            await asyncio.gather(*tasks)

        # Trim results to the actual TTL reached for each path
        for path_id in self.results:
            if path_id in self.stopped_paths:
                # Trim all trailing entries after destination was reached
                trace = self.results[path_id]
                cutoff = trace.index(self.destination) + 1
                self.results[path_id] = trace[:cutoff]

        return dict(self.results)

