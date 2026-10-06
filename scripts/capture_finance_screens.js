// Capture Smart Finn Track screenshots from the public demo account, in light and dark.
// Run manually; the hourly workflow does not log in anywhere.
//   npm install --no-save puppeteer-core@23
//   node scripts/capture_finance_screens.js [path-to-chrome]
// Read-only: it signs in with the app's own "Try the demo" button, switches months
// and opens a saved conversation. It never sends chat messages or edits data.
const fs = require("fs");
const os = require("os");
const path = require("path");
const puppeteer = require("puppeteer-core");

const BASE = "https://ai-finance-tracker-delta-drab.vercel.app";
const HOST = new URL(BASE).hostname;
const MONTH = "August 2026"; // A complete demo month; the current month is often sparse.
const CHAT = "Kategori Pengeluaran 3"; // Saved conversation whose reply includes a chart.
const OUT = path.resolve(__dirname, "..", "screens");
const CHROME = process.argv[2] || [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].find((candidate) => fs.existsSync(candidate));

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// CSS pixels in the fixed 1440x900 viewport: the content area right of the sidebar.
// One clip for every gallery shot keeps the README grid evenly sized.
const CONTENT = { x: 256, y: 16, width: 1168, height: 640 };
const SHOTS = [
  { name: "finance-dashboard", page: "/dashboard", month: true, clip: null },
  { name: "finance-chat", page: "/chat", chat: true, clip: CONTENT },
  { name: "finance-transactions", page: "/transactions", clip: CONTENT },
  { name: "finance-planning", page: "/planning", month: true, clip: CONTENT },
];

const MONTH_LABEL = /^[A-Z][a-z]+ 20\d\d$/;

async function settle(page) {
  // Data loads client-side after navigation; wait for requests to stop, then for charts to animate.
  await page.waitForNetworkIdle({ idleTime: 1500, timeout: 30000 }).catch(() => {});
  await wait(2500);
}

// Runs in the page: returns the month picker's label, e.g. "August 2026", and can step one month back.
function monthPicker(source, stepBack) {
  let node = [...document.querySelectorAll("*")].find((e) => e.children.length === 0 && new RegExp(source).test(e.textContent.trim()));
  const label = node ? node.textContent.trim() : null;
  if (node && stepBack) {
    while (node && !node.querySelector("button")) node = node.parentElement;
    node.querySelector("button").click(); // The picker's first button is "previous month".
  }
  return label;
}

async function selectMonth(page) {
  await page.waitForFunction(monthPicker, { timeout: 30000 }, MONTH_LABEL.source, false)
    .catch(() => { throw new Error("Month picker not found at " + page.url()); });
  for (let step = 0; step < 24; step++) {
    if (await page.evaluate(monthPicker, MONTH_LABEL.source, false) === MONTH) return settle(page);
    await page.evaluate(monthPicker, MONTH_LABEL.source, true);
    await wait(1500);
  }
  throw new Error(`Could not reach ${MONTH}`);
}

async function main() {
  if (!CHROME) throw new Error("Chrome not found; pass its path as the first argument");
  fs.mkdirSync(OUT, { recursive: true });
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "sft-capture-"));
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: true, userDataDir: profile,
    defaultViewport: { width: 1440, height: 900, deviceScaleFactor: 1.25 },
  });
  try {
    for (const theme of ["light", "dark"]) {
      const page = await browser.newPage();
      await page.setCookie({ name: "sft-locale", value: "en", domain: HOST, path: "/" });
      await page.evaluateOnNewDocument((value) => localStorage.setItem("theme", value), theme);
      await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: theme }]);
      await page.goto(BASE + "/dashboard", { waitUntil: "networkidle2" });
      if (new URL(page.url()).pathname !== "/dashboard") { // Signed out: /login?next=/dashboard
        await page.goto(BASE + "/", { waitUntil: "networkidle2" });
        const [demo] = await page.$$("xpath/.//button[contains(., 'Try the demo')]");
        if (!demo) throw new Error("Demo button not found on the landing page");
        await demo.click();
        await page.waitForFunction(() => location.pathname.startsWith("/dashboard"), { timeout: 30000 });
      }
      for (const shot of SHOTS) {
        await page.goto(BASE + shot.page, { waitUntil: "networkidle2" });
        await settle(page);
        if (shot.month) await selectMonth(page);
        if (shot.chat) {
          const [conversation] = await page.$$(`xpath/.//*[starts-with(normalize-space(.), '${CHAT}')]`);
          if (!conversation) throw new Error(`Saved conversation "${CHAT}" not found`);
          await conversation.click();
          await page.waitForSelector("svg, [class*='bar']", { timeout: 20000 }).catch(() => {});
          await wait(4000);
        }
        const file = path.join(OUT, `${shot.name}-${theme}.png`);
        await page.screenshot({ path: file, ...(shot.clip ? { clip: shot.clip } : {}) });
        console.log("Captured", path.relative(process.cwd(), file));
      }
      await page.close();
    }
    const manifest = { source: BASE, account: "public demo", month: MONTH,
                       captured_at: new Date().toISOString().replace(/\.\d+Z$/, "Z") };
    fs.writeFileSync(path.join(OUT, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
  } finally {
    await browser.close();
    fs.rmSync(profile, { recursive: true, force: true });
  }
}

main().catch((error) => { console.error(error); process.exit(1); });
