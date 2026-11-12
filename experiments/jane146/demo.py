"""Run a deterministic-shaped, cryptographically signed fixture with ephemeral keys."""
import json
import tempfile
from datetime import timedelta
from pathlib import Path
from hashlib import sha256
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from enrollment import Enrollment,Authority,CHRONOS,canonical,utc

def public(k):
 return k.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)

def run():
 with tempfile.TemporaryDirectory() as d:
  keys=[Ed25519PrivateKey.generate() for _ in range(3)]
  witness=Ed25519PrivateKey.generate()
  new=Ed25519PrivateKey.generate()
  registry={f'a{i}':Authority(f'a{i}',public(keys[i]),f'attestor:{i}') for i in range(3)}
  e=Enrollment(Path(d)/'db.sqlite',Path(d)/'external-fixture-anchor.json',registry)
  now=utc(CHRONOS,-360);nonce='demo-challenge-nonce-00001'
  challenge=e.challenge(nonce,'operator:demo','external:demo',public(witness),CHRONOS,-360,now)
  body=dict(domain='JANE-146-ENROLL',nonce=nonce,key_id='k0',operator='operator:demo',root='external:demo',public_sha256=sha256(public(witness)).hexdigest(),chronos=CHRONOS,utc_offset=-360)
  approvals=[(f'a{i}',keys[i].sign(canonical(dict(domain='JANE-146-APPROVE',binding=body,authority=f'a{i}')))) for i in (0,1)]
  enrollment=e.enroll(nonce,'k0',witness.sign(canonical(body)),approvals,now)
  rotation=dict(domain='JANE-146-ROTATE',root='external:demo',old_key='k0',new_key='k1',new_public_sha256=sha256(public(new)).hexdigest(),generation=1,nonce='demo-rotation-nonce-00001',chronos=CHRONOS,utc_offset=-360)
  rotated=e.rotate('external:demo','k1',public(new),rotation['nonce'],CHRONOS,-360,witness.sign(canonical(rotation)),now)
  checkpoint=e.export_anchor()
  report=e.report()
  e.db.close()
  return dict(version='JANE-146',chronos=CHRONOS,challenge=challenge,enrollment=enrollment,rotation=rotated,checkpoint=checkpoint,report=report,fixture_only=True,
              note='Ephemeral local test keys; no external operators contacted')

if __name__=='__main__':print(json.dumps(run(),indent=2))