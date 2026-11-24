import { expect, test } from '@playwright/test';

for (const viewport of [
  { width: 1366, height: 768 },
  { width: 1920, height: 1080 },
]) {
  test(`workspace layout ${viewport.width}x${viewport.height}`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await page.goto('/');
    await expect(
      page.getByRole('button', { name: 'Tổng quan', exact: true }),
    ).toBeVisible();
    await expect(page.locator('.template-card')).toHaveCount(3);
    const templatesBottom = await page
      .locator('.template-grid')
      .evaluate((el) => el.getBoundingClientRect().bottom);
    expect(templatesBottom).toBeLessThanOrEqual(viewport.height);
    await page.getByRole('button', { name: 'Dự án', exact: true }).click();
    await expect(
      page.getByRole('heading', { name: 'Quản lý dự án' }),
    ).toBeVisible();
    await page.getByRole('button', { name: 'Cài đặt', exact: true }).click();
    await expect(
      page.getByRole('heading', { name: 'Cài đặt', exact: true }),
    ).toBeVisible();
    await page.getByRole('button', { name: 'Tổng quan', exact: true }).click();
    await page
      .getByRole('button', { name: 'Tạo video mới', exact: false })
      .click();
    await expect(page.locator('.preview-stage')).toBeVisible();
    await expect(page.locator('.inspector')).toBeVisible();
    await expect(page.locator('.timeline-dock')).toBeVisible();
    await page.getByRole('button', { name: 'Toàn màn hình Preview' }).click();
    await expect
      .poll(() => page.evaluate(() => Boolean(document.fullscreenElement)))
      .toBe(true);
    await page.evaluate(() => document.exitFullscreen());
    const geometry = await page.evaluate(() => ({
      body: document.documentElement.scrollHeight,
      height: window.innerHeight,
      preview: document.querySelector('.preview-stage')!.getBoundingClientRect()
        .bottom,
      timeline: document
        .querySelector('.timeline-dock')!
        .getBoundingClientRect().bottom,
    }));
    expect(geometry.body).toBeLessThanOrEqual(geometry.height + 2);
    expect(geometry.preview).toBeLessThan(geometry.height);
    expect(geometry.timeline).toBeLessThanOrEqual(geometry.height + 2);
    await page
      .getByRole('button', { name: 'Xuất video', exact: false })
      .click();
    await expect(
      page.getByRole('dialog', { name: 'Xuất video' }),
    ).toBeVisible();
    await page.getByRole('button', { name: 'Đóng dialog xuất video' }).click();
    await expect(page.getByRole('dialog', { name: 'Xuất video' })).toHaveCount(
      0,
    );
  });
}

test('settings storage uses backend policy and project recovery is separate', async ({
  page,
}) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Cài đặt', exact: true }).click();
  await page
    .getByRole('button', { name: 'Lưu trữ', exact: true })
    .last()
    .click();
  await expect(page.getByLabel('Giới hạn cache (MiB)')).toHaveValue('512');
  await page.getByRole('button', { name: 'Tổng quan', exact: true }).click();
  await page
    .getByRole('button', { name: 'Tạo video mới', exact: false })
    .click();
  await expect(page.locator('.preview-stage')).toBeVisible();
  await page.getByRole('button', { name: 'Dự án', exact: true }).click();
  await page
    .getByRole('button', { name: 'Recovery', exact: true })
    .first()
    .click();
  await expect(
    page.getByRole('heading', { name: 'Phiên khôi phục' }),
  ).toBeVisible();
});

test('lyrics draft survives project switching within the studio', async ({
  page,
}) => {
  page.on('dialog', (dialog) => dialog.accept());
  await page.goto('/');
  await page
    .getByRole('button', { name: 'Lyrics Video', exact: false })
    .click();
  await expect(page.getByLabel('Lời có timestamp')).toBeVisible();
  await page.getByLabel('Lời có timestamp').fill('[00:01.00]Bản nháp chưa ghi');
  await page.getByRole('button', { name: 'Tổng quan', exact: true }).click();
  await page
    .getByRole('button', { name: 'Tạo video mới', exact: false })
    .click();
  await expect(page.locator('.preview-stage')).toBeVisible();
  await page.getByRole('button', { name: 'Tổng quan', exact: true }).click();
  await page
    .locator('.recent-projects button')
    .filter({ hasText: 'Video lời hát' })
    .first()
    .click();
  await expect(page.getByLabel('Lời có timestamp')).toHaveValue(
    '[00:01.00]Bản nháp chưa ghi',
  );
});

test('recent project and view preference are shared with a new tab', async ({
  page,
}) => {
  await page.goto('/');
  await page
    .getByRole('button', { name: 'Tạo video mới', exact: false })
    .click();
  await expect(page.locator('.preview-stage')).toBeVisible();
  await page.getByRole('button', { name: 'Tổng quan', exact: true }).click();
  await expect(
    page
      .locator('.recent-projects button')
      .filter({ hasText: 'Video' })
      .first(),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Dự án', exact: true }).click();
  await page.getByRole('button', { name: 'Danh sách', exact: true }).click();
  await expect(page.getByText('Đã lưu chế độ xem.')).toBeVisible();
  const newTab = await page.context().newPage();
  await newTab.goto('/');
  await newTab.getByRole('button', { name: 'Dự án', exact: true }).click();
  await expect(
    newTab.getByRole('button', { name: 'Danh sách', exact: true }),
  ).toHaveAttribute('aria-pressed', 'true');
  await newTab.getByRole('button', { name: 'Tổng quan', exact: true }).click();
  await expect(
    newTab
      .locator('.recent-projects button')
      .filter({ hasText: 'Video' })
      .first(),
  ).toBeVisible();
});

test('timeline resizes by keyboard and pointer without changing project content', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1366, height: 768 });
  await page.goto('/');
  await page
    .getByRole('button', { name: 'Tạo video mới', exact: false })
    .click();
  const separator = page.getByRole('separator', {
    name: 'Thay đổi chiều cao Timeline',
  });
  const dock = page.locator('.timeline-dock');
  await expect(separator).toHaveAttribute('aria-valuenow', '280');
  await separator.focus();
  await page.keyboard.press('ArrowUp');
  await expect(separator).toHaveAttribute('aria-valuenow', '300');
  const box = await separator.boundingBox();
  if (!box) throw new Error('Không thấy tay nắm Timeline.');
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2 - 40);
  await page.mouse.up();
  await expect
    .poll(() =>
      dock.evaluate((el) => parseInt((el as HTMLElement).style.height, 10)),
    )
    .toBeGreaterThan(300);
  await page.getByRole('button', { name: 'Đặt lại chiều cao' }).click();
  await expect(separator).toHaveAttribute('aria-valuenow', '280');
  await expect(page.locator('.save-state')).toContainText('Chưa lưu thủ công');
});
