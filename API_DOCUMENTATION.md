# Blog Generator API Documentation

REST API for automated blog generation with OpenAI, S3 storage, and Google Sheets integration.

## Base URL

```
http://localhost:5000
```

## Endpoints

### 1. Health Check

Check API status and service availability.

**Endpoint**: `GET /api/health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-30T21:15:00",
  "services": {
    "openai": true,
    "s3": true,
    "google_sheets": true,
    "email": false
  }
}
```

---

### 2. Generate Blog Article

Generate a blog article on a given topic.

**Endpoint**: `POST /api/generate`

**Request Body**:
```json
{
  "topic": "The Future of Artificial Intelligence",
  "audience": "Tech enthusiasts and business leaders",
  "email_list": ["user@example.com"]
}
```

**Parameters**:
- `topic` (required): Blog topic/title
- `audience` (optional): Target audience description
- `email_list` (optional): Array of email addresses to send the PDF to

**Response**:
```json
{
  "success": true,
  "topic": "The Future of Artificial Intelligence",
  "article": "# The Future of Artificial Intelligence\n\n...",
  "pdf_filename": "blog_article_The_Future_of_AI_20251130_211500.pdf",
  "s3_url": "https://your-bucket.s3.us-east-1.amazonaws.com/blog_article_...",
  "emails_sent": ["user@example.com"],
  "timestamp": "20251130_211500"
}
```

---

### 3. Get All Topics

Retrieve all topics from Google Sheets.

**Endpoint**: `GET /api/topics`

**Response**:
```json
{
  "success": true,
  "count": 15,
  "topics": [
    {
      "date": "2025-11-30",
      "topic": "The Future of AI in Healthcare",
      "status": "Pending",
      "row": 2
    },
    {
      "date": "2025-12-01",
      "topic": "Climate Change Solutions",
      "status": "Pending",
      "row": 3
    }
  ]
}
```

---

### 4. Get Today's Topic

Get the topic scheduled for today (or next available).

**Endpoint**: `GET /api/topics/today`

**Response**:
```json
{
  "success": true,
  "topic": "The Future of AI in Healthcare",
  "source": "google_sheets",
  "date": "2025-11-30"
}
```

**Alternative Endpoint**: `GET /api/topics/next` (same functionality)

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Missing required field: topic"
}
```

### 404 Not Found
```json
{
  "error": "No topics available"
}
```

### 500 Internal Server Error
```json
{
  "error": "Error message here"
}
```

### 503 Service Unavailable
```json
{
  "error": "Google Sheets not configured"
}
```

---

## Usage Examples

### cURL

**Generate Blog**:
```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "The Future of AI",
    "audience": "Tech enthusiasts"
  }'
```

**Get Today's Topic**:
```bash
curl http://localhost:5000/api/topics/today
```

**Health Check**:
```bash
curl http://localhost:5000/api/health
```

### Python

```python
import requests

# Generate blog
response = requests.post('http://localhost:5000/api/generate', json={
    'topic': 'The Future of AI',
    'audience': 'Tech enthusiasts'
})
data = response.json()
print(f"S3 URL: {data['s3_url']}")

# Get today's topic
response = requests.get('http://localhost:5000/api/topics/today')
topic_data = response.json()
print(f"Today's topic: {topic_data['topic']}")
```

### JavaScript (Fetch)

```javascript
// Generate blog
fetch('http://localhost:5000/api/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    topic: 'The Future of AI',
    audience: 'Tech enthusiasts'
  })
})
.then(res => res.json())
.then(data => console.log('S3 URL:', data.s3_url));

// Get today's topic
fetch('http://localhost:5000/api/topics/today')
  .then(res => res.json())
  .then(data => console.log('Topic:', data.topic));
```

---

## Running the API

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables in .env
OPENAI_API_KEY=your_key
AWS_S3_BUCKET_NAME=your_bucket
GOOGLE_SHEET_CSV_URL=your_csv_url
FLASK_ENV=development
FLASK_PORT=5000

# Run the API
python app.py
```

The API will start on `http://localhost:5000`

### Production

Set `FLASK_ENV=production` in your `.env` file for production deployment.

---

## CORS

CORS is enabled for all origins by default. To restrict origins, modify the `CORS(app)` line in `app.py`.

---

## Rate Limiting

Currently no rate limiting is implemented. Consider adding rate limiting for production use.

---

## Authentication

Currently no authentication is required. For production, consider adding:
- API keys
- OAuth2
- JWT tokens

---

## Notes

- PDFs are saved locally and optionally uploaded to S3
- Email sending requires SMTP configuration
- Google Sheets integration is optional (falls back to local file)
- All timestamps are in ISO 8601 format
