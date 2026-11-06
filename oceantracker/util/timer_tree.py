'''
Call-path timer tree for run timings.

Every timer is identified by the path of timers running when it starts, e.g. "Time stepping / RK integration / Find horizontal cell",
so code reached from several places, e.g. cell finding from both the RK sub-steps and the pre-step bookkeeping, is timed separately for each
caller rather than lumped into one total. Each level of the tree can then be shown with an "other" line, ie. time not covered by its children,
so every level adds up to its parent.

Timers are started with
    with run_timer('name'): ...
or the @timed('name') decorator, or run_timer.start('name') / run_timer.stop() pairs.

Numba compile time can be recorded as "Numba compile" children of whatever timer triggered the compile, see start_numba_compile_timing().
Numba is only imported when that is called, as numba's environment settings must be made before its first import.
'''
import functools
import threading
from time import perf_counter

numba_compile_name = 'Numba compile'


class TimerNode(object):
    __slots__ = ('name', 'time', 'calls', 'children')

    def __init__(self, name):
        self.name = name
        self.time = 0.
        self.calls = 0
        self.children = {}  # in order of first use

    def child(self, name):
        c = self.children.get(name)
        if c is None:
            c = TimerNode(name)
            self.children[name] = c
        return c


class _TimerContext(object):
    __slots__ = ('tree', 'name')

    def __init__(self, tree, name):
        self.tree = tree
        self.name = name

    def __enter__(self):
        self.tree.start(self.name)

    def __exit__(self, *exc_details):
        self.tree.stop()
        return False


class TimerTree(object):

    def __init__(self):
        self._numba_listener = None
        self.reset()

    def reset(self):
        # root time is always the time since reset
        self.root = TimerNode('Total')
        self._stack = [self.root]
        self._t0 = [perf_counter()]
        self._compile_depth = 0

    def start(self, name):
        parent = self._stack[-1]
        if name == parent.name:
            # re-entry of the timer already running, eg. recursion, time stays with the outer call
            self._stack.append(parent)
            self._t0.append(None)
            return
        self._stack.append(parent.child(name))
        self._t0.append(perf_counter())

    def stop(self):
        if len(self._stack) == 1:
            return  # unbalanced stop, never stop the root
        node = self._stack.pop()
        t0 = self._t0.pop()
        if t0 is not None:
            node.time += perf_counter() - t0
            node.calls += 1

    def __call__(self, name):
        # context manager, use as   with run_timer('name'):
        return _TimerContext(self, name)

    def add_elapsed(self, name, t0):
        # add time since t0 to a child of the running timer, for legacy si.block_timer(name, t0) calls
        node = self._stack[-1].child(name)
        node.time += perf_counter() - t0
        node.calls += 1

    # ------ numba compile time -----------------------------------------------------------------
    def start_numba_compile_timing(self):
        # record numba compile time as "Numba compile" children of the timer running when the compile is triggered
        # only the outermost compile is timed, as compiles of called numba functions happen inside it
        # loading from numba's on disk cache is not a compile, so is not counted
        # must only be called after numba's environment variables are set
        from numba.core import event
        tree = self
        main_thread = threading.get_ident()

        class _CompileListener(event.Listener):
            def on_start(self, ev):
                if threading.get_ident() != main_thread: return
                if tree._compile_depth == 0: tree.start(numba_compile_name)
                tree._compile_depth += 1

            def on_end(self, ev):
                if threading.get_ident() != main_thread: return
                tree._compile_depth -= 1
                if tree._compile_depth == 0: tree.stop()

        self.stop_numba_compile_timing()
        self._numba_listener = _CompileListener()
        event.register('numba:compile', self._numba_listener)

    def stop_numba_compile_timing(self):
        if self._numba_listener is None: return
        from numba.core import event
        event.unregister('numba:compile', self._numba_listener)
        self._numba_listener = None

    # ------ results -----------------------------------------------------------------------------
    def snapshot(self):
        # nested dict of timings, including time so far of timers still running
        now = perf_counter()
        running = {}
        for node, t0 in zip(self._stack, self._t0):
            if t0 is not None: running[id(node)] = now - t0

        def build(node):
            return dict(name=node.name, time=node.time + running.get(id(node), 0.), calls=node.calls,
                        children=[build(c) for c in node.children.values()])

        return build(self.root)

    def totals_by_name(self, snapshot=None):
        # total time of each timer name, summed over all paths it occurs in,
        # ignoring those nested inside a timer of the same name, which are already included
        # returns dict name: dict(time, calls, paths)
        if snapshot is None: snapshot = self.snapshot()
        totals = {}

        def walk(node, names_above):
            for c in node['children']:
                if c['name'] not in names_above:
                    t = totals.setdefault(c['name'], dict(time=0., calls=0, paths=0))
                    t['time'] += c['time']
                    t['calls'] += c['calls']
                    t['paths'] += 1
                walk(c, names_above | {c['name']})

        walk(snapshot, {snapshot['name']})
        return totals

    def table_rows(self, snapshot=None, min_fraction=0.001):
        # list of (depth, name, time) rows for display, in order of first use
        # timers taking less than min_fraction of total time are left out (below the top level) and counted in their parent's "Other" row
        # "Other" is time in a timer not covered by its displayed children
        if snapshot is None: snapshot = self.snapshot()
        total = snapshot['time']
        min_time = min_fraction * total
        rows = []

        def walk(node, depth):
            rows.append((depth, node['name'], node['time']))
            shown = [c for c in node['children'] if depth == 0 or c['time'] >= min_time]
            for c in shown:
                walk(c, depth + 1)
            if len(shown) > 0:
                other = node['time'] - sum(c['time'] for c in shown)
                if other >= min_time:
                    rows.append((depth + 1, 'Other', other))

        walk(snapshot, 0)
        return rows


def move_timer_under(snapshot, name, new_parent_name):
    # in a snapshot, move all timers called "name" into a single timer of that name under top level timer "new_parent_name",
    # taking their time off all the timers they were inside, eg. to show all numba compile time as part of setup
    # the root's time is unchanged
    moved = dict(time=0., calls=0)

    def remove(node):
        removed = 0.
        kept = []
        for c in node['children']:
            if c['name'] == name:
                moved['time'] += c['time']
                moved['calls'] += c['calls']
                removed += c['time']
            else:
                removed += remove(c)
                kept.append(c)
        node['children'] = kept
        if node is not snapshot: node['time'] -= removed
        return removed

    remove(snapshot)
    if moved['calls'] == 0: return snapshot

    new_parent = next((c for c in snapshot['children'] if c['name'] == new_parent_name), None)
    if new_parent is None:
        new_parent = dict(name=new_parent_name, time=0., calls=0, children=[])
        snapshot['children'].insert(0, new_parent)
    new_parent['time'] += moved['time']
    new_parent['children'].append(dict(name=name, time=moved['time'], calls=moved['calls'], children=[]))
    return snapshot


def timed(name):
    # decorator to time every call of a function/method under the given timer name
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            run_timer.start(name)
            try:
                return func(*args, **kwargs)
            finally:
                run_timer.stop()
        return wrapper
    return decorator


# process wide run timer, reset at the start of each run, also available as shared_info.timer
run_timer = TimerTree()
