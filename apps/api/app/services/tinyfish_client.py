import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
import json


class TinyFishClient:
    def __init__(self):
        self.api_key = settings.TINYFISH_API_KEY
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        self.agent_base = settings.TINYFISH_BASE_URL
        self.search_base = settings.TINYFISH_SEARCH_URL
        self.fetch_base = settings.TINYFISH_FETCH_URL
        self.browser_base = settings.TINYFISH_BROWSER_URL

    async def search(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """Use TinyFish Search API"""
        url = f"{self.search_base}/search"
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.get(url, headers=self.headers, params={"q": query, "num": num_results})
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                return {"error": str(e), "results": []}

    async def fetch(self, url: str) -> Dict[str, Any]:
        """Use TinyFish Fetch API"""
        endpoint = self.fetch_base
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(endpoint, headers=self.headers, json={"url": url})
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                return {"error": str(e), "content": ""}

    async def run_agent(self, goal: str, url: Optional[str] = None, browser_profile: str = "lite") -> Dict[str, Any]:
        """Use TinyFish Agent API"""
        endpoint = f"{self.agent_base}/v1/automation/run"
        payload = {
            "goal": goal,
            "browser_profile": browser_profile,
        }
        if url:
            payload["url"] = url
        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                resp = await client.post(endpoint, headers=self.headers, json=payload)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                return {"error": str(e)}

    async def run_agent_async(self, goal: str, url: Optional[str] = None) -> Dict[str, Any]:
        endpoint = f"{self.agent_base}/v1/automation/run-async"
        payload = {"goal": goal}
        if url:
            payload["url"] = url
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(endpoint, headers=self.headers, json=payload)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                return {"error": str(e)}


tinyfish_client = TinyFishClient()
