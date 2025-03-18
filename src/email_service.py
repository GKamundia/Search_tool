import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime

from src.models import SavedSearch, SearchResult

class EmailService:
    """Service to send email notifications"""
    
    def __init__(self, app=None):
        self.logger = logging.getLogger(__name__)
        self.app = app
        
        # Email configuration
        if app:
            self.sender = app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
            self.smtp_server = app.config.get('MAIL_SERVER', 'localhost')
            self.smtp_port = app.config.get('MAIL_PORT', 25)
            self.username = app.config.get('MAIL_USERNAME')
            self.password = app.config.get('MAIL_PASSWORD')
            self.use_tls = app.config.get('MAIL_USE_TLS', False)
        else:
            # Default configuration
            self.sender = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@example.com')
            self.smtp_server = os.getenv('MAIL_SERVER', 'localhost')
            self.smtp_port = int(os.getenv('MAIL_PORT', 25))
            self.username = os.getenv('MAIL_USERNAME')
            self.password = os.getenv('MAIL_PASSWORD')
            self.use_tls = os.getenv('MAIL_USE_TLS', 'False').lower() == 'true'
    
    def send_new_papers_notification(self, email: str, search: SavedSearch, 
                                    new_papers: List[Dict]) -> bool:
        """
        Send email notification about new papers
        
        Args:
            email: Recipient email address
            search: SavedSearch object
            new_papers: List of new papers
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not email or not new_papers:
            return False
            
        # Create email subject
        subject = f"New papers found for '{search.name}'"
        
        # Create email body
        html = self._create_new_papers_email_html(search, new_papers)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.sender
        msg['To'] = email
        
        # Attach HTML content
        msg.attach(MIMEText(html, 'html'))
        
        # Send email
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)
                self.logger.info(f"Email notification sent to {email}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _create_new_papers_email_html(self, search: SavedSearch, new_papers: List[Dict]) -> str:
        """Create HTML content for new papers email"""
        app_url = os.getenv('APP_URL', 'http://localhost:5000')
        
        html = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
              .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
              h1 {{ color: #2c3e50; font-size: 24px; }}
              h2 {{ color: #3498db; font-size: 20px; margin-top: 20px; }}
              .paper {{ margin-bottom: 20px; padding: 15px; border-left: 4px solid #3498db; background-color: #f9f9f9; }}
              .paper h3 {{ margin-top: 0; color: #2c3e50; }}
              .paper p {{ margin: 5px 0; }}
              .paper .meta {{ font-size: 12px; color: #7f8c8d; }}
              .paper .abstract {{ font-style: italic; color: #555; margin-top: 10px; }}
              .button {{ display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; 
                        text-decoration: none; border-radius: 4px; margin-top: 15px; }}
              .footer {{ margin-top: 30px; font-size: 12px; color: #7f8c8d; border-top: 1px solid #eee; padding-top: 10px; }}
            </style>
          </head>
          <body>
            <div class="container">
              <h1>New Papers Alert</h1>
              <p>We found {len(new_papers)} new papers matching your saved search "{search.name}":</p>
              
              <div class="papers">
        """
        
        # Add papers
        for paper in new_papers:
            title = paper.get('title', 'Untitled')
            authors = paper.get('authors', '')
            abstract = paper.get('abstract', '')
            url = paper.get('url') or paper.get('pdf_url', '#')
            database = paper.get('database', '').upper()
            
            # Truncate abstract if too long
            if len(abstract) > 300:
                abstract = abstract[:300] + "..."
            
            html += f"""
              <div class="paper">
                <h3><a href="{url}" target="_blank">{title}</a></h3>
                <p><strong>Authors:</strong> {authors}</p>
                <p class="meta">Source: {database}</p>
                <div class="abstract">{abstract}</div>
              </div>
            """
        
        # Add footer
        html += f"""
              </div>
              
              <a href="{app_url}/new_papers" class="button">View All New Papers</a>
              
              <div class="footer">
                <p>You received this email because you subscribed to alerts for this search.</p>
                <p>To manage your alert preferences, <a href="{app_url}/saved_searches">click here</a>.</p>
              </div>
            </div>
          </body>
        </html>
        """
        
        return html
    
    def send_test_email(self, email: str) -> bool:
        """Send a test email to verify configuration"""
        subject = "Test Email from Academic Search Portal"
        
        html = """
        <html>
          <body>
            <h1>Test Email</h1>
            <p>This is a test email from the Academic Search Portal.</p>
            <p>If you received this email, your email configuration is working correctly.</p>
          </body>
        </html>
        """
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.sender
        msg['To'] = email
        
        # Attach HTML content
        msg.attach(MIMEText(html, 'html'))
        
        # Send email
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)
                self.logger.info(f"Test email sent to {email}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to send test email: {str(e)}")
            return False
