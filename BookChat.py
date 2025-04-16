import os
import io
import uuid
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from werkzeug.utils import secure_filename
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# === CONFIGURATION === #
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt'}
MAX_CONTENT_LENGTH = 1024*1024*1024  # 1GB for very large files

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")  # Set this env variable for deployment

# === Flask Setup === #
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

print("API Key loaded:", bool(OPENAI_API_KEY))

# === Helper Functions === #
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def read_file(filepath):
    """Reads a (large) text file and returns as string."""
    with io.open(filepath, mode="r", encoding="utf-8") as f:
        return f.read()


# === Branding & Style === #
APP_BRAND = "📚 AskMyDocs"
APP_SUBTITLE = "Upload large files and ask questions about them!"
PRIMARY_COLOR = "#5176f8"
ACCENT_COLOR = "#cbd3ff"

# --- Main Page HTML Template --- #
HTML = f"""
<!doctype html>
<html lang="en">
<head>
    <title>{APP_BRAND}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
    body {{
        background: #f5f7fb;
        margin:0;
        font-family: 'Segoe UI', 'Roboto', Arial, sans-serif;
        color: #222;
    }}
    .navbar {{
        background: {PRIMARY_COLOR};
        padding: 12px 24px;
        color: white;
        font-size: 1.5em;
        display:flex;align-items:center;gap: 12px;
    }}
    .subtitle {{
        font-size: 1em;
        padding: 0 24px 12px 24px; color: #6b747f;
    }}
    .container {{
        max-width:830px;margin:32px auto;
        padding:24px;
        background: white;
        border-radius:16px;
        box-shadow:0 2px 16px #bfcdf04d;
        min-height:500px;
        display: flex;
    }}
    .left-pane {{
        flex: 1.1;
        border-right:1px solid #e3e6ed;
        padding-right: 24px;
    }}
    .right-pane {{
        flex: 1.9;
        padding-left:32px;
        min-width:0;
        display:flex;
        flex-direction:column;
        height: 600px;
    }}
    .brand-accent {{ color: {PRIMARY_COLOR};font-weight:600; }}
    /* File Upload */
    #file-upload-label {{
        padding:38px 12px;
        display:block;
        border:2px dashed #aac7ff;
        text-align:center;
        color: #42548d;
        background: #eef3fb;
        border-radius:12px;
        cursor:pointer;
        transition: border .2s;
    }}
    #file-upload-label.dragover {{
        border-color: {PRIMARY_COLOR};
        color: {PRIMARY_COLOR};
    }}
    #file-upload-input {{
        display:none;
    }}
    .file-status-list {{
        margin-top:18px;
        font-size:.97em;
        line-height:1.6;
        padding-left:0;
        list-style:none;
    }}
    .file-status-list li {{
        display:flex;align-items:center;gap:6px;
    }}
    .file-status-uploading::before {{
        content:"⏳";
        animation: blink 1s infinite;
    }}
    .file-status-uploaded::before {{
        content:"✅";
    }}
    @keyframes blink {{
        50% {{ opacity:.3; }}
    }}
    /* Chat UI */
    .chat-box {{
        flex: 1 1 0;
        overflow-y:auto;
        padding:4px 0 0 0;
    }}
    .chat-msg {{
        margin:18px 0;
        display:flex;
        align-items:flex-start;
        gap:12px;
        line-height:1.5;
    }}
    .chat-msg.user .avatar {{
        background:#5176f8;color:white
    }}
    .chat-msg.llm .avatar {{
        background:#e8f0ff;color:#5176f8
    }}
    .avatar {{
        border-radius: 50%;
        width:32px;height:32px;
        align-self:flex-start;
        display:grid;place-items:center;
        font-weight:600;font-size:1.04em;
    }}
    .bubble {{
        background: #f1f5fb;
        padding:12px 18px;
        border-radius:18px 18px 6px 18px;
        color:#222;font-size:1.06em;
        max-width:70ch;word-break:break-word;
        box-shadow: 0 1px 2px #bfd8fb1b;
    }}
    .chat-msg.llm .bubble {{
        background: {ACCENT_COLOR};
        border-radius:18px 18px 18px 6px;
    }}
    /* Chat input */
    .chat-input-area {{
        margin-top:auto;
        display:flex;gap:12px;
        padding:12px 0 0 0;
    }}
    .chat-input {{
        flex:1;
        padding:10px 14px;
        border-radius:8px;
        border:1.4px solid #b3bbe1;
        font-size:1.08em;
    }}
    .ask-btn {{
        padding:0 22px;
        background: {PRIMARY_COLOR};
        color:white;
        border:none;
        border-radius:7px;
        font-size:1.09em;
        font-weight:500;
        cursor:pointer;
        line-height:2;
        box-shadow:0 1px 7px {PRIMARY_COLOR}24;
        transition:background .2s;
    }}
    .ask-btn:disabled {{
        background:#c4ceec;
        cursor: not-allowed;
    }}
    .status-bar {{
        margin-top:14px;font-size:.96em;
        color:#4977e6;
        display: flex;align-items:center;gap:6px;
        min-height:24px;
    }}
    @media (max-width:900px){{
        .container {{
            flex-direction:column;
            padding:16px 4px;
            min-width: auto;
        }}
        .right-pane, .left-pane {{
            padding:0;
            border:none;
            min-width:0;
        }}
        .right-pane {{margin-top:26px;}}
    }}
    </style>
</head>
<body>
    <div class="navbar">
        {APP_BRAND}
        <span style="font-size:0.8em;padding-left:12px;letter-spacing:0;" class="brand-accent">Alpha</span>
    </div>
    <div class="subtitle">
        {APP_SUBTITLE}
    </div>
    <div class="container">
        <!-- Left: Upload files -->
        <div class="left-pane">
            <form id="file-upload-form" enctype="multipart/form-data">
                <label id="file-upload-label" for="file-upload-input">
                    <b>Click or drag</b> to upload multiple .txt files
                    <br><span style="font-size:0.93em;color:#7d8eba;">(up to 1GB per file)</span>
                </label>
                <input type="file" id="file-upload-input" name="files" multiple accept=".txt"/>
            </form>
            <ul class="file-status-list" id="file-status-list"></ul>
            <div class="status-bar" id="upload-status"></div>
        </div>

        <!-- Right: Q&A -->
        <div class="right-pane">
            <div class="chat-box" id="chat-box"></div>
            <form class="chat-input-area" id="question-form" autocomplete="off">
                <input class="chat-input" id="chat-input" type="text" placeholder="Ask a question about your uploaded files..." autocomplete="off" />
                <button type="submit" class="ask-btn" id="ask-btn" disabled>Ask</button>
            </form>
            <div class="status-bar" id="chat-status"></div>
        </div>
    </div>
    <script>
    // --- File Upload Logic ---
    let fileStatus = {{}};
    let uploadedFiles = [];

    function renderFileStatus() {{
        const list = document.getElementById('file-status-list');
        list.innerHTML = '';
        Object.entries(fileStatus).forEach(([name, st]) => {{
            let cls = st.status === 'uploaded' ? 'file-status-uploaded' : 'file-status-uploading';
            let li = document.createElement('li');
            li.className = cls;
            li.innerHTML = "<span>" + name + "</span>";
            list.appendChild(li);
        }});
    }}
    function markFileStatus(name, status) {{
        fileStatus[name] = {{ status: status }};
        renderFileStatus();
        // Enable ask button only if *any* file uploaded
        document.getElementById('ask-btn').disabled = (Object.values(fileStatus).filter(x => x.status === 'uploaded').length === 0);
    }}

    // Drag & Drop for upload area
    let lbl = document.getElementById('file-upload-label');
    lbl.addEventListener('dragover', function(e) {{
        e.preventDefault(); e.stopPropagation();
        lbl.classList.add('dragover');
    }});
    lbl.addEventListener('dragleave', function(e) {{
        e.preventDefault(); e.stopPropagation();
        lbl.classList.remove('dragover');
    }});
    lbl.addEventListener('drop', function(e) {{
        e.preventDefault(); e.stopPropagation();
        lbl.classList.remove('dragover');
        let files = e.dataTransfer.files;
        handleFilesUpload(files);
    }});

    document.getElementById('file-upload-input').addEventListener('change', function(e) {{
        let files = e.target.files;
        handleFilesUpload(files);
    }});

    function handleFilesUpload(files) {{
        Array.from(files).forEach(file => {{
            if (file && file.name.toLowerCase().endsWith('.txt')) {{
                markFileStatus(file.name, "uploading");
                uploadOne(file);
            }}
        }});
    }}

    function uploadOne(file) {{
        let fd = new FormData();
        fd.append("file", file, file.name);

        fetch('/upload', {{
            method: 'POST',
            body: fd
        }}).then(resp => resp.json())
        .then(data => {{
            if(data.success) {{
                uploadedFiles.push(data.id);
                markFileStatus(file.name, "uploaded");
            }} else {{
                markFileStatus(file.name, "Error");
                setUploadStatus("Error: " + data.error);
            }}
        }}).catch(e => {{
            markFileStatus(file.name, "Error");
            setUploadStatus("Error uploading file.");
        }});
    }}

    function setUploadStatus(msg) {{
        document.getElementById('upload-status').textContent = msg;
        setTimeout(()=>{{ document.getElementById('upload-status').textContent=''; }}, 4600);
    }}

    // --- Chat UI Logic ---
    let chatBox = document.getElementById('chat-box');
    let chat = []; // {{role, content}}

    function addMessage(role, content) {{
        chat.push({{role, content}});
        renderChat();
        if(role === "user") scrollChatToBottom();
        else setTimeout(()=>scrollChatToBottom(), 300);
    }}
    function renderChat() {{    
        chatBox.innerHTML = chat.map(msg =>
            `<div class="chat-msg ${{msg.role}}">
                <span class="avatar">${{msg.role==="user"?"🧑":"🤖"}}</span>
                <span class="bubble">${{escapeHTML(msg.content)}}</span>
            </div>`
        ).join('');
    }}
    function escapeHTML(txt) {{
        let div = document.createElement('div');
        div.textContent = txt;
        return div.innerHTML;
    }}
    function scrollChatToBottom() {{
        chatBox.scrollTop = chatBox.scrollHeight+9000;
    }}

    // --- Send Question Logic ---
    let questionForm = document.getElementById('question-form');
    let chatStatus = document.getElementById('chat-status');
    questionForm.addEventListener('submit', async function(e) {{
        e.preventDefault();
        let q = document.getElementById('chat-input').value.trim();
        if(!q) return;
        addMessage("user", q);
        document.getElementById('chat-input').value='';
        document.getElementById('ask-btn').disabled = true;
        chatStatus.innerHTML = '<span style="color: #5176f8">●</span> Asking model...';
        let resp = await askQuestion(q);
        addMessage("llm", resp);
        chatStatus.innerHTML = '';
        // Re-enable after answer and if files uploaded
        document.getElementById('ask-btn').disabled = uploadedFiles.length === 0;
    }});

    // Enable send on typing (while files uploaded)
    document.getElementById('chat-input').oninput = function() {{
        document.getElementById('ask-btn').disabled = (
            !this.value.trim() 
            || (Object.values(fileStatus).filter(x => x.status === 'uploaded').length === 0)
        );
    }}

    async function askQuestion(q) {{
        try {{
            let resp = await fetch('/ask', {{
                method: 'POST',
                headers: {{'Content-Type':'application/json'}},
                body: JSON.stringify({{question: q, file_ids: uploadedFiles}})
            }});
            if(resp.ok) {{
                let data = await resp.json();
                return data.answer || "[No answer received]";
            }} else {{
                return "[Server error.]";
            }}
        }} catch(e) {{
            return "[Connection failed!]";
        }}
    }}
    </script>
</body>
</html>
"""

# ===== Flask Endpoints =======

@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML)

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"})
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"})
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_id = f"{uuid.uuid4().hex}_{filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
        file.save(save_path)
        return jsonify({"success": True, "id": file_id})
    else:
        return jsonify({"success": False, "error": "Invalid file type"})

@app.route('/uploads/<file_id>', methods=["GET"])
def download_file(file_id):
    return send_from_directory(app.config['UPLOAD_FOLDER'], file_id)

@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    question = data.get("question")
    file_ids = data.get("file_ids")
    if not question or not file_ids:
        return jsonify({"answer": "Missing question or files."})

    # read all selected files (concatenate)
    docs = []
    for file_id in file_ids:
        fp = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
        if not os.path.exists(fp): continue
        docs.append(read_file(fp))
    if not docs:
        return jsonify({"answer": "No content found in uploaded files."})
    # Compose prompt (user Q + all files)
    # prompt = f"""Given the content of the following text files:\n{' '.join(docs)}\n\nQuestion: {question}\nAnswer:"""
    # We'll feed as: input="...."

    prompt = (
        "Answer the user's question based only on the following documents (from uploaded files):\n\n"
        f"{'-'*32}\n"
        f"{''.join(docs)}\n"
        f"{'-'*32}\n"
        f"User Question: {question}\n"
        f"Answer as helpfully as possible."
    )
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        # responses API supports long context models
        resp = client.responses.create(
            model="gpt-4.1-nano-2025-04-14",
            input=prompt
        )
        answer = resp.output_text.strip()
    except Exception as ex:
        answer = f"Error from OpenAI API: {ex}"
    # short answer
    if len(answer) > 10000:
        answer = answer[:10000] + "\n...[truncated]..."
    return jsonify({"answer": answer})

# ===== Static serving for favicon on localhost (optional) =====
@app.route('/favicon.ico')
def favicon():
    return "", 204

# ========= Run App =========
if __name__ == '__main__':
    import webbrowser
    import threading
    port = int(os.environ.get("PORT", 5600))
    url = f"http://127.0.0.1:{port}/"
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    print(f"\n* App running at {url}\n")
    app.run(host="0.0.0.0", port=port, debug=False)