import { Api, ApiError, type RecordState } from './api';

type Lease = { canWrite: boolean; expiresInSeconds: number };
type Hooks = {
  record: () => RecordState | null;
  apply: (record: RecordState) => void;
  pins: () => object;
  state: (writable: boolean) => void;
  message: (message: string) => void;
};

/** One authority epoch per open/recovery. Never replays a draft onto a newer revision. */
export class EditorLease {
  private epoch = 0;
  private id: string | null = null;
  private writable = false;
  private deadline = 0;
  private stopped = false;
  private checking = false;
  private recover = false;
  private renewal: Promise<void> | null = null;
  private timer: ReturnType<typeof setInterval>;
  private requests = new Set<AbortController>();
  private releases = new Map<string, Promise<unknown>>();
  constructor(
    private api: Api,
    private hooks: Hooks,
  ) {
    this.timer = setInterval(() => {
      if (this.writable && Date.now() >= this.deadline)
        this.fail(
          new Error('Quyền chỉnh sửa đã hết hạn. Đang kiểm tra lại kết nối.'),
        );
      if (this.id && (this.writable || this.recover) && !this.checking)
        void this.pulse();
    }, 5000);
  }
  stamp() {
    return this.epoch;
  }
  current(epoch: number) {
    return !this.stopped && epoch === this.epoch;
  }
  canWrite() {
    if (this.writable && Date.now() >= this.deadline)
      this.fail(
        new Error('Quyền chỉnh sửa đã hết hạn. Đang kiểm tra lại kết nối.'),
      );
    return !this.stopped && this.writable;
  }
  private set(writable: boolean) {
    this.writable = writable;
    this.hooks.state(writable);
  }
  private begin() {
    ++this.epoch;
    // Old requests may still finish on the server; epoch fences their callbacks.
    this.checking = false;
    this.recover = false;
    this.set(false);
    return this.epoch;
  }
  private async request<T>(path: string, body?: object) {
    const controller = new AbortController();
    this.requests.add(controller);
    const timeout = setTimeout(() => controller.abort(), 8000);
    try {
      return await this.api.call<T>(path, {
        signal: controller.signal,
        ...(body ? { method: 'POST', body: JSON.stringify(body) } : {}),
      });
    } finally {
      clearTimeout(timeout);
      this.requests.delete(controller);
    }
  }
  private async claim(id: string, takeover: boolean) {
    const started = Date.now();
    const lease = await this.request<Lease>(`projects/${id}/editor-session`, {
      takeover,
      ...this.hooks.pins(),
    });
    return { lease, deadline: started + lease.expiresInSeconds * 1000 };
  }
  private denied() {
    this.recover = false;
    this.set(false);
    this.hooks.message(
      'Project đang mở ở tab khác. Tab này chỉ đọc; bản nháp được giữ trong bộ nhớ. Có thể nhận quyền chỉnh sửa.',
    );
  }
  open(id: string) {
    if (this.id && this.id !== id) this.release(this.id);
    this.id = id;
    void this.acquire(false);
  }
  async acquire(takeover: boolean) {
    const id = this.id;
    if (!id || this.stopped) return;
    const epoch = this.begin();
    this.checking = true;
    try {
      const pendingRelease = this.releases.get(id);
      if (pendingRelease) await pendingRelease;
      if (!this.current(epoch)) return;
      const first = await this.claim(id, takeover);
      if (!this.current(epoch)) return;
      if (!first.lease.canWrite) {
        this.denied();
        return;
      }
      const latest = await this.request<RecordState>(`projects/${id}`);
      if (!this.current(epoch)) return;
      const confirmed = await this.claim(id, false);
      if (!this.current(epoch)) return;
      if (!confirmed.lease.canWrite) {
        this.denied();
        return;
      }
      if (confirmed.deadline <= Date.now())
        throw new Error('Phản hồi quyền đã hết hạn. Hãy thử lại.');
      this.hooks.apply(latest);
      this.deadline = confirmed.deadline;
      this.set(true);
      this.hooks.message(
        'Đã xác nhận quyền chỉnh sửa và tải project mới nhất.',
      );
      return true;
    } catch (error) {
      if (this.current(epoch)) {
        this.set(false);
        // A failed reload needs explicit consent before discarding the local draft.
        this.hooks.message(
          `Không thể nhận quyền hoặc tải project: ${(error as Error).message}. Hãy kiểm tra kết nối rồi nhận quyền lại; nếu vẫn lỗi, tải lại Studio.`,
        );
      }
    } finally {
      if (this.current(epoch)) this.checking = false;
    }
  }
  fail(error: unknown) {
    if (this.stopped) return;
    this.begin();
    this.recover = !(
      error instanceof ApiError && [401, 409].includes(error.status)
    );
    this.hooks.message(
      `Đã tạm khóa chỉnh sửa: ${(error as Error).message}. Bản nháp vẫn giữ trong bộ nhớ. ${this.recover ? 'Đang chờ kết nối để kiểm tra lại quyền.' : 'Hãy tải lại Studio hoặc nhận quyền để nạp bản mới nhất.'}`,
    );
  }
  private pulse() {
    if (this.renewal) return this.renewal;
    if (this.checking) return Promise.resolve();
    const renewal = this.heartbeat();
    this.renewal = renewal;
    void renewal.finally(() => {
      if (this.renewal === renewal) this.renewal = null;
    });
    return renewal;
  }
  async checkpoint() {
    const epoch = this.epoch;
    if (!this.canWrite()) throw new Error('Tab này chỉ đọc.');
    await this.pulse();
    if (!this.current(epoch) || !this.canWrite())
      throw new Error(
        'Không xác nhận được quyền chỉnh sửa. Hãy nhận quyền lại.',
      );
  }
  private async heartbeat() {
    const epoch = this.epoch,
      id = this.id!;
    const recovering = !this.writable;
    this.checking = true;
    try {
      const response = await this.claim(id, false);
      if (!this.current(epoch)) return;
      if (!response.lease.canWrite) {
        this.begin();
        this.denied();
        return;
      }
      if (recovering) {
        const latest = await this.request<RecordState>(`projects/${id}`);
        if (!this.current(epoch)) return;
        if (latest.revision !== this.hooks.record()?.revision) {
          this.begin();
          this.hooks.message(
            'Project trên máy đã thay đổi. Bản nháp vẫn giữ trong bộ nhớ; nhận quyền để nạp bản mới nhất trước khi ghi.',
          );
          return;
        }
      }
      if (Date.now() >= response.deadline)
        throw new Error('Phản hồi quyền đã hết hạn.');
      this.deadline = response.deadline;
      this.recover = false;
      this.set(true);
      if (recovering)
        this.hooks.message(
          'Đã khôi phục kết nối, quyền và revision. Bản nháp được giữ nguyên.',
        );
    } catch (error) {
      if (this.current(epoch)) this.fail(error);
    } finally {
      if (this.current(epoch)) this.checking = false;
    }
  }
  release(id = this.id) {
    if (!id || this.releases.has(id)) return;
    const released = this.api.call(`projects/${id}/editor-session`, {
      method: 'DELETE',
      keepalive: true,
    });
    this.releases.set(id, released);
    void released.then(
      () => {
        if (this.releases.get(id) === released) this.releases.delete(id);
      },
      () => {
        // Keep the failed release recorded: a later open must not race an unconfirmed DELETE.
        // Unload remains best effort; the unchanged backend TTL recovers abandoned leases.
      },
    );
  }
  dispose() {
    this.stopped = true;
    ++this.epoch;
    clearInterval(this.timer);
    for (const request of this.requests) request.abort();
    this.release();
  }
}
