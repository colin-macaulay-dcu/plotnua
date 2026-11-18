# PROVE · PlotArt publisher · an interrupted photograph download is fetched again (18 Nov 2026, Carmel Marrinan's first
# publication failed with "IncompleteRead(71654 bytes read, 1366688 more expected)"). Local only: a tiny server that cuts
# the first responses short. Nothing is relaxed: the fingerprint check is unchanged and a third failure still refuses.
#   python3 worker/plotart-studio/test/prove-image-download-retry.py
import hashlib, http.client, http.server, importlib.util, os, sys, threading
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BODY = os.urandom(1_438_342)
state = {"cut": 0, "served": 0}
class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def do_GET(self):
        state["served"] += 1
        self.send_response(200); self.send_header("Content-Type", "image/jpeg"); self.send_header("X-Sha256", hashlib.sha256(BODY).hexdigest())
        self.send_header("Content-Length", str(len(BODY))); self.send_header("Connection", "close"); self.end_headers()
        if state["cut"] > 0:
            state["cut"] -= 1; self.wfile.write(BODY[:71_654]); self.wfile.flush(); self.connection.shutdown(2); return
        self.wfile.write(BODY)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
sys.argv = ["x", "--studio", "http://127.0.0.1:%d/" % srv.server_address[1], "--token", "t", "--simulate"]
spec = importlib.util.spec_from_file_location("pub", os.path.join(ROOT, "atlas-tools", "plotart-gallery-publish.py"))
pub = importlib.util.module_from_spec(spec); spec.loader.exec_module(pub)
pub.time.sleep = lambda s: None
res = []
def check(name, ok, d=""):
    res.append(bool(ok)); print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  [%s]" % d))
print("PROVE · PlotArt publisher · interrupted image downloads")
state.update(cut=0, served=0); body, h = pub.fetch_image("q1", "i1")
check("R1 a normal download is fetched once, whole, and matches its fingerprint", state["served"] == 1 and hashlib.sha256(body).hexdigest() == h["X-Sha256"])
state.update(cut=2, served=0); body, h = pub.fetch_image("q1", "i1")
check("R2 a download cut off twice (as Carmel's was) is fetched again and arrives whole on the third try", state["served"] == 3 and body == BODY)
state.update(cut=3, served=0)
try: pub.fetch_image("q1", "i1"); ok = False
except http.client.IncompleteRead: ok = True
check("R3 three interrupted downloads still refuse the publication (no endless retrying)", ok and state["served"] == 3, state)
src = open(os.path.join(ROOT, "atlas-tools", "plotart-gallery-publish.py")).read()
check("R4 the fingerprint check on every photograph is unchanged", 'if hashlib.sha256(body).hexdigest() != headers.get("X-Sha256"):\n                return "refused: image %s changed in transit" % iid' in src)
print("PLOTART IMAGE DOWNLOAD RETRY · %d checks, %d passed, %d failed" % (len(res), sum(res), len(res) - sum(res)))
sys.exit(0 if all(res) else 1)
