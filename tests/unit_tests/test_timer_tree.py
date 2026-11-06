from time import sleep

import pytest

from oceantracker.util.timer_tree import TimerTree, numba_compile_name


def _child(node, name):
    return next(c for c in node['children'] if c['name'] == name)


def test_same_timer_under_two_parents_is_kept_separate():
    t = TimerTree()
    with t('A'):
        with t('find'): sleep(0.02)
    with t('B'):
        with t('find'): sleep(0.01)

    s = t.snapshot()
    a_find = _child(_child(s, 'A'), 'find')['time']
    b_find = _child(_child(s, 'B'), 'find')['time']
    assert a_find > b_find > 0.

    totals = t.totals_by_name(s)
    assert totals['find']['paths'] == 2
    assert totals['find']['calls'] == 2
    assert totals['find']['time'] == pytest.approx(a_find + b_find)


def test_reentry_of_running_timer_is_not_double_counted():
    t = TimerTree()
    with t('A'):
        with t('A'): sleep(0.01)

    s = t.snapshot()
    a = _child(s, 'A')
    assert a['children'] == [] and a['calls'] == 1
    assert t.totals_by_name(s)['A']['time'] == pytest.approx(a['time'])


def test_rows_add_up_with_other():
    t = TimerTree()
    with t('A'):
        sleep(0.02)  # becomes "Other"
        with t('child'): sleep(0.02)

    rows = t.table_rows(min_fraction=0.)
    names = [(depth, name) for depth, name, _ in rows]
    assert names[:4] == [(0, 'Total'), (1, 'A'), (2, 'child'), (2, 'Other')]
    a, child, other = rows[1][2], rows[2][2], rows[3][2]
    assert child + other == pytest.approx(a)


def test_snapshot_includes_running_timers():
    t = TimerTree()
    t.start('running')
    sleep(0.01)
    assert _child(t.snapshot(), 'running')['time'] >= 0.01
    t.stop()


def test_numba_compile_is_timed_under_the_caller():
    import numba
    import numpy as np

    t = TimerTree()
    t.start_numba_compile_timing()
    try:
        @numba.njit
        def inner(x): return 2. * x

        @numba.njit
        def outer(a):
            s = 0.
            for i in range(a.size): s += inner(a[i])
            return s

        with t('first call'):
            outer(np.ones(3))
        with t('second call'):
            outer(np.ones(3))
    finally:
        t.stop_numba_compile_timing()

    s = t.snapshot()
    first = _child(s, 'first call')
    compile_node = _child(first, numba_compile_name)
    assert compile_node['calls'] == 1  # inner compiles inside outer's compile, counted once
    assert 0. < compile_node['time'] <= first['time']
    assert _child(s, 'second call')['children'] == []


def test_move_timer_under_takes_time_off_old_parents():
    from oceantracker.util.timer_tree import move_timer_under
    leaf = lambda name, time: dict(name=name, time=time, calls=1, children=[])
    s = dict(name='Total', time=10., calls=0, children=[
        dict(name='Setup', time=1., calls=1, children=[]),
        dict(name='Run', time=8., calls=1, children=[
            dict(name='step', time=5., calls=1, children=[leaf('compile', 2.)]),
            leaf('compile', 1.)])])

    move_timer_under(s, 'compile', 'Setup')

    setup, run = s['children']
    assert s['time'] == 10.
    assert setup['time'] == 4. and setup['children'] == [dict(name='compile', time=3., calls=2, children=[])]
    assert run['time'] == 5. and run['children'][0]['time'] == 3. and run['children'][0]['children'] == []
