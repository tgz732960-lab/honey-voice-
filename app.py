from flask import Flask, request, render_template_string
import requests
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Honey Voice</title>
</head>
<body style="font-family: Arial; padding: 30px;">
    <h1>Honey Voice 🎙️</h1>

    <form method="POST">
        <textarea name="text" rows="5" cols="50" placeholder="输入你想转语音的话"></textarea>
        <br><br>
        <button type="submit">生成语音</button>
    </form>

    {% if audio %}
        <h3>生成成功：</h3>
        <audio controls>
            <source src="{{ audio }}" type="audio/mpeg">
        </audio>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    audio_url = None

    if request.method == "POST":
        text = request.form.get("text")

        api_key = os.getenv("ELEVENLABS_API_KEY")
        voice_id = "21m00Tcm4TlvDq8ikWAM"

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }

        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2"
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            with open("output.mp3", "wb") as f:
                f.write(response.content)
            audio_url = "/audio"

    return render_template_string(HTML, audio=audio_url)


@app.route("/audio")
def audio():
    with open("output.mp3", "rb") as f:
        return f.read(), 200, {"Content-Type": "audio/mpeg"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)