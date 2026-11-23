import { test, expect } from '@playwright/test';
import path from 'node:path';
const token = 'e2e-disposable-session-' + 'x'.repeat(48);
test('TPL01: import → edit → undo/redo → save/reopen → background MP4', async ({
  page,
  browser,
  request,
  playwright,
  baseURL,
}, testInfo) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  // Only OS folder interaction is replaced. The grants belong to the disposable
  // test API workspace; uploads, persistence, preview and rendering remain real.
  await page.route('**/api/v1/folder-grants', async (route) => {
    const scope = route.request().postDataJSON().scope;
    await route.fulfill({
      json: { id: 'e2e-' + scope, label: 'Thư mục kiểm thử', scope },
    });
  });
  await page.goto('/#session=' + token);
  await expect(
    page.getByRole('button', { name: 'Tạo video mới' }),
  ).toBeEnabled();
  await page.screenshot({
    path: testInfo.outputPath('dashboard.png'),
    fullPage: true,
  });
  await page.getByRole('button', { name: 'Tạo video mới' }).click();
  await expect(page.getByLabel('Nội dung caption')).toBeVisible();
  await page.getByLabel('Độ dài video', { exact: true }).fill('2');
  await page.getByLabel('Tôi có quyền sử dụng media này').check();
  await page
    .getByLabel('Thêm ảnh hoặc nhạc')
    .setInputFiles(path.resolve('.local/test-assets/artwork.png'));
  await expect(page.getByRole('status')).toContainText('Đã cập nhật bản nháp');
  await expect(page.getByLabel('Thêm ảnh hoặc nhạc')).toBeEnabled();
  await page
    .getByLabel('Thêm ảnh hoặc nhạc')
    .setInputFiles(path.resolve('.local/test-assets/control.wav'));
  await expect(page.locator('.clip.music')).toBeVisible();
  await page.getByLabel('Nội dung caption').fill('Một giai điệu riêng');
  await page.getByLabel('Nội dung caption').blur();
  await expect(page.locator('.clip.text')).toContainText('Một giai điệu riêng');
  const ruler = page.locator('.ruler');
  const rulerBox = await ruler.boundingBox();
  await ruler.click({ position: { x: rulerBox!.width / 2, y: 5 } });
  await expect(page.locator('[data-frame]')).toHaveAttribute(
    'data-frame',
    '30',
  );
  await page.getByLabel('Hoàn tác').click();
  await expect(page.locator('.clip.text')).toContainText('Giai điệu của bạn');
  await page.getByLabel('Làm lại').click();
  await expect(page.locator('.clip.text')).toContainText('Một giai điệu riêng');
  await page.getByRole('button', { name: 'Lưu project', exact: true }).click();
  await expect(page.locator('.save-state')).toContainText('Đã lưu');
  await page.screenshot({
    path: testInfo.outputPath('editor.png'),
    fullPage: true,
  });
  const title = await page.getByLabel('Tên project').inputValue();
  await page.getByRole('button', { name: title, exact: true }).click();
  await expect(page.getByLabel('Nội dung caption')).toHaveValue(
    'Một giai điệu riêng',
  );
  await page.getByRole('button', { name: 'Xuất video', exact: false }).click();
  await expect(page.locator('.job-panel')).toBeVisible();
  // Keep admission at the production 4 GiB, with the UI browser still open.
  await page.screenshot({
    path: testInfo.outputPath('job-queued.png'),
    fullPage: true,
  });
  await expect(page.getByRole('link', { name: 'Xem / tải MP4' })).toBeVisible({
    timeout: 150000,
  });
  const headers = { authorization: 'Bearer ' + token, origin: baseURL! };
  let job: { id: string; status: string; message: string } | undefined;
  const status = await request.get(baseURL + '/api/v1/jobs', { headers });
  job = (await status.json())[0];
  expect(job?.status).toBe('succeeded');
  const response = await request.get(baseURL + `/api/v1/outputs/${job!.id}`, {
    headers,
  });
  expect(response.status()).toBe(200);
  expect(response.headers()['content-type']).toContain('video/mp4');
  expect((await response.body()).length).toBeGreaterThan(10000);
  await page.screenshot({
    path: testInfo.outputPath('render-complete.png'),
    fullPage: true,
  });
  await browser.close();
  const reopened = await playwright.chromium.launch({
    executablePath:
      process.env.AMVS_BROWSER ??
      path.resolve(
        'node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe',
      ),
  });
  const next = await reopened.newPage({
    viewport: { width: 1440, height: 1000 },
  });
  await next.goto(baseURL + '/#session=' + token);
  await expect(
    next.getByRole('button', { name: title, exact: true }),
  ).toBeVisible();
  await next.getByRole('button', { name: title, exact: true }).click();
  await expect(next.locator('[data-frame]')).toHaveAttribute(
    'data-frame',
    '30',
  );
  await expect(next.getByRole('link', { name: 'Xem / tải MP4' })).toBeVisible();
  await next.screenshot({
    path: testInfo.outputPath('reopened-job.png'),
    fullPage: true,
  });
  await reopened.close();
  expect(errors).toEqual([]);
});
