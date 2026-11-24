import { expect, test } from '@playwright/test';

test('Drive: cấu hình và hủy OAuth local, chưa truy cập Google thật', async ({
  page,
  request,
  baseURL,
}) => {
  const token = 'e2e-disposable-session-' + 'x'.repeat(48);
  await page.goto('/');
  await page.getByRole('button', { name: 'Lưu trữ', exact: true }).click();
  await page.getByRole('tab', { name: 'Cấu hình' }).click();
  const toggle = page.getByRole('button', { name: /Kho Google Drive/ });
  await expect(toggle).toBeEnabled();
  await toggle.click();
  await expect(page.getByLabel('Link thư mục Drive')).toBeVisible();
  await page
    .getByLabel('Link thư mục Drive')
    .fill('https://drive.google.com/drive/folders/fixture_folder_12345');
  await page.getByLabel('OAuth client JSON', { exact: true }).setInputFiles({
    name: 'fixture-oauth.json',
    mimeType: 'application/json',
    buffer: Buffer.from(
      JSON.stringify({
        installed: {
          client_id: 'fixture.apps.googleusercontent.com',
          client_secret: 'fixture-only-secret',
        },
      }),
    ),
  });
  await page.getByRole('button', { name: 'Lưu cấu hình Drive' }).click();
  await expect(
    page.getByRole('button', { name: 'Đăng nhập Google', exact: true }),
  ).toBeEnabled();
  await page
    .getByRole('button', { name: 'Đăng nhập Google', exact: true })
    .click();
  const authLink = page.getByRole('link', { name: /Mở Google để cấp quyền/ });
  await expect(authLink).toBeVisible();
  const url = new URL((await authLink.getAttribute('href'))!);
  expect(url.origin).toBe('https://accounts.google.com');
  expect(url.searchParams.get('scope')).toBe(
    'https://www.googleapis.com/auth/drive.file',
  );
  expect(url.searchParams.get('trigger_onepick')).toBe('true');
  expect(url.href).not.toContain('fixture-only-secret');
  await expect(
    page.getByRole('button', {
      name: 'Sao lưu dữ liệu lên Drive',
      exact: true,
    }),
  ).toBeDisabled();
  await page.getByRole('button', { name: 'Ngắt / hủy kết nối' }).click();
  await expect(authLink).toHaveCount(0);
  const state = await request.get(baseURL + '/api/v1/drive', {
    headers: { origin: baseURL!, authorization: 'Bearer ' + token },
  });
  expect((await state.json()).connected).toBe(false);
  expect(await state.text()).not.toContain('fixture-only-secret');
});

test('Phiên local không cấp cho yêu cầu ngoài trang Studio', async ({
  request,
  baseURL,
}) => {
  const cases: Record<string, string>[] = [
    {},
    { 'sec-fetch-site': 'cross-site', referer: 'https://example.com/' },
    { 'sec-fetch-site': 'same-origin', referer: 'https://example.com/' },
  ];
  for (const headers of cases) {
    const response = await request.get(`${baseURL}/api/v1/session/bootstrap`, {
      headers,
    });
    expect(response.status()).toBe(403);
    expect(await response.text()).not.toContain('e2e-disposable-session');
  }
});
