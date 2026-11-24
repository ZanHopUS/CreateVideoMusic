'use client';
import { useEffect, useState } from 'react';
import type { Api } from '../lib/api';
type Policy = {
  cacheQuotaMiB: number;
  reserveGiB: number;
  cacheBytes: number;
  freeBytes: number;
  warning: string;
};
type Candidate = { id: string; name: string; bytes: number };
type Section =
  | 'Chung'
  | 'Giao diện'
  | 'Lưu trữ'
  | 'AI & Xử lý'
  | 'Google Drive'
  | 'Hệ thống';
export function SettingsWorkspace({
  api,
  active,
  onStorage,
  prepare,
  projectView,
  onProjectView,
  preferenceStatus,
  viewPending,
}: {
  api: Api | null;
  active: boolean;
  onStorage: () => void;
  prepare: () => Promise<void>;
  projectView: 'grid' | 'list';
  onProjectView: (next: 'grid' | 'list') => Promise<void>;
  preferenceStatus: string;
  viewPending: boolean;
}) {
  const [section, setSection] = useState<Section>('Chung');
  const [policy, setPolicy] = useState<Policy | null>(null),
    [draft, setDraft] = useState<Policy | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]),
    [selection, setSelection] = useState<string[]>([]);
  const [providers, setProviders] = useState<
    { id: string; enabled: boolean; models?: Record<string, boolean> }[]
  >([]);
  const [drive, setDrive] = useState<{
    connected: boolean;
    folderName: string;
    autoSync: boolean;
  } | null>(null);
  const [health, setHealth] = useState('Đang kiểm tra…');
  const [message, setMessage] = useState(''),
    [busy, setBusy] = useState(false);
  const dirty = Boolean(
    policy &&
    draft &&
    (policy.cacheQuotaMiB !== draft.cacheQuotaMiB ||
      policy.reserveGiB !== draft.reserveGiB),
  );
  useEffect(() => {
    if (!api) return;
    let live = true;
    Promise.allSettled([
      api.call<Policy>('storage/policy'),
      api.call<{ providers: typeof providers }>('ai/providers'),
      api.call<typeof drive>('drive'),
      api.call('session').then(() => 'Đang chạy'),
    ])
      .then(([p, a, d, h]) => {
        if (!live) return;
        if (p.status === 'fulfilled') {
          setPolicy(p.value);
          setDraft(p.value);
        }
        if (a.status === 'fulfilled') setProviders(a.value.providers);
        if (d.status === 'fulfilled') setDrive(d.value);
        if (h.status === 'fulfilled') setHealth(h.value);
        else setHealth('Không kết nối');
      })
      .catch((e) => setMessage(String(e)));
    return () => {
      live = false;
    };
  }, [api]);
  useEffect(() => {
    if (!active || !api) return;
    let live = true;
    api
      .call<{ connected: boolean; folderName: string; autoSync: boolean }>(
        'drive',
      )
      .then((value) => {
        if (live) setDrive(value);
      })
      .catch(() => {
        if (live) setDrive(null);
      });
    return () => {
      live = false;
    };
  }, [active, api]);
  function select(next: Section) {
    if (
      dirty &&
      !window.confirm(
        'Cài đặt lưu trữ chưa được lưu. Bỏ thay đổi và chuyển mục?',
      )
    )
      return;
    if (dirty) setDraft(policy);
    setSection(next);
    setMessage('');
  }
  async function run(action: () => Promise<void>) {
    if (!api || busy) return;
    setBusy(true);
    setMessage('');
    try {
      await action();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Thao tác chưa hoàn tất.');
    } finally {
      setBusy(false);
    }
  }
  const sections: Section[] = [
    'Chung',
    'Giao diện',
    'Lưu trữ',
    'AI & Xử lý',
    'Google Drive',
    'Hệ thống',
  ];
  return (
    <section className="settings-workspace">
      <h1>Cài đặt</h1>
      <nav aria-label="Nhóm cài đặt">
        {sections.map((name) => (
          <button
            key={name}
            aria-current={name === section ? 'page' : undefined}
            onClick={() => select(name)}
          >
            {name}
          </button>
        ))}
      </nav>
      <div className="settings-content">
        {section === 'Chung' && (
          <section>
            <h2>Cài đặt chung</h2>
            <p>Ngôn ngữ giao diện: Tiếng Việt</p>
          </section>
        )}
        {section === 'Giao diện' && (
          <section>
            <h2>Giao diện</h2>
            <p>Chế độ xem dự án được lưu ngoài project.</p>
            <label>
              Hiển thị dự án
              <select
                aria-label="Hiển thị dự án"
                disabled={viewPending}
                value={projectView}
                onChange={(e) =>
                  void onProjectView(e.target.value as 'grid' | 'list')
                }
              >
                <option value="grid">Lưới</option>
                <option value="list">Danh sách</option>
              </select>
            </label>
            {preferenceStatus && <p role="status">{preferenceStatus}</p>}
          </section>
        )}
        {section === 'Lưu trữ' && (
          <section>
            <h2>Lưu trữ</h2>
            {draft && (
              <>
                <p>
                  Cache thumbnail: {(draft.cacheBytes / 1048576).toFixed(1)} MiB
                  · Trống: {(draft.freeBytes / 1073741824).toFixed(1)} GiB
                </p>
                <p>{draft.warning}</p>
                <label>
                  Giới hạn cache (MiB)
                  <input
                    type="number"
                    min={32}
                    max={4096}
                    value={draft.cacheQuotaMiB}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        cacheQuotaMiB: Number(e.target.value),
                      })
                    }
                  />
                </label>
                <label>
                  Dung lượng dự phòng (GiB)
                  <input
                    type="number"
                    min={2}
                    max={64}
                    value={draft.reserveGiB}
                    onChange={(e) =>
                      setDraft({ ...draft, reserveGiB: Number(e.target.value) })
                    }
                  />
                </label>
                {dirty && (
                  <div className="settings-savebar">
                    <button onClick={() => setDraft(policy)}>Hủy</button>
                    <button
                      disabled={busy}
                      onClick={() =>
                        run(async () => {
                          const saved = await api!.json<Policy>(
                            'storage/policy',
                            'PATCH',
                            {
                              cacheQuotaMiB: draft.cacheQuotaMiB,
                              reserveGiB: draft.reserveGiB,
                            },
                          );
                          setPolicy(saved);
                          setDraft(saved);
                          setMessage('Đã lưu chính sách dung lượng.');
                        })
                      }
                    >
                      Lưu
                    </button>
                  </div>
                )}
                <hr />
                <button
                  disabled={busy}
                  onClick={() =>
                    run(async () => {
                      if (
                        !window.confirm('Dọn cache thumbnail có thể tạo lại?')
                      )
                        return;
                      const result = await api!.json<{
                        deleted: number;
                        failed: number;
                      }>('storage/cache/cleanup', 'POST', { confirmed: true });
                      setMessage(
                        `Đã dọn ${result.deleted} file cache; ${result.failed} file chưa dọn được.`,
                      );
                      const fresh = await api!.call<Policy>('storage/policy');
                      setPolicy(fresh);
                      setDraft(fresh);
                    })
                  }
                >
                  Dọn cache thumbnail
                </button>
                <button
                  disabled={busy}
                  onClick={() =>
                    run(async () => {
                      const result = await api!.call<{
                        jobs: { id: string; bytes: number }[];
                      }>('storage/temp');
                      if (!result.jobs.length) {
                        setMessage('Không có temp job đủ điều kiện dọn.');
                        return;
                      }
                      if (
                        !window.confirm(
                          `Dọn temp của ${result.jobs.length} job đã kết thúc?`,
                        )
                      )
                        return;
                      const done = await api!.json<{
                        deleted?: string[];
                        failed?: string[];
                      }>('storage/temp/cleanup', 'POST', {
                        ids: result.jobs.map((x) => x.id),
                        confirmed: true,
                      });
                      setMessage(
                        `Đã xử lý temp; ${done.failed?.length ?? 0} job chưa dọn được.`,
                      );
                    })
                  }
                >
                  Dọn temp job
                </button>
                <hr />
                <button
                  disabled={busy}
                  onClick={() =>
                    run(async () => {
                      await prepare();
                      const preview = await api!.call<{
                        candidates: Candidate[];
                      }>('storage/source-gc');
                      setCandidates(preview.candidates);
                      setSelection([]);
                      setMessage(
                        preview.candidates.length
                          ? 'Chọn media nguồn không dùng; backend sẽ kiểm pins lại trước khi xóa.'
                          : 'Không có media đủ điều kiện dọn.',
                      );
                    })
                  }
                >
                  Xem media nguồn không dùng
                </button>
                {candidates.map((x) => (
                  <label key={x.id}>
                    <input
                      type="checkbox"
                      checked={selection.includes(x.id)}
                      onChange={(e) =>
                        setSelection((old) =>
                          e.target.checked
                            ? [...old, x.id]
                            : old.filter((id) => id !== x.id),
                        )
                      }
                    />
                    {x.name} · {(x.bytes / 1048576).toFixed(1)} MiB
                  </label>
                ))}
                <button
                  disabled={busy || !selection.length}
                  onClick={() =>
                    run(async () => {
                      if (
                        !window.confirm(
                          `Xóa vĩnh viễn ${selection.length} media nguồn đã chọn?`,
                        )
                      )
                        return;
                      await prepare();
                      const result = await api!.json<{
                        deleted: string[];
                        failed: string[];
                      }>('storage/source-gc', 'POST', {
                        ids: selection,
                        confirmed: true,
                      });
                      setMessage(
                        `Đã xóa ${result.deleted.length}; ${result.failed.length} chưa xóa được.`,
                      );
                      setCandidates([]);
                      setSelection([]);
                    })
                  }
                >
                  Xóa media nguồn đã chọn
                </button>
              </>
            )}
          </section>
        )}
        {section === 'AI & Xử lý' && (
          <section>
            <h2>AI & Xử lý</h2>
            {providers.map((p) => (
              <p key={p.id}>
                {p.id === 'local' ? 'AI local' : p.id}:{' '}
                {p.enabled ? 'Khả dụng theo cấu hình' : 'Chưa bật'}
                {p.models &&
                  Object.entries(p.models).map(([name, ok]) => (
                    <span key={name}>
                      {' '}
                      · {name}: {ok ? 'Có file model' : 'Thiếu model'}
                    </span>
                  ))}
              </p>
            ))}
          </section>
        )}
        {section === 'Google Drive' && (
          <section>
            <h2>Google Drive</h2>
            <p>
              {drive?.connected
                ? `Đã kết nối ${drive.folderName || ''}`
                : 'Chưa kết nối'}
            </p>
            <p>Tự sao lưu: {drive?.autoSync ? 'Đang bật' : 'Đang tắt'}</p>
            <button onClick={onStorage}>Mở Kho lưu trữ</button>
          </section>
        )}
        {section === 'Hệ thống' && (
          <section>
            <h2>Hệ thống</h2>
            <p>Local backend: {health}</p>
          </section>
        )}
        {message && <p role="status">{message}</p>}
      </div>
    </section>
  );
}
