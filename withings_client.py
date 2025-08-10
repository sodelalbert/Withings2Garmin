"""Simplified Withings client using .env configuration."""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

AUTHORIZE_URL = "https://account.withings.com/oauth2_user/authorize2"
TOKEN_URL = "https://wbsapi.withings.net/v2/oauth2"
GETMEAS_URL = "https://wbsapi.withings.net/measure?action=getmeas"


class WithingsException(Exception):
    """Exception for Withings API errors."""

    pass


class WithingsClient:
    """Simplified Withings client using .env configuration."""

    def __init__(self):
        # Load configuration from environment variables
        self.client_id = os.getenv("WITHINGS_CLIENT_ID")
        self.client_secret = os.getenv("WITHINGS_CLIENT_SECRET")
        self.callback_url = os.getenv(
            "WITHINGS_CALLBACK_URL", "http://localhost:8080/callback"
        )

        if not self.client_id or not self.client_secret:
            raise WithingsException(
                "Missing required environment variables:"
                " WITHINGS_CLIENT_ID, WITHINGS_CLIENT_SECRET"
            )

        # User tokens file - store in project directory
        self.tokens_file = ".withings_tokens.json"
        self.tokens = self._load_tokens()

        # Ensure we have valid tokens
        self._ensure_authenticated()

    def _load_tokens(self) -> Dict:
        """Load tokens from file."""
        try:
            with open(self.tokens_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_tokens(self):
        """Save tokens to file."""
        with open(self.tokens_file, "w") as f:
            json.dump(self.tokens, f, indent=2)

    def _ensure_authenticated(self):
        """Ensure we have valid authentication tokens."""
        if not self.tokens.get("access_token"):
            if not self.tokens.get("auth_code"):
                self.tokens["auth_code"] = self._get_auth_code()
            self._get_access_token()

        # Try to refresh token
        self._refresh_access_token()
        self._save_tokens()

    def _get_auth_code(self) -> str:
        """Get authorization code from user."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "state": "OK",
            "scope": "user.metrics",
            "redirect_uri": self.callback_url,
        }

        url = AUTHORIZE_URL + "?" + "&".join([f"{k}={v}" for k, v in params.items()])

        print("\n" + "=" * 60)
        print("WITHINGS AUTHORIZATION REQUIRED")
        print("=" * 60)
        print("Open this URL in your browser and copy the authorization code:")
        print(f"\n{url}\n")
        print("You have 30 seconds to complete this process!")
        print("=" * 60)

        auth_code = input("Enter authorization code: ").strip()
        if not auth_code:
            raise WithingsException("No authorization code provided")

        return auth_code

    def _get_access_token(self):
        """Exchange authorization code for access token."""
        params = {
            "action": "requesttoken",
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": self.tokens["auth_code"],
            "redirect_uri": self.callback_url,
        }

        response = requests.post(TOKEN_URL, params=params)
        data = response.json()

        if data.get("status") != 0:
            raise WithingsException(f"Token request failed: {data}")

        body = data.get("body", {})
        self.tokens.update(
            {
                "access_token": body.get("access_token"),
                "refresh_token": body.get("refresh_token"),
                "user_id": body.get("userid"),
            }
        )

        logger.info("Successfully obtained access token")

    def _refresh_access_token(self):
        """Refresh the access token."""
        if not self.tokens.get("refresh_token"):
            return

        params = {
            "action": "requesttoken",
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.tokens["refresh_token"],
        }

        response = requests.post(TOKEN_URL, params=params)
        data = response.json()

        if data.get("status") == 0:
            body = data.get("body", {})
            self.tokens.update(
                {
                    "access_token": body.get("access_token"),
                    "refresh_token": body.get("refresh_token"),
                    "user_id": body.get("userid"),
                }
            )
            logger.info("Successfully refreshed access token")
        else:
            logger.warning(f"Token refresh failed: {data}")

    def get_measurements(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get measurements from Withings API."""
        params = {
            "access_token": self.tokens["access_token"],
            "category": 1,  # All measurements
            "startdate": int(start_date.timestamp()),
            "enddate": int(end_date.timestamp()),
        }

        response = requests.post(GETMEAS_URL, params=params)
        data = response.json()

        if data.get("status") != 0:
            raise WithingsException(f"Measurements request failed: {data}")

        measurements = data.get("body", {}).get("measuregrps", [])
        logger.info(f"Retrieved {len(measurements)} measurement groups")

        return self._process_measurements(measurements)

    def get_height(self) -> Optional[float]:
        """Get user's height."""
        params = {
            "access_token": self.tokens["access_token"],
            "meastype": 4,  # Height type
            "category": 1,
        }

        response = requests.post(GETMEAS_URL, params=params)
        data = response.json()

        if data.get("status") != 0:
            return None

        measurements = data.get("body", {}).get("measuregrps", [])
        if not measurements:
            return None

        # Get the latest height measurement
        latest_height = None
        latest_date = None

        for group in measurements:
            for measure in group.get("measures", []):
                if measure.get("type") == 4:  # Height
                    value = measure["value"] * (10 ** measure["unit"])
                    date = datetime.fromtimestamp(group["date"])

                    if latest_date is None or date > latest_date:
                        latest_height = value
                        latest_date = date

        return latest_height

    def _process_measurements(self, raw_measurements: List[Dict]) -> List[Dict]:
        """Process raw measurements into structured format."""
        processed = []

        for group in raw_measurements:
            timestamp = datetime.fromtimestamp(group["date"])
            measurements = {}

            for measure in group.get("measures", []):
                value = measure["value"] * (10 ** measure["unit"])
                measure_type = measure["type"]

                # Map measurement types to readable names
                type_mapping = {
                    1: "weight",
                    4: "height",
                    5: "fat_free_mass",
                    6: "fat_ratio",
                    8: "fat_mass_weight",
                    9: "diastolic_bp",
                    10: "systolic_bp",
                    11: "heart_rate",
                    12: "temperature",
                    76: "muscle_mass",
                    77: "hydration",
                    88: "bone_mass",
                }

                if measure_type in type_mapping:
                    measurements[type_mapping[measure_type]] = round(value, 2)

            if measurements:
                processed.append({"timestamp": timestamp, "measurements": measurements})

        return processed

    def get_last_sync(self) -> int:
        """Get last sync timestamp."""
        return self.tokens.get(
            "last_sync", int(time.time()) - 86400
        )  # Default to 24h ago

    def set_last_sync(self):
        """Set last sync timestamp to now."""
        self.tokens["last_sync"] = int(time.time())
        self._save_tokens()
        logger.info("Updated last sync timestamp")
