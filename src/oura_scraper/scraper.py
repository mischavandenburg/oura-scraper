"""Main scraper orchestration for all Oura API endpoints."""

import logging
from typing import Any

import psycopg

from oura_scraper.api_client import OuraAPIClient, get_date_range
from oura_scraper.auth import DatabaseTokenStorage, OuraAuth
from oura_scraper.config import get_settings
from oura_scraper.db import operations as ops

logger = logging.getLogger(__name__)


class OuraScraper:
    """Orchestrates scraping all Oura API endpoints and storing in database."""

    def __init__(self, days: int = 7) -> None:
        """Initialize scraper.

        Args:
            days: Number of days to scrape (default 7)
        """
        self.days = days
        self.start_date, self.end_date = get_date_range(days)
        self.settings = get_settings()

        # Use database token storage for stateless container deployments
        token_storage = DatabaseTokenStorage(self.settings.database_url)
        self.auth = OuraAuth(token_storage=token_storage)
        self.client = OuraAPIClient(self.auth)
        self.stats: dict[str, Any] = {}

    def scrape_all(self) -> dict[str, Any]:
        """Scrape all endpoints and store in database.

        Returns:
            Dictionary with statistics about what was scraped
        """
        logger.info(
            "Starting scrape for %d days: %s to %s",
            self.days, self.start_date, self.end_date
        )

        with psycopg.connect(self.settings.database_url) as conn:
            # Personal info (no date range)
            self._scrape_personal_info(conn)

            # Daily endpoints (with date range)
            self._scrape_daily_activity(conn)
            self._scrape_daily_sleep(conn)
            self._scrape_daily_readiness(conn)
            self._scrape_daily_stress(conn)
            self._scrape_daily_spo2(conn)

            # Sleep endpoints
            self._scrape_sleep(conn)
            self._scrape_sleep_time(conn)

            # Heart rate (high volume)
            self._scrape_heartrate(conn)

            # Activity endpoints
            self._scrape_workout(conn)
            self._scrape_session(conn)

            # Tags and rest mode
            self._scrape_enhanced_tag(conn)
            self._scrape_rest_mode_period(conn)

        logger.info("Scrape completed successfully")
        return self.stats

    def _scrape_personal_info(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape personal info endpoint."""
        try:
            logger.info("Scraping personal_info...")
            data = self.client.get_personal_info()
            ops.upsert_personal_info(conn, data)
            self.stats["personal_info"] = {"success": True, "records": 1}
        except Exception as e:
            logger.error("Failed to scrape personal_info: %s", e)
            self.stats["personal_info"] = {"success": False, "error": str(e)}

    def _scrape_daily_activity(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape daily activity endpoint."""
        try:
            logger.info("Scraping daily_activity...")
            data = self.client.get_daily_activity(self.start_date, self.end_date)
            count = ops.upsert_daily_activity(conn, data.get("data", []))
            self.stats["daily_activity"] = {"success": True, "records": count}
        except Exception as e:
            logger.error("Failed to scrape daily_activity: %s", e)
            self.stats["daily_activity"] = {"success": False, "error": str(e)}

    def _scrape_daily_sleep(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape daily sleep endpoint."""
        try:
            logger.info("Scraping daily_sleep...")
            data = self.client.get_daily_sleep(self.start_date, self.end_date)
            count = ops.upsert_daily_sleep(conn, data.get("data", []))
            self.stats["daily_sleep"] = {"success": True, "records": count}
        except Exception as e:
            logger.error("Failed to scrape daily_sleep: %s", e)
            self.stats["daily_sleep"] = {"success": False, "error": str(e)}

    def _scrape_daily_readiness(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape daily readiness endpoint."""
        try:
            logger.info("Scraping daily_readiness...")
            data = self.client.get_daily_readiness(self.start_date, self.end_date)
            count = ops.upsert_daily_readiness(conn, data.get("data", []))
            self.stats["daily_readiness"] = {"success": True, "records": count}
        except Exception as e:
            logger.error("Failed to scrape daily_readiness: %s", e)
            self.stats["daily_readiness"] = {"success": False, "error": str(e)}

    def _scrape_daily_stress(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape daily stress endpoint."""
        try:
            logger.info("Scraping daily_stress...")
            data = self.client.get_daily_stress(self.start_date, self.end_date)
            count = ops.upsert_daily_stress(conn, data.get("data", []))
            self.stats["daily_stress"] = {"success": True, "records": count}
        except Exception as e:
            logger.error("Failed to scrape daily_stress: %s", e)
            self.stats["daily_stress"] = {"success": False, "error": str(e)}

    def _scrape_daily_spo2(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape daily SpO2 endpoint."""
        try:
            logger.info("Scraping daily_spo2...")
            data = self.client.get_daily_spo2(self.start_date, self.end_date)
            count = ops.upsert_daily_spo2(conn, data.get("data", []))
            self.stats["daily_spo2"] = {"success": True, "records": count}
        except Exception as e:
            logger.error("Failed to scrape daily_spo2: %s", e)
            self.stats["daily_spo2"] = {"success": False, "error": str(e)}

    def _scrape_sleep(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape sleep (detailed) endpoint."""
        try:
            logger.info("Scraping sleep...")
            data = self.client.get_sleep(self.start_date, self.end_date)
            count = ops.upsert_sleep_data(conn, data.get("data", []))
            self.stats["sleep"] = {"success": True, "records": count}
        except Exception as e:
            logger.error("Failed to scrape sleep: %s", e)
            self.stats["sleep"] = {"success": False, "error": str(e)}

    def _scrape_sleep_time(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape sleep time endpoint."""
        try:
            logger.info("Scraping sleep_time...")
            data = self.client.get_sleep_time(self.start_date, self.end_date)
            count = ops.upsert_sleep_time(conn, data.get("data", []))
            self.stats["sleep_time"] = {"success": True, "records": count}
        except Exception as e:
            logger.error("Failed to scrape sleep_time: %s", e)
            self.stats["sleep_time"] = {"success": False, "error": str(e)}

    def _scrape_heartrate(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape heart rate endpoint."""
        try:
            logger.info("Scraping heartrate...")
            data = self.client.get_heartrate(self.start_date, self.end_date)
            count = ops.upsert_heart_rate(conn, data.get("data", []))
            self.stats["heartrate"] = {"success": True, "records": count}
        except Exception as e:
            logger.error("Failed to scrape heartrate: %s", e)
            self.stats["heartrate"] = {"success": False, "error": str(e)}

    def _scrape_workout(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape workout endpoint."""
        try:
            logger.info("Scraping workout...")
            data = self.client.get_workout(self.start_date, self.end_date)
            count = ops.upsert_workout(conn, data.get("data", []))
            self.stats["workout"] = {"success": True, "records": count}
        except Exception as e:
            logger.error("Failed to scrape workout: %s", e)
            self.stats["workout"] = {"success": False, "error": str(e)}

    def _scrape_session(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape session endpoint."""
        try:
            logger.info("Scraping session...")
            data = self.client.get_session(self.start_date, self.end_date)
            count = ops.upsert_session(conn, data.get("data", []))
            self.stats["session"] = {"success": True, "records": count}
        except Exception as e:
            logger.error("Failed to scrape session: %s", e)
            self.stats["session"] = {"success": False, "error": str(e)}

    def _scrape_enhanced_tag(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape enhanced tag endpoint."""
        try:
            logger.info("Scraping enhanced_tag...")
            data = self.client.get_enhanced_tag(self.start_date, self.end_date)
            count = ops.upsert_enhanced_tag(conn, data.get("data", []))
            self.stats["enhanced_tag"] = {"success": True, "records": count}
        except Exception as e:
            logger.error("Failed to scrape enhanced_tag: %s", e)
            self.stats["enhanced_tag"] = {"success": False, "error": str(e)}

    def _scrape_rest_mode_period(self, conn: psycopg.Connection[tuple[object, ...]]) -> None:
        """Scrape rest mode period endpoint."""
        try:
            logger.info("Scraping rest_mode_period...")
            data = self.client.get_rest_mode_period(self.start_date, self.end_date)
            count = ops.upsert_rest_mode_period(conn, data.get("data", []))
            self.stats["rest_mode_period"] = {"success": True, "records": count}
        except Exception as e:
            logger.error("Failed to scrape rest_mode_period: %s", e)
            self.stats["rest_mode_period"] = {"success": False, "error": str(e)}
