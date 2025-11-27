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
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.email_from = os.getenv("EMAIL_FROM", self.email_user)
        self.email_enabled = all(
            [self.smtp_server, self.smtp_port, self.email_user, self.email_password, self.email_from]
        )
        if not self.email_enabled:
            print("⚠️  Email credentials not found. Email sending is disabled.")
    
    def generate_blog_article(self, prompt: str) -> str:
        """
        Generate a blog article using OpenAI API
        
        Args:
            prompt: The topic or prompt for the blog article
            
        Returns:
            The generated blog article text
        """
        system_prompt = """You are a professional blog writer. Write a well-structured, engaging blog article 
        on the given topic. The article should be comprehensive, informative, and well-formatted with:
        - A compelling title
        - An introduction
        - Multiple sections with clear headings
        - A conclusion
        
        Format the article with markdown-style headings (## for main headings, ### for subheadings).
        Make the article at least 1000 words long."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Write a blog article about: {prompt}"}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            article = response.choices[0].message.content
            return article
        except Exception as e:
            raise Exception(f"Error generating blog article: {str(e)}")
    
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
        Main processing function: generates article, creates PDF, and sends emails
        
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
        
        if not self.email_enabled:
            print("Email credentials not configured, skipping email delivery.")
            print(f"PDF saved as: {pdf_filename}")
            return pdf_filename

        # Load email list and send
        emails = self.load_email_list(email_list_file)
        if not emails:
            print(f"No email addresses found in {email_list_file}")
            print(f"PDF saved as: {pdf_filename}")
            return
        
        print(f"\nSending emails to {len(emails)} recipients...")
        for email in emails:
            self.send_email(email, pdf_filename, subject=f"Blog Article: {prompt}")
        
        print(f"\n✓ Process completed! PDF saved as: {pdf_filename}")


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python main.py <prompt> [email_list_file]")
        print("\nExample: python main.py 'The Future of Artificial Intelligence'")
        sys.exit(1)
    
    prompt = sys.argv[1]
    email_list_file = sys.argv[2] if len(sys.argv) > 2 else "email_list.txt"
    
    try:
        generator = BlogGenerator()
        generator.process(prompt, email_list_file)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

