import re
import asyncio
import argparse
from enum import Enum
from typing import List, Awaitable, Any
import aiohttp
import aiohttp_socks
from logger import setup_colored_logger


from rich.console import Console
from rich.table import Table


class ProxyType(Enum):
    HTTP = "HTTP"
    SOCKS5 = "SOCKS5"


class ProxyTableDisplay:
    COLUMNS = ["host", "port", "login", "password", "http", "socks5"]

    def __init__(self) -> None:
        self.console = Console()

    def create_table(self, proxies: list["Proxy"]) -> Table:
        table = Table(title="Proxies")
        for column in self.COLUMNS:
            table.add_column(
                column,
                header_style="bright_cyan",
                style="cyan",
                no_wrap=True,
                justify="center",
            )
        for proxy in proxies:
            proxy_data = [
                proxy.host,
                str(proxy.port),
                proxy.login,
                proxy.password,
                "✅" if proxy.http else "❌",
                "✅" if proxy.socks5 else "❌",
            ]
            table.add_row(*proxy_data, style="bright_green")
        return table

    def display_proxies(self, proxies: list["Proxy"]) -> None:
        """Displays the proxy data in a formatted table"""
        table = self.create_table(proxies)
        self.console.print(table)


class _ProxyConnector:
    def __init__(self) -> None:
        self.http_connector: "aiohttp_socks.ProxyConnector" = None
        self.socks5_connector: "aiohttp_socks.ProxyConnector" = None

        self.host: str = ""
        self.port: int = 0
        self.login: str = ""
        self.password: str = ""

    def connector(self):
        """Initialize SOCKS5 and HTTP proxy connectors with authentication"""
        if self.host and self.port:
            self.socks5_connector = aiohttp_socks.ProxyConnector(
                host=self.host,
                port=self.port,
                username=self.login,
                password=self.password,
                proxy_type=aiohttp_socks.ProxyType.SOCKS5,
            )
            self.http_connector = aiohttp_socks.ProxyConnector(
                host=self.host,
                port=self.port,
                username=self.login,
                password=self.password,
                proxy_type=aiohttp_socks.ProxyType.HTTP,
            )


class Proxy(_ProxyConnector):
    def __init__(self, proxy: str) -> None:
        super().__init__()
        self.logger = setup_colored_logger("Proxy")
        self.normalize_proxy(proxy)
        self.connector()

        self.http: bool = False
        self.socks5: bool = False
        self.proxy_types = []
        self.auth = False
        if self.login and self.password:
            self.auth = True

    def __repr__(self) -> str:
        return "<Proxy({0} {1} {2} {3} {4})>".format(
            f"{self.host=}",
            f"{self.port=}",
            f"{self.auth=}",
            f"{self.http=}",
            f"{self.socks5=}",
        )

    def normalize_proxy(self, proxy: str) -> None:
        """Normalize proxy string to standard format and extract components

        Args:
            proxy (str): Proxy string in any supported format

        Note:
            Parses and sets the proxy attributes
        """
        elements: list[Any] = proxy.replace("@", ":").split(":")
        if len(elements) == 4:
            if re.match(r"\d+$", elements[-1]):
                self.login, self.password, self.host, self.port = elements
                self.logger.debug(f"proxy format passed: {proxy}")
            elif re.match(r"\d+$", elements[1]):
                self.host, self.port, self.login, self.password = elements
                self.logger.debug(f"proxy format passed: {proxy}")
            else:
                self.logger.warning(f"proxy format failed: '{proxy}'")
        elif len == 2:
            pass
        else:
            self.logger.warning(f"proxy format failed: '{proxy}'")


class ProxyPulse:
    _URL: str = "https://httpbin.org/ip"

    def __init__(self, args: "argparse.Namespace") -> None:
        self.proxies: list["Proxy"] = []
        self.args = args
        self.logger = setup_colored_logger(
            name="ProxyPulse", debug=self.args.debug
        )

    def parse_proxies_file(self, data: str) -> None:
        """Parse proxy addresses from text and create Proxy objects for each one

        Args:
            data (str): Raw proxy data text with one proxy per line.
        """
        for row in data.splitlines():
            if row.strip():
                for line in row.split():
                    self.proxies.append(Proxy(line))

    def parse_proxies(self):
        """Parse proxy configurations from command-line arguments
        and file sources
        """
        if self.args:
            if self.args.proxies:
                for proxy in self.args.proxies:
                    proxy_obj = Proxy(proxy)
                    if proxy_obj.host and proxy_obj.host:
                        self.proxies.append(proxy_obj)

            if self.args.file:
                try:
                    with open(self.args.file, "r", encoding="utf-8") as readf:
                        data = readf.read()
                        self.parse_proxies_file(data)
                except FileNotFoundError as err:
                    self.logger.error(err)
                except IOError as err:
                    self.logger.error(err)

    @property
    def url(self) -> str:
        """Parse url line from command-line arguments or use url by default

        Returns:
            str: _description_
        """
        if self.args.url:
            self.logger.debug(f"using URL from args: '{self.args.url}'")
            return self.args.url
        else:
            self.logger.debug(f"using default URL: '{self._URL}'")
            return self._URL

    def _is_valid_proxy(self, proxy: "Proxy") -> bool:
        """Validate that proxy by host and port

        Args:
            proxy (Proxy): The proxy to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not proxy.host and proxy.port:
            self.logger.error(f"invalid proxy: '{proxy}'")
            return False
        return True

    def _proxy_type(
        self, connector: aiohttp_socks.ProxyConnector
    ) -> ProxyType | None:
        """Get proxy protocol type from connector protected attribute

        Args:
            connector (aiohttp_socks.ProxyConnector): The proxy connector
                to extract type from

        Returns:
            ProxyType | None: Available proxy protocol, None otherwise
        """
        if connector._proxy_type.name in ProxyType._member_names_:
            return ProxyType[connector._proxy_type.name]
        return None

    def _proxy_status(
        self, proxy: "Proxy", proxy_type: str, status_code: int | None
    ) -> None:
        """Updates the availabiity sttus of a specific proxy protocol

        Args:
            proxy (Proxy): The proxy instance
            proxy_type (str): Type protocol type to set status for
                (e.g. 'http', 'soscks5')
            status_code (int | None): HTTP status code from the proxy check,
                None if check failed
        """
        if status_code in [200, 204]:
            if proxy_type == ProxyType.HTTP.name:
                proxy.http = True
            if proxy_type == ProxyType.SOCKS5.name:
                proxy.socks5 = True
            self.logger.debug(
                f"{proxy_type.lower()} proxy protocol type is available"
            )
        else:
            self.logger.warning(
                f"{proxy_type.lower()} proxy protocol type is not available"
            )

    async def _execute_request(
        self,
        proxy: "Proxy",
        connector: aiohttp_socks.ProxyConnector,
        proxy_type: "ProxyType",
    ) -> int | None:
        """Execute request to check proxy availability

        Args:
            proxy (Proxy): Proxy instance
            connector (aiohttp_socks.ProxyConnector): Proxy connector
                (e.g. 'HTTP', "SOCKS5')
            proxy_type (ProxyType): Current proxy protocol type

        Returns:
            int | None: status code, None otherwise
        """

        self.logger.debug(
            f"try request {proxy_type.name.lower()} proxy: '{proxy}'"
        )
        async with aiohttp.ClientSession(connector=connector) as client:
            try:
                self.logger.debug(connector)

                async with client.get(
                    url=self.url,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp and resp.status in [200, 204]:
                        self.logger.debug(
                            f"success with {proxy_type.name.lower()} "
                            f"proxy: '{proxy}': code: {resp.status}"
                        )
                        return resp.status
                    else:
                        self.logger.warning(
                            f"Failed with proxy: '{proxy}': {resp}"
                        )
            except aiohttp_socks.ProxyError as err:
                self.logger.warning(
                    f"problem with {proxy_type.name.lower()} "
                    f"proxy: {proxy}, {err.args}"
                )
            except aiohttp_socks.ProxyConnectionError as err:
                self.logger.warning(
                    f"problem with connection to {proxy_type.name.lower()} "
                    f"proxy '{proxy}', {err.args}"
                )
            except Exception as err:
                self.logger.warning(
                    f"failed with {proxy_type.name.lower()} "
                    f"proxy '{proxy}': {err}"
                )

        return None

    async def make_request(
        self,
        proxy: "Proxy",
        connector: aiohttp_socks.ProxyConnector,
    ) -> None:
        """Make request to check proxy connectivity

        Args:
            proxy (Proxy): Proxy instance
            connector (aiohttp_socks.ProxyConnector): Proxy connector
                with protocol configuration
        """

        if not self._is_valid_proxy(proxy):
            return None
        proxy_type = self._proxy_type(connector)

        if not proxy_type:
            return
        result = await self._execute_request(proxy, connector, proxy_type)
        self._proxy_status(proxy, proxy_type.name, result)


async def main():
    try:
        argp = argparse.ArgumentParser(
            prog="proxy_checker", description="Proxy Pulse"
        )
        argp.add_argument(
            "-f", "--file", help="Path to txt file containing proxies"
        )
        argp.add_argument(
            "-p", "--proxies", help="Space-separated proxy list", nargs="+"
        )
        argp.add_argument(
            "--url",
            help="URL to test proxy connectivity",
        )
        argp.add_argument(
            "--debug",
            help="Enable debug logging",
            action="store_true",
        )
        args: argparse.Namespace = argp.parse_args()
    except Exception:
        args = argparse.Namespace()

    p = ProxyPulse(args)
    p.parse_proxies()
    tasks: List[Awaitable[Any]] = []
    for proxy in p.proxies:
        tasks.append(p.make_request(proxy, proxy.http_connector))
        tasks.append(p.make_request(proxy, proxy.socks5_connector))
    await asyncio.gather(*tasks, return_exceptions=True)

    # Console display
    disp = ProxyTableDisplay()
    disp.display_proxies(p.proxies)


if __name__ == "__main__":
    asyncio.run(main())
