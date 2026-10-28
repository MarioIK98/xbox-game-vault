#!/usr/bin/env python3
"""Check declared release scope and hosting evidence; never purchase or deploy."""
from __future__ import annotations
import argparse,copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def evaluate(p):
 errors=[]
 if p.get('project')!='MarioIK98/xbox-game-vault':errors.append('Wrong project identity')
 if not p.get('sources') or not p.get('checked_on'):errors.append('Missing policy evidence')
 intent=p.get('release_intent')
 if intent not in ('existing_catalogue_maintenance','commercial_launch'):errors.append('Unknown release intent')
 if intent=='commercial_launch':
  c=p.get('commercial_hosting',{})
  if p.get('current_host')=='github_pages':errors.append('GitHub Pages is not the approved commercial hosting route')
  if c.get('provider')=='vercel' and str(c.get('plan','')).lower()=='hobby':errors.append('Vercel Hobby is not a commercial hosting route')
  if c.get('status')!='APPROVED':errors.append('Commercial hosting not approved')
  for key in ('account_access_verified','commercial_terms_verified','costs_approved_by_mario'):
   if c.get(key) is not True:errors.append('Missing '+key)
  if not c.get('provider') or not c.get('plan') or not c.get('evidence'):errors.append('Missing provider, plan or evidence')
 return errors
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='verification/hosting.json');args=ap.parse_args()
 p=json.loads((ROOT/'release/hosting_policy.json').read_text());errors=evaluate(p)
 commercial=copy.deepcopy(p);commercial['release_intent']='commercial_launch';commercial['current_host']='github_pages'
 guards={'github_pages_business_launch_blocked':bool(evaluate(commercial))}
 commercial['current_host']='vercel';commercial['commercial_hosting'].update({'provider':'vercel','plan':'hobby'})
 guards['vercel_hobby_business_launch_blocked']=bool(evaluate(commercial))
 commercial['commercial_hosting'].update({'status':'APPROVED','provider':'verified_fixture','plan':'fixture','account_access_verified':True,'commercial_terms_verified':True,'costs_approved_by_mario':True,'evidence':['test-only']});commercial['current_host']='verified_fixture'
 guards['complete_test_fixture_accepted']=not evaluate(commercial)
 if not all(guards.values()):errors.append('Hosting guard regression failed')
 result={'release_intent':p['release_intent'],'passed':not errors,'errors':errors,'guard_tests':guards,'commercial_launch_ready':not evaluate(dict(p,release_intent='commercial_launch')),'note':'Maintenance passing does not approve commercial use or verify the host account. This declarative check does not inspect arbitrary page content, enforce branch protection or replace a current provider review.'}
 out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
