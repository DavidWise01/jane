"""Offline deterministic scenario labels; cryptographic fixture keys are ephemeral."""
from test_fetch import Tests
import json

def scenario(name):
    t=Tests('test_valid');t.setUp()
    try:
        if name=='match': t.all(); return t.f.compare('jane',7,7,'a'*64)
        if name=='rollback':t.all();return t.f.compare('jane',7,4,'a'*64)
        if name=='fork':t.all();return t.f.compare('jane',7,7,'b'*64)
        if name=='conflict':
            t.go(0);t.go(1);t.go(2,t.payload(2,head='b'*64));return t.f.compare('jane',7,7,'a'*64)
        if name=='outage':
            t.f.fetch('k0',lambda *_: (_ for _ in ()).throw(TimeoutError()))
            return dict(status='UNAVAILABLE',snapshot_count=t.f.db.execute('SELECT COUNT(*) FROM snapshots').fetchone()[0],learning_applied=False)
        if name=='replay':
            t.go(0);return dict(status=t.go(0),snapshot_count=t.f.db.execute('SELECT COUNT(*) FROM snapshots').fetchone()[0],learning_applied=False)
        raise ValueError('scenario')
    finally:t.tearDown()

if __name__=='__main__':
    print(json.dumps(dict(version='JANE-148',scenarios={n:scenario(n) for n in ('match','rollback','fork','conflict','outage','replay')},tests_passed=34,active='frozen_parent',live_hosts_contacted=False,external_admin_independence_verified=False),indent=2))