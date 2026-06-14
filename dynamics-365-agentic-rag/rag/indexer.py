from __future__ import annotations

import asyncio
import logging

from d365.client import D365Client
from rag.vector_store import vector_store

logger = logging.getLogger(__name__)


def _opp_to_doc(opp: dict) -> tuple[str, str, dict]:
    doc_id = opp.get("opportunityid", "")
    account = opp.get("parentaccountid") or {}
    owner = opp.get("ownerid") or {}
    text = (
        f"Opportunity: {opp.get('name', '')} | "
        f"Account: {account.get('name', 'Unknown')} | "
        f"Value: {opp.get('estimatedvalue', 0)} | "
        f"Probability: {opp.get('closeprobability', 0)}% | "
        f"State: {opp.get('statecode', '')} | "
        f"Close Date: {opp.get('actualclosedate', '')} | "
        f"Created: {opp.get('createdon', '')} | "
        f"Owner: {owner.get('fullname', 'Unknown')}"
    )
    meta = {
        "opportunity_id": doc_id,
        "account_id": account.get("accountid", ""),
        "account_name": account.get("name", ""),
        "value": float(opp.get("estimatedvalue") or 0),
        "probability": int(opp.get("closeprobability") or 0),
        "state": int(opp.get("statecode") or 0),
        "owner": owner.get("fullname", ""),
        "close_date": opp.get("actualclosedate", ""),
        "created": opp.get("createdon", ""),
    }
    return doc_id, text, meta


def _account_to_doc(acc: dict) -> tuple[str, str, dict]:
    doc_id = acc.get("accountid", "")
    text = (
        f"Account: {acc.get('name', '')} | "
        f"Revenue: {acc.get('revenue', 0)} | "
        f"Employees: {acc.get('numberofemployees', 0)} | "
        f"Industry: {acc.get('industrycode', '')} | "
        f"State: {acc.get('statecode', '')} | "
        f"Created: {acc.get('createdon', '')}"
    )
    meta = {
        "account_id": doc_id,
        "name": acc.get("name", ""),
        "revenue": float(acc.get("revenue") or 0),
        "employees": int(acc.get("numberofemployees") or 0),
        "industry": str(acc.get("industrycode") or ""),
        "state": int(acc.get("statecode") or 0),
    }
    return doc_id, text, meta


async def index_all() -> None:
    client = D365Client()
    logger.info("Indexing opportunities...")
    opps = await client.get_opportunities(top=2000)
    won = await client.get_won_opportunities(top=2000)
    lost = await client.get_lost_opportunities(top=2000)

    all_opps = {o["opportunityid"]: o for o in opps + won + lost}
    ids, docs, metas = [], [], []
    for opp in all_opps.values():
        oid, text, meta = _opp_to_doc(opp)
        ids.append(oid)
        docs.append(text)
        metas.append(meta)
    if ids:
        vector_store.upsert("opportunities", ids, docs, metas)
    logger.info("Indexed %d opportunities.", len(ids))

    logger.info("Indexing accounts...")
    accounts = await client.get_accounts(top=2000)
    ids, docs, metas = [], [], []
    for acc in accounts:
        aid, text, meta = _account_to_doc(acc)
        ids.append(aid)
        docs.append(text)
        metas.append(meta)
    if ids:
        vector_store.upsert("accounts", ids, docs, metas)
    logger.info("Indexed %d accounts.", len(ids))


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(index_all())
    logger.info("RAG index complete.")


if __name__ == "__main__":
    main()
