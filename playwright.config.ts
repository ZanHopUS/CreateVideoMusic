import { defineConfig } from '@playwright/test';
import path from 'node:path';
const root = process.cwd();
const run =
  process.env.AMVS_TEST_RUN ??
  path.join(root, '.local/e2e', Date.now().toString());
process.env.AMVS_TEST_RUN = run;
const webPort = Number(process.env.AMVS_TEST_WEB_PORT ?? 3137),
  apiPort = Number(process.env.AMVS_TEST_API_PORT ?? 8937);
const origin = `http://127.0.0.1:${webPort}`;
const env = {
  ...process.env,
  AMVS_SESSION: 'e2e-disposable-session-' + 'x'.repeat(48),
  AMVS_ORIGIN: origin,
  AMVS_API_HOST: `127.0.0.1:${apiPort}`,
  AMVS_API_URL: `http://127.0.0.1:${apiPort}`,
  AMVS_TEST_RUN: run,
  AMVS_BROWSER: path.join(
    root,
    'node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe',
  ),
  NEXT_TELEMETRY_DISABLED: '1',
};
export default defineConfig({
  testDir: 'tests/e2e',
  workers: 1,
  timeout: 180000,
  retries: 0,
  outputDir: path.join(run, 'playwright'),
  reporter: [
    ['list'],
    ['json', { outputFile: path.join(run, 'results.json') }],
  ],
  use: {
    baseURL: origin,
    viewport: { width: 1440, height: 1000 },
    trace: 'retain-on-failure',
    launchOptions: { executablePath: env.AMVS_BROWSER },
  },
  webServer: [
    {
      command:
        '"' +
        path.join(root, '.venv-api/Scripts/python.exe') +
        '" -m uvicorn tests.fixtures.api_server:app --host 127.0.0.1 --port ' +
        apiPort +
        ' --no-access-log',
      url: `http://127.0.0.1:${apiPort}/health`,
      env,
      timeout: 60000,
      reuseExistingServer: false,
    },
    {
      command:
        'node ../../node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port ' +
        webPort,
      cwd: path.join(root, 'apps/web'),
      url: origin,
      env,
      timeout: 60000,
      reuseExistingServer: false,
    },
  ],
});
