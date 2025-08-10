"""Main sync application."""

import argparse
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from fit_encoder import FitEncoder
from garmin_client import GarminClient, GarminException
from withings_client import WithingsClient, WithingsException


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    # Configure logging level
    level = logging.DEBUG if verbose else logging.INFO

    # Create timestamp for unique log file per execution
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(logs_dir, f"withings_sync_{timestamp}.log")

    # Simple logging configuration
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler(log_filename, encoding="utf-8"),  # File output
        ],
        force=True,  # Override any existing configuration
    )

    # Log the configuration
    logging.info(f"Log file: {log_filename}")
    if verbose:
        logging.debug("Verbose logging enabled")


def load_env_file(env_file: str = ".env"):
    """Load environment variables from .env file."""
    if not os.path.exists(env_file):
        logging.debug(f"Environment file '{env_file}' not found in project root.")
        return

    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value


def convert_to_fit(measurements: List[Dict], height: Optional[float] = None) -> bytes:
    """Convert measurements to FIT file format."""
    encoder = FitEncoder()
    encoder.write_file_id()

    for measurement in measurements:
        timestamp = measurement["timestamp"]
        data = measurement["measurements"]

        # Write device info for each measurement
        encoder.write_device_info(timestamp)

        # Write weight data if available
        if "weight" in data:
            encoder.write_weight_measurement(
                timestamp=timestamp,
                weight=data.get("weight"),
                fat_percentage=data.get("fat_ratio"),
                muscle_mass=data.get("muscle_mass"),
                bone_mass=data.get("bone_mass"),
                body_water=data.get("hydration"),
            )

        # Write blood pressure data if available
        if "systolic_bp" in data and "diastolic_bp" in data:
            encoder.write_blood_pressure(
                timestamp=timestamp,
                systolic=int(data["systolic_bp"]),
                diastolic=int(data["diastolic_bp"]),
                heart_rate=(
                    int(data.get("heart_rate", 0)) if data.get("heart_rate") else None
                ),
            )

    return encoder.finalize()


def save_measurements_json(measurements: List[Dict], filename: str):
    """Save measurements to JSON file."""
    # Convert datetime objects to strings for JSON serialization
    serializable_data = []
    for measurement in measurements:
        data = measurement.copy()
        data["timestamp"] = data["timestamp"].isoformat()
        serializable_data.append(data)

    with open(filename, "w") as f:
        json.dump(serializable_data, f, indent=2)

    print(f"Saved {len(measurements)} measurements to {filename}")


def sync_data(args):
    """Main sync function."""
    logger = logging.getLogger(__name__)

    try:
        # Initialize clients
        logger.info("Initializing Withings client...")
        withings = WithingsClient()

        garmin = None
        if args.garmin:
            logger.info("Initializing Garmin client...")
            garmin = GarminClient()

        # Determine date range
        if args.from_date:
            start_date = datetime.strptime(args.from_date, "%Y-%m-%d")
        else:
            # Use last sync date or default to 7 days ago
            last_sync = withings.get_last_sync()
            start_date = datetime.fromtimestamp(last_sync)

        if args.to_date:
            end_date = datetime.strptime(args.to_date, "%Y-%m-%d")
        else:
            end_date = datetime.now()

        logger.info(f"Syncing data from {start_date.date()} to {end_date.date()}")

        # Get measurements
        measurements = withings.get_measurements(start_date, end_date)

        if not measurements:
            logger.info("No measurements found for the specified period")
            return

        logger.info(f"Found {len(measurements)} measurements")

        # Get height for BMI calculation
        height = withings.get_height()
        if height:
            logger.info(f"User height: {height:.2f} m")

        # Save to JSON if requested
        if args.output_json:
            save_measurements_json(measurements, args.output_json)

        # Convert to FIT format if needed (for file output or Garmin upload)
        fit_data = None
        if args.output_fit or args.garmin:
            logger.info("Converting measurements to FIT format...")
            fit_data = convert_to_fit(measurements, height)

            if args.output_fit:
                with open(args.output_fit, "wb") as f:
                    f.write(fit_data)
                logger.info(f"Saved FIT file to {args.output_fit}")

        # Upload to Garmin if requested
        if args.garmin:
            if fit_data is None:
                logger.info(
                    "Converting measurements to FIT format for Garmin upload..."
                )
                fit_data = convert_to_fit(measurements, height)

            logger.info("Uploading to Garmin Connect...")
            if garmin and garmin.upload_file(fit_data):
                logger.info("Successfully uploaded to Garmin Connect")

                # Update last sync time if upload was successful
                if not args.from_date:  # Only update if we used automatic date range
                    withings.set_last_sync()
            else:
                logger.error("Failed to upload to Garmin Connect")

        logger.info("Sync completed successfully")

    except WithingsException as e:
        logger.error(f"Withings error: {e}")
        return 1
    except GarminException as e:
        logger.error(f"Garmin error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Withings to Garmin sync tool")

    parser.add_argument(
        "-f",
        dest="from_date",
        help="Start date (YYYY-MM-DD). If not specified, uses last sync date",
    )
    parser.add_argument(
        "-t", dest="to_date", help="End date (YYYY-MM-DD). If not specified, uses today"
    )
    parser.add_argument(
        "--garmin", action="store_true", help="Enable Garmin Connect sync"
    )
    parser.add_argument("--output-json", help="Output measurements to JSON file")
    parser.add_argument("--output-fit", help="Save FIT file to specified path")

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    load_env_file()

    setup_logging(args.verbose)

    return sync_data(args)


if __name__ == "__main__":
    exit(main())
