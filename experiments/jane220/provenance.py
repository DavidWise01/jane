"""JANE 220 — signing authority is not genuine hardware provenance; synthetic evidence only."""
import hashlib, json, sqlite3
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

def canon(v): return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def sha(v): return hashlib.sha256(canon(v)).hexdigest()
def key(name): return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(('JANE220-FIXTURE/'+name).encode()).digest())
def pub(name): return key(name).public_key().public_bytes_raw().hex()
def sign(body,name): return {'body':body,'signature':key(name).sign(canon(body)).hex()}
def verify(s,p):
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(p)).verify(bytes.fromhex(s['signature']),canon(s['body']))
        return True
    except (KeyError,TypeError,ValueError,InvalidSignature,AttributeError): return False

class FLAY220:
    def __init__(self,path=':memory:'):
        self.db=sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, nonce TEXT UNIQUE, verdict TEXT, prev TEXT, head TEXT)')
        self.db.commit()
    def close(self):
        if self.db is not None:self.db.close();self.db=None
    def __del__(self):self.close()
    def log_ok(self):
        prev='0'*64
        for seq,nonce,v,stored,head in self.db.execute('SELECT seq,nonce,verdict,prev,head FROM events ORDER BY seq'):
            if stored!=prev or sha([seq,nonce,v,prev])!=head:return False
            prev=head
        return True
    def record(self,nonce,verdict,**extra):
        if not isinstance(nonce,str) or len(nonce)<8 or len(nonce)>128:return {'verdict':'INVALID_NONCE'}
        if not self.log_ok():return {'verdict':'CORRUPT_LOG'}
        if self.db.execute('SELECT 1 FROM events WHERE nonce=?',(nonce,)).fetchone():return {'verdict':'REPLAY_CHALLENGE'}
        seq=self.db.execute('SELECT COALESCE(MAX(seq),0)+1 FROM events').fetchone()[0]
        row=self.db.execute('SELECT head FROM events ORDER BY seq DESC LIMIT 1').fetchone(); prev=row[0] if row else '0'*64
        self.db.execute('INSERT INTO events VALUES(?,?,?,?,?)',(seq,nonce,verdict,prev,sha([seq,nonce,verdict,prev])))
        self.db.commit()
        return {'verdict':verdict,'nonce':nonce,'sequence':seq,**extra}
    def audit(self,challenge,manufactures,transfers,enrollments,acquisitions,revocations=()):
        try:return self._audit(challenge,manufactures,transfers,enrollments,acquisitions,revocations)
        except (KeyError,TypeError,ValueError,IndexError,OverflowError):
            try:return self.record(challenge['body']['nonce'],'MALFORMED_EVIDENCE')
            except (KeyError,TypeError):return {'verdict':'MALFORMED_EVIDENCE'}
    def _audit(self,c,m,t,e,a,r):
        cb=c['body'];nonce=cb['nonce']
        if not verify(c,pub('challenger')):return self.record(nonce,'INVALID_CHALLENGE_SIGNATURE')
        if not(cb['freeze']<cb['release']<cb['deadline']):return self.record(nonce,'INVALID_CHRONOLOGY')
        for obj in (m,t,e,a,r):
            if not isinstance(obj,(list,tuple)):raise ValueError()
        if not m or not e or not a:return self.record(nonce,'INSUFFICIENT_PROVENANCE')
        manufacturers={}; device_claims={}
        for item in m:
            b=item['body'];dev=b['device']
            if dev in manufacturers:return self.record(nonce,'DUPLICATE_DEVICE')
            if b['issuer']!='manufacturer' or not verify(item,pub('manufacturer')):return self.record(nonce,'UNTRUSTED_MANUFACTURER_CLAIM')
            if b['batch'] in device_claims:return self.record(nonce,'DUPLICATE_BATCH')
            device_claims[b['batch']]=dev
            manufacturers[dev]=b
        transfers={d:[] for d in manufacturers}
        for item in t:
            b=item['body'];dev=b['device']
            if dev not in manufacturers:return self.record(nonce,'MISSING_MANUFACTURING_CLAIM')
            if not verify(item,pub(b['from'])):return self.record(nonce,'INVALID_CUSTODY_TRANSFER')
            transfers[dev].append(b)
        enrolled={}
        for item in e:
            b=item['body'];dev=b['device']
            if dev in enrolled:return self.record(nonce,'DUPLICATE_ENROLLMENT')
            if b['issuer']!='enrollment-authority' or not verify(item,pub('enrollment-authority')):return self.record(nonce,'INVALID_ENROLLMENT_ISSUER')
            enrolled[dev]=b
        revoked=set()
        for item in r:
            b=item['body']
            if b['issuer']!='revocation-authority' or not verify(item,pub('revocation-authority')):return self.record(nonce,'INVALID_REVOCATION')
            if b['device'] in revoked:return self.record(nonce,'DUPLICATE_REVOCATION')
            revoked.add(b['device'])
        sensors=set();operators=set();services=set();roots=set();captures=set()
        for item in a:
            b=item['body'];dev=b['device']
            if dev not in enrolled:return self.record(nonce,'SELF_DECLARED_DEVICE')
            en=enrolled[dev]
            if not verify(item,en['public_key']):return self.record(nonce,'DEVICE_SIGNATURE_INVALID')
            if dev in revoked:return self.record(nonce,'REVOKED_DEVICE')
            if dev not in manufacturers:return self.record(nonce,'MISSING_MANUFACTURING_CLAIM')
            mf=manufacturers[dev]
            if mf['public_key']!=en['public_key'] or mf['batch']!=en['batch'] or mf['hardware_model']!=en['hardware_model']:
                return self.record(nonce,'MANUFACTURING_ENROLLMENT_MISMATCH')
            chain=sorted(transfers[dev],key=lambda x:x['time'])
            if not chain:return self.record(nonce,'MISSING_CUSTODY_CHAIN')
            holder='manufacturer';last=mf['time'];seen={holder}
            for step in chain:
                if step['from']!=holder or step['time']<=last or step['to'] in seen:
                    return self.record(nonce,'BROKEN_CUSTODY_CHAIN')
                holder=step['to'];seen.add(holder);last=step['time']
            if holder!=en['custodian'] or not (last<en['enrolled_at']<=b['capture']):return self.record(nonce,'ENROLLMENT_CUSTODY_MISMATCH')
            if not(en['valid_from']<=b['capture']<en['valid_until']):return self.record(nonce,'ENROLLMENT_EXPIRED')
            if not(cb['release']<=b['capture']<=cb['deadline']):return self.record(nonce,'CAPTURE_OUTSIDE_WINDOW')
            if b['nonce']!=nonce or b['content_hash']!=cb['expected_hash']:return self.record(nonce,'RESPONSE_MISMATCH')
            for field,seen_set in [('sensor',sensors),('operator',operators),('service',services),('root',roots),('capture_id',captures)]:
                value=en[field] if field!='capture_id' else b[field]
                if value in seen_set:return self.record(nonce,'SHARED_PROVENANCE_OR_CAPTURE')
                seen_set.add(value)
        if len(a)<2:return self.record(nonce,'INSUFFICIENT_DEVICES')
        return self.record(nonce,'DECLARED_SUPPLY_CHAIN_CONSISTENT_FIXTURE',devices=len(a),physical_origin_proven=False)

def fixture(kind='valid',nonce='jane220-fixture-00000001'):
    c=sign({'nonce':nonce,'freeze':100,'release':140,'deadline':160,'expected_hash':sha('orange-pattern')},'challenger')
    m=[];t=[];e=[];a=[];r=[]
    for i in range(2):
        d=f'device-{i}'; batch=f'batch-{i}'; model='camera-v1'; name=d
        mf={'issuer':'manufacturer','device':d,'batch':batch,'hardware_model':model,'public_key':pub(name),'time':10}
        if kind=='impostor' and i==1:mf['public_key']=pub('fraudulent-hardware')
        m.append(sign(mf,'manufacturer' if kind!='false-maker' or i==0 else 'attacker'))
        holder='manufacturer'
        for step,(dst,tm) in enumerate([('distributor-'+str(i),20),('lab-'+str(i),30)]):
            if kind=='broken' and i==1 and step==1:holder='somebody-else'
            t.append(sign({'device':d,'from':holder,'to':dst,'time':tm},holder))
            holder=dst
        en={'issuer':'enrollment-authority','device':d,'batch':batch,'hardware_model':model,'public_key':pub(name),
            'custodian':f'lab-{i}','enrolled_at':40,'valid_from':40,'valid_until':200,
            'sensor':f'sensor-{i}','operator':f'operator-{i}','service':f'service-{i}','root':f'root-{i}'}
        if kind=='shared' and i==1:en['service']='service-0'
        if kind=='expired' and i==1:en['valid_until']=130
        e.append(sign(en,'enrollment-authority'))
        ab={'device':d,'nonce':nonce,'content_hash':c['body']['expected_hash'],'capture':145,'capture_id':f'capture-{i}-{nonce}'}
        if kind=='late' and i==1:ab['capture']=170
        if kind=='mismatch' and i==1:ab['content_hash']=sha('different')
        a.append(sign(ab,name))
        if kind=='revoked' and i==1:r.append(sign({'issuer':'revocation-authority','device':d},'revocation-authority'))
    if kind=='missing':t=[x for x in t if x['body']['device']!='device-1']
    if kind=='self-signed':e=e[:1]
    return c,m,t,e,a,r

if __name__=='__main__':
    results={}
    for k in ('valid','impostor','false-maker','broken','shared','expired','late','mismatch','revoked','missing','self-signed'):
        x=FLAY220();results[k]=x.audit(*fixture(k,nonce='jane220-'+k+'-nonce-0001'));x.close()
    print(json.dumps({'experiment':'JANE 220','invariant':'Trusted enrollment signature != genuine device provenance','results':results,'physical_hardware_contacted':False},indent=2,sort_keys=True))