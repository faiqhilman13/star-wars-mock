"""Tiny CLI client for the Unreal Editor MCP server (streamable HTTP).

Usage:
  ue.py list                      -> tools/list
  ue.py call <tool> <json|@file>  -> tools/call
  ue.py raw <method> <json>       -> arbitrary JSON-RPC
"""
import json
import os
import sys
sys.stdout.reconfigure(encoding="utf-8")
import urllib.request

URL = os.environ.get("UE_MCP_URL", "http://127.0.0.1:8000/mcp")
SESSION_FILE = os.path.join(os.path.dirname(__file__), ".session")


def _post(payload, session=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if session:
        headers["Mcp-Session-Id"] = session
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=600) as resp:
        sid = resp.headers.get("Mcp-Session-Id")
        body = resp.read().decode("utf-8", "replace")
    if body.lstrip().startswith("event:") or body.lstrip().startswith("data:"):
        datas = [l[5:].strip() for l in body.splitlines() if l.startswith("data:")]
        body = datas[-1] if datas else ""
    return sid, (json.loads(body) if body.strip() else None)


def session():
    if os.path.exists(SESSION_FILE):
        return open(SESSION_FILE).read().strip() or None
    return new_session()


def new_session():
    sid, _ = _post({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "claude-cli", "version": "1"}}})
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    with open(SESSION_FILE, "w") as f:
        f.write(sid or "")
    return sid


def rpc(method, params):
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    try:
        _, res = _post(payload, session())
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            _, res = _post(payload, new_session())
        else:
            raise
    return res


def main():
    cmd = sys.argv[1]
    if cmd == "list":
        res = rpc("tools/list", {})
    elif cmd in ("call", "t"):
        arg = sys.argv[3] if len(sys.argv) > 3 else "{}"
        if cmd == "t":  # ue.py t app.CaptureViewport '{...}'
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "prelude.py")).read()
            ns = {}
            exec(src.split("def T(")[0], ns)
            alias, tool = sys.argv[2].split(".", 1)
            if arg.startswith("@"):
                arg = open(arg[1:], encoding="utf-8").read()
            sys.argv[2] = "call_tool"
            arg = json.dumps({"toolset_name": ns["_TS"][alias], "tool_name": tool, "arguments": json.loads(arg)})
        if arg.startswith("@"):
            arg = open(arg[1:], encoding="utf-8").read()
        res = rpc("tools/call", {"name": sys.argv[2], "arguments": json.loads(arg)})
        if res and "result" in res:
            for c in res["result"].get("content", []):
                if c.get("type") == "text":
                    try:
                        rv = json.loads(c["text"]).get("returnValue")
                        if isinstance(rv, dict) and isinstance(rv.get("image"), dict):
                            rv = rv["image"]
                        if isinstance(rv, dict) and "data" in rv and "mimeType" in rv:
                            c = {"type": "image", "data": rv["data"], "mimeType": rv["mimeType"]}
                    except Exception:
                        pass
                if c.get("type") == "text":
                    print(c["text"] if os.environ.get("UE_FULL") else c["text"][:6000])
                elif c.get("type") == "image":
                    import base64, time
                    ext = c.get("mimeType", "image/png").split("/")[-1]
                    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots",
                                       f"shot_{int(time.time()*1000)}.{ext}")
                    os.makedirs(os.path.dirname(out), exist_ok=True)
                    open(out, "wb").write(base64.b64decode(c["data"]))
                    print("IMAGE:", out)
                else:
                    print(json.dumps(c)[:2000])
            if res["result"].get("isError"):
                sys.exit(1)
            return
    elif cmd == "script":
        # ue.py script file.py  -> run via ProgrammaticToolset with prelude helpers
        here = os.path.dirname(os.path.abspath(__file__))
        code = open(os.path.join(here, "prelude.py"), encoding="utf-8").read() + "\n\n" + \
            open(sys.argv[2], encoding="utf-8").read()
        res = rpc("tools/call", {"name": "call_tool", "arguments": {
            "toolset_name": "editor_toolset.toolsets.programmatic.ProgrammaticToolset",
            "tool_name": "execute_tool_script", "arguments": {"script": code}}})
        r = res.get("result", res)
        for c in r.get("content", []):
            if c.get("type") == "text":
                txt = c["text"]
                try:
                    txt = json.loads(json.loads(txt)["returnValue"])
                    txt = json.dumps(txt, indent=1)
                except Exception:
                    pass
                print(txt)
        if r.get("isError"):
            sys.exit(1)
        return
    else:
        res = rpc(sys.argv[2], json.loads(sys.argv[3]))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
