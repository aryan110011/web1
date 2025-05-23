import os
import time
import requests
import getpass
from datetime import datetime
from termcolor import cprint, colored

SERVER_URL = "https://web1-w6na.onrender.com"

# 🔴 Animated red logo
def print_logo():
    logo = [
        "                  __                    _ _           ",
        "                 / _|                  | | |          ",
        "  ___  __ _ _ __| |_ _   _   _ __ _   _| | | _____  __",
        " / __|/ _` | '__|  _| | | | | '__| | | | | |/ _ \\ \\/ /",
        " \\__ \\ (_| | |  | | | |_| | | |  | |_| | | |  __/>  < ",
        " |___/\\__,_|_|  |_|  \\__,_| |_|   \\__,_|_|_|\\___/_/\\_\\",
        "                                                     ",
        "                                                     "
    ]
    for line in logo:
        cprint(line, "red")
        time.sleep(0.1)

# 🔐 Password check
def authenticate():
    print()
    cprint("Login Time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "yellow")
    print()
    correct_password = "sarfu123"
    password = getpass.getpass(colored("Enter Password: ", "cyan"))
    if password != correct_password:
        cprint("❌ Incorrect password. Access denied.", "red")
        exit()
    cprint("✅ Access granted.\n", "green")

# ⚠️ Warning note
def show_note():
    warning_lines = [
        "Note:",
        "If any user tries to access another user's account,",
        "their approval will be removed.",
        "Also, abusing God is strictly forbidden.",
        "This tool is made only for Legends.",
        "",
        "Made by: ArYan.x3"
    ]
    for line in warning_lines:
        time.sleep(0.4)
        cprint(line, "magenta")

# 🧭 Main menu
def main_menu():
    while True:
        print()
        cprint("=== Main Menu ===", "blue", attrs=["bold"])
        print(colored("[1] Start New Conversation", "green"))
        print(colored("[2] View Active Conversations", "yellow"))
        print(colored("[3] Resume Previous Conversation", "cyan"))
        print(colored("[4] Stop Conversation", "red"))
        print(colored("[5] Exit", "white"))
        choice = input(colored("Choose an option: ", "blue"))

        if choice == "1":
            start_convo()
        elif choice == "2":
            view_convos()
        elif choice == "3":
            resume_convo()
        elif choice == "4":
            stop_convo()
        elif choice == "5":
            cprint("👋 Exiting... Take care!", "red")
            break
        else:
            cprint("❌ Invalid choice! Try again.", "red")

# 🚀 Start New Conversation
def start_convo():
    convo_type = input(colored("Login Type (single/multi): ", "cyan")).strip().lower()
    accounts = []

    if convo_type == "multi":
        file_path = input("Enter file path: ")
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()
            for line in lines:
                parts = line.strip().split("|")
                if len(parts) == 2:
                    acc_type, value = parts
                    try:
                        res = requests.post(f"{SERVER_URL}/validate_id", json={"type": acc_type, "value": value})
                        if res.status_code == 200 and res.json().get("valid"):
                            print(colored(f"✅ {res.json()['name']}", "green"))
                            accounts.append({"type": acc_type, "value": value})
                        else:
                            print(colored("❌ Invalid ID", "red"))
                    except:
                        cprint("❌ Server error during validation.", "red")
        except FileNotFoundError:
            cprint("❌ File not found.", "red")
            return

    elif convo_type == "single":
        acc_type = input("Login using (token/cookie): ").strip().lower()
        value = input(f"Paste your {acc_type}: ").strip()
        try:
            res = requests.post(f"{SERVER_URL}/validate_id", json={"type": acc_type, "value": value})
            if res.status_code == 200 and res.json().get("valid"):
                print(colored(f"✅ {res.json()['name']}", "green"))
                accounts.append({"type": acc_type, "value": value})
            else:
                cprint("❌ Invalid ID", "red")
                return
        except:
            cprint("❌ Server connection failed.", "red")
            return
    else:
        cprint("❌ Invalid login type", "red")
        return

    try:
        group_count = int(input("How many Messenger group UIDs to send messages to? "))
    except:
        cprint("❌ Invalid number", "red")
        return

    group_ids = []
    for i in range(group_count):
        uid = input(f"Group UID {i+1}: ")
        if not uid.isdigit():
            cprint("❌ UID must be numeric", "red")
            return
        group_ids.append(uid)

    hatter_name = input("Enter your hatter name: ")

    message_mode = input("Message Mode (file/single): ").strip().lower()
    if message_mode == "file":
        file_path = input("Enter message file path: ")
        try:
            with open(file_path, "r") as f:
                messages = [line.strip() for line in f if line.strip()]
        except:
            cprint("❌ Message file not found.", "red")
            return
    else:
        messages = [input("Enter your message: ")]

    try:
        delay = int(input("Message delay (in seconds): "))
    except:
        cprint("❌ Invalid delay time.", "red")
        return

    convo_name = input("Enter a name for this conversation: ")

    payload = {
        "accounts": accounts,
        "group_ids": group_ids,
        "hatter_name": hatter_name,
        "messages": messages,
        "delay": delay,
        "convo_name": convo_name
    }

    try:
        res = requests.post(f"{SERVER_URL}/start_convo", json=payload)
        cprint(res.text, "yellow")
    except:
        cprint("❌ Server error while starting convo", "red")

# 👀 View Active Convos
def view_convos():
    try:
        res = requests.get(f"{SERVER_URL}/view_convos")
        convos = res.json().get("conversations", [])
        if not convos:
            cprint("No active conversations.", "red")
            return
        print("\nActive Conversations:")
        for c in convos:
            print(f"- {c}")
        convo = input("Enter convo name to view live messages: ")
        r = requests.get(f"{SERVER_URL}/stream_convo/{convo}", stream=True)
        for line in r.iter_lines():
            print(colored(line.decode(), "cyan"))
    except:
        cprint("❌ Failed to fetch conversations", "red")

# 🔄 Resume
def resume_convo():
    try:
        res = requests.get(f"{SERVER_URL}/resume_convos")
        resumables = res.json().get("resumable", [])
        if not resumables:
            cprint("No resumable conversations found.", "red")
            return
        print("Resumable Conversations:")
        for c in resumables:
            print(f"- {c}")
        convo = input("Enter convo name to resume: ")
        r = requests.get(f"{SERVER_URL}/stream_resume/{convo}", stream=True)
        for line in r.iter_lines():
            print(colored(line.decode(), "green"))
    except:
        cprint("❌ Failed to resume", "red")

# ⛔ Stop Convo
def stop_convo():
    try:
        res = requests.get(f"{SERVER_URL}/view_convos")
        convos = res.json().get("conversations", [])
        if not convos:
            cprint("No running conversations to stop.", "red")
            return
        print("Running Conversations:")
        for c in convos:
            print(f"- {c}")
        convo = input("Enter convo name to stop: ")
        res = requests.post(f"{SERVER_URL}/stop_convo", json={"convo_name": convo})
        print(colored(res.text, "red"))
    except:
        cprint("❌ Failed to stop conversation", "red")

# 🚦 Run
if __name__ == "__main__":
    try:
        os.system("clear")
        print_logo()
        authenticate()
        show_note()
        main_menu()
    except KeyboardInterrupt:
        cprint("\n👋 Tool band kiya gaya. See you!", "cyan")
