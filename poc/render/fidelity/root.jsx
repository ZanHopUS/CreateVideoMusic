import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {FidelityScene} from './scene.jsx';
import {makeProjects} from './projects.mjs';

function Root() {
  return <>{makeProjects().map(project => <Composition key={project.id} id={project.id}
    component={FidelityScene} width={1280} height={720} fps={30} durationInFrames={360}
    defaultProps={{project}} calculateMetadata={({props}) => ({width: props.project.width,
      height: props.project.height, fps: props.project.fps, durationInFrames: props.project.durationInFrames})} />)}</>;
}
registerRoot(Root);
