import logging
import os

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

DRF = os.getenv("DRF", "")
if not DRF or DRF == "":
    logger.info("Missing DRF auth credentials")
    logger.error("Missing DRF auth credentials")
    raise EnvironmentError("Missing DRF auth credentials")


class DRFClient:
    """
    Httpx sync wrapper to interact with DRF API for DB operations.
    """

    def __init__(self):
        auth = httpx.BasicAuth(f"{DRF.split(':')[0]}", f"{DRF.split(':')[1]}")  # type: ignore
        self.HTTPClient = httpx.Client(
            auth=auth, headers=httpx.Headers({"accept": "application/json"})
        )

    def get(self, resource: str, filter: str = ""):
        logger.info(
            f"http://django:8000/api/{resource}/{f'?{filter}' if filter else ''}"
        )
        response = self.HTTPClient.get(
            url=f"http://django:8000/api/{resource}/{f'?{filter}' if filter else ''}"
        )
        logger.debug("DEBUG: HEADERS: ", response.headers)
        try:
            response.raise_for_status()
            # print(response.json())
            return response.json()["results"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                raise HTTPException(
                    status_code=503, detail="DRF auth invalid or credentials missing"
                )
            else:
                raise HTTPException(
                    status_code=e.response.status_code, detail=e.response.text
                )

    def post(self, resource: str, payload: dict):
        response = self.HTTPClient.post(
            url=f"http://django:8000/api/{resource}/",
            json=payload,
        )
        logger.debug("DEBUG: HEADERS: ", response.headers)
        logger.info(response.text)
        try:
            response.raise_for_status()

            logger.debug("DEBUG: POST RESPONSE: ", response.json())
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                raise HTTPException(
                    status_code=503, detail="DRF auth invalid or credentials missing"
                )
            else:
                raise HTTPException(
                    status_code=e.response.status_code, detail=e.response.text
                )

    def close(self):
        logger.debug("Closing httpx client")
        self.HTTPClient.close()


class AsyncDRFClient:
    """
    Httpx async wrapper to interact with DRF API for DB operations.
    """

    def __init__(self):
        user, password = DRF.split(":")
        self.auth = httpx.BasicAuth(user, password)
        self.headers = {"accept": "application/json"}
        self.client = httpx.AsyncClient(auth=self.auth, headers=self.headers)

    async def get(self, resource: str, filter: str = ""):
        url = f"http://django:8000/api/{resource}/{f'?{filter}' if filter else ''}"
        response = await self.client.get(url)
        try:
            response.raise_for_status()
            data = response.json()
            return data.get("results", data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                raise HTTPException(
                    status_code=503, detail="DRF auth invalid or credentials missing"
                )
            else:
                raise HTTPException(
                    status_code=e.response.status_code, detail=e.response.text
                )

    async def post(self, resource: str, payload: dict):
        url = f"http://django:8000/api/{resource}/"
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                raise HTTPException(
                    status_code=503, detail="DRF auth invalid or credentials missing"
                )
            else:
                raise HTTPException(
                    status_code=e.response.status_code, detail=e.response.text
                )

    async def close(self):
        await self.client.aclose()
