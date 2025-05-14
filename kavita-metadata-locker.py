#!/usr/bin/env python3
"""
Kavita Metadata Locker Script

This script connects to a Kavita server to lock specified metadata fields (e.g., genres, tags, summary)
for all series within selected libraries. It uses the Kavita REST API v2 endpoints.
"""
import requests
import sys
__version__ = "2.0.4"

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


def main():
    """
    Main execution flow:
    - Prompt user for Kavita URL, credentials, and lock fields
    - Authenticate and retrieve libraries
    - For each selected library, fetch series, check & lock fields
    - Report statistics
    """
    print("Configure Kavita Metadata Locker")
    base_url = input("Kavita Server URL (e.g. https://kavita.instance.com): ").strip()
    username = input("Username: ").strip()
    api_key  = input("API Key: ").strip()

    lock_fields = prompt_lock_fields()

    print("\nLogging in…")
    token = login_account(base_url, username, api_key)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print("\nFetching libraries…")
    libs = list_libraries(base_url, headers)
    if not libs:
        print("No libraries found.", file=sys.stderr)
        sys.exit(1)

    print("\nAvailable libraries:")
    for idx, lib in enumerate(libs, 1):
        print(f"{idx}. {lib['name']} (ID: {lib['id']})")

    choices = input("\nEnter comma-separated library numbers to process: ").split(',')
    chosen = []
    for c in choices:
        try:
            chosen.append(libs[int(c.strip())-1])
        except (ValueError, IndexError):
            continue
    if not chosen:
        print("No valid libraries selected.", file=sys.stderr)
        sys.exit(1)

    total = 0
    locked_count = 0
    skipped_count = 0

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
                print(f"  Skipping '{title}': selected fields already locked or empty.")
                skipped_count += 1

    print(f"\nProcessed {total} series: Locked {locked_count}, Skipped {skipped_count}.")

if __name__ == '__main__':
    main()
