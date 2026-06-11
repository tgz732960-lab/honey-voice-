from flask import Flask, request, render_template_string, jsonify, send_file
import requests
import os
from anthropic import Anthropic

app = Flask(__name__)

# API KEY
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# 检查 key
if not ANTHROPIC_API_KEY:
    print("❌ 缺少 ANTHROPIC_API_KEY")

if not ELEVENLABS_API_KEY:
    print("❌ 缺少 ELEVENLABS_API_KEY")

anthropic = Anthropic(
    api_key=ANTHROPIC_API_KEY
)

VOICE_ID = "8gg0WXng9B2Fn5w1rJ7I"

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Honey Voice</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>

<body style="font-family: Arial; padding:20px; max-width:600px; margin:auto;">

<h1>Honey Voice</h1>

<div id="chat"
style="
border:1px solid #ddd;
padding:15px;
height:400px;
overflow:auto;
border-radius:12px;
margin-bottom:15px;
">
</div>

<input
id="userInput"
type="text"
placeholder="输入内容..."
style="
width:75%;
padding:12px;
border-radius:10px;
border:1px solid #ccc;
">

<button onclick="sendMessage()" style="padding:12px;">
发送
</button>

<audio
id="audioPlayer"
controls
style="width:100%; margin-top:20px;">
</audio>

<script>
async function sendMessage() {

    const input = document.getElementById("userInput");
    const text = input.value.trim();

    if (!text) return;

    const chat = document.getElementById("chat");

    chat.innerHTML += `
        <p><b>你：</b>${text}</p>
    `;

    input.value = "";

    try {

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

        // 如果后端报错
        if (data.error) {
            chat.innerHTML += `
                <p style="color:red;">
                Honey 出错：${data.error}
                </p>
            `;
            return;
        }

        chat.innerHTML += `
            <p><b>Honey：</b>${data.chinese}</p>
        `;

        const audio = document.getElementById("audioPlayer");

        if (data.audio_url) {
            audio.src =
                data.audio_url +
                "?t=" +
                new Date().getTime();

            audio.play();
        }

        chat.scrollTop = chat.scrollHeight;

    } catch (error) {

        chat.innerHTML += `
            <p style="color:red;">
            请求失败：${error}
            </p>
        `;
    }
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

    try:

        user_message = request.json.get("message")

        if not user_message:
            return jsonify({
                "error": "没有收到消息"
            }), 400

        # Claude 回复
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

        # 翻译成英文（用于语音）
        translation = anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content":
                    f"Translate this Chinese to natural spoken English only:\\n\\n{chinese_reply}"
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

        # 检查 ElevenLabs 是否成功
        if audio_response.status_code != 200:
            return jsonify({
                "error":
                f"ElevenLabs失败: {audio_response.text}"
            }), 500

        with open("output.mp3", "wb") as f:
            f.write(audio_response.content)

        return jsonify({
            "chinese": chinese_reply,
            "audio_url": "/audio"
        })

    except Exception as e:

        print("报错：", str(e))

        return jsonify({
            "error": str(e)
        }), 500


@app.route("/audio")
def audio():

    if os.path.exists("output.mp3"):
        return send_file(
            "output.mp3",
            mimetype="audio/mpeg"
        )

    return "No audio", 404


@app.route("/health")
def health():
    return {
        "status": "ok"
    }


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000
    )