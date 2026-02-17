from flask import Flask, request, jsonify
import base64

# Flask
app = Flask(__name__)

# ---------------- FLASK API ----------------
@app.route("/api/", methods=["POST"])
def receive_plate():
    
    data = request.get_json()

    placa = data.get("placa")
    timestamp = data.get("timestamp")  # vem da câmera

    # Salva imagem se vier
    imagem_base64 = data.get("img")
    if imagem_base64:
        with open(f"imgs/img{timestamp}.jpeg", "wb") as f:
            f.write(base64.b64decode(imagem_base64))
        print(f"Imagem salva como img{timestamp}.jpeg")

    return jsonify({"status": "ok"}), 200

app.run(host="10.16.135.22", port=80)
