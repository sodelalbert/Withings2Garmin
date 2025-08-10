"""Simplified Garmin client using .env configuration."""

import io
import logging
import os

import garth

logger = logging.getLogger(__name__)


class GarminException(Exception):
    """Exception for Garmin API errors."""

    pass


class GarminClient:
    """Simplified Garmin client using .env configuration."""

    def __init__(self):
        # Load configuration from environment variables
        self.username = os.getenv("GARMIN_USERNAME")
        self.password = os.getenv("GARMIN_PASSWORD")

        if not self.username or not self.password:
            raise GarminException(
                "Missing required environment variables:"
                " GARMIN_USERNAME, GARMIN_PASSWORD"
            )

        # Session file location - store in project directory
        self.session_file = ".garmin_session"

        # Initialize Garth client
        # Temporary fix for Garth user agent
        garth.http.USER_AGENT = {"User-Agent": "GCM-iOS-5.7.2.1"}
        self.client = garth.Client()

        # Authenticate
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Garmin Connect."""
        # Try to load existing session
        if os.path.exists(self.session_file):
            try:
                self.client.load(self.session_file)
                if hasattr(self.client, "username"):
                    logger.info("Loaded existing Garmin session")
                    return
            except Exception as e:
                logger.warning(f"Failed to load existing session: {e}")

        # Login with credentials
        try:
            logger.info("Logging into Garmin Connect...")
            self.client.login(self.username, self.password)
            self.client.dump(self.session_file)
            logger.info("Successfully authenticated with Garmin Connect")
        except Exception as e:
            raise GarminException(f"Garmin authentication failed: {e}")

    def upload_file(
        self, file_data: bytes, filename: str = "withings_sync.fit"
    ) -> bool:
        """Upload FIT file to Garmin Connect."""
        try:
            fit_file = io.BytesIO(file_data)
            fit_file.name = filename

            self.client.upload(fit_file)
            logger.info(f"Successfully uploaded {filename} to Garmin Connect")
            return True

        except Exception as e:
            logger.error(f"Failed to upload file to Garmin Connect: {e}")
            return False

    def test_connection(self) -> bool:
        """Test connection to Garmin Connect."""
        try:
            # Simple test to see if we can access the API
            if hasattr(self.client, "username"):
                logger.info(f"Connected to Garmin Connect as: {self.client.username}")
                return True
            return False
        except Exception as e:
            logger.error(f"Garmin connection test failed: {e}")
            return False
