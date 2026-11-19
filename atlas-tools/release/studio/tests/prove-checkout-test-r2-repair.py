#!/usr/bin/env python3
# Mock-API test matrix for checkout-test-setup.py r2_plan / r2_apply (fail-closed review, PR #22). Runs offline; touches no real resource.
import json, re, threading, http.server, sys, os, subprocess, tempfile
SCN = None
def fresh(): return {"default": {"plotart-studio-test-images", "plotart-studio-test-applications", "plotart-studio-images", "plotart-applications"}, "eu": set(), "calls": []}
state = fresh()
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def send(self, code, body): b=json.dumps(body).encode(); self.send_response(code); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(b)
    def jur(self): return "eu" if self.headers.get("cf-r2-jurisdiction")=="eu" else "default"
    def do_GET(self):
        p=self.path.split("/client/v4",1)[1]
        if p.endswith("/tokens/verify"): return self.send(200,{"result":{"status":"active"}})
        if p.endswith("/workers/subdomain"): return self.send(200,{"result":{"subdomain":"colin-a41"}})
        if p.endswith("/workers/scripts"): return self.send(200,{"result":[{"id":"plotart-studio"},{"id":"other"}]})
        if "/settings" in p:
            if SCN=="settings_403" and "/other/" in p: return self.send(403,{"errors":[{"code":10000,"message":"auth"}]})
            b=[{"type":"r2_bucket","bucket_name":"plotart-studio-images","jurisdiction":"eu"}]
            if SCN=="in_use" and "/other/" in p: b.append({"type":"r2_bucket","bucket_name":"plotart-studio-test-images"})
            return self.send(200,{"result":{"bindings":b}})
        m=re.search(r"/r2/buckets/([^/?]+)(.*)",p)
        if m:
            n,rest=m.group(1),m.group(2); j=self.jur()
            if not rest and SCN=="lookup_403" and n=="plotart-studio-test-applications": return self.send(403,{"errors":[{"code":10000,"message":"forbidden"}]})
            if not rest and SCN=="lookup_500": return self.send(500,{"errors":[{"code":1,"message":"internal"}]})
            if n not in state[j]: return self.send(404,{"errors":[{"code":10006,"message":"no such bucket"}]})
            if rest.startswith("/objects"):
                if SCN=="objects_malformed": return self.send(200,{"result":None})
                if SCN=="not_empty" and n=="plotart-studio-test-applications": return self.send(200,{"result":[{"key":"x"}]})
                return self.send(200,{"result":[]})
            if rest=="/domains/custom": return self.send(200,{"result":{"domains":[]}})
            if rest=="/domains/managed": return self.send(200,{"result":{"enabled":SCN=="public"}})
            return self.send(200,{"result":{"name":n,"jurisdiction":"eu" if j=="eu" else ("eu" if SCN=="wrong_jur" else "default")}})
        if "/r2/buckets" in p: return self.send(200,{"result":{"buckets":[{"name":n} for n in state[self.jur()]]}})
        if "event_notifications" in p: return self.send(404,{})
        if "/d1/database/" in p: return self.send(200,{"result":{"name":"plotart-checkout-test","running_in_region":"WEUR"}})
        if "/access/" in p: return self.send(200,{"result":[]})
        return self.send(404,{})
    def do_POST(self):
        p=self.path.split("/client/v4",1)[1]; l=int(self.headers.get("Content-Length",0)); b=json.loads(self.rfile.read(l) or b"{}")
        if p.endswith("/r2/buckets"):
            n=b["name"]; state["calls"].append(("CREATE",n,self.jur()))
            if SCN=="create_fail": return self.send(500,{"errors":[{"code":1,"message":"internal"}]})
            if SCN in ("conflict","conflict_then_fail") and n in state["default"]:
                return self.send(409,{"errors":[{"code":10004,"message":"exists"}]})
            if SCN=="conflict_then_fail": return self.send(500,{"errors":[{"code":1,"message":"internal"}]})
            if SCN=="conflict_other_409" and n in state["default"]: return self.send(409,{"errors":[{"code":99999,"message":"other"}]})
            state[self.jur()].add(n); return self.send(200,{"result":{"name":n}})
        if "/query" in p: return self.send(200,{"result":[{"results":[]}]})
        return self.send(404,{})
    def do_DELETE(self):
        p=self.path.split("/client/v4",1)[1]; n=p.rsplit("/",1)[1]; j=self.jur()
        state["calls"].append(("DELETE",n,j)); state[j].discard(n); return self.send(200,{"success":True,"result":{}})
srv=http.server.HTTPServer(("127.0.0.1",8782),H); threading.Thread(target=srv.serve_forever,daemon=True).start()
env=dict(os.environ, CLOUDFLARE_ACCOUNT_ID="a"*32, CHECKOUT_TEST_CF_TOKEN="x"*30, CHECKOUT_TEST_D1_DATABASE_ID="12345678-1234-1234-1234-123456789abc",
  CHECKOUT_TEST_ACCESS_TEAM="https://plotnua.cloudflareaccess.com", CHECKOUT_TEST_ORIGIN="https://plotart-checkout-test.colin-a41.workers.dev")
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "checkout-test-setup.py")).read().replace('API = "https://api.cloudflare.com/client/v4"','API = "http://127.0.0.1:8782/client/v4"')
open(os.path.join(tempfile.gettempdir(), "checkout-test-setup-mock.py"),"w").write(src)
PROD = {"plotart-studio-images","plotart-applications"}
cases = [
 ("normal","r2_apply", lambda rc,st: rc==0 and st["eu"]=={"plotart-studio-test-images","plotart-studio-test-applications"} and st["default"]==PROD),
 ("already_eu","r2_apply", None),
 ("lookup_403","r2_plan", lambda rc,st: rc==1 and not st["calls"]),
 ("lookup_500","r2_apply", lambda rc,st: rc==1 and not st["calls"]),
 ("settings_403","r2_apply", lambda rc,st: rc==1 and not st["calls"]),
 ("objects_malformed","r2_apply", lambda rc,st: rc==1 and not st["calls"]),
 ("wrong_jur","r2_apply", lambda rc,st: rc==1 and not st["calls"]),
 ("in_use","r2_apply", lambda rc,st: rc==1 and not st["calls"]),
 ("not_empty","r2_apply", lambda rc,st: rc==1 and not st["calls"]),
 ("public","r2_apply", lambda rc,st: rc==1 and not st["calls"]),
 ("create_fail","r2_apply", lambda rc,st: rc==1 and not any(c[0]=="DELETE" for c in st["calls"]) and len(st["calls"])==1),
 ("conflict","r2_apply", lambda rc,st: rc==0 and st["eu"]=={"plotart-studio-test-images","plotart-studio-test-applications"} and st["default"]==PROD),
 ("conflict_other_409","r2_apply", lambda rc,st: rc==1 and not any(c[0]=="DELETE" for c in st["calls"])),
 ("conflict_then_fail","r2_apply", lambda rc,st: rc==1 and [c[0] for c in st["calls"]]==["CREATE","DELETE","CREATE"] and "plotart-studio-test-applications" in st["default"]),
]
ok_all=True
for scn,mode,expect in cases:
    SCN=scn; state.clear(); state.update(fresh())
    if scn=="already_eu":
        state["default"]=set(PROD); state["eu"]={"plotart-studio-test-images","plotart-studio-test-applications"}
        expect=lambda rc,st: rc==0 and not st["calls"]
    r=subprocess.run([sys.executable,os.path.join(tempfile.gettempdir(), "checkout-test-setup-mock.py"),mode],env=env,capture_output=True,text=True)
    good=expect(r.returncode,state) and PROD<=state["default"]
    ok_all&=good
    last=[l.strip() for l in r.stdout.splitlines() if "STOPPED" in l or "REFUSED" in l or "final check" in l or "nothing to do" in l][-1:] 
    print(f"{'PASS' if good else 'FAIL'}  {scn:<20} {mode:<9} exit {r.returncode} · creates {sum(c[0]=='CREATE' for c in state['calls'])} deletes {sum(c[0]=='DELETE' for c in state['calls'])} · {last[0][:150] if last else ''}")
    if r.stderr.strip(): print("   stderr:", r.stderr.strip()[-300:])
print("MATRIX", "PASS" if ok_all else "FAIL")
sys.exit(0 if ok_all else 1)
