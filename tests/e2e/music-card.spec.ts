import { test, expect } from '@playwright/test';
import path from 'node:path';

test('Music Card: hai ảnh, bài hát, chỉnh metadata, lưu và xuất MP4', async ({
  page,
  request,
  baseURL,
}) => {
  const token = 'e2e-disposable-session-' + 'x'.repeat(48);
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.route('**/api/v1/folder-grants', async (route) => {
    const scope = route.request().postDataJSON().scope;
    await route.fulfill({
      json: { id: 'e2e-' + scope, label: 'Test folder', scope },
    });
  });
  await page.goto('/#session=' + token);
  await expect(page.getByRole('button', { name: 'Music Card' })).toBeEnabled();
  await page.getByRole('button', { name: 'Music Card' }).click();
  await expect(
    page.getByRole('textbox', { name: 'Tên bài hát' }),
  ).toBeVisible();
  await page
    .getByRole('textbox', { name: 'Tên bài hát' })
    .fill('Bài hát kiểm thử');
  await page.getByRole('textbox', { name: 'Tên bài hát' }).blur();
  await page.getByRole('textbox', { name: 'Tên nghệ sĩ' }).fill('Nghệ sĩ thử');
  await page.getByRole('textbox', { name: 'Tên nghệ sĩ' }).blur();
  await page.getByLabel('Độ dài video', { exact: true }).fill('3');
  await page.getByLabel('Tôi có quyền sử dụng media này').check();
  await page
    .getByLabel('Thêm ảnh, video hoặc nhạc')
    .setInputFiles([
      path.resolve('.local/test-assets/artwork.png'),
      path.resolve('.local/test-assets/artwork-2.png'),
      path.resolve('.local/test-assets/control.wav'),
    ]);
  await expect(page.locator('.clip.background')).toHaveCount(2);
  await expect(page.locator('.clip.music')).toHaveCount(1);
  await page.locator('.ruler').click({ position: { x: 700, y: 10 } });
  await expect(page.getByText('Bài hát kiểm thử').first()).toBeVisible();
  await page.getByRole('button', { name: 'Lưu project', exact: true }).click();
  await expect(page.locator('.save-state')).toContainText('Đã lưu');
  await page.getByRole('button', { name: 'Xuất video', exact: false }).click();
  await expect(page.getByRole('link', { name: 'Xem / tải MP4' })).toBeVisible({
    timeout: 150000,
  });
  const jobs = await (
    await request.get(`${baseURL}/api/v1/jobs`, {
      headers: { authorization: 'Bearer ' + token, origin: baseURL! },
    })
  ).json();
  expect(jobs[0].status).toBe('succeeded');
  expect(errors).toEqual([]);
});
