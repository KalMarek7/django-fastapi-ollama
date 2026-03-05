import json
import logging
import os
import random
from datetime import date, datetime
from pathlib import Path
from time import sleep
from typing import Optional

import httpx
from bs4 import BeautifulSoup, Tag
from google import genai
from google.api_core import exceptions
from google.genai import types
from pydantic import BaseModel, Field, HttpUrl

logger = logging.getLogger(__name__)


class JobListingSchema(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    text_content: Optional[str] = None
    portal_id: Optional[int] = None
    expiry_date: Optional[date] = None
    url: Optional[HttpUrl] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    score: Optional[float] = None

    class Config:
        from_attributes = True


class BaseScraper:
    def __init__(self, url: str, portal: str):
        self.url = url
        self.portal = portal

        base_path = Path(__file__).resolve().parent
        json_path = base_path / "user_agents.json"

        try:
            with open(json_path, "r") as f:
                self.user_agents = json.load(f)
        except FileNotFoundError:
            logger.warning(
                "user_agents.json not found at %s. Using fallback.", json_path
            )
            self.user_agents = {"user_agents": [{"string": "Mozilla/5.0"}]}  # Fallback

    def get_data(
        self,
        url: str | None = None,
        as_json: bool = False,
        post: bool = False,
        raw: bool = False,
    ):
        if url is None:
            url = self.url
        headers = {
            "User-Agent": self._get_random_ua(),
            "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8",
        }

        # We use httpx.Client() for synchronous requests inside background tasks
        with httpx.Client(follow_redirects=True, timeout=10.0) as client:
            logger.debug("Making request to %s", url)
            if post:
                content = '{"criteria":"","url":{"searchParam":"Python"},"rawSearch":"Python","pageSize":20,"withSalaryMatch":true}'
                response = client.post(url, headers=headers, content=content)
            else:
                response = client.get(url, headers=headers)
            # Ensures we handle 4xx/5xx errors
            response.raise_for_status()
            logger.debug("Request headers: %s", response.request.headers)
            if as_json:
                return response.json()
            if raw:
                sleep(2)
                if self.portal == "Pracuj.pl":
                    soup = BeautifulSoup(response.content, "html.parser")
                    return self._clean_html_content(soup, self.portal)
                elif self.portal == "JustJoinIT":
                    soup = BeautifulSoup(response.json()["body"], "html.parser")
                    return self._clean_html_content(soup, self.portal)
                elif self.portal == "theprotocol.it":
                    soup = BeautifulSoup(response.content, "html.parser")
                    return self._clean_html_content(soup, self.portal)

            return BeautifulSoup(response.content, "html.parser")

    def get_all_listings(self):
        raise NotImplementedError("Subclasses must implement get_all_listings()")

    def insert_data(self):
        raise NotImplementedError("Subclasses must implement insert_data()")

    def _get_random_ua(self) -> str:
        result = random.choice(self.user_agents["user_agents"])["string"]
        return result

    def _clean_html_content(self, soup_target: BeautifulSoup, portal_name: str) -> str:
        container_mapping = {
            "Pracuj.pl": {"tag": "div", "id": "offer-details"},
            "theprotocol.it": {"tag": "section", "id": "section-offerView"},
        }

        junk_tags = ["svg", "script", "style", "button", "img"]
        if portal_name == "theprotocol.it":
            junk_tags.append("a")

        target = soup_target
        if portal_name in container_mapping:
            mapping = container_mapping[portal_name]
            container = soup_target.find(mapping["tag"], id=mapping["id"])
            if container:
                target = container

        for junk in target.find_all(junk_tags):
            junk.decompose()

        return target.getText("\n")


class PracujplScraper(BaseScraper):
    def get_all_listings(self) -> list[str]:
        all_offers = []
        # 1. Initial request to get the first page and the page count
        first_soup = self.get_data(url=self.url)
        if not first_soup:
            return []

        if isinstance(first_soup, BeautifulSoup):
            pagination_wrapper: Optional[Tag] = first_soup.find(
                "div", {"class": "listing_n1mxvncp"}
            )
            if pagination_wrapper:
                # Logic: Find all buttons/links and get the highest number
                page_links = pagination_wrapper.find_all(["a", "button"])
                # Filter for digits only to avoid "Next" arrows
                page_numbers = [int(s.text) for s in page_links if s.text.isdigit()]
                total_pages = max(page_numbers) if page_numbers else 1
            else:
                total_pages = 1

            logger.debug("Found %s pages.", total_pages)

            # 3. Process the first page we already fetched
            first_page_offers = first_soup.find_all(
                "div", attrs={"data-test": "default-offer"}
            )
            all_offers.extend(first_page_offers)

            # 4. Loop for remaining pages
            for i in range(2, total_pages + 1):
                sleep(3)
                # URL construction: PN is the standard query param for Pracuj.pl
                page_url = f"{self.url}&pn={i}"

                logger.debug("Fetching page %s of %s", i, total_pages)
                soup = self.get_data(url=page_url)

                if isinstance(soup, BeautifulSoup):
                    div_cnt = soup.find_all("div", attrs={"data-test": "default-offer"})
                    all_offers.extend(div_cnt)

            all_offers_urls = [offer.find("a").get("href") for offer in all_offers]
            logger.debug("Total offers collected: %s", len(all_offers_urls))
            # print(all_offers_urls)

            return all_offers_urls
        else:
            return []


class TheProtocolITScraper(BaseScraper):
    def _extract_next_data(self, url: str) -> Optional[dict]:
        """Helper to fetch a URL and extract the __NEXT_DATA__ dictionary."""
        soup = self.get_data(url=url)
        if isinstance(soup, BeautifulSoup):
            script_tag = soup.find("script", id="__NEXT_DATA__")

            if not script_tag or not script_tag.string:
                return None

            return json.loads(script_tag.string)

    def get_all_listings(self) -> list[str]:
        all_offers = []

        # 1. Get the first page to determine total pages
        first_page_data = self._extract_next_data(self.url)
        if not first_page_data:
            return []

        try:
            resp = first_page_data["props"]["pageProps"]["offersResponse"]
            total_pages = resp["page"]["count"]
            # Add the offers we already have from page 1
            all_offers.extend(resp["offers"])
        except KeyError:
            return []

        logger.debug("Found %s pages. Starting pagination...", total_pages)

        # 2. Loop through remaining pages (starting from page 2)
        for page_num in range(2, total_pages + 1):
            sleep(3)

            # Use a cleaner way to handle the URL
            separator = "&" if "?" in self.url else "?"
            page_url = f"{self.url}{separator}pageNumber={page_num}"

            logger.debug("Fetching page %s of %s", page_num, total_pages)

            page_data = self._extract_next_data(page_url)
            if page_data:
                try:
                    offers = page_data["props"]["pageProps"]["offersResponse"]["offers"]
                    all_offers.extend(offers)
                except KeyError:
                    continue
        all_offers_urls = [
            f"{self.url}/praca/{offer['offerUrlName']}" for offer in all_offers
        ]
        logger.debug("Found %s offers.", len(all_offers_urls))
        return all_offers_urls


class JustJoinITScraper(BaseScraper):
    def get_all_listings(self) -> list[str]:
        all_offer_urls = []
        page_size = 100
        current_offset = 0
        total_items = 1  # Temporary starter value

        logger.debug("Starting JustJoinIT API scan...")

        while current_offset < total_items:
            # Construct the URL with dynamic offset
            url = (
                f"https://justjoin.it/api/candidate-api/offers?"
                f"from={current_offset}&itemsCount={page_size}&"
                f"categories=python&currency=pln&orderBy=descending&sortBy=publishedAt"
            )

            data = self.get_data(url=url, as_json=True)

            if not isinstance(data, dict) or "data" not in data:
                break

            # Update total_items from the first response's meta
            if current_offset == 0:
                total_items = data.get("meta", {}).get("totalItems", 0)
                logger.debug("Found %s items total.", total_items)

            # Extract slugs and build URLs
            batch = [
                f"https://justjoin.it/api/candidate-api/offers/{offer['slug']}"
                for offer in data["data"]
            ]
            all_offer_urls.extend(batch)

            logger.debug("Processed %s/%s URLs...", len(all_offer_urls), total_items)

            # Increment offset for next page
            current_offset += page_size

            if current_offset < total_items:
                sleep(1.5)

        return all_offer_urls


class NoFluffJobsScraper(BaseScraper):
    def get_all_listings(self) -> list[str]:
        """data = self.get_data(
            url=self.url,
            as_json=True,
            post=True,
        )
        print(len(data["postings"]))
        print(data["totalCount"])
        print(data["totalPages"])"""
        return []


def get_listings_details(job_listing: JobListingSchema, system_instruction: str):
    """
    Processes a receipt image using the Gemini API and returns a list of items.

    Args:
        image_bytes: The bytes of the receipt image.

    Returns:
        A list of dictionaries, each representing an item from the receipt.

    Raises:
        ValueError: If the API key is not configured.
        RuntimeError: If there is an error calling the Gemini API.
    """
    logger.debug("Starting get_listings_details() to gemma model")
    sleep(1)
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Google API key is missing.")

    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model="gemma-3-27b-it",
            contents=[
                types.Part.from_text(text=system_instruction),
                types.Part.from_text(text=job_listing.text_content),  # type: ignore
            ],
        )
        if response.text:
            logger.info("LLM raw response: %s", response.text)
            clean_json = (
                response.text.replace("```json", "")
                .replace("```", "")
                .replace("None", "null")
                .replace("\n", "")
                .strip()
            )
            data = json.loads(clean_json)
            logger.info("LLM clean data: %s", data)

            # This returns the validated Pydantic object
            return JobListingSchema(**data)
        return ""
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as e:
        raise RuntimeError(f"Error calling Gemini API: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error decoding JSON response from Gemini API: {e}") from e
