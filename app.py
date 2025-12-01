#!/usr/bin/env python3
"""
Flask API for Blog Generator
Provides REST API endpoints for blog generation and topic management
"""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from main import BlogGenerator
from topic_manager import TopicManager
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'timezone': 'UTC',
        'services': {
            'openai': bool(os.getenv('OPENAI_API_KEY')),
            's3': bool(os.getenv('AWS_S3_BUCKET_NAME')),
            'email': bool(os.getenv('EMAIL_USER'))
        }
    }), 200


@app.route('/api/generate', methods=['POST'])
def generate_blog():
    """
    Generate a blog article
    
    Request body:
    {
        "topic": "string (required)",
        "audience": "string (optional)",
        "email_list": ["email1@example.com", "email2@example.com"] (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'topic' not in data:
            return jsonify({
                'error': 'Missing required field: topic'
            }), 400
        
        topic = data['topic']
        audience = data.get('audience', 'General readers interested in the topic')
        
        # Initialize blog generator
        generator = BlogGenerator()
        
        # Generate article
        print(f"Generating blog for topic: {topic}")
        article = generator.generate_blog_article(topic)
        
        # Create PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c for c in topic[:50] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_topic = safe_topic.replace(' ', '_')
        pdf_filename = f"blog_article_{safe_topic}_{timestamp}.pdf"
        
        generator.create_pdf(article, pdf_filename, title=topic)
        
        # Upload to S3 if configured
        s3_url = None
        if generator.s3_handler.enabled:
            s3_url = generator.s3_handler.upload_file(pdf_filename)
        
        # Send emails if requested
        email_list = data.get('email_list', [])
        emails_sent = []
        if email_list and generator.email_enabled:
            for email in email_list:
                try:
                    generator.send_email(email, pdf_filename, subject=f"Blog Article: {topic}", s3_url=s3_url)
                    emails_sent.append(email)
                except Exception as e:
                    print(f"Error sending email to {email}: {str(e)}")
        
        return jsonify({
            'success': True,
            'topic': topic,
            'article': article,
            'pdf_filename': pdf_filename,
            's3_url': s3_url,
            'emails_sent': emails_sent,
            'timestamp': timestamp
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/topics', methods=['GET'])
def get_topics():
    """Get all topics from local file"""
    try:
        topic_manager = TopicManager()
        topics = topic_manager.get_all_topics()
        
        return jsonify({
            'success': True,
            'count': len(topics),
            'topics': topics
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/topics/today', methods=['GET'])
def get_today_topic():
    """Get today's scheduled topic (UTC)"""
    try:
        topic_manager = TopicManager()
        topic = topic_manager.get_next_available_topic()
        
        if not topic:
            return jsonify({
                'error': 'No topics available'
            }), 404
        
        return jsonify({
            'success': True,
            'topic': topic,
            'source': 'local_file',
            'date': datetime.utcnow().strftime("%Y-%m-%d"),
            'timezone': 'UTC'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/topics/next', methods=['GET'])
def get_next_topic():
    """Get next available topic (alias for /api/topics/today)"""
    return get_today_topic()


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    
    print(f"Starting Flask API on port {port}...")
    print(f"Debug mode: {debug}")
    print(f"API endpoints:")
    print(f"  GET  /api/health")
    print(f"  POST /api/generate")
    print(f"  GET  /api/topics")
    print(f"  GET  /api/topics/today")
    print(f"  GET  /api/topics/next")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
