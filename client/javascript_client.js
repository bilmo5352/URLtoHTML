/**
 * JavaScript/Node.js client for URL to HTML Converter API.
 * 
 * Simple, easy-to-use client for fetching HTML content from URLs.
 * 
 * Usage:
 *   const { URLToHTMLClient } = require('./client/javascript_client.js');
 *   
 *   const client = new URLToHTMLClient('http://localhost:8000');
 *   
 *   const urls = [
 *     'https://example.com/page1',
 *     'https://example.com/page2'
 *   ];
 *   
 *   const response = await client.fetchBatch(urls);
 *   console.log(`Success: ${response.summary.success}`);
 */

class URLToHTMLClient {
    /**
     * Initialize the client.
     * 
     * @param {string} baseUrl - Base URL of the API (default: 'http://localhost:8000')
     * @param {number} timeout - Request timeout in milliseconds (default: 3600000 = 1 hour)
     */
    constructor(baseUrl = 'http://localhost:8000', timeout = 3600000) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.timeout = timeout;
    }

    /**
     * Check API health.
     * 
     * @returns {Promise<Object>} Health status information
     * 
     * @example
     * const health = await client.healthCheck();
     * console.log(health.status); // 'healthy'
     */
    async healthCheck() {
        const response = await fetch(`${this.baseUrl}/health`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error(`Health check failed: ${response.statusText}`);
        }
        
        return await response.json();
    }

    /**
     * Get API information.
     * 
     * @returns {Promise<Object>} API information
     * 
     * @example
     * const info = await client.getApiInfo();
     * console.log(info.version); // '1.0.0'
     */
    async getApiInfo() {
        const response = await fetch(`${this.baseUrl}/`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error(`API info request failed: ${response.statusText}`);
        }
        
        return await response.json();
    }

    /**
     * Fetch HTML content for a batch of URLs.
     * 
     * This is the main method for fetching HTML content. It uses a progressive
     * fallback strategy:
     * 1. Static HTTP GET
     * 2. XHR/API fetch
     * 3. Custom JS rendering (multi-service parallel)
     * 4. Decodo fallback (for failed URLs)
     * 
     * @param {string[]} urls - List of URLs to fetch (1-10000 URLs)
     * @param {Object} config - Optional configuration
     * @param {number} config.static_xhr_concurrency - Max concurrent static/XHR requests
     * @param {string[]} config.custom_js_service_endpoints - Custom JS rendering service endpoints
     * @param {number} config.custom_js_batch_size - URLs per batch for custom JS
     * @param {number} config.custom_js_cooldown_seconds - Cooldown between batches
     * @param {number} config.custom_js_timeout - Timeout for custom JS batch requests
     * @param {boolean} config.decodo_enabled - Whether to use Decodo as fallback
     * @param {number} config.decodo_timeout - Timeout for Decodo requests
     * 
     * @returns {Promise<Object>} Batch response with results and summary
     * 
     * @example
     * // Simple usage
     * const urls = ['https://example.com/page1', 'https://example.com/page2'];
     * const response = await client.fetchBatch(urls);
     * 
     * console.log(`Total: ${response.summary.total}`);
     * console.log(`Success: ${response.summary.success}`);
     * console.log(`Failed: ${response.summary.failed}`);
     * 
     * // Get successful results
     * response.results
     *   .filter(r => r.status === 'success')
     *   .forEach(r => {
     *     console.log(`${r.url}: ${r.html.length} bytes via ${r.method}`);
     *   });
     * 
     * // With custom configuration
     * const response = await client.fetchBatch(urls, {
     *   static_xhr_concurrency: 200,
     *   custom_js_service_endpoints: [
     *     'service1.com',
     *     'service2.com',
     *     'service3.com'
     *   ],
     *   custom_js_batch_size: 20
     * });
     */
    async fetchBatch(urls, config = {}) {
        // Build request body
        const body = {
            urls: urls,
            config: Object.keys(config).length > 0 ? config : undefined
        };

        // Remove undefined config
        if (body.config && Object.keys(body.config).length === 0) {
            delete body.config;
        }

        // Make API request
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(`${this.baseUrl}/api/v1/fetch-batch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(body),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                let errorData;
                try {
                    errorData = await response.json();
                } catch (e) {
                    errorData = { error: response.statusText };
                }
                throw new Error(
                    errorData.error || errorData.detail || `Request failed: ${response.statusText}`
                );
            }

            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error(`Request timeout after ${this.timeout}ms`);
            }
            throw error;
        }
    }

    /**
     * Fetch HTML content for a single URL (convenience method).
     * 
     * @param {string} url - URL to fetch
     * @param {Object} config - Optional configuration (same as fetchBatch)
     * 
     * @returns {Promise<string|null>} HTML content as string, or null if failed
     * 
     * @example
     * const html = await client.fetchSingle('https://example.com');
     * if (html) {
     *   console.log(`Got ${html.length} bytes`);
     * }
     */
    async fetchSingle(url, config = {}) {
        const response = await this.fetchBatch([url], config);
        if (response.results && response.results.length > 0) {
            const result = response.results[0];
            if (result.status === 'success' && result.html) {
                return result.html;
            }
        }
        return null;
    }
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { URLToHTMLClient };
}

// Export for ES6 modules
if (typeof window !== 'undefined') {
    window.URLToHTMLClient = URLToHTMLClient;
}

