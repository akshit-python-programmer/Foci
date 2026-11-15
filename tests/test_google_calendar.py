import datetime

import google_calendar as gcal

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
PST = datetime.timezone(datetime.timedelta(hours=-8))


def test_day_bounds_use_local_offset_not_utc():
    start, end = gcal.local_day_bounds(datetime.date(2026, 3, 11), tz=IST)
    assert start == "2026-03-11T00:00:00+05:30"
    assert end == "2026-03-12T00:00:00+05:30"


def test_event_time_is_converted_to_local_timezone():
    ev = gcal.gcal_event_to_local(
        {
            "id": "abc",
            "summary": "Standup",
            "start": {"dateTime": "2026-03-11T17:00:00Z"},
            "end": {"dateTime": "2026-03-11T17:45:00Z"},
        },
        tz=PST,
    )
    assert (ev["hour"], ev["minute"], ev["duration"]) == (9, 0, 45)
    assert ev["google_id"] == "abc"
    assert ev["title"] == "Standup"


def test_offset_timestamps_are_handled():
    ev = gcal.gcal_event_to_local(
        {
            "id": "x",
            "start": {"dateTime": "2026-03-11T09:30:00+05:30"},
            "end": {"dateTime": "2026-03-11T10:00:00+05:30"},
        },
        tz=IST,
    )
    assert (ev["hour"], ev["minute"], ev["duration"]) == (9, 30, 30)
    assert ev["title"] == "No Title"


def test_all_day_and_malformed_events_are_skipped():
    all_day = {"id": "d", "start": {"date": "2026-03-11"}, "end": {"date": "2026-03-12"}}
    assert gcal.gcal_event_to_local(all_day, tz=IST) is None
    assert gcal.gcal_event_to_local({"id": "m"}, tz=IST) is None
    bad = {"id": "b", "start": {"dateTime": "soon"}, "end": {"dateTime": "later"}}
    assert gcal.gcal_event_to_local(bad, tz=IST) is None


def test_short_events_get_minimum_duration():
    ev = gcal.gcal_event_to_local(
        {"id": "s", "start": {"dateTime": "2026-03-11T09:00:00Z"}, "end": {"dateTime": "2026-03-11T09:05:00Z"}},
        tz=datetime.timezone.utc,
    )
    assert ev["duration"] == 15
