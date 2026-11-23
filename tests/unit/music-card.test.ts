import { describe, expect, it } from 'vitest';
import { newMusicCardProject, validateProject } from '@amvs/domain';

describe('Music Card template', () => {
  it('starts with editable song and artist fields in the shared project schema', () => {
    const project = newMusicCardProject('music-card-fixture');
    expect(() => validateProject(project)).not.toThrow();
    expect(project.templateRef).toEqual({ id: 'TPL-02', version: 1 });
    expect(
      project.items
        .filter((item) => item.type === 'text')
        .map((item) => item.id),
    ).toEqual(['song-title', 'artist-name']);
    expect(project.assetRefs).toEqual([]);
  });
});
