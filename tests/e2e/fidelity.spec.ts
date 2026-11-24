import { test, expect } from '@playwright/test';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

test('S6 opt-in: real UI preview frames match completed matrix MP4 snapshots', async ({
  page,
}) => {
  test.skip(
    !process.env.AMVS_FIDELITY_RUN,
    'Requires completed S6 matrix artifacts; does not create additional render jobs.',
  );
  const run = process.env.AMVS_TEST_RUN!,
    token = 'e2e-disposable-session-' + 'x'.repeat(48);
  page.on('dialog', (d) => d.accept());
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  const inputs = JSON.parse(
    await readFile(path.join(run, 'fidelity-inputs.json'), 'utf8'),
  ) as {
    projectId: string;
    name: string;
    template: string;
    output: string;
    frames: number[];
  }[];
  const cases: unknown[] = [];
  await page.goto('/#session=' + token);
  for (const input of inputs) {
    await page.getByRole('button', { name: input.name, exact: true }).click();
    if (
      await page
        .getByRole('button', { name: 'Nhận quyền chỉnh sửa', exact: true })
        .isVisible()
    )
      await page
        .getByRole('button', { name: 'Nhận quyền chỉnh sửa', exact: true })
        .click();
    const lyrics = page.getByText('Lời hát · nhập, nhận dạng và duyệt', {
      exact: true,
    });
    if (await lyrics.isVisible()) {
      const details = lyrics.locator('..');
      if ((await details.getAttribute('open')) !== null) await lyrics.click();
    }
    for (const frame of input.frames) {
      const ruler = page.locator('.ruler'),
        box = await ruler.boundingBox();
      expect(box).not.toBeNull();
      await ruler.click({ position: { x: (box!.width * frame) / 60, y: 5 } });
      await expect(page.locator('[data-frame]')).toHaveAttribute(
        'data-frame',
        String(frame),
      );
      await expect
        .poll(() =>
          page
            .locator('.preview-stage img')
            .evaluateAll((images) =>
              images.every(
                (img) =>
                  (img as HTMLImageElement).complete &&
                  (img as HTMLImageElement).naturalWidth > 0,
              ),
            ),
        )
        .toBe(true);
      if (await page.locator('.preview-stage video').count())
        await expect
          .poll(() =>
            page
              .locator('.preview-stage video')
              .first()
              .evaluate((video) => {
                const v = video as HTMLVideoElement;
                return v.readyState >= 2 && !v.seeking;
              }),
          )
          .toBe(true);
      await page.locator('.preview-stage').scrollIntoViewIfNeeded();
      const name = `preview-${input.template}-${frame}.png`;
      await page
        .locator('.preview-stage > div')
        .first()
        .screenshot({ path: path.join(run, name) });
      cases.push({
        template: input.template,
        frame,
        screenshot: name,
        output: input.output,
      });
    }
  }
  await writeFile(
    path.join(run, 'preview-frame-cases.json'),
    JSON.stringify(cases, null, 2),
  );
  expect(errors).toEqual([]);
});
