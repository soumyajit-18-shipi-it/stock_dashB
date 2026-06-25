const { chromium } = require('playwright');

const tickers = [
  'RELIANCE.NS',
  'TCS.NS',
  'INFY.NS',
  'HDFCBANK.NS',
  'ICICIBANK.NS',
  'SBIN.NS'
];

(async () => {
  console.log('Starting chromium...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Store received payloads
  const payloads = {};

  // Listen to network responses
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('/api/v1/stock/')) {
      const parsedUrl = new URL(url);
      const ticker = parsedUrl.pathname.split('/').pop().toUpperCase();
      try {
        const json = await response.json();
        payloads[ticker] = json.profile;
        console.log(`[API Response Captured] Ticker: ${ticker}`);
      } catch (err) {
        // Not a JSON response or failed to parse
      }
    }
  });

  try {
    console.log('Navigating to http://localhost:5173...');
    await page.goto('http://localhost:5173', { timeout: 15000 });

    console.log('Waiting for auth store to be exposed...');
    await page.waitForFunction(() => typeof window.__auth_store__ !== 'undefined', { timeout: 5000 });

    console.log('Setting mock authenticated user state...');
    await page.evaluate(() => {
      window.__auth_store__.setState({
        user: { id: 'test-user-id', email: 'test@example.com' },
        token: 'mock-access-token',
        loading: false,
        isAdmin: false,
      });
    });

    console.log('Waiting for search input...');
    const searchInput = await page.waitForSelector('input[type="text"], input[placeholder*="Search"]', { timeout: 5000 });

    for (const ticker of tickers) {
      console.log(`\n=== Processing Ticker: ${ticker} ===`);
      
      // Fill and search
      await searchInput.fill(ticker);
      await searchInput.press('Enter');

      // Wait for UI to update and network call to finish
      // We wait up to 10 seconds for the card to contain the correct ticker text
      console.log(`Waiting for UI card to display ${ticker}...`);
      await page.waitForFunction((t) => {
        const el = document.querySelector('.glass');
        return el && el.innerText.includes(t) && !el.innerText.includes('Loading');
      }, ticker, { timeout: 15000 });

      // Add a small extra delay for safety
      await page.waitForTimeout(1000);

      // Get rendered card text
      const cardText = await page.locator('.glass').first().innerText();
      console.log('--- Rendered UI Values ---');
      console.log(cardText);
      console.log('--------------------------');

      // Print captured API response
      console.log('--- Captured API Profile JSON ---');
      console.log(JSON.stringify(payloads[ticker] || null, null, 2));
      console.log('---------------------------------');
    }

  } catch (err) {
    console.error('Error during E2E verification:', err);
  } finally {
    await browser.close();
    console.log('Browser closed.');
  }
})();
