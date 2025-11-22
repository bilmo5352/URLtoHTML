/**
 * JavaScript example using the URL to HTML Converter API client.
 * 
 * This example demonstrates:
 * - Initializing the client
 * - Fetching a batch of URLs
 * - Processing results
 * - Error handling
 */

const { URLToHTMLClient } = require('./javascript_client.js');

async function main() {
    // Initialize client
    const client = new URLToHTMLClient('http://localhost:8000');
    
    // List of URLs to fetch
    const urls = [
        'https://example.com',
        'https://www.python.org',
        'https://github.com'
    ];
    
    console.log(`Fetching HTML for ${urls.length} URLs...`);
    console.log('-'.repeat(60));
    
    try {
        // Check API health first
        const health = await client.healthCheck();
        console.log(`API Status: ${health.status}`);
        console.log(`API Version: ${health.version}`);
        console.log();
        
        // Fetch batch
        const response = await client.fetchBatch(urls);
        
        // Print summary
        console.log('\nSummary:');
        console.log(`  Total: ${response.summary.total}`);
        console.log(`  Success: ${response.summary.success}`);
        console.log(`  Failed: ${response.summary.failed}`);
        console.log(`  Processing Time: ${response.summary.total_time.toFixed(2)}s`);
        console.log(`\nResults by Method:`);
        for (const [method, count] of Object.entries(response.summary.by_method)) {
            console.log(`  ${method}: ${count}`);
        }
        
        // Print individual results
        console.log(`\nIndividual Results:`);
        response.results.forEach(result => {
            if (result.status === 'success') {
                console.log(`  ✓ ${result.url}`);
                console.log(`    Method: ${result.method}`);
                console.log(`    Size: ${result.html ? result.html.length : 0} bytes`);
            } else {
                console.log(`  ✗ ${result.url}`);
                console.log(`    Error: ${result.error}`);
            }
        });
        
        // Get successful results
        const successful = response.results.filter(r => r.status === 'success');
        console.log(`\n${successful.length} URLs fetched successfully!`);
        
    } catch (error) {
        console.error(`Error: ${error.message}`);
        if (error.stack) {
            console.error(error.stack);
        }
    }
}

// Run the example
if (require.main === module) {
    main().catch(console.error);
}

module.exports = { main };

