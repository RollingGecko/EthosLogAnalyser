# -*- coding: utf-8 -*-
"""Playback clock of the flight recorder (recorder/playback.py) with a wall clock the test moves."""

import pytest

from ethosloganalyser.recorder.playback import DEFAULT_SPEED, JUMP_S, SPEEDS, PlaybackClock


class FakeClock:
    """A wall clock that only moves when the test says so."""

    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return FakeClock()


ROWS = [0.0, 0.27, 0.54, 0.81, 1.08, 30.0, 60.0]


def test_the_position_follows_the_wall_clock_and_the_speed(clock):
    playback = PlaybackClock(ROWS, clock)
    assert playback.speed == DEFAULT_SPEED == 1 and not playback.running and playback.position == 0.0
    playback.play()
    clock.now += 0.5
    assert playback.position == pytest.approx(0.5) and playback.row == 1
    playback.set_speed(4)                                          # no jump when the speed changes
    assert playback.position == pytest.approx(0.5)
    clock.now += 1.0
    assert playback.position == pytest.approx(4.5) and playback.row == 4
    playback.stop()
    clock.now += 10
    assert playback.position == pytest.approx(4.5) and not playback.running
    assert SPEEDS == (0.25, 0.5, 1, 2, 4, 8, 16)
    with pytest.raises(ValueError):
        playback.set_speed(3)


def test_a_late_tick_does_not_slow_the_playback_down(clock):
    playback = PlaybackClock(ROWS, clock)
    playback.set_speed(0.25)
    playback.play()
    clock.now += 2.0                                               # one tick of 2 s instead of fifty of 40 ms
    assert playback.advance() == pytest.approx(0.5)


def test_seek_stays_inside_the_flight_and_keeps_running(clock):
    playback = PlaybackClock(ROWS, clock)
    playback.seek(-3)
    assert playback.position == 0.0
    playback.seek(1000)
    assert playback.position == 60.0 and playback.at_end
    playback.seek(20)
    playback.play()
    clock.now += 1
    playback.seek(40)                                              # dragging on the timeline while it plays
    assert playback.running and playback.position == 40.0
    clock.now += 2
    assert playback.position == pytest.approx(42.0)
    playback.jump(JUMP_S)
    assert playback.position == pytest.approx(52.0)
    playback.jump(-100)
    assert playback.position == 0.0


def test_row_steps_stop_the_playback_and_go_to_the_next_row(clock):
    playback = PlaybackClock(ROWS, clock)
    playback.play()
    clock.now += 0.6
    playback.step_rows(1)
    assert not playback.running and playback.row == 3 and playback.position == 0.81
    playback.step_rows(-2)
    assert playback.row == 1 and playback.position == 0.27
    playback.step_rows(-5)
    assert playback.row == 0
    playback.step_rows(50)
    assert playback.row == 6 and playback.at_end


def test_the_playback_stops_at_the_end_and_starts_again_from_the_beginning(clock):
    playback = PlaybackClock(ROWS, clock)
    playback.seek(59)
    playback.play()
    clock.now += 5
    assert playback.position == 60.0                               # not beyond the end
    playback.advance()
    assert not playback.running and playback.at_end and playback.row == 6
    playback.toggle()                                              # play at the end: from the beginning
    assert playback.running and playback.position == 0.0
    playback.toggle()
    assert not playback.running
    playback.go_to_end()
    assert playback.position == 60.0 and not playback.running
    playback.go_to_start()
    assert playback.position == 0.0


def test_a_clock_without_rows():
    playback = PlaybackClock([])
    playback.play()
    playback.advance()
    assert playback.position == 0.0 and playback.row == 0 and not playback.running
    playback.step_rows(1)
    assert playback.row == 0
