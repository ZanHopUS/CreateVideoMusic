import React from 'react';
import { Composition, registerRoot, staticFile } from 'remotion';
import { ProjectScene, type SceneProps } from '@amvs/composition';
import { newProject, TICKS } from '@amvs/domain';
function Scene(props: SceneProps) {
  return (
    <ProjectScene
      {...props}
      assets={Object.fromEntries(
        Object.entries(props.assets).map(([id, file]) => [
          id,
          staticFile(file),
        ]),
      )}
    />
  );
}
function Root() {
  return (
    <Composition
      id="Project"
      component={Scene}
      width={720}
      height={1280}
      fps={30}
      durationInFrames={450}
      defaultProps={{ project: newProject('initial'), assets: {} }}
      calculateMetadata={({ props }) => ({
        ...props.project.preset,
        durationInFrames: Math.ceil(
          (props.project.durationTicks * props.project.preset.fps) / TICKS,
        ),
      })}
    />
  );
}
registerRoot(Root);
