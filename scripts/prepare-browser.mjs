import { ensureBrowser } from '@remotion/renderer';
// Explicit setup step only. Runtime render requires a local executable.
const browser = await ensureBrowser();
console.log(JSON.stringify({ browser: browser.type }));
