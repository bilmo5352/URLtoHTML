# URL to HTML Converter Library

A Python library that fetches HTML content from URLs using a progressive fallback strategy when initial methods fail or return insufficient content.

## Features

- **Three-tier fallback strategy**: Static fetch → XHR fetch → JS rendering
- **Intelligent content detection**: Automatically detects blocked or skeleton content
- **Configurable**: Customizable thresholds, timeouts, and API endpoints
- **Robust error handling**: Graceful degradation through fallback chain

## Installation

```bash
pip install url-to-html
```

For faster HTML parsing:
```bash
pip install url-to-html[fast]
```

## Usage

```python
from url_to_html import fetch_html

html = fetch_html("https://example.com")
# Automatically tries: static → XHR → JS rendering
```

## License

MIT

