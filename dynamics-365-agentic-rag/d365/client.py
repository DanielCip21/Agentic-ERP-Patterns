from __future__ import annotations

import time
from typing import Any

import httpx
import msal

from config.settings import settings


class D365Client:
    """Async client for Microsoft Dynamics 365 Web API (OData v4)."""

    _token: str | None = None
    _token_expiry: float = 0.0

    def __init__(self) -> None:
        self._authority = f"https://login.microsoftonline.com/{settings.d365_tenant_id}"
        self._scope = [f"{settings.d365_base_url}/.default"]
        self._app = msal.ConfidentialClientApplication(
            settings.d365_client_id,
            authority=self._authority,
            client_credential=settings.d365_client_secret,
        )

    async def _get_token(self) -> str:
        if self._token and time.time() < self._token_expiry - 60:
            return self._token
        result = self._app.acquire_token_for_client(scopes=self._scope)
        if "access_token" not in result:
            raise RuntimeError(f"MSAL token error: {result.get('error_description')}")
        self._token = result["access_token"]
        self._token_expiry = time.time() + result.get("expires_in", 3600)
        return self._token

    async def _request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        token = await self._get_token()
        url = f"{settings.d365_base_url}/api/data/v9.2/{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json",
            "Prefer": "odata.include-annotations=*",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=headers, params=params or {})
            resp.raise_for_status()
            return resp.json()

    async def get_opportunities(self, top: int = 200) -> list[dict]:
        data = await self._request(
            "opportunities",
            {
                "$select": "opportunityid,name,estimatedvalue,actualclosedate,statecode,statuscode,closeprobability,createdon,modifiedon",
                "$expand": "parentaccountid($select=name,accountid),ownerid($select=fullname)",
                "$top": top,
                "$orderby": "modifiedon desc",
            },
        )
        return data.get("value", [])

    async def get_opportunity(self, opportunity_id: str) -> dict:
        return await self._request(
            f"opportunities({opportunity_id})",
            {
                "$select": "*",
                "$expand": "parentaccountid,ownerid,parentcontactid",
            },
        )

    async def get_accounts(self, top: int = 500) -> list[dict]:
        data = await self._request(
            "accounts",
            {
                "$select": "accountid,name,revenue,numberofemployees,industrycode,statecode,createdon,modifiedon,telephone1,emailaddress1",
                "$top": top,
                "$orderby": "modifiedon desc",
            },
        )
        return data.get("value", [])

    async def get_account(self, account_id: str) -> dict:
        return await self._request(
            f"accounts({account_id})",
            {"$select": "*", "$expand": "primarycontactid"},
        )

    async def get_account_activities(self, account_id: str, top: int = 50) -> list[dict]:
        data = await self._request(
            "activitypointers",
            {
                "$select": "activityid,activitytypecode,subject,createdon,modifiedon,statecode",
                "$filter": f"_regardingobjectid_value eq {account_id}",
                "$top": top,
                "$orderby": "createdon desc",
            },
        )
        return data.get("value", [])

    async def get_account_cases(self, account_id: str, top: int = 50) -> list[dict]:
        data = await self._request(
            "incidents",
            {
                "$select": "incidentid,title,statecode,prioritycode,createdon,modifiedon,resolvedon",
                "$filter": f"_customerid_value eq {account_id}",
                "$top": top,
                "$orderby": "createdon desc",
            },
        )
        return data.get("value", [])

    async def get_account_orders(self, account_id: str) -> list[dict]:
        data = await self._request(
            "salesorders",
            {
                "$select": "salesorderid,name,totalamount,statecode,createdon,submitdate",
                "$filter": f"_customerid_value eq {account_id}",
                "$orderby": "createdon desc",
            },
        )
        return data.get("value", [])

    async def get_contacts(self, account_id: str) -> list[dict]:
        data = await self._request(
            "contacts",
            {
                "$select": "contactid,fullname,jobtitle,emailaddress1,telephone1,createdon",
                "$filter": f"_parentcustomerid_value eq {account_id}",
            },
        )
        return data.get("value", [])

    async def get_won_opportunities(self, top: int = 500) -> list[dict]:
        data = await self._request(
            "opportunities",
            {
                "$select": "opportunityid,name,estimatedvalue,actualvalue,actualclosedate,closeprobability,createdon",
                "$filter": "statecode eq 1",
                "$top": top,
                "$orderby": "actualclosedate desc",
            },
        )
        return data.get("value", [])

    async def get_lost_opportunities(self, top: int = 500) -> list[dict]:
        data = await self._request(
            "opportunities",
            {
                "$select": "opportunityid,name,estimatedvalue,actualclosedate,closeprobability,createdon",
                "$filter": "statecode eq 2",
                "$top": top,
                "$orderby": "actualclosedate desc",
            },
        )
        return data.get("value", [])

    async def get_user_activities(self, user_id: str, top: int = 200) -> list[dict]:
        data = await self._request(
            "activitypointers",
            {
                "$select": "activityid,activitytypecode,subject,createdon,statecode",
                "$filter": f"_ownerid_value eq {user_id}",
                "$top": top,
                "$orderby": "createdon desc",
            },
        )
        return data.get("value", [])

    async def get_emails(self, regarding_id: str, top: int = 50) -> list[dict]:
        data = await self._request(
            "emails",
            {
                "$select": "activityid,subject,description,createdon,directioncode,statecode",
                "$filter": f"_regardingobjectid_value eq {regarding_id}",
                "$top": top,
                "$orderby": "createdon desc",
            },
        )
        return data.get("value", [])

    async def get_notes(self, regarding_id: str, top: int = 50) -> list[dict]:
        data = await self._request(
            "annotations",
            {
                "$select": "annotationid,subject,notetext,createdon,modifiedon",
                "$filter": f"_objectid_value eq {regarding_id}",
                "$top": top,
                "$orderby": "createdon desc",
            },
        )
        return data.get("value", [])

    async def get_phone_calls(self, regarding_id: str, top: int = 50) -> list[dict]:
        data = await self._request(
            "phonecalls",
            {
                "$select": "activityid,subject,description,createdon,directioncode,statecode",
                "$filter": f"_regardingobjectid_value eq {regarding_id}",
                "$top": top,
                "$orderby": "createdon desc",
            },
        )
        return data.get("value", [])
