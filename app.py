from flask import Flask, request, jsonify
import re

app = Flask(__name__)

user_context = {}

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    data = request.json
    incoming_msg = data.get("payload", {}).get("text", "").strip()
    sender = data.get("sender", "")
    print(f"📩 {sender}: {incoming_msg}")

    lower_msg = incoming_msg.lower()

    reply_text = None
    image_url = None

    def extract_class_number(text):
        matches = re.findall(r"\d+", text)
        if matches:
            return int(matches[0])
        return None

    # Step 4: Ask phone
    if sender in user_context and user_context[sender]["step"] == "ask_phone":
        if not re.fullmatch(r"\d{10}", incoming_msg):
            reply_text = "⚠️ Please enter a valid *10-digit phone number* (digits only)."
        else:
            user_context[sender]["phone"] = incoming_msg
            student_class = user_context[sender]["class"]
            student_name = user_context[sender]["name"]
            student_phone = user_context[sender]["phone"]

            reply_text = (
                f"✅ Thank you, *{student_name}*! Your admission enquiry for *Class {student_class}* "
                f"has been received.\n📱 Contact: *{student_phone}*\n\n"
                "📝 Please fill the admission form:\n"
                "👉 https://kvidukki.ac.in/admission\n\n"
                "Our team will contact you soon. 📞"
            )

            user_context.pop(sender)

    # Step 3: Ask name
    elif sender in user_context and user_context[sender]["step"] == "ask_name":
        if not re.fullmatch(r"[A-Za-z ]+", incoming_msg):
            reply_text = "⚠️ Please enter your name using *alphabets only* (e.g., John Doe)."
        else:
            user_context[sender]["name"] = incoming_msg
            user_context[sender]["step"] = "ask_phone"
            reply_text = "📞 Please provide your *contact number* (10 digits)."

    # Step 2: Ask class
    elif sender in user_context and user_context[sender]["step"] == "ask_class":
        if not re.fullmatch(r"\d{1,2}", incoming_msg) or not (1 <= int(incoming_msg) <= 12):
            reply_text = "⚠️ Please enter your class between *1 and 12* (e.g., 5)."
        else:
            user_context[sender]["class"] = incoming_msg
            user_context[sender]["step"] = "ask_name"
            reply_text = "👤 Great! Please tell me the *student's full name*."

    # Step 1: Start admission
    elif "admission" in lower_msg or lower_msg == "1":
        reply_text = (
            "📚 Admissions for 2025 are open!\n"
            "Please tell me which *class* you are seeking admission for?"
        )
        user_context[sender] = {"step": "ask_class"}

    # Greeting menu
    elif "hi" in lower_msg or "hello" in lower_msg:
        reply_text = (
            "👋 Hello! Welcome to *KV Idukki School*.\n\n"
            "Please choose an option:\n"
            "1️⃣ Admission Info\n"
            "2️⃣ Fee Details\n"
            "3️⃣ Contact Info\n\n"
            "👉 Type 1 or 2 or 3."
        )
        image_url = "https://raw.githubusercontent.com/sinan117/kv-whatsapp-bot/main/welcome.jpg"

    # Fee step 1
    elif "fee" in lower_msg or lower_msg == "2":
        reply_text = "💰 Enter the *class number* (e.g., 1, 5, 10)."
        user_context[sender] = {"step": "ask_fee_class"}

    # Fee step 2
    elif sender in user_context and user_context[sender].get("step") == "ask_fee_class":
        cls = extract_class_number(incoming_msg)
        if cls and 1 <= cls <= 12:
            user_context[sender]["class"] = cls
            user_context[sender]["step"] = "ask_fee_category"
            reply_text = (
                "👩‍🎓 Choose category:\n"
                "1️⃣ General\n"
                "2️⃣ SC/ST/OBC\n"
                "3️⃣ Single Girl Child"
            )
        else:
            reply_text = "⚠️ Please enter a valid class number between 1 and 12."

    # Fee step 3
    elif sender in user_context and user_context[sender].get("step") == "ask_fee_category":
        cls = user_context[sender]["class"]

        if 1 <= cls <= 3:
            fees = {"general": 500, "sc/st/obc": 300, "single girl child": 350}
        elif 4 <= cls <= 7:
            fees = {"general": 800, "sc/st/obc": 600, "single girl child": 650}
        else:
            fees = {"general": 1100, "sc/st/obc": 800, "single girl child": 950}

        if "1" in lower_msg:
            category = "General"
            fee = fees["general"]
        elif "2" in lower_msg:
            category = "SC/ST/OBC"
            fee = fees["sc/st/obc"]
        elif "3" in lower_msg:
            category = "Single Girl Child"
            fee = fees["single girl child"]
        else:
            reply_text = "⚠️ Please type 1, 2 or 3."
            return jsonify({"message": {"text": reply_text}})

        reply_text = f"🏫 Fee for *Class {cls}* ({category}) is *₹{fee}*."
        user_context.pop(sender)

    # Contact info
    elif lower_msg in ["3", "contact", "phone", "info"]:
        reply_text = (
            "*🌐 Website*: https://painavu.kvs.ac.in\n"
            "*📧 Email*: kvidukki@yahoo.in\n"
            "*📞 Phone*: 04862-232205"
        )

    elif "bye" in lower_msg:
        reply_text = "Goodbye! 👋 Have a great day!"

    else:
        reply_text = (
            "❓ I didn’t understand.\n"
            "Options:\n"
            "1️⃣ Admission  2️⃣ Fees  3️⃣ Contact"
        )

    # Build Gupshup response
    response = {"message": {}}
    if reply_text:
        response["message"]["text"] = reply_text
    if image_url:
        response["message"]["media"] = {"type": "image", "url": image_url}

    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
