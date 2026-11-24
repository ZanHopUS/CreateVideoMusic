import { test, expect } from '@playwright/test';
import path from 'node:path';
const token = 'e2e-disposable-session-' + 'x'.repeat(48);
test('TPL-03: import, review, styles, preset, recovery and portable package through UI', async ({
  page,
  request,
  baseURL,
}) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('dialog', (d) => d.accept());
  await page.route('**/api/v1/folder-grants', async (route) => {
    const scope = route.request().postDataJSON().scope;
    await route.fulfill({
      json: { id: 'e2e-' + scope, label: 'Disposable', scope },
    });
  });
  await page.goto('/#session=' + token);
  await page.getByRole('button', { name: 'Lyrics Video' }).click();
  await page.getByLabel('Độ dài video', { exact: true }).fill('3');
  await page.getByLabel('Tôi có quyền sử dụng media này').check();
  await page
    .getByLabel('Thêm ảnh, video hoặc nhạc')
    .setInputFiles([
      path.resolve('.local/test-assets/artwork.png'),
      path.resolve('.local/test-assets/control.wav'),
    ]);
  await expect(page.locator('.clip.music')).toHaveCount(1);
  await page
    .getByLabel('Lời có timestamp')
    .fill('[00:00]Xin chào Việt Nam\n[00:01.50]Giai điệu của tôi');
  await page.getByRole('button', { name: 'Đọc lời thành bản nháp' }).click();
  await expect(
    page.getByRole('button', { name: 'Áp dụng lời đã duyệt' }),
  ).toBeDisabled();
  await page.getByLabel('Đã duyệt câu 1').check();
  await page.getByLabel('Đã duyệt câu 2').check();
  await page.getByRole('button', { name: 'Áp dụng lời đã duyệt' }).click();
  await expect(page.locator('.clip.lyrics')).toHaveCount(2);
  await page.locator('.clip.lyrics').first().click();
  await page.getByLabel('Hiệu ứng clip').selectOption('fade');
  await page.getByLabel('Cỡ chữ', { exact: true }).fill('42');
  await page.getByLabel('Định dạng xuất').selectOption('720x720-60');
  await page.getByLabel('Loại lớp mới', { exact: true }).selectOption('lyrics');
  await page.getByRole('button', { name: 'Thêm lớp', exact: true }).click();
  await page.locator('.clip.lyrics').first().click();
  await page
    .getByLabel('Lớp chứa clip', { exact: true })
    .selectOption({ label: 'Lớp 2' });
  await page
    .getByRole('button', { name: 'Thêm chú thích', exact: true })
    .click();
  await page.locator('.clip.text').first().click();
  await page
    .getByLabel('Nội dung caption', { exact: true })
    .fill('Chú thích trên lớp riêng');
  await page.getByLabel('Nội dung caption', { exact: true }).blur();

  await page.getByRole('button', { name: 'Làm lại', exact: true }).click(); // Empty redo must be safe.
  await page
    .getByText('Dữ liệu project · recovery và bản di chuyển', { exact: true })
    .click();
  await page.getByRole('button', { name: 'Tạo recovery ngay' }).click();
  await expect(
    page.getByRole('button', { name: 'Khôi phục', exact: true }),
  ).toBeVisible();
  await page
    .getByLabel('Tên project', { exact: true })
    .fill('Đổi sau recovery');
  await page.getByLabel('Tên project', { exact: true }).blur();
  await page.getByRole('button', { name: 'Khôi phục', exact: true }).click();
  await expect(page.getByLabel('Tên project', { exact: true })).toHaveValue(
    'Video lời hát của tôi',
  );
  await expect(page.locator('.clip.lyrics')).toHaveCount(2);
  await page.getByRole('button', { name: 'Lưu project', exact: true }).click();
  await expect(page.locator('.save-state')).toContainText('Đã lưu');
  await page
    .getByRole('button', { name: 'Đóng gói di chuyển (.amvs)', exact: true })
    .click();
  await expect(page.getByText(/Đã tạo .+\.amvs; chứa project/)).toBeVisible({
    timeout: 30000,
  });
  await page.getByLabel('Giới hạn cache', { exact: true }).fill('64');
  await page
    .getByRole('button', { name: 'Lưu giới hạn dung lượng', exact: true })
    .click();
  await expect(
    page.getByText('Đã cập nhật giới hạn dung lượng; không tự xóa media.', {
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Tìm media không dùng để dọn', exact: true })
    .click();
  await expect(
    page.getByRole('button', {
      name: 'Xóa các media không dùng đã chọn',
      exact: true,
    }),
  ).toBeDisabled();
  await page
    .getByRole('button', { name: 'Dọn cache thumbnail', exact: true })
    .click();
  await expect(
    page.getByText('Đã dọn cache thumbnail.', { exact: true }),
  ).toBeVisible();
  const headers = { authorization: 'Bearer ' + token, origin: baseURL! };
  const projects = await (
    await request.get(`${baseURL}/api/v1/projects`, { headers })
  ).json();
  const current = await (
    await request.get(`${baseURL}/api/v1/projects/${projects[0].id}`, {
      headers,
    })
  ).json();
  expect(current.project.preset).toEqual({ width: 720, height: 720, fps: 60 });
  expect(
    current.project.lyrics.every(
      (l: { status: string }) => l.status === 'reviewed',
    ),
  ).toBe(true);
  expect(
    current.project.items.filter((i: { type: string }) => i.type === 'lyrics'),
  ).toHaveLength(2);
  expect(errors).toEqual([]);
});

test('library search/reuse and immutable template instance through UI', async ({
  page,
}) => {
  page.on('dialog', (d) => d.accept());
  await page.goto('/#session=' + token);
  await page
    .getByRole('button', { name: 'Tạo video mới', exact: false })
    .click();
  await page.getByLabel('Độ dài video', { exact: true }).fill('3');
  await page.getByLabel('Tôi có quyền sử dụng media này').check();
  await page
    .getByLabel('Thêm ảnh, video hoặc nhạc')
    .setInputFiles([
      path.resolve('.local/test-assets/artwork.png'),
      path.resolve('.local/test-assets/control.wav'),
    ]);
  await expect(page.locator('.clip.music')).toHaveCount(1);
  await page
    .getByText('Thư viện media · tìm, nghe và dùng lại', { exact: true })
    .click();
  await page.getByLabel('Tìm media', { exact: true }).fill('artwork');
  await expect(
    page.getByRole('button', {
      name: 'Thêm artwork.png vào project',
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Thêm artwork.png vào project', exact: true })
    .click();
  await expect(page.locator('.clip.background')).toHaveCount(2);
  await page
    .getByText('Mẫu cá nhân · lưu từ project và tái sử dụng', { exact: true })
    .click();
  await page.getByLabel('Tên mẫu cá nhân').fill('Mẫu kiểm thử UI');
  await page.getByLabel('Giai điệu của bạn', { exact: true }).check();
  await page
    .getByRole('button', { name: 'Lưu thành mẫu', exact: true })
    .click();
  await expect(
    page.getByText('Đã lưu mẫu cá nhân.', { exact: true }),
  ).toBeVisible();
  await page
    .getByLabel('Chọn mẫu cá nhân')
    .selectOption({ label: 'Mẫu kiểm thử UI' });
  await page.getByLabel('Nội dung thay thế 1').fill('Chữ từ mẫu mới');
  await page
    .getByRole('button', { name: 'Tạo project từ mẫu cá nhân', exact: true })
    .click();
  await expect(page.getByLabel('Tên project', { exact: true })).toHaveValue(
    'Mẫu kiểm thử UI · bản mới',
  );
  await expect(page.locator('.clip.text')).toContainText('Chữ từ mẫu mới');
});

test('AI review polling uses a labelled transport fixture; success stays draft and failure preserves edits', async ({
  page,
}) => {
  const id = 'e'.repeat(32);
  let attempt = 0;
  await page.route('**/api/v1/lyrics/jobs', (route) => {
    attempt++;
    return route.fulfill({
      status: 202,
      json: {
        id,
        kind: 'asr',
        status: 'queued',
        phase: 'queued',
        progress: 0,
        message: 'Transport fixture, no real inference',
      },
    });
  });
  await page.route(`**/api/v1/jobs/${id}`, (route) =>
    route.fulfill({
      json: {
        id,
        kind: 'asr',
        status: attempt === 1 ? 'succeeded' : 'failed',
        phase: attempt === 1 ? 'succeeded' : 'failed',
        progress: attempt === 1 ? 1 : 0,
        message: attempt === 1 ? 'Fixture complete' : 'Fixture error',
      },
    }),
  );
  await page.route(`**/api/v1/jobs/${id}/lyrics`, (route) =>
    route.fulfill({
      json: {
        message: 'Transport fixture only',
        lines: [
          {
            id: 'fixture-line',
            text: 'Lời nháp kiểm thử',
            sourceStartTicks: 0,
            sourceEndTicks: 48000,
            source: 'asr',
            status: 'draft',
            alignmentStatus: 'sentence',
            words: [],
          },
        ],
      },
    }),
  );
  await page.goto('/#session=' + token);
  await page.getByRole('button', { name: 'Lyrics Video' }).click();
  await page.getByLabel('Độ dài video', { exact: true }).fill('3');
  await page.getByLabel('Tôi có quyền sử dụng media này').check();
  await page
    .getByLabel('Thêm ảnh, video hoặc nhạc')
    .setInputFiles([
      path.resolve('.local/test-assets/artwork.png'),
      path.resolve('.local/test-assets/control.wav'),
    ]);
  await expect(page.locator('.clip.music')).toHaveCount(1);
  await page
    .getByRole('button', { name: 'Nhận dạng trên máy', exact: true })
    .click();
  await expect(page.getByLabel('Lời câu 1', { exact: true })).toHaveValue(
    'Lời nháp kiểm thử',
    { timeout: 10000 },
  );
  await expect(page.locator('.clip.lyrics')).toHaveCount(0);
  await page
    .getByLabel('Lời câu 1', { exact: true })
    .fill('Bản sửa phải được giữ');
  await page
    .getByRole('button', { name: 'Nhận dạng trên máy', exact: true })
    .click();
  await expect(page.getByText('Fixture error', { exact: false })).toBeVisible({
    timeout: 10000,
  });
  await expect(page.getByLabel('Lời câu 1', { exact: true })).toHaveValue(
    'Bản sửa phải được giữ',
  );
  await page
    .getByRole('button', { name: 'Lưu bản nháp lời vào project', exact: true })
    .click();
  await expect(page.getByText(/Đã ghi bản nháp vào project/)).toBeVisible();
});

test('S6 measures real UI selection-to-paint and preview frames for generated 12/100-image fixtures', async ({
  page,
  request,
  baseURL,
}) => {
  page.on('dialog', (d) => d.accept());
  let editor = '';
  page.on('request', (request) => {
    editor = request.headers()['x-amvs-editor'] ?? editor;
  });
  await page.goto('/#session=' + token);
  await page
    .getByRole('button', { name: 'Tạo video mới', exact: false })
    .click();
  await page.getByLabel('Độ dài video', { exact: true }).fill('4');
  await page.getByLabel('Tôi có quyền sử dụng media này').check();
  await page
    .getByLabel('Thêm ảnh, video hoặc nhạc')
    .setInputFiles([
      path.resolve('.local/test-assets/artwork.png'),
      path.resolve('.local/test-assets/control.wav'),
    ]);
  await expect(page.locator('.clip.music')).toHaveCount(1);
  await page.getByRole('button', { name: 'Phát hoặc tạm dừng' }).click();
  await page.getByRole('button', { name: 'Phát hoặc tạm dừng' }).click();
  const headers = { authorization: 'Bearer ' + token, origin: baseURL! };
  // Let the normal working-save settle before modifying the disposable fixture.
  await expect
    .poll(async () => {
      const list = await (
        await request.get(`${baseURL}/api/v1/projects`, { headers })
      ).json();
      const record = await (
        await request.get(`${baseURL}/api/v1/projects/${list[0].id}`, {
          headers,
        })
      ).json();
      return record.project.items.filter(
        (i: { type: string }) => i.type === 'image',
      ).length;
    })
    .toBe(1);
  const list = await (
    await request.get(`${baseURL}/api/v1/projects`, { headers })
  ).json();
  const id = list[0].id;
  const measurements: unknown[] = [];
  for (const count of [12, 100]) {
    const record = await (
      await request.get(`${baseURL}/api/v1/projects/${id}`, { headers })
    ).json();
    const project = record.project;
    const image = project.items.find(
      (i: { type: string }) => i.type === 'image',
    );
    project.name = `Hiệu năng fixture ${count}`;
    project.items = [
      ...project.items.filter((i: { type: string }) => i.type !== 'image'),
      ...Array.from({ length: count }, (_, n) => ({
        ...image,
        id: `perf-image-${n}`,
        startTicks: n * 1600,
        durationTicks: 1600,
      })),
    ];
    const response = await request.patch(`${baseURL}/api/v1/projects/${id}`, {
      headers: { ...headers, 'x-amvs-editor': editor },
      data: { project, revision: record.revision, view: {} },
    });
    expect(response.ok()).toBe(true);

    await page.reload();
    await page
      .getByRole('button', { name: `Hiệu năng fixture ${count}`, exact: true })
      .click();
    await expect(page.locator('.clip.background')).toHaveCount(count);
    const latency = await page.evaluate(async () => {
      const elements = [
        ...document.querySelectorAll<HTMLButtonElement>('.clip.background'),
      ];
      const times: number[] = [];
      for (let n = 0; n < 30; n++) {
        const start = performance.now();
        elements[n % elements.length].click();
        await new Promise<void>((resolve) =>
          requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
        );
        times.push(performance.now() - start);
      }
      return times;
    });
    await page.getByRole('button', { name: 'Phát hoặc tạm dừng' }).click();
    const playback = await page.evaluate(async () => {
      const start = performance.now();
      const frames = new Set<string>();
      while (performance.now() - start < 1500) {
        await new Promise<void>((resolve) =>
          requestAnimationFrame(() => resolve()),
        );
        const frame = document
          .querySelector('[data-frame]')
          ?.getAttribute('data-frame');
        if (frame) frames.add(frame);
      }
      return {
        uniqueFrames: frames.size,
        elapsedMs: performance.now() - start,
      };
    });
    await page.getByRole('button', { name: 'Phát hoặc tạm dừng' }).click();
    const sorted = [...latency].sort((a, b) => a - b);
    measurements.push({
      imageClips: count,
      selectionToPaintP95Ms: sorted[Math.ceil(sorted.length * 0.95) - 1],
      latencySamples: latency,
      previewObservedFps: playback.uniqueFrames / (playback.elapsedMs / 1000),
      playback,
      scope:
        'Controlled DOM click to double-rAF on real React UI; short preview, no AI/render contention; not full interaction acceptance',
    });
  }
  const fs = await import('node:fs/promises');
  await fs.writeFile(
    path.join(process.env.AMVS_TEST_RUN!, 'ui-performance.json'),
    JSON.stringify({ measurements, thresholdsApproved: false }, null, 2),
  );
  await page.screenshot({
    path: path.join(process.env.AMVS_TEST_RUN!, 'editor-100-clips.png'),
    fullPage: true,
  });
  expect(measurements).toHaveLength(2);
});

test('second tab is read-only until explicit editor takeover', async ({
  page,
  context,
  request,
  baseURL,
}) => {
  await page.goto('/#session=' + token);
  await page
    .getByRole('button', { name: 'Tạo video mới', exact: false })
    .click();
  await expect(
    page.getByRole('button', { name: 'Lưu project', exact: true }),
  ).toBeEnabled();
  await page
    .getByLabel('Tên project', { exact: true })
    .fill('Project lease fixture');
  await page.getByLabel('Tên project', { exact: true }).blur();
  const headers = { authorization: 'Bearer ' + token, origin: baseURL! };
  await expect
    .poll(async () => {
      const rows = await (
        await request.get(`${baseURL}/api/v1/projects`, { headers })
      ).json();
      return rows[0].name;
    })
    .toBe('Project lease fixture');
  const other = await context.newPage();
  other.on('dialog', (d) => d.accept());
  try {
    await other.goto('/#session=' + token);
    await other
      .getByRole('button', { name: 'Project lease fixture', exact: true })
      .click();
    await expect(
      other.getByRole('button', { name: 'Nhận quyền chỉnh sửa', exact: true }),
    ).toBeVisible();
    await expect(
      other.getByLabel('Tên project', { exact: true }),
    ).toBeDisabled();
    await other
      .getByRole('button', { name: 'Nhận quyền chỉnh sửa', exact: true })
      .click();
    await expect(
      other.getByLabel('Tên project', { exact: true }),
    ).toBeEnabled();
    await expect(page.getByLabel('Tên project', { exact: true })).toBeDisabled({
      timeout: 10000,
    });
    await other
      .getByLabel('Tên project', { exact: true })
      .fill('Chỉ tab sở hữu ghi');
    await other.getByLabel('Tên project', { exact: true }).blur();
    await expect
      .poll(async () => {
        const rows = await (
          await request.get(`${baseURL}/api/v1/projects`, { headers })
        ).json();
        return rows[0].name;
      })
      .toBe('Chỉ tab sở hữu ghi');
  } finally {
    await other.close();
  }
});
