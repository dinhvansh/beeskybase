"""Check agent transport with an issued site key, without scanning or controlling miners.
Set BEESKY_AGENT_KEY in your environment. --send-fixture explicitly writes ONE
synthetic test miner, so use it only in a dedicated test workshop.
"""
import argparse
import os
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from beesky.agent import _get_json,_post_json,redact
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--url',required=True)
p.add_argument('--send-fixture',action='store_true')
a=p.parse_args();key=os.getenv('BEESKY_AGENT_KEY','')
if not key:raise SystemExit('Set BEESKY_AGENT_KEY; do not place the key in command history.')
url=a.url.rstrip('/')
if not url.startswith('https://') and not url.startswith(('http://127.0.0.1:','http://localhost:')):raise SystemExit('Use HTTPS outside localhost.')
try:
    result=_get_json(url+'/api/agent/commands',key)
    if result.get('commands') or result.get('control_available') is not False:raise ValueError('Unexpected control capability; stop and review server configuration.')
    print('Agent authentication OK; remote control disabled.')
    if a.send_fixture:
        ts=time.time();record={'site':'connection-check','ts':ts,'interval':30,'miners':[{'ip':'192.0.2.21','mac_or_serial':'BEESKY-CONNECTION-CHECK-ONLY','model':'S21 Hydro 335T','power_w':5360,'max_temp_c':55,'worker':'connection.check'}]}
        for _ in range(2):_post_json(url+'/api/ingest',record,key)
        _post_json(url+'/api/ingest/events',{'events':[{'ts':ts,'type':'CONNECTION_CHECK','message':'Synthetic connection test; not a physical miner'}]},key)
        print('Snapshot, retry and event transport OK. Check the dedicated workshop in the web app.')
except Exception as exc:
    print(redact('Agent check failed: '+str(exc),key),file=sys.stderr);sys.exit(1)
