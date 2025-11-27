# Blog Generator

A Python application that generates blog articles from prompts using AI, converts them to PDF, and emails them to a list of recipients.

## Features

-  AI-powered blog article generation using OpenAI API
-  Automatic PDF conversion with professional formatting
-  Optional email distribution to multiple recipients
-  Configurable via environment variables

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Email account with SMTP access (only if you plan to auto-send emails)

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `env_template.txt` to `.env`
   - Edit `.env` and add your credentials:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     OPENAI_MODEL=gpt-4
     # The following are optional. Omit them to skip email sending.
     SMTP_SERVER=smtp.gmail.com
     SMTP_PORT=587
     EMAIL_USER=your_email@gmail.com
     EMAIL_PASSWORD=your_app_password_here
     EMAIL_FROM=your_email@gmail.com
     ```

## Email Setup

### Gmail (optional)
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
   - Use this password in `EMAIL_PASSWORD`

### Other Email Providers (optional)
- **Outlook/Hotmail**: `smtp-mail.outlook.com`, port 587
- **Yahoo**: `smtp.mail.yahoo.com`, port 587
- **Custom SMTP**: Update `SMTP_SERVER` and `SMTP_PORT` in `.env`

## Email List

Edit `email_list.txt` and add recipient email addresses, one per line:
```
recipient1@example.com
recipient2@example.com
recipient3@example.com
```

Lines starting with `#` are ignored (useful for comments).

## Usage

### Basic Usage (PDF only)
```bash
python main.py "The Future of Artificial Intelligence"
```

### With Email Delivery
```bash
python main.py "Climate Change Solutions" custom_emails.txt
```

### As a Python Module
```python
from main import BlogGenerator

generator = BlogGenerator()
generator.process("Your blog topic here")
```

## How It Works

1. **Prompt Input**: Takes a topic/prompt as input
2. **AI Generation**: Uses OpenAI API to generate a comprehensive blog article
3. **PDF Creation**: Converts the article to a professionally formatted PDF
4. **Email Distribution** (optional): Sends the PDF to recipients if SMTP credentials are configured

## Output

- PDF files are saved in the current directory with format: `blog_article_<topic>_<timestamp>.pdf`
- Email confirmations are printed to the console when email is enabled

## Configuration Options

### OpenAI Models
You can use different OpenAI models by changing `OPENAI_MODEL` in `.env`:
- `gpt-4` (default) - Best quality, slower
- `gpt-3.5-turbo` - Faster, lower cost

### PDF Customization
Edit the `create_pdf` method in `main.py` to customize:
- Font sizes
- Colors
- Spacing
- Page layout
