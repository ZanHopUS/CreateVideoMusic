/* Generated from template.schema.json. Run npm run types; do not edit. */

export interface TemplateDefinition {
  schemaVersion: 'amvs-template/1';
  id: string;
  version: number;
  name: string;
  defaultProject: import('./generated').ProjectContent;
  slots: {
    id: string;
    itemId: string;
    kind: 'image' | 'video' | 'audio' | 'text' | 'lyrics';
    required: boolean;
  }[];
}
