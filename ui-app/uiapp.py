import json
from flask import Flask, request, jsonify, Response
from flask_basicauth import BasicAuth

from python.helpers.files import get_absolute_path
from python.helpers.dotenv import load_dotenv
from python.helpers.print_style import PrintStyle

from initialize import initialize

from agent import AgentContext

import threading
import uuid
import os
from werkzeug.serving import WSGIRequestHandler
from pathlib import Path

app = Flask("app", static_folder=get_absolute_path("./web"), static_url_path="/")
app.config["JSON_SORT_KEYS"] = False

lock = threading.Lock()

app.config["BASIC_AUTH_USERNAME"] = (
   os.environ.get("BASIC_AUTH_USERNAME") or "admin"
)

app.config["BASIC_AUTH_PASSWORD"] = (
   os.environ.get("BASIC_AUTH_PASSWORD") or "admin"
)

basic_auth = BasicAuth(app)

def get_context(ctxid: str):
    with lock:
        if not ctxid:
            first = AgentContext.first()
            if first:
                return first
            return AgentContext(config=initialize())
        got = AgentContext.get(ctxid)
        if got:
            return got
        return AgentContext(config=initialize(), id=ctxid)

@app.route("/", methods=["GET"])
async def test_form():
    return Path(get_absolute_path("./web/index.html")).read_text()

# send message to agent (async UI)
@app.route("/msg", methods=["POST"])
async def handle_message_async():
    print("Se recibe peticion")
    return await handle_message(False)

# send message to agent (synchronous API)
@app.route("/msg_sync", methods=["POST"])
async def handle_msg_sync():
    return await handle_message(True)

# simple health check, just return OK to see the server is running
@app.route("/ok", methods=["GET", "POST"])
async def health_check():
    return "OK"

async def handle_message(sync: bool):
    try:
        input = request.get_json()
        text = input.get("text", "")
        ctxid = input.get("context", "")
        blev = input.get("broadcast", 1)

        context = get_context(ctxid)

        PrintStyle(background_color="#6C3483", 
                font_color="white", 
                bold=True, 
                padding=True
        ).print(f"User message:")

        PrintStyle(font_color="white", padding=False).print(f"> {text}")
        context.log.log(type="user", heading="User message", content=text)

        if sync:
            context.communicate(text)
            result = await context.process.result()  # type: ignore
            response = {
                    "ok": True,
                    "message": result,
                    "context": context.id,
            }
        else:
            context.communicate(text)
            response = {
                    "ok": True,
                    "message": "Message received.",
                    "context": context.id,
            }
    except Exception as e:
        response = {
                "ok": False,
                "message": str(e),
        }
        PrintStyle.error(str(e))

    return jsonify(response)

@app.route("/poll", methods=["POST"])
async def poll():
    try:
        input = request.get_json()
        ctxid = input.get("context", None)
        from_no = input.get("log_from", 0)
        context = get_context(ctxid)
        logs = context.log.output(start=from_no)
        
        ctxs = []
        for ctx in AgentContext._contexts.values():
            ctxs.append(
                    {
                        "id": ctx.id,
                        "no": ctx.no,
                        "log_guid": ctx.log.guid,
                        "log_version": len(ctx.log.updates),
                        "log_length": len(ctx.log.logs),
                        "paused": ctx.paused,
                    }
            )

            response = {
                    "ok": True,
                    "context": context.id,
                    "contexts": ctxs,
                    "logs": logs,
                    "log_guid": context.log.guid,
                    "log_version": len(context.log.updates),
                    "log_progress": context.log.progress,
                    "paused": context.paused,
            }
    except Exception as e:
        response = {
                "ok": False,
                "message": str(e),
                }
        PrintStyle.error(str(e))
    
    response_json = json.dumps(response)
    return Response(response=response_json, status=200, mimetype="application/json")

class NoRequestLoggingWSGIRequestHandler(WSGIRequestHandler):
    def log_request(self, code='-', size='-'):
        pass

def run():
    load_dotenv()
    host = os.environ.get("WEB_UI_HOST", "0.0.0.0")
    port = int(os.environ.get("WEB_UI_PORT", 0)) or None
    app.run(port = port, host=host)
    #app.run(request.handler=NoRequestLoggingWSGIRequestHandler, port=port)

if __name__ == "__main__":
    run()
