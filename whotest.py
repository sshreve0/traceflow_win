import asyncio
import ipaddress

from ipwhois import IPWhois, IPDefinedError

from traceflow_win import TraceflowWin


TARGETS = [
    "1.1.1.1",
    "8.8.8.8",
    "169.252.21.57",
    "169.252.21.61"
]



def isip(ip):
    print(ip)
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def get_domain_info(ip):
    results = ""
    try:
        obj = IPWhois(ip)  # Example IP address
        results = obj.lookup_whois()
    except IPDefinedError:
        return "RFC 1918 Address"
    except Exception as e:
        print(e)

    return results

async def test():
    for ip in TARGETS:
        tracer = TraceflowWin(ip)
        results = await tracer.run()
        for path_id, hops in results.items():
            for hop in hops:
                if isip(hop):
                    res = get_domain_info(hop)
                    print(res)

asyncio.run(test())