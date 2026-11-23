import { test, expect } from '@playwright/test';
import path from 'node:path';
import { readFile } from 'node:fs/promises';
const token = 'e2e-disposable-session-' + 'x'.repeat(48);
test('S2: batch media → reorder/trim/undo → save/reopen → mixed MP4', async ({
  page,
  request,
  baseURL,
}, info) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/api/v1/folder-grants', async (route) => {
    const scope = route.request().postDataJSON().scope;
    await route.fulfill({
      json: { id: 'e2e-' + scope, label: 'Test folder', scope },
    });
  });
  await page.goto('/#session=' + token);
  await expect(
    page.getByRole('button', { name: 'Tạo video mới' }),
  ).toBeEnabled();
  await page.getByRole('button', { name: 'Tạo video mới' }).click();
  await page.getByLabel('Tên project').fill('Montage S2');
  await page.getByLabel('Tên project').blur();
  await page.getByLabel('Độ dài video', { exact: true }).fill('3');
  await page.getByLabel('Tôi có quyền sử dụng media này').check();
  await page
    .getByLabel('Thêm ảnh, video hoặc nhạc')
    .setInputFiles([
      path.resolve('.local/test-assets/artwork.png'),
      path.resolve('.local/test-assets/artwork-2.png'),
      path.resolve('.local/test-assets/background.mp4'),
      path.resolve('.local/test-assets/control.wav'),
    ]);
  await expect(page.locator('.clip.background')).toHaveCount(3);
  await expect(page.locator('.clip.music')).toHaveCount(1);
  await expect(page.getByLabel('Thêm ảnh, video hoặc nhạc')).toBeEnabled();
  const video = page.getByRole('button', {
    name: 'Video background.mp4',
    exact: true,
  });
  await video.click();
  await page.getByLabel('Cắt từ nguồn').fill('0.5');
  await page.getByLabel('Cách hiển thị').selectOption('contain');
  await page.getByRole('button', { name: 'Đưa clip lên trước' }).click();
  await expect(page.locator('.clip.background').nth(1)).toHaveAttribute(
    'aria-label',
    'Video background.mp4',
  );
  await page.getByLabel('Hoàn tác').click();
  await expect(page.locator('.clip.background').nth(2)).toHaveAttribute(
    'aria-label',
    'Video background.mp4',
  );
  await page.getByLabel('Làm lại').click();
  await page.getByRole('button', { name: 'Gỡ clip khỏi project' }).click();
  await expect(page.locator('.clip.background')).toHaveCount(2);
  await page.getByLabel('Hoàn tác').click();
  await expect(page.locator('.clip.background')).toHaveCount(3);
  await video.click();
  await expect(page.getByLabel('Cắt từ nguồn')).toHaveValue('0.5');
  await expect(page.getByLabel('Cách hiển thị')).toHaveValue('contain');
  await page.getByRole('button', { name: 'Lưu project', exact: true }).click();
  await expect(page.locator('.save-state')).toContainText('Đã lưu');
  const title = await page.getByLabel('Tên project').inputValue();
  const selectedProject = await page
    .locator('.navigation .current-project')
    .getAttribute('class');
  expect(selectedProject).toContain('current-project');
  // Sidebar names may repeat across fixtures: open the selected project explicitly.
  await page.locator('.navigation .current-project').click();
  await expect(page.locator('.clip.background')).toHaveCount(3);
  await video.click();
  await expect(page.getByLabel('Cắt từ nguồn')).toHaveValue('0.5');
  await expect(page.getByLabel('Cách hiển thị')).toHaveValue('contain');
  await page.screenshot({
    path: info.outputPath('multi-media-editor.png'),
    fullPage: true,
  });
  await page.getByRole('button', { name: 'Xuất video', exact: false }).click();
  await expect(page.getByRole('link', { name: 'Xem / tải MP4' })).toBeVisible({
    timeout: 150000,
  });
  const headers = { authorization: 'Bearer ' + token, origin: baseURL! };
  const response = await request.get(baseURL + '/api/v1/jobs', { headers });
  const jobs = await response.json();
  expect(jobs[0].status).toBe('succeeded');
  const download = await request.get(
    baseURL + '/api/v1/outputs/' + jobs[0].id,
    { headers },
  );
  expect(download.status()).toBe(200);
  expect((await download.body()).length).toBeGreaterThan(10000);
  expect(errors).toEqual([]);
});

test('S2: lỗi một file trong batch không làm mất clip hợp lệ hoặc thay đổi cũ', async ({
  page,
}) => {
  await page.goto('/#session=' + token);
  await expect(
    page.getByRole('button', { name: 'Tạo video mới' }),
  ).toBeEnabled();
  await page.getByRole('button', { name: 'Tạo video mới' }).click();
  await page.getByLabel('Tên project').fill('Import có lỗi');
  await page.getByLabel('Tên project').blur();
  await page.getByLabel('Thêm ảnh, video hoặc nhạc').click();
  await expect(
    page.getByText(
      'Tích ô “Tôi có quyền sử dụng media này” trước khi chọn file.',
    ),
  ).toBeVisible();
  await page.getByLabel('Tôi có quyền sử dụng media này').check();
  await page.getByLabel('Thêm ảnh, video hoặc nhạc').setInputFiles([
    {
      name: 'valid.png',
      mimeType: 'image/png',
      buffer: await readFile(path.resolve('.local/test-assets/artwork.png')),
    },
    {
      name: 'broken.png',
      mimeType: 'image/png',
      buffer: Buffer.from('not an image'),
    },
  ]);
  await expect(page.getByRole('status')).toContainText('Đã thêm 1/2 file');
  await expect(page.locator('.clip.background')).toHaveCount(1);
  await expect(page.locator('.clip.text')).toContainText('Giai điệu của bạn');
  await page.getByLabel('Hoàn tác').click();
  await expect(page.locator('.clip.background')).toHaveCount(0);
  await expect(page.locator('.clip.text')).toContainText('Giai điệu của bạn');
});
