/** R0 fixed-behavior regression on a fresh isolated build. No lease overrides or TTL changes.
 * Usage: node scripts/diagnose_editor_lease.mjs <prepared .local/evidence/ui-r0/run>
 * See UI_R0_LEASE_DIAGNOSIS.md for preparation/evidence boundaries.
 */
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import readline from 'node:readline';
import { chromium, expect as baseExpect } from '@playwright/test';

const expect = baseExpect.configure({ timeout: 15000 });
const root = process.cwd();
const report = process.env.AMVS_R0_REPORT_NAME || 'r0';
assert(/^[a-z0-9-]+$/.test(report));
let run;
if (process.argv[2]) run = path.resolve(process.argv[2]);
else
  throw new Error(
    'Pass an isolated prepared run with a fresh production build.',
  );

assert(
  run.startsWith(path.join(root, '.local', 'evidence', 'ui-r0') + path.sep),
);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const results = [],
  trace = [],
  pending = new Set();
const inventory = JSON.parse(
  await readFile(path.join(run, 'source-inventory.json'), 'utf8'),
);
let mode,
  origin,
  browser,
  service,
  sequence = 0,
  label = 0;
const browserFile = path.join(
  root,
  'node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe',
);
const privateId = (value) =>
  value ? createHash('sha256').update(value).digest('hex').slice(0, 12) : null;
const save = async () => {
  await Promise.allSettled([...pending]);
  await mkdir(
    path.join(run, report === 'r0' ? 'harness' : report + '-harness'),
    { recursive: true },
  );
  for (const file of [
    'verify_editor_lease.mjs',
    'diagnose_editor_lease_server.py',
  ]) {
    const bytes = await readFile(path.join(root, 'scripts', file));
    const target = path.join(
      run,
      report === 'r0' ? 'harness' : report + '-harness',
      file,
    );
    try {
      await writeFile(target, bytes, { flag: 'wx' });
    } catch (error) {
      if (error.code !== 'EEXIST') throw error;
    }
  }
  await writeFile(
    path.join(run, report + '-results.json'),
    JSON.stringify(
      {
        commit: inventory.commit,
        mode: 'R0 fixed-behavior browser regression; not redesign acceptance',
        sourceUnmodified: false,
        buildProvenance: inventory.fixedBuild ?? null,
        caseFilter: process.env.AMVS_R0_CASE_FILTER || null,
        results,
      },
      null,
      2,
    ),
  );
  await writeFile(
    path.join(
      run,
      report === 'r0' ? 'redacted-network.json' : report + '-network.json',
    ),
    JSON.stringify(trace, null, 2),
  );
};
function observe(page, actor) {
  page.on('dialog', (d) => d.accept());
  page.on('pageerror', (e) =>
    trace.push({
      mode,
      actor: actor.name,
      kind: 'pageerror',
      message: e.message,
    }),
  );
  page.on('request', (request) => {
    if (!request.url().includes('/api/v1/')) return;
    actor.editor = request.headers()['x-amvs-editor'] ?? actor.editor;
    const endpoint = new URL(request.url()).pathname;
    if (!/editor-session|\/projects(?:\/[^/]+)?$|\/save$/.test(endpoint))
      return;
    const body = request.postDataJSON();
    trace.push({
      sequence: ++sequence,
      ms: Date.now(),
      mode,
      actor: actor.name,
      kind: 'request',
      method: request.method(),
      endpoint,
      editorHash: privateId(actor.editor),
      takeover: body?.takeover,
      expectedRevision: body?.revision,
    });
  });
  page.on('response', (response) => {
    const endpoint = new URL(response.url()).pathname;
    if (!/editor-session|\/projects(?:\/[^/]+)?$|\/save$/.test(endpoint))
      return;
    const work = (async () => {
      let value = {};
      try {
        value = await response.json();
      } catch {}
      trace.push({
        sequence: ++sequence,
        ms: Date.now(),
        mode,
        actor: actor.name,
        kind: 'response',
        method: response.request().method(),
        endpoint,
        status: response.status(),
        canWrite: value?.canWrite,
        expiresInSeconds: value?.expiresInSeconds,
        revision: value?.revision,
        code: value?.code,
      });
    })();
    pending.add(work);
    work.finally(() => pending.delete(work));
  });
}
async function session(context) {
  const page = await context.newPage(),
    actor = { name: `tab-${++label}`, page, context, editor: null };
  observe(page, actor);
  await page.goto(origin, { waitUntil: 'domcontentloaded' });
  await expect(
    page.getByRole('button', { name: 'Tạo video mới', exact: false }),
  ).toBeEnabled({ timeout: 60000 });
  actor.token = await page.evaluate(
    async () =>
      (
        await (
          await fetch('/api/v1/session/bootstrap', {
            credentials: 'same-origin',
            cache: 'no-store',
          })
        ).json()
      ).session,
  );
  return actor;
}
async function call(actor, method, endpoint, body) {
  return actor.context.request.fetch(origin + '/api/v1/' + endpoint, {
    method,
    headers: {
      authorization: 'Bearer ' + actor.token,
      origin,
      'x-amvs-editor': actor.editor,
    },
    ...(body === undefined ? {} : { data: body }),
  });
}
async function record(actor, id) {
  const response = await call(actor, 'GET', 'projects/' + id);
  assert.equal(response.status(), 200);
  return response.json();
}
async function create(actor, tag) {
  await actor.page
    .getByRole('button', { name: 'Tạo video mới', exact: false })
    .click();
  await expect(
    actor.page.getByLabel('Tên project', { exact: true }),
  ).toBeEnabled();
  const name = `R0 ${tag} ${mode} ${Date.now()}`;
  await actor.page.getByLabel('Tên project', { exact: true }).fill(name);
  await actor.page.getByLabel('Tên project', { exact: true }).blur();
  let item;
  await expect
    .poll(async () => {
      const list = await (await call(actor, 'GET', 'projects')).json();
      item = list.find((p) => p.name === name);
      return Boolean(item);
    })
    .toBe(true);
  return { id: item.id, name };
}
async function open(actor, project) {
  await actor.page
    .getByRole('button', { name: project.name, exact: true })
    .click();
  await expect(
    actor.page.getByLabel('Tên project', { exact: true }),
  ).toBeVisible();
}
async function ownerPair(tag) {
  const context = await browser.newContext({
    viewport: { width: 1366, height: 768 },
  });
  const a = await session(context),
    project = await create(a, tag),
    b = await session(context);
  await open(b, project);
  await expect(
    b.page.getByLabel('Tên project', { exact: true }),
  ).toBeDisabled();
  return { context, a, b, project };
}
async function scenario(id, kind, action) {
  if (mode === 'development-fixture' && !/^(C02|C10)/.test(id)) return;
  if (
    process.env.AMVS_R0_CASE_FILTER &&
    !id.includes(process.env.AMVS_R0_CASE_FILTER)
  )
    return;
  const began = Date.now();
  try {
    const evidence = await action();
    results.push({
      id,
      mode,
      kind,
      diagnosticStatus: 'observed',
      regressionStatus: 'passed',
      elapsedMs: Date.now() - began,
      ...evidence,
    });
  } catch (error) {
    results.push({
      id,
      mode,
      kind,
      diagnosticStatus: 'probe-failed',
      regressionStatus: 'failed',
      elapsedMs: Date.now() - began,
      error: String(error).slice(0, 1600),
    });
  }
  await save();
  console.log(JSON.stringify({ mode, id, ...results.at(-1) }));
}
async function services() {
  service = spawn(
    path.join(root, '.venv-api/Scripts/python.exe'),
    [path.join(root, 'scripts/diagnose_editor_lease_server.py'), run, mode],
    { cwd: root, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] },
  );
  const lines = readline.createInterface({ input: service.stdout }),
    queue = [],
    listeners = [];
  lines.on('line', (text) => {
    try {
      const row = JSON.parse(text);
      if (listeners.length) listeners.shift()(row);
      else queue.push(row);
    } catch {}
  });
  let diagnostics = '';
  service.stderr.on('data', (data) => {
    diagnostics += String(data);
  });
  const next = () =>
    new Promise((resolve, reject) => {
      if (queue.length) return resolve(queue.shift());
      const timeout = setTimeout(
        () =>
          reject(
            new Error(
              'Disposable services not ready: ' + diagnostics.slice(-1200),
            ),
          ),
        200000,
      );
      listeners.push((row) => {
        clearTimeout(timeout);
        resolve(row);
      });
      service.once('exit', (code) => {
        clearTimeout(timeout);
        reject(
          new Error(
            `Disposable services exited ${code}: ${diagnostics.slice(-1200)}`,
          ),
        );
      });
    });
  origin = (await next()).origin;
  return next;
}
async function main() {
  for (mode of (
    process.env.AMVS_R0_MODES || 'production,development,development-fixture'
  ).split(',')) {
    const nextReady = await services();
    browser = await chromium.launch({ executablePath: browserFile });
    try {
      await scenario('C01-single-tab-and-layout', 'real-control', async () => {
        const context = await browser.newContext({
          viewport: { width: 1366, height: 768 },
        });
        try {
          const a = await session(context),
            project = await create(a, 'single');
          const lease = await (
            await call(a, 'POST', `projects/${project.id}/editor-session`, {
              takeover: false,
            })
          ).json();
          assert.equal(lease.canWrite, true);
          const geometry = [];
          for (const size of [
            { width: 1366, height: 768 },
            { width: 1920, height: 1080 },
          ]) {
            await a.page.setViewportSize(size);
            const row = await a.page.evaluate(() => {
              const bounds = (s) => {
                const r = document.querySelector(s).getBoundingClientRect();
                return {
                  x: r.x,
                  y: r.y,
                  width: r.width,
                  height: r.height,
                  bottom: r.bottom,
                };
              };
              return {
                viewport: { width: innerWidth, height: innerHeight },
                documentHeight: document.documentElement.scrollHeight,
                scrollY,
                preview: bounds('.preview-stage'),
                timeline: bounds('.timeline'),
                inspector: bounds('.inspector'),
              };
            });
            geometry.push(row);
            await a.page.screenshot({
              path: path.join(
                run,
                mode,
                `baseline-${size.width}x${size.height}.png`,
              ),
              fullPage: true,
            });
          }
          return {
            leaseSpecificationViolation: false,
            layoutViolations: geometry.map((g) => ({
              viewport: g.viewport,
              pageOverflow: g.documentHeight > g.viewport.height,
              timelineOutsideViewport: g.timeline.bottom > g.viewport.height,
            })),
            canWrite: lease.canWrite,
            editorHash: privateId(a.editor),
            geometry,
          };
        } finally {
          await context.close();
        }
      });
      await scenario(
        'C02-normal-takeover-protection-edit-history-save',
        'real-control',
        async () => {
          const { context, a, b, project } = await ownerPair('normal');
          try {
            await b.page
              .getByRole('button', {
                name: 'Nhận quyền chỉnh sửa',
                exact: true,
              })
              .click();
            await expect(
              b.page.getByLabel('Tên project', { exact: true }),
            ).toBeEnabled();
            await expect(
              a.page.getByLabel('Tên project', { exact: true }),
            ).toBeDisabled({ timeout: 12000 });
            const current = await record(b, project.id);
            const rejected = await call(a, 'PATCH', `projects/${project.id}`, {
              project: current.project,
              revision: current.revision,
            });
            assert.equal(rejected.status(), 409);
            await b.page
              .getByLabel('Tên project', { exact: true })
              .fill(project.name + ' changed');
            await b.page.getByLabel('Tên project', { exact: true }).blur();
            await b.page
              .getByRole('button', { name: 'Hoàn tác', exact: true })
              .click();
            await expect(
              b.page.getByLabel('Tên project', { exact: true }),
            ).toHaveValue(project.name);
            await b.page
              .getByRole('button', { name: 'Làm lại', exact: true })
              .click();
            await expect(
              b.page.getByLabel('Tên project', { exact: true }),
            ).toHaveValue(project.name + ' changed');
            await b.page.locator('.clip.text').first().click();
            const caption = b.page.getByLabel('Nội dung caption', {
              exact: true,
            });
            const originalCaption = await caption.inputValue();
            await caption.fill('R0 thuộc tính sau takeover');
            await caption.blur();
            await b.page
              .getByRole('button', { name: 'Hoàn tác', exact: true })
              .click();
            await expect(caption).toHaveValue(originalCaption);
            await b.page
              .getByRole('button', { name: 'Làm lại', exact: true })
              .click();
            await expect(caption).toHaveValue('R0 thuộc tính sau takeover');
            let manualSave =
              'not-run: real development launcher has no injected native folder grants';
            if (mode !== 'development') {
              await b.page.route('**/api/v1/folder-grants', (route) =>
                route.fulfill({
                  json: {
                    id: 'e2e-project',
                    label: 'Disposable folder',
                    scope: 'project',
                  },
                }),
              );
              await b.page
                .getByRole('button', { name: 'Lưu project', exact: true })
                .click();
              await expect(b.page.locator('.save-state')).toContainText(
                'Đã lưu',
              );
              const saved = await record(b, project.id);
              assert.equal(saved.dirty, false);
              manualSave =
                'real save endpoint/hash, test-only native folder grant';
            }
            return {
              specificationViolation: false,
              staleWriterStatus: rejected.status(),
              undoRedo: true,
              clipPropertyEditedAfterTakeover: true,
              manualSave,
            };
          } finally {
            await context.close();
          }
        },
      );
      for (let repeat = 1; repeat <= 3; repeat++)
        await scenario(
          `C03-delayed-denial-after-success-${repeat}`,
          'real-backend-responses-with-controlled-latency',
          async () => {
            const context = await browser.newContext();
            let release;
            const gate = new Promise((resolve) => {
              release = resolve;
            });
            try {
              const a = await session(context),
                project = await create(a, 'race'),
                b = await session(context);
              let held = false,
                oldResponse;
              await b.page.route(
                `**/api/v1/projects/${project.id}/editor-session`,
                async (route) => {
                  const body = route.request().postDataJSON();
                  if (
                    route.request().method() === 'POST' &&
                    body.takeover === false &&
                    !held
                  ) {
                    held = true;
                    const response = await route.fetch();
                    oldResponse = await response.json();
                    assert.equal(oldResponse.canWrite, false);
                    trace.push({
                      sequence: ++sequence,
                      ms: Date.now(),
                      mode,
                      actor: b.name,
                      kind: 'held-real-denial',
                      canWrite: oldResponse.canWrite,
                      editorHash: privateId(b.editor),
                    });
                    await gate;
                    await route.fulfill({ response });
                  } else await route.continue();
                },
              );
              await open(b, project);
              await expect.poll(() => Boolean(oldResponse)).toBe(true);
              // Wait for the follow-up claim after GET/adopt, not the optimistic
              // enable immediately after POST takeover. This avoids mistaking
              // adopt's temporary disabled state for a persistent stale response.
              const adoptedClaim = b.page.waitForResponse(
                async (response) =>
                  new URL(response.url()).pathname ===
                    `/api/v1/projects/${project.id}/editor-session` &&
                  response.request().method() === 'POST' &&
                  response.request().postDataJSON().takeover === false &&
                  (await response.json()).canWrite === true,
              );
              await b.page
                .getByRole('button', {
                  name: 'Nhận quyền chỉnh sửa',
                  exact: true,
                })
                .click();
              await expect(
                b.page.getByLabel('Tên project', { exact: true }),
              ).toBeEnabled();
              await adoptedClaim;
              await b.page.evaluate(
                () =>
                  new Promise((resolve) =>
                    requestAnimationFrame(() => requestAnimationFrame(resolve)),
                  ),
              );
              await expect(
                b.page.getByLabel('Tên project', { exact: true }),
              ).toBeEnabled();
              release();
              await expect(
                b.page.getByLabel('Tên project', { exact: true }),
              ).toBeEnabled();
              await sleep(6000);
              await expect(
                b.page.getByLabel('Tên project', { exact: true }),
              ).toBeEnabled();
              const actual = await (
                await call(b, 'POST', `projects/${project.id}/editor-session`, {
                  takeover: false,
                })
              ).json();
              assert.equal(actual.canWrite, true);
              const current = await record(b, project.id),
                oldWrite = await call(a, 'PATCH', `projects/${project.id}`, {
                  project: current.project,
                  revision: current.revision,
                });
              assert.equal(oldWrite.status(), 409);
              await b.page.screenshot({
                path: path.join(
                  run,
                  mode,
                  `race-${repeat}-server-owner-ui-writable.png`,
                ),
                fullPage: true,
              });
              return {
                specificationViolation: false,
                oldRealClaimCanWrite: oldResponse.canWrite,
                takeoverEnabledBeforeLateResponse: true,
                uiReadOnlyAfterLateResponse: false,
                latestAdoptClaimCompletedBeforeReleasingOldResponse: true,
                stillReadOnlyAfterHeartbeatInterval: false,
                backendStillOwnsLease: actual.canWrite,
                oldOwnerWriteStatus: oldWrite.status(),
                editorHash: privateId(b.editor),
              };
            } finally {
              release();
              await context.close();
            }
          },
        );
      await scenario(
        'C04-failed-takeover-hidden',
        'labelled-http-fault-injection',
        async () => {
          const { context, a, b, project } = await ownerPair('hidden');
          try {
            let injected = 0;
            await b.page.route(
              `**/api/v1/projects/${project.id}/editor-session`,
              async (route) => {
                if (
                  route.request().method() === 'POST' &&
                  route.request().postDataJSON().takeover
                ) {
                  injected++;
                  await route.fulfill({
                    status: 503,
                    json: {
                      code: 'R0_TEST_UNAVAILABLE',
                      message: 'R0 lỗi takeover được gây có kiểm soát',
                    },
                  });
                } else await route.continue();
              },
            );
            await b.page
              .getByRole('button', {
                name: 'Nhận quyền chỉnh sửa',
                exact: true,
              })
              .click();
            await expect.poll(() => injected).toBe(1);
            await sleep(400);
            await expect(b.page.locator('footer')).toContainText(
              'R0 lỗi takeover',
            );
            await expect(
              b.page.getByLabel('Tên project', { exact: true }),
            ).toBeDisabled();
            const owner = await (
              await call(a, 'POST', `projects/${project.id}/editor-session`, {
                takeover: false,
              })
            ).json();
            assert.equal(owner.canWrite, true);
            return {
              specificationViolation: false,
              injectedStatus: 503,
              errorShown: true,
              remainsReadOnly: true,
              originalOwnerRetained: owner.canWrite,
            };
          } finally {
            await context.close();
          }
        },
      );
      await scenario(
        'C05-takeover-reload-fails-stale-editable',
        'labelled-network-fault-injection-after-real-takeover',
        async () => {
          const { context, a, b, project } = await ownerPair('reload');
          try {
            const newName = project.name + ' newer server';
            await a.page
              .getByLabel('Tên project', { exact: true })
              .fill(newName);
            await a.page.getByLabel('Tên project', { exact: true }).blur();
            await expect
              .poll(async () => (await record(a, project.id)).project.name)
              .toBe(newName);
            const before = await record(a, project.id);
            let fault = 0;
            await b.page.route(
              `**/api/v1/projects/${project.id}`,
              async (route) => {
                if (route.request().method() === 'GET' && fault === 0) {
                  fault++;
                  await route.abort('failed');
                } else await route.continue();
              },
            );
            await b.page
              .getByRole('button', {
                name: 'Nhận quyền chỉnh sửa',
                exact: true,
              })
              .click();
            await expect.poll(() => fault).toBe(1);
            await expect(
              b.page.getByLabel('Tên project', { exact: true }),
            ).toBeDisabled();
            await expect(b.page.locator('footer')).toContainText(
              'Không thể nhận quyền hoặc tải project',
            );
            await expect(
              b.page.getByLabel('Tên project', { exact: true }),
            ).toHaveValue(project.name);
            const after = await record(b, project.id);
            assert.equal(after.contentHash, before.contentHash);
            await b.page
              .getByRole('button', {
                name: 'Nhận quyền chỉnh sửa',
                exact: true,
              })
              .click();
            await expect(
              b.page.getByLabel('Tên project', { exact: true }),
            ).toBeEnabled();
            await expect(
              b.page.getByLabel('Tên project', { exact: true }),
            ).toHaveValue(newName);

            return {
              specificationViolation: false,
              realTakeoverSucceeded: true,
              reloadFailed: true,
              staleUiEditable: false,
              reloadRetryVerified: true,
              serverContentPreserved: true,
            };
          } finally {
            await context.close();
          }
        },
      );
      await scenario(
        'C06-heartbeat-failure-real-expiry',
        'labelled-network-loss-real-30s-expiry',
        async () => {
          const context = await browser.newContext();
          try {
            const a = await session(context),
              project = await create(a, 'expiry');
            let lost = 0;
            await a.page.route(
              `**/api/v1/projects/${project.id}/editor-session`,
              async (route) => {
                if (route.request().method() === 'POST') {
                  lost++;
                  await route.abort('failed');
                } else await route.continue();
              },
            );
            const began = Date.now();
            await sleep(32000);
            assert(lost >= 5);
            await expect(
              a.page.getByLabel('Tên project', { exact: true }),
            ).toBeDisabled();
            const before = await record(a, project.id);
            const rejected = await call(a, 'PATCH', `projects/${project.id}`, {
              project: before.project,
              revision: before.revision,
            });
            assert.equal(rejected.status(), 409);
            const restoredAt = Date.now();
            trace.push({
              mode,
              actor: a.name,
              kind: 'network-restored',
              ms: restoredAt,
            });
            await a.page.unroute(
              `**/api/v1/projects/${project.id}/editor-session`,
            );
            await expect(
              a.page.getByLabel('Tên project', { exact: true }),
            ).toBeEnabled({ timeout: 35000 });
            await a.page.screenshot({
              path: path.join(run, mode, report + '-expiry-recovered.png'),
              fullPage: true,
            });
            return {
              reconnectElapsedMs: Date.now() - restoredAt,
              recoveredAfterReconnect: true,
              specificationViolation: false,
              elapsedWithoutRenewalMs: Date.now() - began,
              failedHeartbeats: lost,
              uiEditableAfterExpiry: false,
              expiredWriterStatus: 409,
              ttlUnchanged: 30,
            };
          } finally {
            await context.close();
          }
        },
      );
      await scenario(
        'C07-owner-close-expiry-explicit-recovery',
        'real-control-with-lost-release',
        async () => {
          const { context, a, b, project } = await ownerPair('close');
          try {
            await a.page.route(
              `**/api/v1/projects/${project.id}/editor-session`,
              (route) => route.abort('failed'),
            );
            await a.page.close();
            await sleep(32000);
            await b.page
              .getByRole('button', {
                name: 'Nhận quyền chỉnh sửa',
                exact: true,
              })
              .click();
            await expect(
              b.page.getByLabel('Tên project', { exact: true }),
            ).toBeEnabled();
            const actual = await (
              await call(b, 'POST', `projects/${project.id}/editor-session`, {
                takeover: false,
              })
            ).json();
            assert.equal(actual.canWrite, true);
            return {
              specificationViolation: false,
              recovery:
                'explicit takeover after real expiry works; no automatic reclaim required',
              ttlUnchanged: 30,
            };
          } finally {
            await context.close();
          }
        },
      );
      await scenario('C09-repeated-takeovers', 'real-control', async () => {
        const { context, a, b, project } = await ownerPair('repeated');
        try {
          for (const actor of [b, a, b, a, b]) {
            await expect(
              actor.page.getByLabel('Tên project', { exact: true }),
            ).toBeDisabled({ timeout: 12000 });
            await actor.page
              .getByRole('button', {
                name: 'Nhận quyền chỉnh sửa',
                exact: true,
              })
              .click();
            await expect(
              actor.page.getByLabel('Tên project', { exact: true }),
            ).toBeEnabled();
          }
          const latest = await record(b, project.id);
          const stale = await call(a, 'PATCH', `projects/${project.id}`, {
            project: latest.project,
            revision: latest.revision,
          });
          assert.equal(stale.status(), 409);
          return {
            specificationViolation: false,
            consecutiveTakeovers: 5,
            staleWriterStatus: 409,
          };
        } finally {
          await context.close();
        }
      });
      if (mode !== 'development')
        await scenario(
          'C10-save-B-edit-C-dirty',
          'real-save-with-native-grant-fixture',
          async () => {
            const { context, a, b, project } = await ownerPair('save-dirty');
            let release;
            const gate = new Promise((resolve) => {
              release = resolve;
            });
            try {
              await b.page
                .getByRole('button', {
                  name: 'Nhận quyền chỉnh sửa',
                  exact: true,
                })
                .click();
              await expect(
                b.page.getByLabel('Tên project', { exact: true }),
              ).toBeEnabled();
              await b.page.route('**/api/v1/folder-grants', (route) =>
                route.fulfill({
                  json: {
                    id: 'e2e-project',
                    label: 'Disposable',
                    scope: 'project',
                  },
                }),
              );
              const name = b.page.getByLabel('Tên project', { exact: true });
              await name.fill(project.name + ' B');
              await name.blur();
              await expect
                .poll(async () => (await record(b, project.id)).project.name)
                .toBe(project.name + ' B');
              let saved;
              await b.page.route(
                `**/api/v1/projects/${project.id}/save`,
                async (route) => {
                  const response = await route.fetch();
                  saved = await response.json();
                  assert.equal(response.status(), 200);
                  await gate;
                  await route.fulfill({ response });
                },
              );
              await b.page
                .getByRole('button', { name: 'Lưu project', exact: true })
                .click();
              await expect.poll(() => Boolean(saved)).toBe(true);
              await name.fill(project.name + ' C');
              await name.blur();
              release();
              await expect(b.page.locator('.save-state')).toContainText(
                'Chưa lưu',
              );
              await expect
                .poll(async () => (await record(b, project.id)).project.name)
                .toBe(project.name + ' C');
              const current = await record(b, project.id);
              assert.equal(current.manualSavedHash, saved.manualSavedHash);
              assert.equal(current.dirty, true);
              await b.page.screenshot({
                path: path.join(run, mode, 'save-B-edit-C-dirty.png'),
                fullPage: true,
              });
              return {
                specificationViolation: false,
                savedB: true,
                retainedC: true,
                dirty: current.dirty,
              };
            } finally {
              release();
              await context.close();
            }
          },
        );
      await scenario(
        'C11-owner-close-fresh-reopen',
        'real-control',
        async () => {
          const context = await browser.newContext();
          try {
            const a = await session(context),
              project = await create(a, 'fresh-reopen');
            const before = await record(a, project.id);
            await a.page.close();
            const b = await session(context);
            await open(b, project);
            await expect(
              b.page.getByLabel('Tên project', { exact: true }),
            ).toBeEnabled();
            assert.equal(
              (await record(b, project.id)).contentHash,
              before.contentHash,
            );
            return {
              specificationViolation: false,
              freshReopenWritable: true,
              contentPreserved: true,
            };
          } finally {
            await context.close();
          }
        },
      );
      await scenario(
        'C12-reconnect-new-revision-keeps-draft',
        'real-backend-with-labelled-network-loss',
        async () => {
          const context = await browser.newContext();
          try {
            const a = await session(context),
              project = await create(a, 'draft-conflict');
            await a.page.route(
              `**/api/v1/projects/${project.id}/editor-session`,
              (route) => route.abort('failed'),
            );
            await a.page.route(`**/api/v1/projects/${project.id}`, (route) =>
              route.request().method() === 'PATCH'
                ? route.abort('failed')
                : route.continue(),
            );
            const input = a.page.getByLabel('Tên project', { exact: true });
            await input.fill(project.name + ' local C');
            await input.blur();
            await expect(input).toBeDisabled();
            const b = await session(context);
            await open(b, project);
            await b.page
              .getByRole('button', {
                name: 'Nhận quyền chỉnh sửa',
                exact: true,
              })
              .click();
            await expect(
              b.page.getByLabel('Tên project', { exact: true }),
            ).toBeEnabled();
            await b.page
              .getByLabel('Tên project', { exact: true })
              .fill(project.name + ' server D');
            await b.page.getByLabel('Tên project', { exact: true }).blur();
            await expect
              .poll(async () => (await record(b, project.id)).project.name)
              .toBe(project.name + ' server D');
            await b.page.close();
            await a.page.unroute(
              `**/api/v1/projects/${project.id}/editor-session`,
            );
            await a.page.unroute(`**/api/v1/projects/${project.id}`);
            await expect(a.page.locator('footer')).toContainText(
              'Project trên máy đã thay đổi',
              { timeout: 15000 },
            );
            await expect(input).toBeDisabled();
            await expect(input).toHaveValue(project.name + ' local C');
            assert.equal(
              (await record(a, project.id)).project.name,
              project.name + ' server D',
            );
            await a.page.screenshot({
              path: path.join(run, mode, 'reconnect-keeps-local-draft.png'),
              fullPage: true,
            });
            await a.page
              .getByRole('button', {
                name: 'Nhận quyền chỉnh sửa',
                exact: true,
              })
              .click();
            await expect(input).toBeEnabled();
            await expect(input).toHaveValue(project.name + ' server D');
            return {
              specificationViolation: false,
              localDraftRetainedUntilConsent: true,
              serverContentPreserved: true,
              explicitReloadConfirmed: true,
            };
          } finally {
            await context.close();
          }
        },
      );
      if (mode === 'development')
        await scenario(
          'C08-disposable-launcher-restart',
          'real-copied-launcher-control',
          async () => {
            let context = await browser.newContext();
            try {
              const a = await session(context),
                project = await create(a, 'restart');
              const before = await record(a, project.id),
                oldToken = a.token;
              await context.close();
              service.stdin.write('restart\n');
              origin = (await nextReady()).origin;
              context = await browser.newContext();
              const b = await session(context);
              await open(b, project);
              await expect(
                b.page.getByLabel('Tên project', { exact: true }),
              ).toBeEnabled();
              const after = await record(b, project.id);
              assert.equal(after.contentHash, before.contentHash);
              const oldSession = await context.request.get(
                origin + '/api/v1/projects',
                { headers: { authorization: 'Bearer ' + oldToken, origin } },
              );
              assert.equal(oldSession.status(), 401);
              return {
                specificationViolation: false,
                launcher:
                  'unchanged copied scripts/dev.py --restart --no-browser in disposable source',
                reopenedWritable: true,
                contentHashPreserved: true,
                oldSessionStatus: 401,
              };
            } finally {
              await context.close();
            }
          },
        );
    } finally {
      await browser.close();
      service.stdin.end('stop\n');
      await new Promise((resolve) => {
        if (service.exitCode !== null) resolve();
        else service.once('exit', resolve);
      });
    }
  }
}
try {
  await main();
} finally {
  await save();
}
console.log(
  JSON.stringify({
    evidence: run,
    scenarios: results.length,
    pageErrors: trace.filter((r) => r.kind === 'pageerror').length,
    probeFailures: results.filter((r) => r.diagnosticStatus !== 'observed')
      .length,
  }),
);
if (
  trace.some((r) => r.kind === 'pageerror') ||
  results.some((r) => r.diagnosticStatus !== 'observed')
)
  process.exitCode = 2;
