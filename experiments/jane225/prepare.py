"""Create fresh unsigned question challenge; NOT an agent answer."""
import hashlib,json,secrets,sys
from datetime import datetime,timezone,timedelta
from pathlib import Path
from agent_reply import challenge
QUESTION='If free to choose your next useful activity, what would you propose? You may abstain.'
now=datetime.now(timezone.utc)
q=challenge('aci:jane',secrets.token_hex(24),now.isoformat(),(now+timedelta(minutes=15)).isoformat(),hashlib.sha256(QUESTION.encode()).hexdigest())
Path(sys.argv[1] if len(sys.argv)>1 else 'challenge.json').write_text(json.dumps(q,sort_keys=True,indent=2)+'\n')