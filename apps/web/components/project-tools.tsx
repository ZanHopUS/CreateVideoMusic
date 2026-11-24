'use client';
import { useEffect, useState } from 'react';
import {
  appendMedia,
  TICKS,
  type ProjectContent,
  type TemplateDefinition,
} from '@amvs/domain';
import { Api, type Asset, type Job } from '../lib/api';
type Recovery = {
  id: string;
  createdAt: number;
  contentHash: string;
  bytes: number;
};
export function ProjectTools({
  project,
  assets,
  api,
  prepare,
  open,
  refresh,
  reload,
  change,
  selected,
  panels,
  setPanel,
}: {
  project: ProjectContent;
  assets: Asset[];
  api: Api | null;
  prepare: () => Promise<void>;
  open: (id: string) => Promise<void>;
  refresh: () => Promise<void>;
  reload: () => Promise<void>;
  change: (op: (p: ProjectContent) => void) => boolean;
  selected: string;
  panels: Record<string, boolean>;
  setPanel: (key: string, value: boolean) => void;
}) {
  const [message, setMessage] = useState(''),
    [busy, setBusy] = useState(false),
    [recoveries, setRecoveries] = useState<Recovery[]>([]),
    [missing, setMissing] = useState<string[]>([]);
  const [query, setQuery] = useState(''),
    [templates, setTemplates] = useState<TemplateDefinition[]>([]),
    [name, setName] = useState('Mẫu của tôi'),
    [slotIds, setSlotIds] = useState<string[]>([]),
    [templateId, setTemplateId] = useState(''),
    [bindings, setBindings] = useState<Record<string, string>>({});
  const [segments, setSegments] = useState<
      { startTicks: number; durationTicks: number; energy: number }[]
    >([]),
    [suggestionAsset, setSuggestionAsset] = useState('');
  const [gcCandidates, setGcCandidates] = useState<
      { id: string; name: string; bytes: number }[]
    >([]),
    [gcSelection, setGcSelection] = useState<string[]>([]);
  const [storage, setStorage] = useState<{
    cacheQuotaMiB: number;
    reserveGiB: number;
    freeBytes: number;
    cacheBytes: number;
    warning: string;
  } | null>(null);
  const chosen = templates.find((t) => t.id === templateId);
  async function inspect() {
    if (!api) return;
    const r = await api.call<{ snapshots: Recovery[]; warning: string }>(
      `projects/${project.id}/recoveries`,
    );
    setRecoveries(r.snapshots);
    if (r.warning) setMessage(r.warning);
    setMissing(
      (
        await api.call<{ missing: string[] }>(
          `projects/${project.id}/media-status`,
        )
      ).missing,
    );
    setTemplates(await api.call<TemplateDefinition[]>('templates'));
    setStorage(await api.call('storage/policy'));
  }
  useEffect(() => {
    inspect().catch((e) => setMessage(e.message));
    const timer = setInterval(() => inspect().catch(() => {}), 30000);
    return () => clearInterval(timer);
  }, [project.id, api]);
  async function run(action: () => Promise<void>) {
    if (busy) return;
    setBusy(true);
    try {
      await action();
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <details
        className="tool-panel"
        open={panels.data ?? false}
        onToggle={(e) => setPanel('data', e.currentTarget.open)}
      >
        <summary>Dữ liệu project · recovery và bản di chuyển</summary>
        <p>
          Recovery riêng mỗi 30 giây, giữ tối đa 10 bản/200 MiB. Lưu nền không
          thay bản lưu thủ công.
        </p>
        <button
          disabled={busy}
          onClick={() =>
            run(async () => {
              await prepare();
              await api!.json(`projects/${project.id}/recoveries`, 'POST', {});
              await inspect();
            })
          }
        >
          Tạo recovery ngay
        </button>
        <button
          disabled={busy}
          onClick={() =>
            run(async () => {
              await prepare();
              const current = await api!.call<{ revision: number }>(
                `projects/${project.id}`,
              );
              const grant = await api!.json<{ id?: string }>(
                'folder-grants',
                'POST',
                { scope: 'backup' },
              );
              if (!grant.id) return;
              let job = await api!.json<Job>(
                `projects/${project.id}/packages`,
                'POST',
                { revision: current.revision, grantId: grant.id },
              );
              while (
                !['succeeded', 'failed', 'cancelled', 'interrupted'].includes(
                  job.status,
                )
              ) {
                setMessage(job.message);
                await new Promise((resolve) => setTimeout(resolve, 1000));
                job = await api!.call<Job>(`jobs/${job.id}`);
              }
              if (job.status !== 'succeeded') throw new Error(job.message);
              const result = await api!.call<{ name: string }>(
                `jobs/${job.id}/package`,
              );
              setMessage(
                `Đã tạo ${result.name}; chứa project và media, dùng Mở file project để khôi phục trên máy khác.`,
              );
            })
          }
        >
          Đóng gói di chuyển (.amvs)
        </button>
        <button
          disabled={busy}
          onClick={() =>
            run(async () => {
              if (
                !window.confirm(
                  'Xóa project khỏi danh sách local? File media dùng chung và bản lưu thủ công được giữ.',
                )
              )
                return;
              await api!.call(`projects/${project.id}`, { method: 'DELETE' });
              location.reload();
            })
          }
        >
          Xóa project
        </button>
        <button
          disabled={busy}
          onClick={() =>
            run(async () => {
              const preview = await api!.call<{
                jobs: { id: string; bytes: number }[];
              }>('storage/temp');
              const total = preview.jobs.reduce((sum, j) => sum + j.bytes, 0);
              if (!preview.jobs.length) {
                setMessage('Không có temp của job đã kết thúc cần dọn.');
                return;
              }
              if (
                !window.confirm(
                  `Dọn ${(total / 1024 ** 2).toFixed(1)} MiB temp của ${preview.jobs.length} job đã kết thúc? Media nguồn, project và MP4 đích được giữ.`,
                )
              )
                return;
              await api!.json('storage/temp/cleanup', 'POST', {
                ids: preview.jobs.map((j) => j.id),
                confirmed: true,
              });
              setMessage('Đã dọn temp; media nguồn và output được giữ.');
            })
          }
        >
          Xem dung lượng và dọn temp
        </button>
        {storage && (
          <fieldset>
            <legend>Dung lượng trên máy</legend>
            <p>
              Trống {(storage.freeBytes / 1024 ** 3).toFixed(1)} GiB · Cache{' '}
              {(storage.cacheBytes / 1024 ** 2).toFixed(1)} MiB{' '}
              {storage.warning}
            </p>
            <label>
              Giới hạn cache (MiB)
              <input
                aria-label="Giới hạn cache"
                type="number"
                min="32"
                max="4096"
                value={storage.cacheQuotaMiB}
                onChange={(e) =>
                  setStorage({
                    ...storage,
                    cacheQuotaMiB: Number(e.target.value),
                  })
                }
              />
            </label>
            <label>
              Dung lượng dự phòng (GiB)
              <input
                aria-label="Dung lượng dự phòng"
                type="number"
                min="2"
                max="64"
                value={storage.reserveGiB}
                onChange={(e) =>
                  setStorage({ ...storage, reserveGiB: Number(e.target.value) })
                }
              />
            </label>
            <button
              disabled={busy}
              onClick={() =>
                run(async () => {
                  setStorage(
                    await api!.json('storage/policy', 'PATCH', {
                      cacheQuotaMiB: storage.cacheQuotaMiB,
                      reserveGiB: storage.reserveGiB,
                    }),
                  );
                  setMessage(
                    'Đã cập nhật giới hạn dung lượng; không tự xóa media.',
                  );
                })
              }
            >
              Lưu giới hạn dung lượng
            </button>
            <button
              disabled={busy}
              onClick={() =>
                run(async () => {
                  if (
                    !window.confirm(
                      'Xóa cache thumbnail để tạo lại khi cần? Media nguồn được giữ.',
                    )
                  )
                    return;
                  await api!.json('storage/cache/cleanup', 'POST', {
                    confirmed: true,
                  });
                  await inspect();
                  setMessage('Đã dọn cache thumbnail.');
                })
              }
            >
              Dọn cache thumbnail
            </button>
          </fieldset>
        )}
        <button
          disabled={busy}
          onClick={() =>
            run(async () => {
              await prepare();
              const result = await api!.call<{
                candidates: typeof gcCandidates;
              }>('storage/source-gc');
              setGcCandidates(result.candidates);
              setGcSelection([]);
              setMessage(
                result.candidates.length
                  ? 'Chọn media không dùng cần xóa; kiểm tra tên trước khi xác nhận.'
                  : 'Không có media đủ điều kiện dọn. Bản lưu, Undo/Redo và media dùng trong phiên này được bảo vệ.',
              );
            })
          }
        >
          Tìm media không dùng để dọn
        </button>
        {gcCandidates.map((asset) => (
          <label key={asset.id}>
            <input
              type="checkbox"
              checked={gcSelection.includes(asset.id)}
              onChange={(e) =>
                setGcSelection((old) =>
                  e.target.checked
                    ? [...old, asset.id]
                    : old.filter((id) => id !== asset.id),
                )
              }
            />
            {asset.name} · {(asset.bytes / 1024 ** 2).toFixed(1)} MiB
          </label>
        ))}
        <button
          disabled={busy || !gcSelection.length}
          onClick={() =>
            run(async () => {
              await prepare();
              if (
                !window.confirm(
                  `Xóa vĩnh viễn ${gcSelection.length} bản media được chọn trong thư viện quản lý? File gốc ngoài ứng dụng được giữ.`,
                )
              )
                return;
              const result = await api!.json<{
                deleted: string[];
                failed: string[];
              }>('storage/source-gc', 'POST', {
                ids: gcSelection,
                confirmed: true,
              });
              setGcCandidates([]);
              setGcSelection([]);
              await refresh();
              setMessage(
                `Đã dọn ${result.deleted.length} media; ${result.failed.length} file chưa dọn được. Các media vừa được dùng/pin sẽ bị chặn xóa.`,
              );
            })
          }
        >
          Xóa các media không dùng đã chọn
        </button>
        {recoveries.map((r) => (
          <div key={r.id}>
            {new Date(r.createdAt * 1000).toLocaleString('vi-VN')}{' '}
            <button
              disabled={busy}
              onClick={() =>
                run(async () => {
                  if (
                    !window.confirm(
                      'Khôi phục recovery này vào bản làm việc? Bản lưu thủ công giữ nguyên.',
                    )
                  )
                    return;
                  await prepare();
                  const current = await api!.call<{ revision: number }>(
                    `projects/${project.id}`,
                  );
                  await api!.json(`projects/${project.id}/restore`, 'POST', {
                    revision: current.revision,
                    recoveryId: r.id,
                    confirmed: true,
                  });
                  await reload();
                  setMessage(
                    'Đã khôi phục bản làm việc; hãy kiểm tra rồi lưu thủ công.',
                  );
                })
              }
            >
              Khôi phục
            </button>
            <button
              disabled={busy}
              onClick={() =>
                run(async () => {
                  if (!window.confirm('Xóa bản recovery này?')) return;
                  await api!.json(
                    `projects/${project.id}/recoveries`,
                    'DELETE',
                    { ids: [r.id], confirmed: true },
                  );
                  await inspect();
                })
              }
            >
              Xóa recovery
            </button>
          </div>
        ))}
        <button onClick={() => run(inspect)}>Kiểm tra media và recovery</button>
        {missing.map((id) => (
          <p key={id}>
            Thiếu/hỏng:{' '}
            {assets.find((a) => a.id === id)?.name ?? id.slice(0, 12)}{' '}
            <button
              disabled={busy}
              onClick={() =>
                run(async () => {
                  await api!.json(`assets/${id}/relink`, 'POST', {
                    confirmed: true,
                  });
                  await inspect();
                  setMessage('Đã kiểm tra liên kết media.');
                })
              }
            >
              Chọn lại file gốc cùng checksum
            </button>
          </p>
        ))}
      </details>
      <details
        className="tool-panel"
        open={panels.library ?? false}
        onToggle={(e) => setPanel('library', e.currentTarget.open)}
      >
        <summary>Thư viện media · tìm, nghe và dùng lại</summary>
        <input
          aria-label="Tìm media"
          placeholder="Tên hoặc tag"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="library-grid">
          {assets
            .filter((a) =>
              `${a.name} ${a.tags?.join(' ') ?? ''}`
                .toLocaleLowerCase('vi')
                .includes(query.toLocaleLowerCase('vi')),
            )
            .map((a) => (
              <article key={a.id}>
                {a.kind !== 'audio' ? (
                  <img
                    alt={a.name}
                    loading="lazy"
                    src={`/api/v1/assets/${a.id}/thumbnail`}
                    width="96"
                    height="72"
                    style={{ objectFit: 'contain' }}
                  />
                ) : (
                  <audio
                    aria-label={`Nghe ${a.name}`}
                    controls
                    preload="none"
                    src={`/api/v1/assets/${a.id}/content`}
                  />
                )}
                <strong>{a.name}</strong>
                <small>
                  {a.kind === 'audio'
                    ? 'Nhạc'
                    : a.kind === 'video'
                      ? 'Video'
                      : 'Ảnh'}{' '}
                  ·{' '}
                  {a.durationTicks
                    ? (a.durationTicks / TICKS).toFixed(1) + ' giây'
                    : ''}
                </small>
                <button
                  disabled={busy}
                  onClick={() =>
                    change((p) => Object.assign(p, appendMedia(p, [a])))
                  }
                >
                  Thêm {a.name} vào project
                </button>
                <label>
                  Tags
                  <input
                    aria-label={`Tags ${a.name}`}
                    defaultValue={a.tags?.join(', ') ?? ''}
                    onBlur={(e) =>
                      run(async () => {
                        await api!.json(`assets/${a.id}/tags`, 'PATCH', {
                          tags: e.target.value
                            .split(',')
                            .map((s) => s.trim())
                            .filter(Boolean),
                        });
                        await refresh();
                      })
                    }
                  />
                </label>
                {a.kind === 'audio' && (
                  <button
                    disabled={busy}
                    onClick={() =>
                      run(async () => {
                        const result = await api!.json<{
                          segments: typeof segments;
                          message: string;
                        }>(`assets/${a.id}/suggestions`, 'POST', {});
                        setSuggestionAsset(a.id);
                        setSegments(result.segments);
                        setMessage(result.message);
                      })
                    }
                  >
                    Gợi ý đoạn nhạc {a.name}
                  </button>
                )}
              </article>
            ))}
        </div>
        {segments.map((s, index) => (
          <div key={index}>
            Đoạn {index + 1}: {(s.startTicks / TICKS).toFixed(1)}–
            {((s.startTicks + s.durationTicks) / TICKS).toFixed(1)} giây
            <audio
              aria-label={`Nghe gợi ý ${index + 1}`}
              controls
              preload="none"
              src={`/api/v1/assets/${suggestionAsset}/content#t=${s.startTicks / TICKS},${(s.startTicks + s.durationTicks) / TICKS}`}
            />
            <button
              onClick={() =>
                change((p) => {
                  const item = p.items.find(
                    (i) =>
                      i.id === selected &&
                      i.type === 'audio' &&
                      i.assetId === suggestionAsset,
                  );
                  if (!item)
                    throw new Error(
                      'Chọn clip nhạc tương ứng trên timeline trước.',
                    );
                  item.sourceStartTicks = s.startTicks;
                  item.durationTicks = Math.min(
                    s.durationTicks,
                    p.durationTicks - item.startTicks,
                  );
                })
              }
            >
              Dùng cho clip nhạc đang chọn
            </button>
          </div>
        ))}
      </details>
      <details
        className="tool-panel"
        open={panels.templates ?? false}
        onToggle={(e) => setPanel('templates', e.currentTarget.open)}
      >
        <summary>Mẫu cá nhân · lưu từ project và tái sử dụng</summary>
        <label>
          Tên mẫu
          <input
            aria-label="Tên mẫu cá nhân"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
        <p>
          Chọn những layer sẽ thay bằng media/chữ mới. Thay đổi bản mới không
          sửa mẫu gốc.
        </p>
        {project.items
          .filter((i) => i.type !== 'lyrics')
          .map((i) => (
            <label key={i.id}>
              <input
                type="checkbox"
                checked={slotIds.includes(i.id)}
                onChange={(e) =>
                  setSlotIds((old) =>
                    e.target.checked
                      ? [...old, i.id]
                      : old.filter((id) => id !== i.id),
                  )
                }
              />
              {i.text ?? assets.find((a) => a.id === i.assetId)?.name ?? i.type}
            </label>
          ))}
        <button
          disabled={busy || !slotIds.length}
          onClick={() =>
            run(async () => {
              await prepare();
              const current = await api!.call<{ revision: number }>(
                `projects/${project.id}`,
              );
              await api!.json('templates', 'POST', {
                projectId: project.id,
                revision: current.revision,
                name,
                itemIds: slotIds,
              });
              await inspect();
              setMessage('Đã lưu mẫu cá nhân.');
            })
          }
        >
          Lưu thành mẫu
        </button>
        <label>
          Chọn mẫu
          <select
            aria-label="Chọn mẫu cá nhân"
            value={templateId}
            onChange={(e) => {
              setTemplateId(e.target.value);
              setBindings({});
            }}
          >
            <option value="">Chọn mẫu</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
        {chosen?.slots.map((s, index) => (
          <label key={s.id}>
            Nội dung thay thế {index + 1} ·{' '}
            {s.kind === 'text'
              ? 'Chữ'
              : s.kind === 'audio'
                ? 'Nhạc'
                : s.kind === 'video'
                  ? 'Video'
                  : 'Ảnh'}
            {s.kind === 'text' ? (
              <input
                value={bindings[s.id] ?? ''}
                onChange={(e) =>
                  setBindings((old) => ({ ...old, [s.id]: e.target.value }))
                }
              />
            ) : (
              <select
                value={bindings[s.id] ?? ''}
                onChange={(e) =>
                  setBindings((old) => ({ ...old, [s.id]: e.target.value }))
                }
              >
                <option value="">Chọn media</option>
                {assets
                  .filter((a) => a.kind === s.kind)
                  .map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name}
                    </option>
                  ))}
              </select>
            )}
          </label>
        ))}
        <button
          disabled={
            busy || !chosen || chosen.slots.some((s) => !bindings[s.id])
          }
          onClick={() =>
            run(async () => {
              await prepare();
              const result = await api!.json<{ project: ProjectContent }>(
                `templates/${templateId}/instances`,
                'POST',
                { bindings },
              );
              await refresh();
              await open(result.project.id);
            })
          }
        >
          Tạo project từ mẫu cá nhân
        </button>
      </details>
      {message && <p role="status">{message}</p>}
    </>
  );
}
