import csv
import getpass
import os
import time
import requests
import sys

NETWORK = "di"
BASE = "https://api.audioaddict.com/v1"

def app_dir():
    # If packaged by PyInstaller, sys.executable is the path to the .exe
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # Running as a .py script
    return os.path.dirname(os.path.abspath(__file__))

CSV_FILE = os.path.join(app_dir(), "di_likes.csv")

FIELDNAMES = ["TrackID", "Artist", "Track", "Source", "Duration", "Liked"]

def write_full_csv(path: str, rows: list[list]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(FIELDNAMES)
        w.writerows(rows)


def login(username: str, password: str):
    url = f"{BASE}/{NETWORK}/member_sessions"
    payload = {"member_session": {"username": username, "password": password}}
    r = requests.post(url, json=payload, auth=("streams", "diradio"), timeout=30)
    r.raise_for_status()
    data = r.json()

    session_key = data["key"]
    member = data.get("member", {})
    member_id = member.get("id") or member.get("member_id")
    if not member_id:
        raise RuntimeError("Login succeeded but member id was not found in response.")
    return session_key, str(member_id)

def fetch_votes(session_key: str, member_id: str, per_page: int = 200):
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
        
    }

    rows = []
    page = 1
    while True:
        url = f"{BASE}/{NETWORK}/members/{member_id}/track_votes"
        params = {"vote_type": "up", "page": page, "per_page": per_page}
        r = requests.get(url, headers=headers, params=params, timeout=30)
        r.raise_for_status()
        payload = r.json()

        if isinstance(payload, list):
            items = payload
        else:
            items = (
                payload.get("track_votes")
                or payload.get("votes")
                or payload.get("items")
                or payload.get("data")
                or []
            )

        if not items:
            break

        for vote in items:
            track = vote.get("track") or vote.get("resource") or vote
            track_id = track.get("id")
            artist = (track.get("artist") or {}).get("name")
            title = track.get("title") or track.get("name")
            duration = track.get("duration")
            source = (track.get("channel") or {}).get("name") or track.get("channel_name")
            liked_at = vote.get("created_at") or vote.get("voted_at") or vote.get("liked_at")

            rows.append([track_id, artist, title, source, duration, liked_at])

        print(f"page {page}: +{len(items)} (total {len(rows)})")
        page += 1
        time.sleep(0.15)

    return rows



def fetch_new_votes_until_overlap(session_key: str, member_id: str, existing_ids: set[str], per_page: int = 200, max_pages: int = 5):
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
        "X-Session-Key": session_key,
    }

    new_rows = []
    page = 1

    while page <= max_pages:
        url = f"{BASE}/{NETWORK}/members/{member_id}/track_votes"
        params = {"vote_type": "up", "page": page, "per_page": per_page}
        r = requests.get(url, headers=headers, params=params, timeout=30)
        r.raise_for_status()
        payload = r.json()

        if isinstance(payload, list):
            items = payload
        else:
            items = (
                payload.get("track_votes")
                or payload.get("votes")
                or payload.get("items")
                or payload.get("data")
                or []
            )

        if not items:
            break

        for vote in items:
            track = vote.get("track") or vote.get("resource") or vote
            track_id = track.get("id")
            tid = str(track_id) if track_id is not None else None

            # If we hit something we already have, we can stop (assuming newest-first)
            if tid and tid in existing_ids:
                return new_rows  # stop scanning; older pages won't contain new items

            artist = (track.get("artist") or {}).get("name")
            title = track.get("title") or track.get("name")
            duration = track.get("duration")
            source = (track.get("channel") or {}).get("name") or track.get("channel_name")
            liked_at = vote.get("created_at") or vote.get("voted_at") or vote.get("liked_at")

            new_rows.append([track_id, artist, title, source, duration, liked_at])

        page += 1
        time.sleep(0.15)

    return new_rows



def load_existing_track_ids(path: str) -> set[str]:
    ids: set[str] = set()
    if not os.path.exists(path):
        return ids

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # If the file was created with the old header (no TrackID), we can't de-dupe by ID.
        # In that case, we return empty and the script will rewrite cleanly on next step below.
        if not reader.fieldnames or "TrackID" not in reader.fieldnames:
            return set()

        for row in reader:
            tid = (row.get("TrackID") or "").strip()
            if tid:
                ids.add(tid)
    return ids


def prepend_new_rows(path: str, new_rows: list[list]):
    """
    new_rows items are: [track_id, artist, title, source, duration, liked_at]
    Writes newest-first by putting new rows at the top of the CSV.
    """
    if not new_rows:
        print("No new likes.")
        return

    existing_rows = []
    existing_ids = set()

    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            # If file is old-format, just rewrite it cleanly with new-format rows
            if not r.fieldnames or "TrackID" not in r.fieldnames:
                print("Existing CSV is old-format (no TrackID). Rewriting to new format...")
            else:
                for row in r:
                    tid = (row.get("TrackID") or "").strip()
                    if tid:
                        existing_ids.add(tid)
                    existing_rows.append([
                        row.get("TrackID"),
                        row.get("Artist"),
                        row.get("Track"),
                        row.get("Source"),
                        row.get("Duration"),
                        row.get("Liked"),
                    ])

    # Filter out any accidental duplicates in new_rows
    filtered_new = []
    for track_id, artist, title, source, duration, liked_at in new_rows:
        tid = str(track_id) if track_id is not None else ""
        if tid and tid in existing_ids:
            continue
        if tid:
            existing_ids.add(tid)
        filtered_new.append([track_id, artist, title, source, duration, liked_at])

    if not filtered_new:
        print("No new likes (all already present).")
        return

    # Write: new rows first, then existing rows
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(FIELDNAMES)
        w.writerows(filtered_new)
        w.writerows(existing_rows)

    print(f"Prepended {len(filtered_new)} new likes to {path}")


def main():
    username = input("DI.fm email/username: ").strip()
    password = getpass.getpass("DI.fm password: ")

    session_key, member_id = login(username, password)
    print(f"Logged in. member_id={member_id}")

    # Load existing tracks from CSV
    existing_ids = load_existing_track_ids(CSV_FILE)

    # Only scan newest pages until overlap is found
    new_rows = fetch_new_votes_until_overlap(
        session_key,
        member_id,
        existing_ids=existing_ids,
        per_page=200,
        max_pages=3
    )

    prepend_new_rows(CSV_FILE, new_rows)



if __name__ == "__main__":
    main()
