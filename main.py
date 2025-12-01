#!/usr/bin/env python3
"""
Blog Generator - Creates blog articles from prompts and emails them as PDFs
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from openai import OpenAI
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from datetime import datetime
from s3_handler import S3Handler

# Load environment variables
load_dotenv()


class BlogGenerator:
    def __init__(self):
        """Initialize the Blog Generator with API keys and configuration"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        # Email configuration (optional)
        self.smtp_server = os.getenv("SMTP_SERVER") or "smtp.gmail.com"
        self.smtp_port = int(os.getenv("SMTP_PORT") or "587")
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.email_from = self.email_user
        self.email_enabled = all(
            [self.smtp_server, self.smtp_port, self.email_user, self.email_password, self.email_from]
        )
        if not self.email_enabled:
            print("⚠️  Email credentials not found. Email sending is disabled.")
        
        # S3 configuration (optional)
        self.s3_handler = S3Handler()
    
    def generate_blog_article(self, prompt: str) -> str:
        """
        Generate a blog article using OpenAI API
        
        Args:
            prompt: The topic or prompt for the blog article
            
        Returns:
            The generated blog article text
        """
        # Try to load custom prompt from frame.txt
        system_prompt = self._load_prompt_template()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Topic: {prompt}\nAudience: General readers interested in the topic\nGenerate the blog following the system instructions."}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            article = response.choices[0].message.content
            return article
        except Exception as e:
            raise Exception(f"Error generating blog article: {str(e)}")
    
    def _load_prompt_template(self) -> str:
        """
        Load prompt template from frame.txt if it exists, otherwise use default
        
        Returns:
            System prompt string
        """
        frame_file = "frame.txt"
        
        if os.path.exists(frame_file):
            try:
                with open(frame_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        print("✓ Using custom prompt template from frame.txt")
                        return content
            except Exception as e:
                print(f"⚠️  Error reading frame.txt: {str(e)}, using default prompt")
        
        # Default prompt if frame.txt doesn't exist or is empty
        print("✓ Using default prompt template")
        return """You are an expert-level writer who specializes in creating authoritative, well-researched, and polished professional blogs. Follow these instructions carefully:

Topic: {topic}

Goal:
- Explain the topic with clarity and depth
- Provide original insights, not generic filler
- Use real facts or credible reasoning—never invent data
- Challenge assumptions and add expert-level commentary

Tone & Style:
- Professional, concise, confident
- No fluff, no motivational padding
- No clichés or obvious statements
- Short, punchy sentences with tight logic
- Maintain a human, analytical voice

Structure:
- Strong, problem-focused introduction
- Clear, non-generic headings
- Use real examples when they strengthen the argument
- Include at least one unconventional insight
- Provide actionable takeaways
- Conclusion must reinforce the central argument

Depth & Constraints:
- Write at expert depth—assume an intelligent reader
- Target 900–1400 words
- Avoid surface-level summaries
- Ensure logical narrative arc

Quality Rules:
- No fake stats, sources, or invented research
- No repetition, filler, or vague statements
- Flow and quality must match top-tier publications

Format the article with markdown-style headings (## for main headings, ### for subheadings)."""
    
    def create_pdf(self, article: str, output_path: str, title: str = "Blog Article"):
        """
        Convert the blog article to a PDF file
        
        Args:
            article: The blog article text
            output_path: Path where the PDF will be saved
            title: Title for the PDF document
        """
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#1a1a1a',
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=18,
            textColor='#2c3e50',
            spaceAfter=12,
            spaceBefore=12
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=14,
            textColor='#34495e',
            spaceAfter=8,
            spaceBefore=8
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            textColor='#333333',
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leading=14
        )
        
        # Parse and add content
        lines = article.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.2*inch))
                continue
            
            if line.startswith('## '):
                # Main heading
                heading_text = line[3:].strip()
                story.append(Paragraph(heading_text, heading_style))
            elif line.startswith('### '):
                # Subheading
                subheading_text = line[4:].strip()
                story.append(Paragraph(subheading_text, subheading_style))
            elif line.startswith('#'):
                # Title (single #)
                title_text = line[1:].strip()
                story.append(Paragraph(title_text, title_style))
            else:
                # Body text
                story.append(Paragraph(line, body_style))
        
        doc.build(story)
    
    def load_email_list(self, file_path: str = "email_list.txt") -> list:
        """
        Load email addresses from a text file
        
        Args:
            file_path: Path to the file containing email addresses
            
        Returns:
            List of email addresses
        """
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found. Creating a sample file.")
            with open(file_path, 'w') as f:
                f.write("# Add email addresses here, one per line\n")
                f.write("# Lines starting with # are ignored\n")
            return []
        
        emails = []
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    emails.append(line)
        
        return emails
    
    def send_email(self, recipient: str, pdf_path: str, subject: str = "Your Blog Article"):
        """
        Send the PDF via email
        
        Args:
            recipient: Email address of the recipient
            pdf_path: Path to the PDF file
            subject: Email subject line
        """
        if not self.email_enabled:
            raise RuntimeError("Email sending is disabled because SMTP credentials are missing.")
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = recipient
            msg['Subject'] = subject
            
            body = f"""Hello,

Please find attached the blog article you requested.

Best regards,
Blog Generator
"""
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach PDF
            with open(pdf_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(pdf_path)}'
            )
            msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_from, recipient, text)
            server.quit()
            
            print(f"✓ Email sent successfully to {recipient}")
        except Exception as e:
            print(f"✗ Error sending email to {recipient}: {str(e)}")
    
    def process(self, prompt: str, email_list_file: str = "email_list.txt"):
        """
        Main processing function: generates article, creates PDF, uploads to S3, and sends emails
        
        Args:
            prompt: The topic/prompt for the blog article
            email_list_file: Path to file containing email addresses
        """
        print(f"Generating blog article for: {prompt}")
        
        # Generate article
        print("Creating blog article...")
        article = self.generate_blog_article(prompt)
        print("✓ Blog article generated successfully")
        
        # Create PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_prompt = "".join(c for c in prompt[:50] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_prompt = safe_prompt.replace(' ', '_')
        pdf_filename = f"blog_article_{safe_prompt}_{timestamp}.pdf"
        
        print(f"Creating PDF: {pdf_filename}")
        self.create_pdf(article, pdf_filename, title=prompt)
        print("✓ PDF created successfully")
        
        # Upload to S3 if configured
        s3_url = None
        if self.s3_handler.enabled:
            print("\nUploading PDF to S3...")
            s3_url = self.s3_handler.upload_file(pdf_filename)
            if s3_url:
                print(f"✓ S3 URL: {s3_url}")
        
        if not self.email_enabled:
            print("\nEmail credentials not configured, skipping email delivery.")
            print(f"PDF saved locally as: {pdf_filename}")
            if s3_url:
                print(f"PDF available at: {s3_url}")
            return pdf_filename

        # Load email list and send
        emails = self.load_email_list(email_list_file)
        if not emails:
            print(f"\nNo email addresses found in {email_list_file}")
            print(f"PDF saved locally as: {pdf_filename}")
            if s3_url:
                print(f"PDF available at: {s3_url}")
            return pdf_filename
        
        print(f"\nSending emails to {len(emails)} recipients...")
        for email in emails:
            self.send_email(email, pdf_filename, subject=f"Blog Article: {prompt}")
        
        print(f"\n✓ Process completed!")
        print(f"PDF saved locally as: {pdf_filename}")
        if s3_url:
            print(f"PDF available at: {s3_url}")
        
        return pdf_filename


def main():
    """Main entry point"""
    import sys
    from topic_manager import TopicManager
    
    # Check if a prompt was provided as argument
    if len(sys.argv) >= 2:
        # Use provided prompt
        prompt = sys.argv[1]
        email_list_file = sys.argv[2] if len(sys.argv) > 2 else "email_list.txt"
    else:
        # Use topic manager to get next topic
        print("No topic provided, using topic manager...")
        topic_manager = TopicManager()
        prompt = topic_manager.get_next_topic()
        
        if not prompt:
            print("Error: No topics available. Please add topics to topics.txt")
            print("\nUsage: python main.py [prompt] [email_list_file]")
            print("  If no prompt is provided, the next topic from topics.txt will be used.")
            sys.exit(1)
        
        email_list_file = "email_list.txt"
    
    try:
        generator = BlogGenerator()
        generator.process(prompt, email_list_file)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

