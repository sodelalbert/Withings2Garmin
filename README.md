# Withings2Garmin

A comprehensive Withings to Garmin Connect synchronization tool built with modern Python tooling and `.env` configuration.

## Features

- **Automatic data synchronization** from Withings to Garmin Connect
- **Multiple output formats**: JSON, FIT files, and direct Garmin upload
- **Comprehensive health metrics support**:
  - Weight measurements with BMI calculation
  - Body composition (fat percentage, muscle mass, bone mass, body water)
  - Blood pressure readings (systolic, diastolic, heart rate)
- **Flexible date range selection** with automatic last sync tracking
- **Authentication management**:
  - OAuth 2.0 flow for Withings API
  - Multi-factor authentication support for Garmin Connect
  - Local token storage and automatic refresh
- **Robust logging system** with timestamped log files
- **FIT file encoding** compatible with Garmin devices
- **Environment-based configuration** using `.env` files
- **Modern Python packaging** with uv dependency management

## Installation

This project requires Python 3.12+ and uses [uv](https://docs.astral.sh/uv/) for dependency management.

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install the project

```bash
git clone https://github.com/sodelalbert/Withings2Garmin.git
cd Withings2Garmin
uv sync
```

## Configuration

### Environment Setup

Copy the example environment file and configure your credentials:

```bash
cp sample/.env.example .env
```

Edit `.env` with your credentials:

```bash
# Withings API Configuration
WITHINGS_CLIENT_ID=your_withings_client_id
WITHINGS_CLIENT_SECRET=your_withings_client_secret
WITHINGS_CALLBACK_URL=https://jaroslawhartman.github.io/withings-sync/contrib/withings.html

# Garmin Connect Configuration
GARMIN_USERNAME=your_garmin_username
GARMIN_PASSWORD=your_garmin_password
```

### Withings API Setup

1. Create a Withings developer account at [Withings Developer Portal](https://developer.withings.com/)
2. Create a new application
3. Set the callback URL to: `https://jaroslawhartman.github.io/withings-sync/contrib/withings.html`
4. Copy the Client ID and Client Secret to your `.env` file

## Usage

All commands use `uv run` to ensure proper environment isolation and dependency management.

### Basic Operations

**Export measurements to JSON:**

```bash
uv run sync.py --output-json measurements.json
```

**Sync to Garmin Connect:**

```bash
uv run sync.py --garmin
```

**Generate FIT file:**

```bash
uv run sync.py --output-fit measurements.fit
```

**Multiple outputs with Garmin sync:**

```bash
uv run sync.py --garmin --output-json backup.json --output-fit backup.fit
```

### Date Range Specification

**Sync specific date range:**

```bash
uv run sync.py --garmin -f 2024-01-01 -t 2024-01-31
```

**Sync from specific date to today:**

```bash
uv run sync.py --garmin -f 2024-01-01
```

**Verbose logging for debugging:**

```bash
uv run sync.py --garmin --verbose
```

### Authentication Workflow

#### First-Time Withings Authorization

When running for the first time, you'll see:

```
============================================================
WITHINGS AUTHORIZATION REQUIRED
============================================================
Open this URL in your browser and copy the authorization code:

https://account.withings.com/oauth2_user/authorize2?response_type=code&client_id=...

You have 30 seconds to complete this process!
============================================================
Enter authorization code: [paste code here]
```

1. Open the provided URL in your browser
2. Log into your Withings account and authorize the application
3. Copy the authorization code from the callback URL
4. Paste it into the terminal prompt
5. Tokens are automatically saved for future use

#### Garmin Multi-Factor Authentication

If MFA is enabled on your Garmin account:

```
MFA code: [enter your 6-digit code]
```

1. Check your email for the Garmin verification code
2. Enter the 6-digit code when prompted
3. Session is saved locally for future authentication

## Project Architecture

```
Withings2Garmin/
├── sync.py                 # Main application entry point
├── withings_client.py      # Withings API client with OAuth 2.0
├── garmin_client.py        # Garmin Connect client with MFA support
├── fit_encoder.py          # FIT file format encoder
├── pyproject.toml          # Project configuration and dependencies
├── uv.lock                 # Dependency lock file
├── .env                    # Environment configuration (user-created)
├── sample/
│   └── .env.example        # Environment template
├── .withings_tokens.json   # Withings OAuth tokens (auto-created)
├── .garmin_session/        # Garmin session data (auto-created)
└── logs/                   # Application logs (auto-created)
```

## Dependencies

Core dependencies managed through `pyproject.toml`:

- **requests** (≥2.31.0) - HTTP client for API communications
- **garth** (≥0.4.46) - Garmin Connect authentication and API interface

Development dependencies:

- **black** (≥25.1.0) - Code formatting
- **mypy** (≥1.17.0) - Static type checking
- **flake8** with extensions - Code linting
- **isort** (≥6.0.1) - Import sorting
- **pytest** (≥8.4.1) - Testing framework

## Command Line Reference

```
usage: sync.py [-h] [-f FROM_DATE] [-t TO_DATE] [--garmin]
               [--output-json OUTPUT_JSON] [--output-fit OUTPUT_FIT] [--verbose]

options:
  -h, --help                    Show help message and exit
  -f FROM_DATE                  Start date (YYYY-MM-DD). If not specified, uses last sync date
  -t TO_DATE                    End date (YYYY-MM-DD). If not specified, uses today
  --garmin                      Enable Garmin Connect sync
  --output-json OUTPUT_JSON     Output measurements to JSON file
  --output-fit OUTPUT_FIT       Save FIT file to specified path
  --verbose, -v                 Enable verbose logging
```

## Data Processing

### Supported Withings Metrics

- **Weight**: Body weight with automatic BMI calculation
- **Body Composition**: Fat percentage, muscle mass, bone mass, body water
- **Cardiovascular**: Blood pressure (systolic/diastolic), heart rate
- **Physical**: Height measurements

### FIT File Format

The application generates standard FIT files compatible with:

- Garmin Connect
- Garmin devices
- Third-party fitness applications
- ANT+ ecosystem tools

### Data Transformation

- Automatic unit conversion to metric system
- BMI calculation using stored height data
- Timestamp normalization for cross-platform compatibility
- Data validation and error handling

## Logging and Monitoring

### Log Files

- **Location**: `logs/withings_sync_YYYYMMDD_HHMMSS.log`
- **Retention**: Manual cleanup (logs are not auto-deleted)
- **Format**: Timestamped entries with log levels

### Log Levels

- **INFO**: Standard operation messages
- **DEBUG**: Detailed operation information (use `--verbose`)
- **WARNING**: Non-critical issues
- **ERROR**: Operation failures

### Console Output

- Real-time progress indicators
- Authentication prompts
- Success/failure summaries
- Error messages with context

## Troubleshooting

### Authentication Issues

**Withings token expiration:**

```bash
# Remove invalid tokens and re-authenticate
rm .withings_tokens.json
uv run sync.py --garmin
```

**Garmin session issues:**

```bash
# Clear Garmin session and re-authenticate
rm -rf .garmin_session
uv run sync.py --garmin
```

### Data Issues

**No measurements found:**

- Verify date range with `-f` and `-t` options
- Check Withings account has data for specified period
- Ensure Withings device is synced

**FIT file generation errors:**

- Verify write permissions in target directory
- Check available disk space
- Ensure measurements contain valid data

### Network Issues

**API connection failures:**

- Check internet connectivity
- Verify firewall settings
- Confirm API endpoints are accessible

## Development

### Code Quality

The project uses automated code quality tools:

```bash
# Format code
uv run black .

# Sort imports
uv run isort .

# Lint code
uv run flake8 .

# Type checking
uv run mypy .
```

### Testing

```bash
# Run tests
uv run pytest
```

## License

MIT License - see project repository for full license text.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following code quality standards
4. Submit a pull request

## Support

For issues and feature requests, please use the GitHub issue tracker.
