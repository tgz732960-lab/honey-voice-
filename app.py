from flask import Flask, request, render_template_string, jsonify
import requests
import os
from anthropic import Anthropic

app = Flask(__name__)

# Claude
anthropic = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# ElevenLabs
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "8gg0WXng9B2Fn5wlrJ7I"

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Honey Voice</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
</head>

<body style="font-family: Arial; padding:20px; max-width:600px; margin:auto;">
    <h2>Honey Voice</h2>

    <div id="chat" style="border:1px solid #ddd; padding:15px; height:400px; overflow:auto; border-radius:12px;">
    </div>

    <br>

    <input
        id="userInput"
        type="text"
        placeholder="输入内容..."
        style="width:75%; padding:12px; border-radius:10px; border:1px solid #ccc;"
    >

    <button onclick="sendMessage()" style="padding:12px;">
        发送
    </button>

    <audio id="audioPlayer" controls style="width:100%; margin-top:20px;"></audio>

<script>
async function sendMessage() {
    const input = document.getElementById("userInput");
    const text = input.value;

    if (!text) return;

    const chat = document.getElementById("chat");

    chat.innerHTML += `
        <p><b>你：</b>${text}</p>
    `;

    input.value = "";

    const response = await fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: text
        })
    });

    const data = await response.json();

    chat.innerHTML += `
        <p><b>Honey：</b>${data.chinese}</p>
    `;

    const audio = document.getElementById("audioPlayer");
    audio.src = data.audio_url + "?t=" + new Date().getTime();
    audio.play();

    chat.scrollTop = chat.scrollHeight;
}
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():

    user_message = request.json.get("message")

    # Claude 回复（中文）
    response = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    chinese_reply = response.content[0].text

    # 翻译英文（让 Claude 自己翻）
    translation = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": f"Translate this natural Chinese conversation into natural spoken English only:\\n\\n{chinese_reply}"
            }
        ]
    )

    english_reply = translation.content[0].text

    # ElevenLabs TTS
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "text": english_reply,
        "model_id": "eleven_multilingual_v2"
    }

    audio_response = requests.post(
        url,
        json=payload,
        headers=headers
    )

    with open("output.mp3", "wb") as f:
        f.write(audio_response.content)

    return jsonify({
        "chinese": chinese_reply,
        "audio_url": "/audio"
    })


@app.route("/audio")
def audio():
    with open("output.mp3", "rb") as f:
        return f.read(), 200, {
            "Content-Type": "audio/mpeg"
        }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)