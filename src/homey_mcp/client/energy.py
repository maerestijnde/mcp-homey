import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EnergyAPI:
    def __init__(self, client):
        self.client = client

    async def get_energy_state(self) -> Dict[str, Any]:
        """Get energy manager state."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            return {
                "available": True,
                "currency": "EUR",
                "electricityPriceFixed": 0.30,
                "gasPriceFixed": 1.20,
                "waterPriceFixed": 2.50
            }

        try:
            response = await self.client.session.get("/api/manager/energy/state")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting energy state: {e}")
            raise

    async def get_energy_live_report(self, zone: Optional[str] = None) -> Dict[str, Any]:
        """Get live energy report."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            import random
            return {
                "electricity": {
                    "total": round(random.uniform(500, 2000), 1),
                    "devices": [
                        {"id": "device1", "name": "Washing Machine", "value": round(random.uniform(100, 500), 1)},
                        {"id": "device2", "name": "Refrigerator", "value": round(random.uniform(50, 150), 1)},
                        {"id": "device3", "name": "TV", "value": round(random.uniform(20, 80), 1)}
                    ]
                },
                "gas": {"total": round(random.uniform(0, 20), 1)},
                "water": {"total": round(random.uniform(0, 5), 1)}
            }

        try:
            params = {"zone": zone} if zone else {}
            response = await self.client.session.get("/api/manager/energy/live", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting live energy report: {e}")
            raise

    async def get_energy_report_day(self, date: str, cache: Optional[str] = None) -> Dict[str, Any]:
        """Get daily energy report."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            import random
            return {
                "date": date,
                "electricity": {
                    "consumed": round(random.uniform(15, 35), 2),
                    "produced": round(random.uniform(0, 10), 2),
                    "cost": round(random.uniform(4, 12), 2)
                },
                "gas": {
                    "consumed": round(random.uniform(5, 25), 2),
                    "cost": round(random.uniform(6, 30), 2)
                },
                "water": {
                    "consumed": round(random.uniform(100, 300), 1),
                    "cost": round(random.uniform(0.25, 0.75), 2)
                }
            }

        try:
            params = {"date": date}
            if cache:
                params["cache"] = cache
            response = await self.client.session.get("/api/manager/energy/report/day", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting daily energy report: {e}")
            raise

    async def get_energy_report_week(self, iso_week: str, cache: Optional[str] = None) -> Dict[str, Any]:
        """Get weekly energy report."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            import random
            return {
                "week": iso_week,
                "electricity": {
                    "consumed": round(random.uniform(100, 250), 2),
                    "produced": round(random.uniform(0, 70), 2),
                    "cost": round(random.uniform(30, 80), 2)
                },
                "gas": {
                    "consumed": round(random.uniform(35, 175), 2),
                    "cost": round(random.uniform(42, 210), 2)
                },
                "water": {
                    "consumed": round(random.uniform(700, 2100), 1),
                    "cost": round(random.uniform(1.75, 5.25), 2)
                }
            }

        try:
            params = {"isoWeek": iso_week}
            if cache:
                params["cache"] = cache
            response = await self.client.session.get("/api/manager/energy/report/week", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting weekly energy report: {e}")
            raise

    async def get_energy_report_month(self, year_month: str, cache: Optional[str] = None) -> Dict[str, Any]:
        """Get monthly energy report."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            import random
            return {
                "month": year_month,
                "electricity": {
                    "consumed": round(random.uniform(400, 1000), 2),
                    "produced": round(random.uniform(0, 300), 2),
                    "cost": round(random.uniform(120, 320), 2)
                },
                "gas": {
                    "consumed": round(random.uniform(150, 750), 2),
                    "cost": round(random.uniform(180, 900), 2)
                },
                "water": {
                    "consumed": round(random.uniform(3000, 9000), 1),
                    "cost": round(random.uniform(7.5, 22.5), 2)
                }
            }

        try:
            params = {"yearMonth": year_month}
            if cache:
                params["cache"] = cache
            response = await self.client.session.get("/api/manager/energy/report/month", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting monthly energy report: {e}")
            raise

    async def get_energy_reports_available(self) -> Dict[str, Any]:
        """Get available energy reports."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            today = datetime.now()
            return {
                "days": [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)],
                "weeks": [f"{(today - timedelta(weeks=i)).isocalendar()[0]}-W{(today - timedelta(weeks=i)).isocalendar()[1]:02d}" for i in range(12)],
                "months": [(today - timedelta(days=30*i)).strftime("%Y-%m") for i in range(12)]
            }

        try:
            response = await self.client.session.get("/api/manager/energy/reports/available")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting available reports: {e}")
            raise

    async def get_energy_report_hour(self, date_hour: str, cache: Optional[str] = None) -> Dict[str, Any]:
        """Get hourly energy report."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            import random
            return {
                "hour": date_hour,
                "electricity": {
                    "consumed": round(random.uniform(0.5, 3.0), 2),
                    "produced": round(random.uniform(0, 1.0), 2),
                    "cost": round(random.uniform(0.15, 0.90), 2)
                },
                "gas": {
                    "consumed": round(random.uniform(0.2, 2.0), 2),
                    "cost": round(random.uniform(0.25, 2.40), 2)
                },
                "water": {
                    "consumed": round(random.uniform(5, 25), 1),
                    "cost": round(random.uniform(0.01, 0.06), 2)
                }
            }

        try:
            params = {"hour": date_hour}
            if cache:
                params["cache"] = cache
            response = await self.client.session.get("/api/manager/energy/report/hour", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting hourly energy report: {e}")
            raise

    async def get_energy_report_year(self, year: str, cache: Optional[str] = None) -> Dict[str, Any]:
        """Get yearly energy report."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            import random
            return {
                "year": year,
                "electricity": {
                    "consumed": round(random.uniform(4800, 12000), 2),
                    "produced": round(random.uniform(0, 3600), 2),
                    "cost": round(random.uniform(1440, 3840), 2)
                },
                "gas": {
                    "consumed": round(random.uniform(1800, 9000), 2),
                    "cost": round(random.uniform(2160, 10800), 2)
                },
                "water": {
                    "consumed": round(random.uniform(36000, 108000), 1),
                    "cost": round(random.uniform(90, 270), 2)
                }
            }

        try:
            params = {"year": year}
            if cache:
                params["cache"] = cache
            response = await self.client.session.get("/api/manager/energy/report/year", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting yearly energy report: {e}")
            raise

    async def get_energy_currency(self) -> Dict[str, Any]:
        """Get energy currency settings."""
        if self.client.config.offline_mode or self.client.config.demo_mode:
            return {"currency": "EUR", "symbol": "€"}

        try:
            response = await self.client.session.get("/api/manager/energy/currency")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting energy currency: {e}")
            raise