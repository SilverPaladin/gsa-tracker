# GSA Tracker (Streamlit Staff Portal)

## Requirements

- Python 3.10+ (3.11 recommended)

## Setup

1. Create a virtual environment

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Configure secrets

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set values as needed.

See [Streamlit Secrets Management](https://docs.streamlit.io/develop/concepts/connections/secrets-management) for details.

## Configuration (`.streamlit/secrets.toml`)

| Key               | Description                                              | Default             |
|-------------------|----------------------------------------------------------|---------------------|
| `DB_FILE`         | Path to the JSON file used as the local database.        | `portal_data.json`  |
| `SYSTEM_PASSWORD` | Password used to seed the initial SUPER_ADMIN user.      | `ChangeMeNow!`      |

## Run

```bash
streamlit run app.py
```

## Notes

- The app stores data in a local JSON file (`DB_FILE`). Treat it like application data; avoid committing it to git.
- `.streamlit/secrets.toml` is gitignored by default.

