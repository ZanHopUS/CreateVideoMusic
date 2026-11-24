'use client';
import { useEffect, useState } from 'react';
import type { Api } from '../lib/api';
type Snapshot = {
  id: string;
  createdAt: string;
  contentHash: string;
  bytes: number;
};
export function RecoveryWorkspace({
  api,
  projectId,
  onBack,
  onOpen,
}: {
  api: Api | null;
  projectId: string;
  onBack: () => void;
  onOpen: () => void;
}) {
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]),
    [warning, setWarning] = useState(''),
    [error, setError] = useState(''),
    [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!api) return;
    let live = true;
    setLoading(true);
    setError('');
    api
      .call<{ snapshots: Snapshot[]; warning: string }>(
        `projects/${projectId}/recoveries`,
      )
      .then((value) => {
        if (!live) return;
        setSnapshots(value.snapshots);
        setWarning(value.warning);
        setLoading(false);
      })
      .catch((e) => {
        if (!live) return;
        setError(e instanceof Error ? e.message : 'Không tải được recovery.');
        setLoading(false);
      });
    return () => {
      live = false;
    };
  }, [api, projectId]);
  return (
    <section className="recovery-workspace">
      <button onClick={onBack}>← Danh sách dự án</button>
      <h2>Phiên khôi phục</h2>
      {loading && <p role="status">Đang tải…</p>}
      {error && <p role="alert">{error}</p>}
      {warning && <p role="alert">{warning}</p>}
      {!loading && !error && !snapshots.length && (
        <p>Chưa có phiên khôi phục cho dự án này.</p>
      )}
      <div className="recovery-list">
        {snapshots.map((item) => (
          <article key={item.id}>
            <strong>{new Date(item.createdAt).toLocaleString('vi-VN')}</strong>
            <p>
              {(item.bytes / 1048576).toFixed(1)} MiB · mã nội dung{' '}
              {item.contentHash.slice(0, 12)}
            </p>
            <p>
              Khôi phục ghi vào bản làm việc cùng dự án; bản lưu thủ công được
              giữ.
            </p>
          </article>
        ))}
      </div>
      {snapshots.length > 0 && (
        <button onClick={onOpen}>Mở dự án để xem và khôi phục</button>
      )}
    </section>
  );
}
