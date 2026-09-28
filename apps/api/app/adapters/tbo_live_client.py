"""TBO Holidays live HTTP client (FC Phase 1).

Endpoint paths follow common TBO Rest patterns and are overridable via settings.
When credentials are missing or TBO_LIVE_ENABLED=false, the adapter uses the
simulated client instead — never silently present SIM offers as live.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class TboLiveError(Exception):
    """Raised when live TBO HTTP/auth/business response fails."""

    def __init__(self, message: str, *, status_code: Optional[int] = None, raw: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.raw = raw


class TboLiveClient:
    """
    Real httpx client for TBO Flight Rest API.
    Requires TBO_LIVE_ENABLED + base URL + credentials.
    """

    def __init__(self) -> None:
        self.base_url = (settings.TBO_BASE_URL or "").rstrip("/")
        self.client_id = settings.TBO_CLIENT_ID or ""
        self.user_name = settings.TBO_USER_NAME or ""
        self.password = settings.TBO_PASSWORD or ""
        self.end_user_ip = settings.TBO_END_USER_IP or "127.0.0.1"
        self.timeout = float(settings.TBO_HTTP_TIMEOUT_SECONDS)
        self._token: Optional[str] = None

    def credentials_ready(self) -> bool:
        return bool(self.base_url and self.client_id and self.user_name and self.password)

    def _url(self, path: str) -> str:
        path = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{path}"

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[dict] = None,
        authed: bool = True,
    ) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if authed:
            token = await self.authenticate()
            headers["Authorization"] = f"Bearer {token}"
            # Some TBO deployments expect Token-Id header instead of/in addition to Bearer
            headers["TokenId"] = token

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.request(
                    method, self._url(path), json=json_body, headers=headers
                )
        except httpx.TimeoutException as e:
            raise TboLiveError("TBO request timed out", raw=str(e)) from e
        except httpx.HTTPError as e:
            raise TboLiveError(f"TBO HTTP error: {e}", raw=str(e)) from e

        try:
            data = resp.json()
        except Exception:
            data = {"raw_text": resp.text}

        if resp.status_code >= 400:
            raise TboLiveError(
                f"TBO HTTP {resp.status_code}",
                status_code=resp.status_code,
                raw=data,
            )
        return data if isinstance(data, dict) else {"Response": data}

    async def authenticate(self) -> str:
        if self._token:
            return self._token
        if not self.credentials_ready():
            raise TboLiveError("TBO live credentials incomplete")

        path = settings.TBO_AUTH_PATH
        body = {
            "ClientId": self.client_id,
            "UserName": self.user_name,
            "Password": self.password,
            "EndUserIp": self.end_user_ip,
        }
        data = await self._request("POST", path, json_body=body, authed=False)
        # Common shapes: { TokenId } or { Response: { TokenId, Status } }
        token = data.get("TokenId") or (data.get("Response") or {}).get("TokenId")
        if not token:
            raise TboLiveError("TBO auth succeeded but TokenId missing", raw=data)
        self._token = str(token)
        logger.info("tbo_live_authenticated")
        return self._token

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        *,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        return_date: Optional[str] = None,
        cabin: str = "1",
    ) -> Dict[str, Any]:
        """
        Search flights. Payload keys mirror common TBO Search request fields;
        Sahil may adjust via env path if supplier version differs.
        """
        segments = [
            {
                "Origin": origin,
                "Destination": destination,
                "FlightCabinClass": cabin,
                "PreferredDepartureTime": f"{departure_date}T00:00:00",
            }
        ]
        if return_date:
            segments.append(
                {
                    "Origin": destination,
                    "Destination": origin,
                    "FlightCabinClass": cabin,
                    "PreferredDepartureTime": f"{return_date}T00:00:00",
                }
            )
        body = {
            "EndUserIp": self.end_user_ip,
            "TokenId": await self.authenticate(),
            "AdultCount": adults,
            "ChildCount": children,
            "InfantCount": infants,
            "JourneyType": "2" if return_date else "1",
            "Segments": segments,
        }
        data = await self._request("POST", settings.TBO_SEARCH_PATH, json_body=body)
        logger.info("tbo_live_search_ok", origin=origin, destination=destination)
        return data

    async def fare_quote(self, trace_id: str, result_index: str) -> Dict[str, Any]:
        body = {
            "EndUserIp": self.end_user_ip,
            "TokenId": await self.authenticate(),
            "TraceId": trace_id,
            "ResultIndex": result_index,
        }
        return await self._request("POST", settings.TBO_FARE_QUOTE_PATH, json_body=body)

    async def book(
        self, trace_id: str, result_index: str, passengers: List[dict]
    ) -> Dict[str, Any]:
        pax = []
        for i, p in enumerate(passengers or []):
            pax.append(
                {
                    "Title": p.get("title") or "Mr",
                    "FirstName": p.get("first_name") or p.get("FirstName") or "NA",
                    "LastName": p.get("last_name") or p.get("LastName") or "NA",
                    "PaxType": 1 if i == 0 else 1,
                    "DateOfBirth": p.get("date_of_birth") or p.get("DateOfBirth"),
                    "PassportNo": p.get("passport_number") or p.get("PassportNo"),
                    "Gender": p.get("gender") or 1,
                    "AddressLine1": p.get("address") or "NA",
                    "City": p.get("city") or "NA",
                    "CountryCode": p.get("country_code") or "IN",
                    "CountryName": p.get("country_name") or "India",
                    "ContactNo": p.get("phone") or "0000000000",
                    "Email": p.get("email") or "noreply@tripos.local",
                    "IsLeadPax": i == 0,
                }
            )
        body = {
            "EndUserIp": self.end_user_ip,
            "TokenId": await self.authenticate(),
            "TraceId": trace_id,
            "ResultIndex": result_index,
            "Passengers": pax,
        }
        return await self._request("POST", settings.TBO_BOOK_PATH, json_body=body)

    async def ticket(self, trace_id: str, pnr: str, booking_id: Any) -> Dict[str, Any]:
        body = {
            "EndUserIp": self.end_user_ip,
            "TokenId": await self.authenticate(),
            "TraceId": trace_id,
            "PNR": pnr,
            "BookingId": booking_id,
        }
        return await self._request("POST", settings.TBO_TICKET_PATH, json_body=body)

    async def cancel(self, pnr: str, booking_id: Optional[str] = None) -> Dict[str, Any]:
        body = {
            "EndUserIp": self.end_user_ip,
            "TokenId": await self.authenticate(),
            "PNR": pnr,
        }
        if booking_id:
            body["BookingId"] = booking_id
        return await self._request("POST", settings.TBO_CANCEL_PATH, json_body=body)

    async def booking_details(self, pnr: str, booking_id: Optional[str] = None) -> Dict[str, Any]:
        body = {
            "EndUserIp": self.end_user_ip,
            "TokenId": await self.authenticate(),
            "PNR": pnr,
        }
        if booking_id:
            body["BookingId"] = booking_id
        return await self._request(
            "POST", settings.TBO_BOOKING_DETAILS_PATH, json_body=body
        )
