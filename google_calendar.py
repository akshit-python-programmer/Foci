"""Optional Google Calendar sync for Foci (experimental, not yet wired into the UI).

Needs the extra dependencies from requirements.txt and a ``credentials.json``
OAuth client file in the Foci data directory (``assets/`` when running from
source).  The pure conversion helpers at the top of this module work without
the Google libraries installed, which keeps them unit-testable.
"""

import datetime
import os.path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:  # optional dependency
    GOOGLE_LIBS_AVAILABLE = False

    class HttpError(Exception):
        pass

# If modifying these scopes, delete token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

from foci_store import user_data_dir

# Both files are per-user secrets, so they live in the writable data directory
# (assets/ when running from source) rather than inside the bundled app.
CREDENTIALS_FILE = os.path.join(user_data_dir(), "credentials.json")
TOKEN_FILE = os.path.join(user_data_dir(), "token.json")

SYNCED_EVENT_COLOR = [135, 206, 250]


def local_day_bounds(date, tz=None):
    """RFC 3339 start/end of ``date`` in the user's local timezone.

    The previous version appended "Z" to a naive local midnight, which told
    Google the day started at 00:00 UTC and returned the wrong events for
    anyone not in UTC.
    """
    tz = tz or datetime.datetime.now().astimezone().tzinfo
    start = datetime.datetime.combine(date, datetime.time.min, tzinfo=tz)
    end = start + datetime.timedelta(days=1)
    return start.isoformat(), end.isoformat()


def _parse_rfc3339(value):
    # Python < 3.11 fromisoformat() does not accept a trailing "Z".
    return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))


def gcal_event_to_local(gcal_event, tz=None):
    """Convert a Google Calendar API event into a Foci event dict.

    Returns ``None`` for all-day events (they have no time slot on the
    timeline) and for events without usable start/end times.
    Times are converted to the local timezone before taking hour/minute.
    """
    start = (gcal_event.get("start") or {}).get("dateTime")
    end = (gcal_event.get("end") or {}).get("dateTime")
    if not start or not end:
        return None  # all-day ("date") or malformed event

    tz = tz or datetime.datetime.now().astimezone().tzinfo
    try:
        start_dt = _parse_rfc3339(start).astimezone(tz)
        end_dt = _parse_rfc3339(end).astimezone(tz)
    except ValueError:
        return None

    duration = max(15, int((end_dt - start_dt).total_seconds() // 60))
    return {
        "title": gcal_event.get("summary") or "No Title",
        "hour": start_dt.hour,
        "minute": start_dt.minute,
        "duration": duration,
        "done": False,
        "color": list(SYNCED_EVENT_COLOR),
        "icon": 0,
        "google_id": gcal_event.get("id"),
    }


def get_service():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    if not GOOGLE_LIBS_AVAILABLE:
        print("Google Calendar sync needs: pip install google-api-python-client google-auth-oauthlib")
        return None
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                # If refresh fails, force re-login
                creds = None
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                # Note: This will open a browser window for authentication.
                # For a Pygame app, you might need to handle this more gracefully,
                # perhaps by running the first sync from a command line.
                creds = flow.run_local_server(port=0)
            except FileNotFoundError:
                print("ERROR: credentials.json not found. Please download it from Google Cloud Console and place it in the 'assets' directory.")
                return None
            except Exception as e:
                print(f"An error occurred during authentication: {e}")
                return None
        # Save the credentials for the next run
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred building the service: {error}")
        return None


def sync_events(date, local_events):
    """
    Performs a two-way sync between local events and Google Calendar for a specific date.
    Returns the synchronized list of events for that date.
    """
    service = get_service()
    if not service:
        print("Could not connect to Google Calendar.")
        return local_events # Return local events if sync fails

    # --- 1. Fetch Google Calendar events for the day ---
    start_of_day, end_of_day = local_day_bounds(date)

    try:
        gcal_events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_of_day,
                timeMax=end_of_day,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        gcal_events = gcal_events_result.get("items", [])
    except HttpError as e:
        print(f"Error fetching Google Calendar events: {e}")
        return local_events

    # --- 2. Create maps for efficient lookup ---
    gcal_map = {item["id"]: item for item in gcal_events}
    local_map = {
        event["google_id"]: event for event in local_events if "google_id" in event
    }

    synced_events = []
    processed_gcal_ids = set()

    # --- 3. Sync from Local to Google (Update/Create) ---
    for local_event in local_events:
        google_id = local_event.get("google_id")
        if google_id and google_id in gcal_map:
            # Event exists in both, check for updates
            # A simple check: if local event is different, update Google
            # A more robust system would use timestamps.
            # For now, we assume local is master for updates.
            # TODO: Add timestamp-based update logic
            processed_gcal_ids.add(google_id)
            synced_events.append(local_event) # Keep the local version
        elif not google_id:
            # New local event, create it on Google Calendar
            # TODO: Implement create_event_on_gcal
            print(f"TODO: Create '{local_event['title']}' on Google Calendar.")
            synced_events.append(local_event) # Add to list, will get google_id later

    # --- 4. Sync from Google to Local (Add new events from Google) ---
    for gcal_id, gcal_event in gcal_map.items():
        if gcal_id not in local_map:
            # New event from Google, add it locally (all-day events are skipped)
            new_local_event = gcal_event_to_local(gcal_event)
            if new_local_event is not None:
                synced_events.append(new_local_event)

    # --- 5. Handle Deletions ---
    # If a local event with a google_id is no longer in gcal_map, it was deleted on Google.
    # For now, we'll just remove it from our synced list.
    final_events = []
    for event in synced_events:
        gid = event.get("google_id")
        if gid and gid not in gcal_map:
            print(f"Event '{event['title']}' was deleted from Google Calendar. Removing locally.")
            continue
        final_events.append(event)

    # If an event from gcal_map was not processed, it means it was deleted locally.
    for gcal_id in gcal_map:
        if gcal_id not in processed_gcal_ids and gcal_id not in [e.get('google_id') for e in final_events]:
            # TODO: Implement delete_event_on_gcal
            print(f"TODO: Delete event with ID {gcal_id} from Google Calendar.")

    # Sort events by time before returning
    final_events.sort(key=lambda e: (e["hour"], e.get("minute", 0)))
    
    return final_events

#### `c:\Users\Akshit lal\Documents\Focus\tt\main.py`