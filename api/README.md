# URL to HTML Converter API

Production-ready REST API for fetching HTML content from URLs using a progressive fallback strategy.

## Features

- **Progressive Fallback**: Static → XHR → Custom JS Rendering → Decodo
- **Massive Scaling**: Supports thousands of URLs with configurable concurrency
- **Multi-Service Parallel Processing**: Utilizes multiple custom JS rendering services in parallel
- **Intelligent Skeleton Detection**: Automatically detects and retries skeleton content
- **No Authentication Required**: Ready to deploy anywhere
- **Production Ready**: Health checks, error handling, logging, Docker support

## API Endpoints

### GET `/`
Get API information and available endpoints.

**Response:**
```json
{
  "name": "URL to HTML Converter API",
  "version": "1.0.0",
  "description": "Production-ready API for fetching HTML content...",
  "endpoints": {
    "health": "/health",
    "batch_fetch": "/api/v1/fetch-batch",
    "docs": "/docs",
    "redoc": "/redoc"
  }
}
```

### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 1234.56
}
```

### POST `/api/v1/fetch-batch`
Fetch HTML content for a batch of URLs.

**Request Body:**
```json
{
  "urls": [
    "https://example.com/page1",
    "https://example.com/page2"
  ],
  "config": {
    "static_xhr_concurrency": 100,
    "custom_js_service_endpoints": [
      "service1.com",
      "service2.com"
    ],
    "custom_js_batch_size": 20,
    "decodo_enabled": true
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "url": "https://example.com/page1",
      "html": "<html>...</html>",
      "method": "static",
      "status": "success",
      "error": null
    },
    {
      "url": "https://example.com/page2",
      "html": "<html>...</html>",
      "method": "custom_js",
      "status": "success",
      "error": null
    }
  ],
  "summary": {
    "total": 2,
    "success": 2,
    "failed": 0,
    "by_method": {
      "static": 1,
      "custom_js": 1
    },
    "total_time": 5.23
  },
  "success": true
}
```

## Configuration

### Environment Variables

#### Server Configuration
- `API_HOST`: Server host (default: `0.0.0.0`)
- `API_PORT`: Server port (default: `8000`)
- `API_WORKERS`: Number of worker processes (default: `1`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

#### Default Batch Configuration
- `DEFAULT_STATIC_XHR_CONCURRENCY`: Max concurrent static/XHR requests (default: `100`)
- `DEFAULT_STATIC_XHR_TIMEOUT`: Timeout in seconds (default: `30`)
- `DEFAULT_CUSTOM_JS_BATCH_SIZE`: URLs per batch (default: `20`)
- `DEFAULT_CUSTOM_JS_COOLDOWN`: Cooldown between batches in seconds (default: `120`)
- `DEFAULT_CUSTOM_JS_TIMEOUT`: Timeout in seconds (default: `300`)
- `DEFAULT_DECODO_ENABLED`: Enable Decodo fallback (default: `true`)
- `DEFAULT_DECODO_TIMEOUT`: Decodo timeout in seconds (default: `180`)

#### Custom JS Services
- `CUSTOM_JS_SERVICES`: Comma-separated list of service endpoints
  - Example: `service1.com,service2.com,service3.com`
  - If not set, uses default 13 services

#### Decodo Credentials
- `DECODO_USERNAME`: Decodo username
- `DECODO_PASSWORD`: Decodo password
- `DECODO_API_ENDPOINT`: Decodo API endpoint (default: `https://unblock.decodo.com:60000`)

#### Content Analyzer
- `DEFAULT_MIN_CONTENT_LENGTH`: Minimum content length (default: `1000`)
- `DEFAULT_MIN_TEXT_LENGTH`: Minimum text length (default: `200`)

#### General
- `DEFAULT_SAVE_OUTPUTS`: Save HTML to disk (default: `false`)
- `DEFAULT_OUTPUT_DIR`: Output directory (default: `outputs`)
- `DEFAULT_ENABLE_LOGGING`: Enable detailed logging (default: `true`)

## Scaling

### Massive Concurrency

The API supports massive scaling:

1. **Static/XHR Phase**: 
   - Default: 100 concurrent requests
   - Can be increased to 200-500 via config
   - Processes thousands of URLs in parallel

2. **Custom JS Phase**:
   - Each service processes 20 URLs per batch
   - With 13 services: 260 URLs simultaneously
   - With 50 services: 1,000 URLs simultaneously
   - With 100 services: 2,000 URLs simultaneously
   - **Unlimited scaling** - add as many services as needed

3. **Decodo Fallback**:
   - 3 concurrent requests (hard limit)
   - Only processes URLs that failed in custom JS phase

### Example: Processing 10,000 URLs

- **Static/XHR**: 100 concurrent = ~100 batches of 100 URLs
- **Custom JS**: 50 services × 20 URLs = 1,000 URLs per wave
- **Total**: ~10 waves through custom JS services
- **Time**: ~20-30 minutes (with 2-minute cooldowns)

## Deployment

### Docker

```bash
# Build image
docker build -t url-to-html-api .

# Run container
docker run -d \
  -p 8000:8000 \
  -e DECODO_USERNAME=your_username \
  -e DECODO_PASSWORD=your_password \
  -e CUSTOM_JS_SERVICES=service1.com,service2.com \
  url-to-html-api
```

### Docker Compose

```bash
# Edit docker-compose.yml with your configuration
docker-compose up -d
```

### Direct Python

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DECODO_USERNAME=your_username
export DECODO_PASSWORD=your_password
export CUSTOM_JS_SERVICES=service1.com,service2.com

# Run API
python run_api.py
```

### Production Deployment

For production, use a process manager like:
- **Gunicorn** with Uvicorn workers
- **systemd** service
- **Kubernetes** deployment
- **Cloud platforms** (Railway, Render, AWS, etc.)

Example with Gunicorn:
```bash
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Example Usage

### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/fetch-batch" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com/page1",
      "https://example.com/page2"
    ],
    "config": {
      "static_xhr_concurrency": 200,
      "custom_js_service_endpoints": [
        "service1.com",
        "service2.com",
        "service3.com"
      ]
    }
  }'
```

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/fetch-batch",
    json={
        "urls": [
            "https://example.com/page1",
            "https://example.com/page2"
        ],
        "config": {
            "static_xhr_concurrency": 200,
            "custom_js_batch_size": 20
        }
    }
)

result = response.json()
print(f"Success: {result['summary']['success']}")
print(f"Failed: {result['summary']['failed']}")
```

### JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/v1/fetch-batch', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    urls: [
      'https://example.com/page1',
      'https://example.com/page2'
    ],
    config: {
      static_xhr_concurrency: 200
    }
  })
});

const result = await response.json();
console.log(`Success: ${result.summary.success}`);
```

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `400`: Bad Request (validation errors)
- `422`: Unprocessable Entity (invalid input)
- `500`: Internal Server Error

Error responses include:
```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "status_code": 400
}
```

## Performance Tips

1. **Increase Static/XHR Concurrency**: For large batches, set `static_xhr_concurrency` to 200-500
2. **Add More Custom JS Services**: More services = more parallel processing
3. **Adjust Batch Sizes**: Larger batches reduce overhead but increase memory usage
4. **Disable Output Saving**: Set `save_outputs: false` for better performance
5. **Use Multiple Workers**: Set `API_WORKERS` to match CPU cores

## Limitations

- Maximum 10,000 URLs per request
- Response size limited by available memory
- Custom JS services have 2-minute cooldown between batches
- Decodo has 3 concurrent request limit

