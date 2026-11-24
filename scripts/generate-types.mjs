import { compileFromFile } from 'json-schema-to-typescript';
import { writeFile } from 'node:fs/promises';
for (const [name, file] of [
  ['project', 'generated'],
  ['template', 'generated-template'],
  ['job', 'generated-job'],
]) {
  const output = await compileFromFile(`packages/domain/${name}.schema.json`, {
    bannerComment: `/* Generated from ${name}.schema.json. Run npm run types; do not edit. */`,
    additionalProperties: false,
    style: { singleQuote: true, tabWidth: 2, trailingComma: 'all' },
  });
  await writeFile(`packages/domain/src/${file}.ts`, output);
}
