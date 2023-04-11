from http import HTTPStatus
from traceback import format_exc
from typing import Optional

from sag_py_fastapi_health.models import Check, CheckResult

try:
    from aiohttp import BasicAuth, ClientResponseError, ClientSession, ClientTimeout, TCPConnector
except ImportError as exc:
    raise ImportError("Using this module requires the aiohttp library.") from exc


class HttpCheck(Check):
    _url: str
    _username: Optional[str]
    _password: Optional[str]
    _verify_ssl: bool
    _timeout: float
    _name: str

    def __init__(
        self,
        url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verify_ssl: bool = True,
        timeout: float = 60.0,
        name: str = "HTTP",
    ) -> None:
        self._url = url
        self._username = username
        self._password = password
        self._verify_ssl = verify_ssl
        self._timeout = timeout
        self._name = name

    async def __call__(self) -> CheckResult:
        try:
            async with ClientSession(
                connector=TCPConnector(verify_ssl=self._verify_ssl, enable_cleanup_closed=True),
                auth=BasicAuth(self._username, self._password or "") if self._username else None,
                timeout=ClientTimeout(self._timeout),
            ) as session:
                async with session.get(self._url) as response:
                    if response.status >= HTTPStatus.INTERNAL_SERVER_ERROR or (
                        self._username and response.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN)
                    ):
                        response.raise_for_status()
                    return CheckResult(
                        name=self._name,
                        status="Healthy" if response.ok else "Unhealthy",
                        description=f"Got status {response.status}",
                    )
        except ClientResponseError as response_error:
            return CheckResult(name=self._name, status="Unhealthy", description=str(response_error))
        except Exception:
            return CheckResult(name=self._name, status="Unhealthy", description=format_exc())
