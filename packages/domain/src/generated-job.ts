/* Generated from job.schema.json. Run npm run types; do not edit. */

export type JobState = {
  schemaVersion: 'amvs-job/1';
  id: string;
  kind: 'render' | 'asr' | 'alignment' | 'package';
  projectId: string;
  status:
    | 'queued'
    | 'preparing'
    | 'running'
    | 'finalizing'
    | 'validating'
    | 'succeeded'
    | 'cancelling'
    | 'cancelled'
    | 'failed'
    | 'interrupted';
  phase:
    | 'queued'
    | 'waiting-resources'
    | 'preparing'
    | 'running'
    | 'finalizing'
    | 'validating'
    | 'succeeded'
    | 'cancelling'
    | 'cancelled'
    | 'failed'
    | 'interrupted';
  progress: number;
  snapshotHash: string;
  message: string;
  resourceSampledPass?: boolean;
  resourceScope?: 'render-and-finalize-children-only';
};
