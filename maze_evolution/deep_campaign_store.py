"""Single-writer, transactional search journal; completed task receipts survive resume.

SQLite FULL/WAL commits seal inputs before inference and atomically publish decisions
with RNG/population state. Interrupted tasks retain conservative resource reservations.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import sqlite3
import zlib


def packed(value):
    return zlib.compress(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                   allow_nan=False).encode(), 1)


def unpacked(blob):
    return json.loads(zlib.decompress(blob))


def hashed(blob):
    return hashlib.sha256(blob).hexdigest()


@contextmanager
def writer_lock(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / 'writer.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


class Journal:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.db = sqlite3.connect(self.directory / 'campaign.sqlite')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value BLOB NOT NULL);
        CREATE TABLE IF NOT EXISTS layouts(hash TEXT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS stages(
          n INTEGER PRIMARY KEY, kind TEXT, generation INTEGER, input BLOB,
          input_hash TEXT, decision BLOB, chain_hash TEXT, state_hash TEXT,
          complete INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS tasks(
          stage INTEGER, n INTEGER, spec BLOB, status TEXT DEFAULT 'new',
          result BLOB, result_hash TEXT, attempts INTEGER DEFAULT 0,
          PRIMARY KEY(stage,n));
        CREATE TABLE IF NOT EXISTS states(stage INTEGER PRIMARY KEY, value BLOB, hash TEXT);
        """)

    def get(self, key):
        r = self.db.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
        return unpacked(r[0]) if r else None

    def put(self, key, value):
        self.db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', (key, packed(value)))

    def initialize(self, config, states, previous):
        blob = packed(states)
        layout_hash = hashed(packed(sorted(previous)))
        if self.get('config') is not None:
            if self.get('config') != config:
                raise ValueError('Frozen campaign configuration differs')
            initial = self.db.execute('SELECT value,hash FROM states WHERE stage=-1').fetchone()
            if initial != (blob, hashed(blob)) or self.get('initial_layout_hash') != layout_hash:
                raise ValueError('Initial population/RNG or exclusion corpus differs')
            return
        with self.db:
            self.put('config', config)
            self.put('initial_layout_hash', layout_hash)
            self.put('latest', -1)
            self.put('usage', dict(calls=0, work=0, cpu_seconds=0., candidate_seconds=0.,
                                   receipts=0, uncertain_attempts=0))
            self.db.execute('INSERT INTO states VALUES (-1,?,?)', (blob, hashed(blob)))
            self.db.executemany('INSERT INTO layouts VALUES (?)', ((h,) for h in sorted(previous)))

    def state(self):
        latest = self.get('latest')
        blob, h = self.db.execute('SELECT value,hash FROM states WHERE stage=?', (latest,)).fetchone()
        if hashed(blob) != h:
            raise ValueError('Population checkpoint hash mismatch')
        return unpacked(blob)

    def layouts(self):
        return {r[0] for r in self.db.execute('SELECT hash FROM layouts')}

    def pending(self):
        r = self.db.execute('SELECT n,input,input_hash FROM stages WHERE complete=0').fetchall()
        if len(r) > 1:
            raise ValueError('Multiple pending generations')
        if not r:
            return None
        n, blob, h = r[0]
        if hashed(blob) != h:
            raise ValueError('Pending input hash mismatch')
        return n, unpacked(blob)

    def prepare(self, data, tasks):
        assert self.pending() is None
        n = self.get('latest') + 1
        blob = packed(data)
        with self.db:
            self.db.execute('INSERT INTO stages(n,kind,generation,input,input_hash) VALUES (?,?,?,?,?)',
                            (n, data['kind'], data['generation'], blob, hashed(blob)))
            self.db.executemany('INSERT INTO tasks(stage,n,spec) VALUES (?,?,?)',
                                ((n, k, packed(task)) for k, task in enumerate(tasks)))
            self.db.executemany('INSERT INTO layouts VALUES (?)',
                                ((h,) for h in data['new_layouts']))
        return n

    def tasks(self, n):
        return [(k, unpacked(spec), status) for k, spec, status in
                self.db.execute('SELECT n,spec,status FROM tasks WHERE stage=? ORDER BY n', (n,))]

    def reserve(self, n, k, calls, work):
        status = self.db.execute('SELECT status FROM tasks WHERE stage=? AND n=?', (n, k)).fetchone()[0]
        if status == 'done':
            raise ValueError('Cannot rerun committed receipt')
        usage = self.get('usage')
        if status == 'started':
            usage['uncertain_attempts'] += 1
        usage['calls'] += calls
        usage['work'] += work
        with self.db:
            self.put('usage', usage)
            self.db.execute("UPDATE tasks SET status='started',attempts=attempts+1 WHERE stage=? AND n=?",
                            (n, k))

    def receipt(self, n, k, result, reserved_work):
        blob = packed(result)
        usage = self.get('usage')
        usage['work'] += result['work'] - reserved_work
        assert result['work'] <= reserved_work
        usage['cpu_seconds'] += result['cpu_seconds']
        usage['candidate_seconds'] += result['candidate_seconds']
        usage['receipts'] += 1
        with self.db:
            self.put('usage', usage)
            self.db.execute("UPDATE tasks SET status='done',result=?,result_hash=? WHERE stage=? AND n=?",
                            (blob, hashed(blob), n, k))

    def results(self, n):
        result = []
        for status, blob, h in self.db.execute(
                'SELECT status,result,result_hash FROM tasks WHERE stage=? ORDER BY n', (n,)):
            if status != 'done' or hashed(blob) != h:
                raise ValueError('Incomplete or corrupt receipt')
            result.append(unpacked(blob))
        return result

    def commit(self, n, states, decisions):
        self.results(n)
        assert n == self.get('latest') + 1
        state_blob, decision = packed(states), packed(decisions)
        inp = self.db.execute('SELECT input_hash FROM stages WHERE n=?', (n,)).fetchone()[0]
        hashes = [r[0] for r in self.db.execute(
            'SELECT result_hash FROM tasks WHERE stage=? ORDER BY n', (n,))]
        previous = (self.db.execute('SELECT chain_hash FROM stages WHERE n=?', (n-1,)).fetchone()[0]
                    if n else self.db.execute('SELECT hash FROM states WHERE stage=-1').fetchone()[0])
        chain = hashed(packed([previous, inp, hashes, hashed(state_blob), hashed(decision)]))
        with self.db:
            self.db.execute('INSERT INTO states VALUES (?,?,?)', (n, state_blob, hashed(state_blob)))
            self.db.execute('UPDATE stages SET decision=?,chain_hash=?,state_hash=?,complete=1 WHERE n=?',
                            (decision, chain, hashed(state_blob), n))
            old = self.get('latest')
            self.put('latest', n)
            # Retain every assessment, every 100-round checkpoint, initial and latest.
            if old >= 0:
                kind, g = self.db.execute('SELECT kind,generation FROM stages WHERE n=?', (old,)).fetchone()
                if kind == 'train' and (g + 1) % 100:
                    self.db.execute('DELETE FROM states WHERE stage=?', (old,))
        self.db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        return chain

    def verify_chain(self):
        """Verify all sealed bytes, without claiming a second inference implementation."""
        previous = self.db.execute('SELECT hash FROM states WHERE stage=-1').fetchone()[0]
        for n, inp, ih, decision, chain, sh in self.db.execute(
                'SELECT n,input,input_hash,decision,chain_hash,state_hash FROM stages WHERE complete=1 ORDER BY n'):
            assert hashed(inp) == ih
            hashes = []
            for blob, h in self.db.execute('SELECT result,result_hash FROM tasks WHERE stage=? ORDER BY n', (n,)):
                assert hashed(blob) == h
                hashes.append(h)
            assert chain == hashed(packed([previous, ih, hashes, sh, hashed(decision)]))
            previous = chain
        for blob, h in self.db.execute('SELECT value,hash FROM states'):
            assert hashed(blob) == h
        return previous

    def close(self):
        self.db.close()
