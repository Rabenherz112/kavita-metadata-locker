#!/usr/bin/env python3
"""
Kavita Metadata Locker Script

This script connects to a Kavita server to lock specified metadata fields (e.g., genres, tags, summary)
for all series within selected libraries. It uses the Kavita REST API endpoints.

Supports both interactive and command-line modes.

Command-line Arguments:
    -u/--url            Kavita Server URL (e.g., https://kavita.instance.com)
    -U/--username       Username for authentication
    -k/--api-key        API Key for authentication
    -f/--fields         Comma-separated metadata fields (keys or labels) to lock
    -l/--library-ids    Comma-separated library IDs to process
    -hs/--hide-skipped  Do not print skipped series messages
    --version           Show script version and exit
"""
import requests
import sys
import argparse
__version__ = "2.1.1"

# Kavita API endpoints
API_LOGIN = "/api/Account/login"
API_LIBRARIES = "/api/Library/libraries"
API_SERIES_V2 = "/api/Series/v2"
API_SERIES_METADATA_GET = "/api/Series/metadata"
API_SERIES_METADATA_POST = "/api/Series/metadata"

# Metadata fields for locking: (Label, data key, lock-flag key)
# https://www.kavitareader.com/docs/api/#/Series/post_api_Series_metadata
LOCKABLE_FIELDS = [
    ("Summary", "summary", "summaryLocked"),
    ("Genres", "genres", "genresLocked"),
    ("Tags", "tags", "tagsLocked"),
    ("Age Rating", "ageRating", "ageRatingLocked"),
    ("Publication Status", "publicationStatus", "publicationStatusLocked"),
    ("Release Year", "releaseYear", "releaseYearLocked"),
    ("Language", "language", "languageLocked"),
    ("Writers", "writers", "writerLocked"),
    ("Cover Artists", "coverArtists", "coverArtistLocked"),
    ("Publishers", "publishers", "publisherLocked"),
    ("Characters", "characters", "characterLocked"),
    ("Pencillers", "pencillers", "pencillerLocked"),
    ("Inkers", "inkers", "inkerLocked"),
    ("Imprints", "imprints", "imprintLocked"),
    ("Colorists", "colorists", "coloristLocked"),
    ("Letterers", "letterers", "lettererLocked"),
    ("Editors", "editors", "editorLocked"),
    ("Translators", "translators", "translatorLocked"),
    ("Teams", "teams", "teamLocked"),
    ("Locations", "locations", "locationLocked")
]


def login_account(base_url: str, username: str, api_key: str) -> str:
    """
    Authenticate with Kavita account endpoint to get a JWT token.

    Parameters:
    - base_url: URL of the Kavita server
    - username: Kavita account username
    - api_key: Kavita API key

    Returns:
    - JWT token string

    Exits if authentication fails.
    """
    url = f"{base_url.rstrip('/')}{API_LOGIN}"
    payload = {"username": username, "password": "string", "apiKey": api_key}
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    token = data.get("token")
    if not token:
        print("Failed to retrieve authentication token.", file=sys.stderr)
        sys.exit(1)
    return token


def list_libraries(base_url: str, headers: dict) -> list:
    """
    Retrieve all libraries available on the Kavita server.

    Parameters:
    - base_url: URL of the Kavita server
    - headers: HTTP headers with Authorization

    Returns:
    - List of library objects (dicts)
    """
    resp = requests.get(f"{base_url.rstrip('/')}{API_LIBRARIES}", headers=headers)
    resp.raise_for_status()
    return resp.json()


def list_series_for_library(base_url: str, headers: dict, library_id: int) -> list:
    """
    Fetch all series IDs in a given library using /api/Series/v2.

    Parameters:
    - base_url: URL of the Kavita server
    - headers: HTTP headers with Authorization
    - library_id: integer ID of the library to filter

    Returns:
    - List of series summary objects (dicts)
    """
    params = {"PageNumber": 0, "PageSize": 0}
    payload = {
        "id": 0,
        "name": "",
        "statements": [],
        "combination": 0,
        "sortOptions": {"sortField": 1, "isAscending": True},
        "limitTo": 0,
        "libraryIds": [library_id]
    }
    resp = requests.post(
        f"{base_url.rstrip('/')}{API_SERIES_V2}",
        headers=headers,
        params=params,
        json=payload
    )
    resp.raise_for_status()
    return resp.json()


def get_series_metadata(base_url: str, headers: dict, series_id: int) -> dict:
    """
    GET full metadata for a specific series.

    Parameters:
    - base_url: URL of the Kavita server
    - headers: HTTP headers with Authorization
    - series_id: integer ID of the series

    Returns:
    - Metadata object (dict) including lock flags and fields
    """
    resp = requests.get(
        f"{base_url.rstrip('/')}{API_SERIES_METADATA_GET}",
        headers=headers,
        params={"seriesId": series_id}
    )
    resp.raise_for_status()
    return resp.json()


def update_series_metadata(base_url: str, headers: dict, metadata: dict, lock_fields: list):
    """
    Update metadata for a series, setting selected lock flags to True.

    Parameters:
    - base_url: URL of the Kavita server
    - headers: HTTP headers with Authorization
    - metadata: dict of existing series metadata
    - lock_fields: list of tuples defining which fields to lock

    Returns:
    - None (raises on HTTP errors)
    """
    for _, _, lock_key in lock_fields:
        metadata[lock_key] = True
    payload = {"seriesMetadata": metadata}
    resp = requests.post(
        f"{base_url.rstrip('/')}{API_SERIES_METADATA_POST}",
        headers=headers,
        json=payload
    )
    resp.raise_for_status()


def prompt_lock_fields() -> list:
    """
    Display lockable metadata options and return user selections.

    Returns:
    - List of selected LOCKABLE_FIELDS entries
    """
    print("\nSelect metadata fields to lock:")
    for idx, (label, _, _) in enumerate(LOCKABLE_FIELDS, 1):
        print(f"{idx}. {label}")
    choices = input("Enter comma-separated field numbers (e.g. 2,3): ").split(',')
    selected = []
    for c in choices:
        try:
            selected.append(LOCKABLE_FIELDS[int(c.strip())-1])
        except (ValueError, IndexError):
            continue
    if not selected:
        print("No valid fields selected. Exiting.", file=sys.stderr)
        sys.exit(1)
    return selected


def parse_field_args(field_args: str) -> list:
    """
    Parse a comma-separated string of field keys or labels into lockable field entries.

    Args:
        field_args: Comma-separated list of metadata field keys or labels.

    Returns:
        A list of matching LOCKABLE_FIELDS tuples.

    Exits:
        SystemExit if none of the provided fields match.
    """
    keys = [f.strip().lower() for f in field_args.split(',') if f.strip()]
    selected = []
    for key in keys:
        matched = False
        for label, data_key, lock_key in LOCKABLE_FIELDS:
            if key == data_key.lower() or key == label.lower():
                selected.append((label, data_key, lock_key))
                matched = True
                break
        if not matched:
            print(f"Unknown field '{key}'. Skipping.", file=sys.stderr)
    if not selected:
        print("No valid fields provided. Exiting.", file=sys.stderr)
        sys.exit(1)
    return selected


def main():
    """
    Main execution flow:
    - Prompt user for Kavita URL, credentials, and lock fields
    - Authenticate and retrieve libraries
    - For each selected library, fetch series, check & lock fields
    - Report statistics
    """
    parser = argparse.ArgumentParser(description="Kavita Metadata Locker")
    parser.add_argument("-u", "--url", help="Kavita Server URL (e.g., https://kavita.instance.com)")
    parser.add_argument("-U", "--username", help="Username for authentication")
    parser.add_argument("-k", "--api-key", help="API Key for authentication")
    parser.add_argument("-f", "--fields", help="Comma-separated metadata fields (keys or labels) to lock")
    parser.add_argument("-l", "--library-ids", help="Comma-separated library IDs to process")
    parser.add_argument("-hs", "--hide-skipped", action="store_true", help="Do not print skipped series messages")
    parser.add_argument('--version', action='version', version=__version__)
    args = parser.parse_args()

    # Credential input
    if args.url and args.username and args.api_key:
        base_url = args.url
        username = args.username
        api_key = args.api_key
    else:
        print("Configure Kavita Metadata Locker")
        base_url = input("Kavita Server URL (e.g. https://kavita.instance.com): ").strip()
        username = input("Username: ").strip()
        api_key  = input("API Key: ").strip()

    # Field selection
    if args.fields:
        lock_fields = parse_field_args(args.fields)
    else:
        lock_fields = prompt_lock_fields()
        # Ask for silent mode
        silent = input("Do you want to hide skipped series messages? (y/n): ").strip().lower()
        if silent in ('y', 'yes'):
            args.hide_skipped = True
        print("\nLogging in…")

    token = login_account(base_url, username, api_key)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Library selection
    libs = list_libraries(base_url, headers)
    if not libs:
        print("No libraries found.", file=sys.stderr)
        sys.exit(1)

    if args.library_ids:
        try:
            ids = {int(i.strip()) for i in args.library_ids.split(',') if i.strip()}
        except ValueError:
            print("Invalid library IDs provided.", file=sys.stderr)
            sys.exit(1)
        chosen = [lib for lib in libs if lib['id'] in ids]
        if not chosen:
            print("No matching libraries found.", file=sys.stderr)
            sys.exit(1)
    else:
        print("Available libraries:")
        for idx, lib in enumerate(libs, 1):
            print(f"{idx}. {lib['name']} (ID: {lib['id']})")
        choices = input("Select libraries (comma-separated numbers): ")
        chosen = []
        for c in choices.split(','):
            try:
                chosen.append(libs[int(c.strip())-1])
            except (ValueError, IndexError):
                continue
        if not chosen:
            print("No valid libraries selected. Exiting.", file=sys.stderr)
            sys.exit(1)

    # Process series
    total = locked_count = skipped_count = 0

    for lib in chosen:
        lib_id = lib['id']
        print(f"\nProcessing Library: {lib['name']} (ID: {lib_id})")
        all_series = list_series_for_library(base_url, headers, lib_id)
        series_list = [s for s in all_series if s.get('libraryId') == lib_id]

        for series in series_list:
            total += 1
            sid = series.get('id')
            title = series.get('name') or series.get('title')
            meta = get_series_metadata(base_url, headers, sid)
            needs_lock = False
            for _, field_key, lock_key in lock_fields:
                if not meta.get(lock_key) and meta.get(field_key):
                    needs_lock = True
                    break
            if needs_lock:
                lock_names = ", ".join([label for label,_,_ in lock_fields])
                print(f"  Locking {lock_names} for '{title}' (ID: {sid})…")
                update_series_metadata(base_url, headers, meta, lock_fields)
                locked_count += 1
            else:
                skipped_count += 1
                if not args.hide_skipped:
                    print(f"  Skipping '{title}': selected fields already locked or empty.")

    print(f"\nProcessed {total} series: Locked {locked_count}, Skipped {skipped_count}.")

if __name__ == '__main__':
    main()
