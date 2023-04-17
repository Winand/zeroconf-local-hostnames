"""
Announce fake HTTP servers pointing to localhost.

See also: mDNS (http://www.multicastdns.org), Apple Bonjour (dns-sd), Avahi
https://github.com/python-zeroconf/python-zeroconf/blob/master/examples/async_registration.py
https://superuser.com/a/1330028 | https://superuser.com/a/491750 | https://superuser.com/a/57314
Bonjour SDK: https://developer.apple.com/download/all/?q=Bonjour%20SDK%20for%20Windows
"""

import asyncio
import socket
import subprocess
from typing import List, Optional
from ipaddress import IPv4Address

import yaml
from zeroconf import IPVersion
from zeroconf.asyncio import AsyncServiceInfo, AsyncZeroconf

COMPOSE_PATHS = "docker-compose-paths"


class AsyncRunner:
    def __init__(self, interface: str):
        self.aiozc: Optional[AsyncZeroconf] = None
        self.interface = interface

    async def register_services(self, infos: List[AsyncServiceInfo]) -> None:
        print("Service registration...")
        for i in infos:
            assert i.server
            print("-", i.server.rstrip("."))
        self.aiozc = AsyncZeroconf(ip_version=IPVersion.V4Only, interfaces=[self.interface])
        tasks = [self.aiozc.async_register_service(info) for info in infos]
        background_tasks = await asyncio.gather(*tasks)
        await asyncio.gather(*background_tasks)
        print("Press Ctrl+C to unregister services")
        while True:
            await asyncio.sleep(1)

    async def unregister_services(self, infos: List[AsyncServiceInfo]) -> None:
        assert self.aiozc is not None
        tasks = [self.aiozc.async_unregister_service(info) for info in infos]
        background_tasks = await asyncio.gather(*tasks)
        await asyncio.gather(*background_tasks)
        await self.aiozc.async_close()


def strip_local(hostname: Optional[str]) -> Optional[str]:
    """Strip .local pseudo top level domain.

    :param hostname: name of a host
    :return: hostname without .local postfix or None
    """
    if not hostname:
        return
    if hostname.lower().endswith(".local"):
        return hostname[:-6]
    return hostname


if __name__ == '__main__':
    hostnames = []

    with open("config.yml") as f:
        config = yaml.safe_load(f)
    if "interface" in config:
        interface = config['interface']
    else:
        print("Warning: Interface not specified, trying to retrieve WSL interface address...")
        interface = subprocess.getoutput("wsl -d docker-desktop ip route ^| head -1 ^| awk '{print $3}'")
        IPv4Address(interface)  # validate IPv4 address
    print(f"Hostnames will be announced via {interface} interface")
    if COMPOSE_PATHS in config and "hostnames" in config:
        print("Warning: docker compose config path specified, hostname list will be ignored")
    if COMPOSE_PATHS in config:
        for dc_path in config[COMPOSE_PATHS]:
            with open(dc_path) as f:
                services = yaml.safe_load(f)['services']
            for name in services:
                # https://stackoverflow.com/a/55523502
                service = services[name]
                hostnames.append(name)
                container_name = strip_local(service.get('container_name'))
                if container_name and container_name not in hostnames:
                    hostnames.append(container_name)
                hostname = strip_local(service.get('hostname'))
                if hostname and hostname not in hostnames:
                    hostnames.append(hostname)
    elif "hostnames" in config:
        hostnames = [i for i in config["hostnames"]]
    else:
        raise ValueError(f"Specify '{COMPOSE_PATHS}' list or 'hostnames' list in config.yml")

    infos = []
    for i in hostnames:
        infos.append(
            AsyncServiceInfo(
                "_http._tcp.local.",
                f"{i}._http._tcp.local.",
                addresses=[socket.inet_aton("127.0.0.1")],
                port=80,
                server=f"{i}.local.",
            )
        )

    loop = asyncio.get_event_loop()
    runner = AsyncRunner(interface)
    try:
        loop.run_until_complete(runner.register_services(infos))
    except KeyboardInterrupt:
        print("Unregistering services...")
        loop.run_until_complete(runner.unregister_services(infos))
