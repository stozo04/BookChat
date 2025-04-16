# 📚 BookChat

BookChat is a web application that allows you to upload text files and ask questions about their content using AI. It's built with Flask and uses OpenAI's GPT-4.1 nano model to provide intelligent responses based on your uploaded documents.

## Features

- 📁 Upload multiple text files (up to 1GB each)
- 💬 Interactive chat interface
- 🤖 AI-powered question answering
- 🎨 Modern, responsive UI
- 🔒 Secure file handling
- ⚡ Fast and efficient document processing

## Prerequisites

- Python 3.7 or higher
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/BookChat.git
cd BookChat
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Start the application:
```bash
python BookChat.py
```

2. Open your web browser and navigate to `http://127.0.0.1:5600`

3. Upload text files by either:
   - Clicking the upload area
   - Dragging and dropping files
   - Using the file picker

4. Once files are uploaded, you can start asking questions about their content

## How It Works

1. Files are securely stored in the `uploads` directory
2. When you ask a question, the application:
   - Reads the content of all uploaded files
   - Sends the content along with your question to OpenAI's API
   - Displays the AI's response in the chat interface

## Security

- Files are stored with unique UUIDs to prevent conflicts
- File names are sanitized before storage
- Only `.txt` files are allowed
- Maximum file size is limited to 1GB

## Development

The application is built using:
- Flask for the web server
- OpenAI API for AI processing
- Modern HTML/CSS for the UI
- Vanilla JavaScript for interactivity

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 