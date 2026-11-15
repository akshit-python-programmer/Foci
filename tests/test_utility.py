import utility


def test_format_time_basic():
    assert utility.format_time(0) == "00:00"
    assert utility.format_time(65) == "01:05"
    assert utility.format_time(-5) == "00:00"


def test_format_time_does_not_wrap_after_a_day():
    # timedelta.seconds drops whole days, so 25h used to render as "60:00"
    assert utility.format_time(25 * 3600) == "1500:00"


def test_clamp_and_lerp():
    assert utility.clamp(5, 0, 3) == 3
    assert utility.lerp_color((0, 0, 0), (100, 200, 50), 0.5) == (50, 100, 25)


def test_get_event_id_is_stable():
    ev = {"hour": 9, "minute": 30, "title": "Deep work"}
    assert utility.get_event_id(ev) == "9-30-Deep work"
    assert utility.get_event_id({"hour": 9, "title": "x"}) == "9-0-x"
