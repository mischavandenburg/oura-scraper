"""Oura API v2 client for fetching health data."""

import logging
from datetime import date, timedelta
from typing import Any

import httpx

from oura_scraper.auth import OuraAuth

logger = logging.getLogger(__name__)

BASE_URL = "https://api.ouraring.com/v2/usercollection"


def get_date_range(days: int = 7) -> tuple[str, str]:
    """Get date range for API queries.

    Args:
        days: Number of days to look back (default 7)

    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    return start_date.isoformat(), end_date.isoformat()


class OuraAPIClient:
    """Client for Oura API v2."""

    def __init__(self, auth: OuraAuth | None = None) -> None:
        """Initialize API client.

        Args:
            auth: OAuth authentication handler. Creates default if not provided.
        """
        self.auth = auth or OuraAuth()
        self.base_url = BASE_URL

    def _get_headers(self) -> dict[str, str]:
        """Get authorization headers with valid token."""
        token = self.auth.get_valid_token()
        return {"Authorization": f"Bearer {token}"}

    def get_personal_info(self) -> dict[str, Any]:
        """Fetch personal information.

        Returns:
            Personal info data from API
        """
        url = f"{self.base_url}/personal_info"
        logger.info("Fetching personal info from %s", url)

        response = httpx.get(url, headers=self._get_headers())
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched personal info")
        return data

    def get_daily_activity(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Fetch daily activity data.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Daily activity data with pagination info
        """
        url = f"{self.base_url}/daily_activity"
        params = {"start_date": start_date, "end_date": end_date}
        logger.info("Fetching daily activity from %s to %s", start_date, end_date)

        response = httpx.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched %d daily activity records", len(data.get("data", [])))
        return data

    def get_daily_sleep(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Fetch daily sleep data."""
        url = f"{self.base_url}/daily_sleep"
        params = {"start_date": start_date, "end_date": end_date}
        logger.info("Fetching daily sleep from %s to %s", start_date, end_date)

        response = httpx.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched %d daily sleep records", len(data.get("data", [])))
        return data

    def get_daily_readiness(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Fetch daily readiness data."""
        url = f"{self.base_url}/daily_readiness"
        params = {"start_date": start_date, "end_date": end_date}
        logger.info("Fetching daily readiness from %s to %s", start_date, end_date)

        response = httpx.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched %d daily readiness records", len(data.get("data", [])))
        return data

    def get_daily_stress(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Fetch daily stress data."""
        url = f"{self.base_url}/daily_stress"
        params = {"start_date": start_date, "end_date": end_date}
        logger.info("Fetching daily stress from %s to %s", start_date, end_date)

        response = httpx.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched %d daily stress records", len(data.get("data", [])))
        return data

    def get_daily_spo2(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Fetch daily SpO2 data."""
        url = f"{self.base_url}/daily_spo2"
        params = {"start_date": start_date, "end_date": end_date}
        logger.info("Fetching daily SpO2 from %s to %s", start_date, end_date)

        response = httpx.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched %d daily SpO2 records", len(data.get("data", [])))
        return data

    def get_daily_cardiovascular_age(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Fetch daily cardiovascular age data."""
        url = f"{self.base_url}/daily_cardiovascular_age"
        params = {"start_date": start_date, "end_date": end_date}
        logger.info("Fetching daily cardiovascular age from %s to %s", start_date, end_date)

        response = httpx.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched %d cardiovascular age records", len(data.get("data", [])))
        return data

    def get_daily_resilience(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Fetch daily resilience data."""
        url = f"{self.base_url}/daily_resilience"
        params = {"start_date": start_date, "end_date": end_date}
        logger.info("Fetching daily resilience from %s to %s", start_date, end_date)

        response = httpx.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched %d daily resilience records", len(data.get("data", [])))
        return data

    def get_sleep(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Fetch detailed sleep periods data."""
        url = f"{self.base_url}/sleep"
        params = {"start_date": start_date, "end_date": end_date}
        logger.info("Fetching sleep data from %s to %s", start_date, end_date)

        response = httpx.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched %d sleep records", len(data.get("data", [])))
        return data

    def get_sleep_time(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Fetch sleep time (optimal bedtime) data."""
        url = f"{self.base_url}/sleep_time"
        params = {"start_date": start_date, "end_date": end_date}
        logger.info("Fetching sleep time from %s to %s", start_date, end_date)

        response = httpx.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched %d sleep time records", len(data.get("data", [])))
        return data

    def get_heartrate(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Fetch heart rate data (5-minute intervals)."""
        url = f"{self.base_url}/heartrate"
        params = {"start_date": start_date, "end_date": end_date}
        logger.info("Fetching heart rate from %s to %s", start_date, end_date)

        response = httpx.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched %d heart rate records", len(data.get("data", [])))
        return data

    def get_vo2_max(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Fetch VO2 max data."""
        url = f"{self.base_url}/vO2_max"
        params = {"start_date": start_date, "end_date": end_date}
        logger.info("Fetching VO2 max from %s to %s", start_date, end_date)

        response = httpx.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched %d VO2 max records", len(data.get("data", [])))
        return data

    def get_workout(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Fetch workout data."""
        url = f"{self.base_url}/workout"
        params = {"start_date": start_date, "end_date": end_date}
        logger.info("Fetching workouts from %s to %s", start_date, end_date)

        response = httpx.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched %d workout records", len(data.get("data", [])))
        return data

    def get_session(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Fetch session data (meditation, breathing, naps)."""
        url = f"{self.base_url}/session"
        params = {"start_date": start_date, "end_date": end_date}
        logger.info("Fetching sessions from %s to %s", start_date, end_date)

        response = httpx.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched %d session records", len(data.get("data", [])))
        return data

    def get_enhanced_tag(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Fetch enhanced tag data."""
        url = f"{self.base_url}/enhanced_tag"
        params = {"start_date": start_date, "end_date": end_date}
        logger.info("Fetching enhanced tags from %s to %s", start_date, end_date)

        response = httpx.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched %d enhanced tag records", len(data.get("data", [])))
        return data

    def get_ring_configuration(self) -> dict[str, Any]:
        """Fetch ring configuration data."""
        url = f"{self.base_url}/ring_configuration"
        logger.info("Fetching ring configuration")

        response = httpx.get(url, headers=self._get_headers())
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched ring configuration")
        return data

    def get_rest_mode_period(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Fetch rest mode period data."""
        url = f"{self.base_url}/rest_mode_period"
        params = {"start_date": start_date, "end_date": end_date}
        logger.info("Fetching rest mode periods from %s to %s", start_date, end_date)

        response = httpx.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()

        data = response.json()
        logger.info("Successfully fetched %d rest mode period records", len(data.get("data", [])))
        return data
