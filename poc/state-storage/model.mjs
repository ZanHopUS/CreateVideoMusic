import {createHash} from 'node:crypto';

export const clone = value => JSON.parse(JSON.stringify(value));
function ordered(value) {
  if (Array.isArray(value)) return value.map(ordered);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(k => [k, ordered(value[k])]));
  return value;
}
export const digest = value => createHash('sha256').update(JSON.stringify(ordered(value))).digest('hex');
export function validate(project) {
  if (!Number.isInteger(project.fps) || project.fps <= 0 || !Number.isInteger(project.durationInFrames) || project.durationInFrames <= 0 || project.durationInFrames / project.fps > 300) throw Error('Invalid project duration');
  if (new Set(project.items.map(i => i.id)).size !== project.items.length) throw Error('Duplicate item ID');
  for (const item of project.items) {
    if (![item.start, item.duration, item.sourceStart ?? 0, item.speed ?? 1].every(Number.isFinite)) throw Error('Non-finite item');
    if (item.start < 0 || item.duration <= 0 || item.start + item.duration > project.durationInFrames || (item.speed ?? 1) <= 0) throw Error('Invalid item range');
  }
  if (project.uiState?.selectedIds.some(id => !project.items.some(i => i.id === id))) throw Error('Dangling selection');
  return project;
}
export class History {
  constructor(project) {this.current = clone(validate(project)); this.undoStack = []; this.redoStack = []; this.savedHash = digest(project);}
  read() {return clone(this.current);}
  get dirty() {return digest(this.current) !== this.savedHash;}
  edit(operation) {
    const next = this.read(); operation(next); validate(next);
    this.undoStack.push(this.current); this.current = clone(next); this.redoStack = [];
  }
  undo() {if (!this.undoStack.length) return false; this.redoStack.push(this.current); this.current = this.undoStack.pop(); return true;}
  redo() {if (!this.redoStack.length) return false; this.undoStack.push(this.current); this.current = this.redoStack.pop(); return true;}
  markSaved(snapshot) {this.savedHash = digest(snapshot);}
}
export function makeTemplate(project, id) {
  return {id, schemaVersion: 'poc-template-1', project: clone(project),
    slots: project.items.filter(i => i.asset).map(i => ({id: `slot-${i.id}`, itemId: i.id, required: true, kind: i.type}))};
}
export function instantiate(template, id, bindings = {}) {
  const project = clone(template.project);
  const remap = new Map(project.items.map(item => [item.id, `${id}-${item.id}`]));
  for (const slot of template.slots) {
    if (Object.hasOwn(bindings, slot.id)) project.items.find(i => i.id === slot.itemId).asset = bindings[slot.id];
  }
  project.id = id; project.originTemplateId = template.id;
  for (const item of project.items) item.id = remap.get(item.id);
  if (project.uiState) project.uiState.selectedIds = project.uiState.selectedIds.map(old => remap.get(old));
  return validate(project);
}
