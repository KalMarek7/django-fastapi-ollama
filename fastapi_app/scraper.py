import json
import random
from pathlib import Path

import httpx
from bs4 import BeautifulSoup


class BaseScraper:
    def __init__(self, url: str):
        self.url = url
        self.soup = None
        self.data = []

        base_path = Path(__file__).resolve().parent
        json_path = base_path / "user_agents.json"

        try:
            with open(json_path, "r") as f:
                self.user_agents = json.load(f)
        except FileNotFoundError:
            print(f"Did not find user_agents.json file at {json_path}.")
            self.user_agents = {"user_agents": [{"string": "Mozilla/5.0"}]}  # Fallback

    def get_soup(self) -> BeautifulSoup:
        headers = {
            "User-Agent": self._get_random_ua(),
            "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8",
        }

        # We use httpx.Client() for synchronous requests inside background tasks
        with httpx.Client(timeout=10.0) as client:
            response = client.get(self.url, headers=headers)

            # Ensures we handle 4xx/5xx errors
            response.raise_for_status()

            # Logging headers (similar to your requests print)
            print(f"DEBUG Headers: {response.request.headers}")

            # Note: response.content returns bytes, which BeautifulSoup handles well
            self.soup = BeautifulSoup(response.content, "html.parser")

        return self.soup

    def get_data(self):
        raise NotImplementedError("Subclasses must implement get_data()")

    def insert_data(self):
        raise NotImplementedError("Subclasses must implement insert_data()")

    def _get_random_ua(self) -> str:
        result = random.choice(self.user_agents["user_agents"])["string"]
        return result


""" class CurrencyScraper(BaseScraper):
    def get_data(self) -> list[dict]:
        soup = self.get_soup()
        rows = []
        tbody = soup.find("tbody")
        if tbody:
            for tr in tbody.find_all("tr", limit=10):
                tds = tr.find_all("td")
                data = {
                    "country": tds[0].get_text(strip=True).replace(",", "."),
                    "exchange_rate": tds[1].get_text(strip=True).replace(",", "."),
                    "symbol": tds[3].get_text(strip=True).replace(",", "."),
                    "currency": tds[4].get_text(strip=True).replace(",", "."),
                }
                rows.append(data)
        print(rows)
        if rows == []:
            print(
                "Do not have the data, something went wrong with scraping in self.get_data() (oop_web_scraper.py)"
            )
        self.data = rows
        return rows

    def insert_data(self) -> dict | None:
        self.get_data()  # Automatically fetch data if we haven't yet
        if self.data == []:
            return None
        try:
            data = self.data
            for row in data:
                ScrapedCurrency.objects.update_or_create(
                    symbol=row["symbol"],
                    defaults={
                        "country": row["country"],
                        "exchange_rate": row["exchange_rate"],
                        "currency": row["currency"],
                    },
                )
            LastRefreshDate.objects.update_or_create(
                id=1, defaults={"date": datetime.now()}
            )
            print("Success I guess")
            return {
                "currencies": ScrapedCurrency.objects.all(),
                "refresh_date": LastRefreshDate.objects.first(),
            }
        except Exception as e:
            print("Error: ", e) """


class JobScraper(BaseScraper):
    def get_data(self) -> list:
        soup = self.get_soup()
        rows = []
        # custom data-test attribute search
        div_cnt = soup.find("div", attrs={"data-test": "default-offer"})
        pages = soup.find("div", class_="listing_n1mxvncp")
        children = len(pages.find_all(recursive=False))
        print(children)
        for i in div_cnt.find_all("div"):
            rows.append(i)
        print(len(rows))
        return rows
