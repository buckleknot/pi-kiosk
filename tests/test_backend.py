from pi_kiosk.backend import Backend, process_memory_mb


def test_increment_emits_and_counts(qtbot):
    b = Backend()
    with qtbot.waitSignal(b.counterChanged, timeout=500):
        b.increment()
    assert b.counter == 1


def test_reset(qtbot):
    b = Backend()
    b.increment()
    b.increment()
    b.reset()
    assert b.counter == 0


def test_clock_is_populated(qtbot):
    b = Backend()
    assert len(b.time) == 8  # HH:MM:SS


def test_memory_reading_is_non_negative():
    assert process_memory_mb() >= 0
