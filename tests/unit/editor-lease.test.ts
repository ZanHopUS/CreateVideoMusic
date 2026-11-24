import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Api, ApiError, type RecordState } from '../../apps/web/lib/api';
import { EditorLease } from '../../apps/web/lib/editor-lease';

const record = (revision = 1) =>
  ({ project: { id: 'project-a' }, revision }) as RecordState;
const granted = { canWrite: true, expiresInSeconds: 30 };
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}
function setup() {
  const api = new Api('unit-only');
  const call = vi
    .spyOn(api, 'call')
    .mockImplementation(async (path) =>
      path.endsWith('editor-session') ? granted : record(),
    );
  let current = record();
  const state = vi.fn(),
    message = vi.fn();
  const apply = vi.fn((next: RecordState) => {
    current = next;
  });
  const lease = new EditorLease(api, {
    record: () => current,
    apply,
    pins: () => ({}),
    state,
    message,
  });
  return {
    lease,
    call,
    apply,
    state,
    message,
    setRecord: (next: RecordState) => {
      current = next;
    },
  };
}
const settle = async () => {
  for (let i = 0; i < 20; ++i) await Promise.resolve();
};
describe('editor authority epochs', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
  });
  it('ignores an old denial after a successful takeover, and keeps heartbeats running', async () => {
    const { lease, call } = setup();
    const old = deferred<unknown>();
    call.mockImplementationOnce(() => old.promise);
    lease.open('project-a');
    await lease.acquire(true);
    expect(lease.canWrite()).toBe(true);
    old.resolve({ canWrite: false, expiresInSeconds: 20 });
    await settle();
    expect(lease.canWrite()).toBe(true);
    const before = call.mock.calls.length;
    await vi.advanceTimersByTimeAsync(5000);
    expect(call.mock.calls.length).toBeGreaterThan(before);
    expect(lease.canWrite()).toBe(true);
    lease.dispose();
  });
  it('only the newest of consecutive takeovers may apply a record', async () => {
    const { lease, call, apply } = setup();
    lease.open('project-a');
    await settle();
    const delayed = deferred<unknown>();
    call.mockImplementationOnce(() => delayed.promise);
    const old = lease.acquire(true);
    await lease.acquire(true);
    const count = apply.mock.calls.length;
    delayed.resolve(granted);
    await old;
    expect(apply).toHaveBeenCalledTimes(count);
    expect(lease.canWrite()).toBe(true);
    lease.dispose();
  });
  it('does not enable writes before reload and final confirmation, and shows reload errors', async () => {
    const { lease, call, message } = setup();
    lease.open('project-a');
    await settle();
    const reload = deferred<unknown>();
    call
      .mockImplementationOnce(async () => granted)
      .mockImplementationOnce(() => reload.promise);
    const action = lease.acquire(true);
    await settle();
    expect(lease.canWrite()).toBe(false);
    reload.resolve(Promise.reject(new Error('reload failed')));
    await action;
    expect(lease.canWrite()).toBe(false);
    expect(message).toHaveBeenLastCalledWith(
      expect.stringContaining('reload failed'),
    );
    lease.dispose();
  });
  it('locks on heartbeat failure and resumes only after matching revision validation', async () => {
    const { lease, call } = setup();
    lease.open('project-a');
    await settle();
    call.mockRejectedValueOnce(new TypeError('offline'));
    await vi.advanceTimersByTimeAsync(5000);
    expect(lease.canWrite()).toBe(false);
    await vi.advanceTimersByTimeAsync(5000);
    expect(lease.canWrite()).toBe(true);
    lease.dispose();
  });
  it('keeps the draft and stays read-only when reconnect finds a newer revision', async () => {
    const { lease, call, apply, message } = setup();
    lease.open('project-a');
    await settle();
    const applies = apply.mock.calls.length;
    lease.fail(new TypeError('offline'));
    call.mockImplementation(async (path) =>
      path.endsWith('editor-session') ? granted : record(9),
    );
    await vi.advanceTimersByTimeAsync(5000);
    expect(lease.canWrite()).toBe(false);
    expect(apply).toHaveBeenCalledTimes(applies);
    expect(message).toHaveBeenLastCalledWith(
      expect.stringContaining('đã thay đổi'),
    );
    lease.dispose();
  });
  it('rejects stale project callbacks across A to B to A, and after disposal', async () => {
    const { lease, call, apply } = setup();
    const old = deferred<unknown>();
    call.mockImplementationOnce(() => old.promise);
    lease.open('project-a');
    lease.open('project-b');
    lease.open('project-a');
    await settle();
    const applies = apply.mock.calls.length;
    lease.dispose();
    old.resolve(granted);
    await settle();
    expect(apply).toHaveBeenCalledTimes(applies);
    expect(lease.canWrite()).toBe(false);
    expect(vi.getTimerCount()).toBe(0);
  });
  it('does not auto-takeover after a backend conflict', async () => {
    const { lease, call } = setup();
    lease.open('project-a');
    await settle();
    lease.fail(new ApiError('stale revision', 409, 'CONFLICT'));
    const count = call.mock.calls.length;
    await vi.advanceTimersByTimeAsync(35000);
    expect(call).toHaveBeenCalledTimes(count);
    expect(lease.canWrite()).toBe(false);
    lease.dispose();
  });
  it('waits for the old release before reopening the same project', async () => {
    const { lease, call } = setup();
    lease.open('project-a');
    await settle();
    const released = deferred<unknown>();
    call.mockImplementationOnce(() => released.promise);
    lease.open('project-b');
    lease.open('project-a');
    await settle();
    expect(lease.canWrite()).toBe(false);
    released.resolve({ released: true });
    await settle();
    expect(lease.canWrite()).toBe(true);
    lease.dispose();
  });
  it('does not overlap heartbeat requests and clears timers on disposal', async () => {
    const { lease, call } = setup();
    lease.open('project-a');
    await settle();
    const response = deferred<unknown>();
    call.mockImplementationOnce(() => response.promise);
    await vi.advanceTimersByTimeAsync(5000);
    const count = call.mock.calls.length;
    await vi.advanceTimersByTimeAsync(5000);
    expect(call).toHaveBeenCalledTimes(count);
    response.resolve(granted);
    await settle();
    lease.dispose();
    await settle();
    expect(vi.getTimerCount()).toBe(0);
  });
  it('checks the TTL synchronously after a suspended tab resumes', async () => {
    const { lease } = setup();
    lease.open('project-a');
    await settle();
    vi.setSystemTime(Date.now() + 31000);
    expect(lease.canWrite()).toBe(false);
    lease.dispose();
  });
});
