from flask import Flask, render_template, request, redirect, url_for, session
import random, json, os, uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "sirli_kalit"


with open("questions.json", "r", encoding="utf-8") as f:
    all_questions = json.load(f)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        role = request.form.get("role")
        partner_name = request.form.get("partner_name")

        # Test ID yaratamiz
        test_id = str(uuid.uuid4())[:8]
        session['test_id'] = test_id
        session['user'] = {'name': name, 'role': role, 'partner_name': partner_name}

        selected = random.sample(all_questions, 25)
        os.makedirs("saved", exist_ok=True)
        with open(f"saved/{test_id}.json", "w", encoding="utf-8") as f:
            json.dump({"questions": selected, "partner_name": partner_name}, f, ensure_ascii=False)

        return render_template("test.html", questions=selected, name=name, role=role, step="first", test_id=test_id)
    return render_template("index.html")

@app.route("/thanks", methods=["POST"])
def thanks():
    test_id = request.form.get("test_id")
    step = request.form.get("step")
    name = request.form.get("name")
    answers = {k: v for k, v in request.form.items() if k.startswith("q")}

    if step == "first":
        with open(f"saved/{test_id}_1.json", "w", encoding="utf-8") as f:
            json.dump({"name": name, "answers": answers}, f)
        return render_template("thanks.html", name=name, test_id=test_id, show_partner_button=True)
    else:
        with open(f"saved/{test_id}_2.json", "w", encoding="utf-8") as f:
            json.dump({"name": name, "answers": answers}, f)
        return redirect(url_for("result", test_id=test_id))

@app.route("/partner", methods=["GET", "POST"])
def partner():
    if request.method == "POST":
        test_id = request.form.get("test_id")
        your_name = request.form.get("your_name")
        try:
            with open(f"saved/{test_id}.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            if your_name.lower() != data["partner_name"].lower():
                return render_template("error.html", message="Ism mos emas. Iltimos, to‘g‘ri ismni kiriting."), 403
            session['test_id'] = test_id
            return render_template("test.html", questions=data["questions"], name=your_name, role="Juft", step="second", test_id=test_id)
        except FileNotFoundError:
            return render_template("error.html", message="Test ID topilmadi. Iltimos, to‘g‘ri ID kiriting."), 404
    return render_template("test_id_kiritish.html")

@app.route("/result/<test_id>")
def result(test_id):
    try:
        with open(f"saved/{test_id}_1.json", "r", encoding="utf-8") as f1:
            user1 = json.load(f1)
        with open(f"saved/{test_id}_2.json", "r", encoding="utf-8") as f2:
            user2 = json.load(f2)

        total = 25
        match = 0
        for i in range(total):
            qid = f"q{i}"
            if user1["answers"].get(qid) == user2["answers"].get(qid):
                match += 1
        percent = int((match / total) * 100)

        if percent >= 90:
            comment = f"🟢 {percent}% moslik – 😍 Ajoyib! Sizlar bir-biringiz uchun yaratilgansiz!"
        elif percent >= 70:
            comment = f"🟢 {percent}% moslik – 😊 Yaxshi! Birga yashab ketishingiz ehtimoli yuqori."
        elif percent >= 50:
            comment = f"🟡 {percent}% moslik – 😐 O‘rtacha. Yaxshi munosabat uchun ko‘proq tushunish zarur."
        else:
            comment = f"🔴 {percent}% moslik – 😞 Juda past. Birga yashashda ko‘plab muammolar bo‘lishi mumkin."

        return render_template("result.html", user1=user1, user2=user2, percent=percent, test_id=test_id, now=datetime.utcnow(), comment=comment)

    except FileNotFoundError:
        return render_template("error.html", message="Test fayllari topilmadi yoki juftlik hali testni tugatmagan."), 404


@app.route("/see_result", methods=["GET", "POST"])
def see_result():
    if request.method == "POST":
        test_id = request.form.get("test_id")
        return redirect(url_for("result", test_id=test_id))
    return render_template("see_result.html")


@app.route("/idlar")
def idlar():
    ids = []
    for filename in os.listdir("saved"):
        if filename.endswith(".json") and "_" not in filename:
            test_id = filename.replace(".json", "")
            user1_file = f"saved/{test_id}_1.json"
            user2_file = f"saved/{test_id}_2.json"

            name1 = name2 = "Noma'lum"
            if os.path.exists(user1_file):
                with open(user1_file, "r", encoding="utf-8") as f1:
                    user1 = json.load(f1)
                    name1 = user1.get("name", "Noma'lum")
            if os.path.exists(user2_file):
                with open(user2_file, "r", encoding="utf-8") as f2:
                    user2 = json.load(f2)
                    name2 = user2.get("name", "Noma'lum")

            ids.append((test_id, f"{name1} ❤️ {name2}"))
    return render_template("idlar.html", ids=ids)

@app.route("/id/<test_id>")
def id_natija(test_id):
    return redirect(url_for("result", test_id=test_id))


if __name__ == "__main__":
    app.run(debug=True)
