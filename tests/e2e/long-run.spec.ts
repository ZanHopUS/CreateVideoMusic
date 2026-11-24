import { test, expect } from '@playwright/test';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { writeFile, readFile } from 'node:fs/promises';

test('S6 opt-in: 300s 1080p60, immutable output and responsive editor under render', async ({
  page,
  request,
  baseURL,
}) => {
  test.skip(
    process.env.AMVS_TEST_LONG_RUN !== '1',
    'Explicit long-run invocation required; production RAM admission stays 4 GiB.',
  );
  test.setTimeout(2700000);
  const run = process.env.AMVS_TEST_RUN!,
    token = 'e2e-disposable-session-' + 'x'.repeat(48),
    headers = { authorization: 'Bearer ' + token, origin: baseURL! };
  let editor = '',
    jobId = '';
  let monitor: ReturnType<typeof spawn> | undefined;
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('dialog', (d) => d.accept());
  page.on('request', (r) => {
    editor = r.headers()['x-amvs-editor'] ?? editor;
  });
  await page.route('**/api/v1/folder-grants', async (route) => {
    const scope = route.request().postDataJSON().scope;
    await route.fulfill({
      json: { id: 'e2e-' + scope, label: 'Disposable folder', scope },
    });
  });
  try {
    await page.goto('/#session=' + token);
    await page
      .getByRole('button', { name: 'Tạo video mới', exact: false })
      .click();
    await expect(
      page.getByRole('button', { name: 'Lưu project', exact: true }),
    ).toBeEnabled();
    await page.getByLabel('Tôi có quyền sử dụng media này').check();
    await page
      .getByLabel('Thêm ảnh, video hoặc nhạc')
      .setInputFiles([
        path.resolve('.local/test-assets/artwork.png'),
        path.resolve('.local/test-assets/control.wav'),
      ]);
    await expect(page.locator('.clip.music')).toHaveCount(1);
    const list = await (
      await request.get(baseURL + '/api/v1/projects', { headers })
    ).json();
    const id = list[0].id;
    await expect
      .poll(async () => {
        const row = await (
          await request.get(`${baseURL}/api/v1/projects/${id}`, { headers })
        ).json();
        return row.project.items.filter(
          (i: { type: string }) => i.type === 'audio',
        ).length;
      })
      .toBe(1);
    const record = await (
        await request.get(`${baseURL}/api/v1/projects/${id}`, { headers })
      ).json(),
      project = record.project;
    const music = project.items.find(
      (i: { type: string }) => i.type === 'audio',
    );
    project.name = 'S6 300 giây · ảnh/nhạc tự tạo';
    project.preset = { width: 1080, height: 1920, fps: 60 };
    project.durationTicks = 300 * 48000;
    project.items = project.items.filter(
      (i: { type: string }) => i.type !== 'audio',
    );
    for (const item of project.items) {
      item.durationTicks = project.durationTicks;
      if (item.type === 'text') {
        item.text = 'Bản dựng chốt trước khi sửa';
        item.style = { ...item.style, x: 84, y: 1275, fontSize: 81 };
      }
    }
    for (let index = 0; index < 75; index++)
      project.items.push({
        ...music,
        id: `long-audio-${index}`,
        startTicks: index * 4 * 48000,
        durationTicks: 4 * 48000,
        sourceStartTicks: 0,
      });
    const update = await request.patch(`${baseURL}/api/v1/projects/${id}`, {
      headers: { ...headers, 'x-amvs-editor': editor },
      data: { project, revision: record.revision, view: {} },
    });
    expect(update.ok()).toBe(true);
    await page.reload();
    await page.getByRole('button', { name: project.name, exact: true }).click();
    const takeover = page.getByRole('button', {
      name: 'Nhận quyền chỉnh sửa',
      exact: true,
    });
    if (await takeover.isVisible()) await takeover.click();
    await expect(
      page.getByRole('button', { name: 'Lưu project', exact: true }),
    ).toBeEnabled();
    await page
      .getByRole('button', { name: 'Lưu project', exact: true })
      .click();
    await expect(page.locator('.save-state')).toContainText('Đã lưu');
    const saved = await (
      await request.get(`${baseURL}/api/v1/projects/${id}`, { headers })
    ).json();
    monitor = spawn(
      path.resolve('.venv-api/Scripts/python.exe'),
      [
        path.resolve('scripts/monitor_e2e_resources.py'),
        run,
        String(process.pid),
      ],
      { windowsHide: true, stdio: 'ignore', env: process.env },
    );
    await page
      .getByRole('button', { name: 'Xuất video', exact: false })
      .click();
    await expect
      .poll(
        async () => {
          const jobs = await (
            await request.get(baseURL + '/api/v1/jobs', { headers })
          ).json();
          const job = jobs.find(
            (j: { kind: string; projectId: string }) =>
              j.kind === 'render' && j.projectId === id,
          );
          if (job) jobId = job.id;
          return job?.status;
        },
        { timeout: 180000, intervals: [1000] },
      )
      .toBe('running');
    await page.locator('.clip.text').first().click();
    await page
      .getByLabel('Nội dung caption', { exact: true })
      .fill('Editor vẫn chỉnh được trong lúc render');
    await page.getByLabel('Nội dung caption', { exact: true }).blur();
    await expect(page.locator('.save-state')).toContainText('Chưa lưu');
    await page.getByRole('button', { name: 'Phát hoặc tạm dừng' }).click();
    const playback = await page.evaluate(async () => {
      const start = performance.now(),
        frames = new Set<string>();
      while (performance.now() - start < 2000) {
        await new Promise<void>((resolve) =>
          requestAnimationFrame(() => resolve()),
        );
        const frame = document
          .querySelector('[data-frame]')
          ?.getAttribute('data-frame');
        if (frame) frames.add(frame);
      }
      return { frames: frames.size, elapsedMs: performance.now() - start };
    });
    await page.getByRole('button', { name: 'Phát hoặc tạm dừng' }).click();
    await page.evaluate(() => {
      const state = { selection: [] as number[], input: [] as number[] };
      (window as unknown as { amvsPerf: typeof state }).amvsPerf = state;
      const mark = (event: Event) => {
        const target = event.target as HTMLElement;
        if (!(target.closest('.clip') || target.closest('.inspector'))) return;
        const began = performance.now();
        requestAnimationFrame(() =>
          requestAnimationFrame(() =>
            state[event.type === 'input' ? 'input' : 'selection'].push(
              performance.now() - began,
            ),
          ),
        );
      };
      document.addEventListener('pointerdown', mark, true);
      document.addEventListener('input', mark, true);
    });
    for (let index = 0; index < 20; index++) {
      await page
        .locator(index % 2 ? '.clip.text' : '.clip.background')
        .first()
        .click();
      if (index % 2)
        await page
          .getByLabel('Cỡ chữ', { exact: true })
          .fill(index % 4 ? '81' : '82');
    }
    const latency = await page.evaluate(
      () =>
        (
          window as unknown as {
            amvsPerf: { selection: number[]; input: number[] };
          }
        ).amvsPerf,
    );
    const p95 = (values: number[]) => {
      const sorted = [...values].sort((a, b) => a - b);
      return sorted.length ? sorted[Math.ceil(sorted.length * 0.95) - 1] : null;
    };
    await writeFile(
      path.join(run, 'long-run-ui.json'),
      JSON.stringify(
        {
          playback,
          observedPreviewFps: playback.frames / (playback.elapsedMs / 1000),
          latency,
          selectionP95Ms: p95(latency.selection),
          inputP95Ms: p95(latency.input),
          thresholdsApproved: false,
          scope:
            'Trusted pointer/input events to double-rAF during real background render; short preview sample',
        },
        null,
        2,
      ),
    );
    await expect
      .poll(
        async () => {
          const job = await (
            await request.get(`${baseURL}/api/v1/jobs/${jobId}`, { headers })
          ).json();
          if (['failed', 'cancelled', 'interrupted'].includes(job.status))
            throw new Error(job.message);
          return job.status;
        },
        { timeout: 1800000, intervals: [5000] },
      )
      .toBe('succeeded');
    const job = await (
      await request.get(`${baseURL}/api/v1/jobs/${jobId}`, { headers })
    ).json();
    expect(job.snapshotHash).toBe(saved.contentHash);
    expect(job.resourceSampledPass).toBe(true);
    const current = await (
      await request.get(`${baseURL}/api/v1/projects/${id}`, { headers })
    ).json();
    expect(current.contentHash).not.toBe(saved.contentHash);
    expect(current.dirty).toBe(true);
    expect(errors).toEqual([]);
    await page.screenshot({
      path: path.join(run, 'long-run-complete.png'),
      fullPage: true,
    });
    await writeFile(
      path.join(run, 'long-run-job.json'),
      JSON.stringify(
        {
          job,
          savedHash: saved.contentHash,
          editedHash: current.contentHash,
          errors,
        },
        null,
        2,
      ),
    );
  } finally {
    if (jobId) {
      try {
        await request.post(`${baseURL}/api/v1/jobs/${jobId}/cancel`, {
          headers,
          data: {},
        });
      } catch {}
    }
    await writeFile(path.join(run, 'resource-monitor.stop'), 'stop');
    if (monitor) {
      await Promise.race([
        new Promise<void>((resolve) => monitor!.once('exit', () => resolve())),
        new Promise<void>((resolve) => setTimeout(resolve, 5000)),
      ]);
      if (monitor.exitCode === null) monitor.kill();
    }
  }
  const resources = JSON.parse(
    await readFile(
      path.join(run, 'application-resources-summary.json'),
      'utf8',
    ),
  );
  expect(resources.samples).toBeGreaterThan(30);
  expect(resources.minimumAvailableBytes).toBeGreaterThanOrEqual(2 * 1024 ** 3);
  expect(resources.peakPrivateBytes).toBeLessThanOrEqual(12 * 1024 ** 3);
});
