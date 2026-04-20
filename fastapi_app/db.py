import logging
import os

import httpx

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
        response.raise_for_status()
        # print(response.json())
        return response.json()["results"]

    def post(self, resource: str, payload: dict):
        response = self.HTTPClient.post(
            url=f"http://django:8000/api/{resource}/",
            json=payload,
        )
        logger.debug("DEBUG: HEADERS: ", response.headers)
        logger.info(response.text)
        response.raise_for_status()

        logger.debug("DEBUG: POST RESPONSE: ", response.json())
        return response.json()

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
        response.raise_for_status()
        data = response.json()
        return data.get("results", data)

    async def post(self, resource: str, payload: dict):
        url = f"http://django:8000/api/{resource}/"
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()


if __name__ == "__main__":
    client = DRFClient()
    # 273
    """ 
    client.post(
        "tasks",
        {
            "task_id": "11111114-a605-42dc-83c5-053dafa5037c",
            "status": "pending",
        },
    ) 
    """
    # 168
    print(
        "AAAAAAA", client.get("tasks", "task_id=ea65ff0b-a605-42dc-83c5-053dafa5037c")
    )
    # 191
    print(client.get("portals", "name=Pracuj.pl"))
    # 194 & 208
    client.post(
        "job_listings",
        {
            "url": "https://theprotocol.it/filtry/python;t/backend;sp/praca/programista-c-z-elementami-java-m-k-os-wroclaw-generala-romualda-traugutta-55a,oferta,cab40000-7b76-c2e5-6254-08de89b64ea3",
            "text_content": "FASTAPI",
            "portal": "JustJoinIT",
        },
    )
    # 202
    client.get("system_instructions", "id=1")
    client.post(
        "tasks",
        {
            "task_id": "ea65ff0b-2222-42dc-83c5-053dafa5037c",
            "status": "failed",
            "created_at": "2026-03-28T10:40:40.243846Z",
            "updated_at": "2026-03-28T11:51:53.839585Z",
        },
    )
