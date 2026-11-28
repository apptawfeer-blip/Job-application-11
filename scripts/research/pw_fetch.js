// Render pages with headless Chromium and save HTML: node pw_fetch.js outdir url1 url2 ...
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [outdir, ...urls] = process.argv.slice(2);
  const browser = await chromium.launch({ proxy: process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined });
  const ctx = await browser.newContext({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36', ignoreHTTPSErrors: true, locale: 'en-US' });
  for (const u of urls) {
    const page = await ctx.newPage();
    const name = u.replace(/[^a-z0-9]+/gi, '_').slice(0, 120) + '.html';
    try {
      const r = await page.goto(u, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await page.waitForTimeout(6000);
      const html = await page.content();
      fs.writeFileSync(path.join(outdir, name), html);
      console.log((r ? r.status() : 0), html.length, name);
    } catch (e) { console.log('ERR', u, String(e).slice(0, 120)); }
    await page.close();
  }
  await browser.close();
})();
