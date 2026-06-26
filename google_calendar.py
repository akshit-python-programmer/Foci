import datetime
import os.path
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def resource_path(relative_path):
    """Get absolute path to resource (works for dev and .exe)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

CREDENTIALS_FILE = resource_path(os.path.join("assets", "credentials.json"))
TOKEN_FILE = resource_path(os.path.join("assets", "token.json"))


def get_service():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
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
    start_of_day = datetime.datetime.combine(date, datetime.time.min).isoformat() + "Z"
    end_of_day = datetime.datetime.combine(date, datetime.time.max).isoformat() + "Z"

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
            # New event from Google, add it locally
            try:
                start = gcal_event["start"].get("dateTime", gcal_event["start"].get("date"))
                end = gcal_event["end"].get("dateTime", gcal_event["end"].get("date"))
                
                start_dt = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
                end_dt = datetime.datetime.fromisoformat(end.replace("Z", "+00:00"))

                duration = int((end_dt - start_dt).total_seconds() / 60)

                new_local_event = {
                    "title": gcal_event.get("summary", "No Title"),
                    "hour": start_dt.hour,
                    "minute": start_dt.minute,
                    "duration": duration,
                    "done": False,
                    "color": [135, 206, 250], # Default color for synced events
                    "icon": 0,
                    "google_id": gcal_id,
                }
                synced_events.append(new_local_event)
            except Exception as e:
                print(f"Error parsing Google event '{gcal_event.get('summary')}': {e}")

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