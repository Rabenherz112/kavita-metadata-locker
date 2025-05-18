# Kavita Metadata Locker

> A Python CLI tool to lock metadata fields (e.g., genres, tags, summary) on your Kavita server for all series within selected libraries.

![](https://img.shields.io/github/stars/Rabenherz112/kavita-metadata-locker?color=yellow&style=plastic&label=Stars) ![](https://img.shields.io/discord/728735370560143360?color=5460e6&label=Discord&style=plastic)

## Features

- Interactive selection of metadata fields to lock
- Full CLI support with arguments for URL, credentials, fields, libraries, and skip suppression
- Reports statistics: total series processed, locked, and skipped

## Requirements

- Python 3.12 or higher (probably works with lower versions, but not tested)
- Kavita server URL, user credentials, and valid API key

## Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/Rabenherz112/kavita-metadata-locker.git
    cd kavita-metadata-locker
    ```
2. Bootstrap virtual environment:
    ```bash
    python3 setup_env.py
    ```

    - Creates a `.venv` directory with a virtual environment
    - Install / update required dependencies (`requests`)
3. Activate the virtual environment:
    ```bash
    source .venv/bin/activate
    ```

## Usage

You can run in **interactive mode** or **non-interactive (CLI) mode**:

### Interactive Mode

1. Run the metadata locker:
    ```bash
    python3 kavita-metadata-locker.py
    ```
2. Follow the interactive prompts to select libraries and metadata fields to lock.
    - Kavita Server URL: `https://kavita.instance.com` or `http://localhost:5000`
    - Username: Your Kavita username
    - API Key: Your Kavita API key for the user
    - Fields to lock: Select the metadata fields you want to lock (e.g., genres, tags, summary)
    - Hide skipped series: Choose whether to hide skipped series in the output
    - Libraries: Select the libraries you want to apply the lock to
3. The script will print per-series actions and a final summary, for example:
    ```
    Processed 120 series: Locked 100, Skipped 20.
    ```

### CLI Mode

```bash
python3 kavita-metadata-locker.py \
    -u https://kavita.instance.com \
    -U myuser \
    -k myapikey \
    -f summary,genres,tags \
    -l 1,3,5 \
    -hs
```

- `-u, --url` Kavita Server URL
- `-U, --username` Username for authentication
- `-k, --api-key` API Key for authentication
- `-f, --fields` Comma-separated metadata fields (keys or labels) to lock
- `-l, --library-ids` Comma-separated library IDs to process
- `-hs, --hide-skipped` Do not display per-series skipped messages
- `--version` Show script version and exit

## Screenshots

![Interactive Menu](./assets/script-interactive.png)
![Output Example](./assets/script-output.png)

## Why I created this

I personally use Kavita with Komf to get and manage my metadata. However since Komf can't lock currently all metadata fields, I created this tool to lock the metadata fields I want to keep. As otherwise when Kavita runs a scan, the metadata gets removed again.

## License

This project is licensed under the GNU AGPL v3.0. See the [LICENSE](./LICENSE) file for details.
