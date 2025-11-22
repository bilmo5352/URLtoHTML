const fs = require('fs');
const path = require('path');

// Configuration
const API_URL = 'https://chromeworkers-copy-production.up.railway.app/render';
// const API_URL = 'http://localhost:3000/render'; // For local testing

// Generate 100 test URLs with diverse domains and search terms
const TEST_URLS = [
    // Flipkart URLs (20)
    "https://www.flipkart.com/search?q=tablets",
    "https://www.flipkart.com/search?q=speakers",
    "https://www.flipkart.com/search?q=keyboards",
    "https://www.flipkart.com/search?q=mice",
    "https://www.flipkart.com/search?q=monitors",
    "https://www.flipkart.com/search?q=printers",
    "https://www.flipkart.com/search?q=hard+drives",
    "https://www.flipkart.com/search?q=pendrives",
    "https://www.flipkart.com/search?q=chargers",
    "https://www.flipkart.com/search?q=cables",
    
    // Amazon URLs (20)
    "https://www.amazon.in/s?k=webcams",
    "https://www.amazon.in/s?k=usb+hubs",
    "https://www.amazon.in/s?k=power+banks",
    "https://www.amazon.in/s?k=wireless+chargers",
    
    // Nykaa URLs (15)
    "https://www.nykaa.com/skin/sunscreens/c/8394",
    "https://www.nykaa.com/hair/hair-care/conditioner/c/1222",
    "https://www.nykaa.com/makeup/cheeks/blush/c/747",
    
    // Myntra URLs (10)
    "https://www.myntra.com/women-jeans",
    "https://www.myntra.com/men-shoes",
    "https://www.myntra.com/women-shoes",

];

/**
 * Test client to hit the Playwright Cloud Renderer API
 * Saves HTML and screenshot for each URL
 */
async function testRenderAPI(urls) {
    console.log('Starting Playwright Cloud Renderer test...\n');
    console.log(`📊 Testing with ${urls.length} URLs in parallel\n`);
    
    const startTime = Date.now();
    
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ urls: urls })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const endTime = Date.now();
        const totalTime = ((endTime - startTime) / 1000).toFixed(2);
        
        console.log(`Received ${data.results.length} results\n`);
        console.log(`⏱️  Total processing time: ${totalTime} seconds`);
        console.log(`📈 Average time per URL: ${(totalTime / urls.length).toFixed(2)} seconds\n`);

        let successCount = 0;
        let errorCount = 0;

        // Process each result
        for (let i = 0; i < data.results.length; i++) {
            const result = data.results[i];
            console.log(`\n--- Result ${i + 1}: ${result.url} ---`);
            console.log(`Status: ${result.status}`);

            if (result.status === 'success') {
                successCount++;
                // Save HTML
                const htmlFilename = `result_${i + 1}_${sanitizeFilename(result.url)}.html`;
                const htmlPath = path.join(__dirname, htmlFilename);
                fs.writeFileSync(htmlPath, result.html, 'utf8');
                console.log(`✓ HTML saved to: ${htmlFilename}`);

                // Save Screenshot
                if (result.screenshot) {
                    // Extract base64 data from data URI
                    const base64Data = result.screenshot.replace(/^data:image\/\w+;base64,/, '');
                    const imageBuffer = Buffer.from(base64Data, 'base64');
                    
                    const imageFilename = `result_${i + 1}_${sanitizeFilename(result.url)}.jpg`;
                    const imagePath = path.join(__dirname, imageFilename);
                    fs.writeFileSync(imagePath, imageBuffer);
                    console.log(`✓ Screenshot saved to: ${imageFilename}`);
                }
            } else {
                errorCount++;
                console.log(`✗ Error: ${result.error}`);
                if (result.errorType) {
                    console.log(`  Error Type: ${result.errorType}`);
                }
            }
        }

        console.log('\n' + '='.repeat(60));
        console.log('📊 TEST SUMMARY');
        console.log('='.repeat(60));
        console.log(`Total URLs: ${urls.length}`);
        console.log(`✅ Successful: ${successCount}`);
        console.log(`❌ Failed: ${errorCount}`);
        console.log(`⏱️  Total Time: ${totalTime} seconds`);
        console.log(`📈 Avg Time/URL: ${(totalTime / urls.length).toFixed(2)} seconds`);
        console.log(`🚀 Parallel Processing: Enabled`);
        console.log('='.repeat(60));
        console.log('\n✓ Test completed!');
        
    } catch (error) {
        console.error('\n✗ Test failed:', error.message);
        process.exit(1);
    }
}

/**
 * Sanitize URL to create a valid filename
 */
function sanitizeFilename(url) {
    return url
        .replace(/^https?:\/\//, '')
        .replace(/[^a-z0-9]/gi, '_')
        .substring(0, 50);
}

// Run the test
testRenderAPI(TEST_URLS);

