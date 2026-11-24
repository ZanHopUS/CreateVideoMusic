'use client';
import { useEffect, useState } from 'react';
import type { Api } from '../lib/api';
import { DrivePanel } from './drive-panel';
type Tab = 'Tổng quan' | 'Bản sao lưu' | 'MP4 khôi phục' | 'Cấu hình';
type State = {
  connected: boolean;
  configured: boolean;
  folderName: string;
  autoSync: boolean;
  lastBackup?: unknown;
  backup: { status: string; message: string };
  restore?: { status: string; message: string };
};
export function StorageWorkspace({
  api,
  active,
  beforeBackup,
}: {
  api: Api | null;
  active: boolean;
  beforeBackup: () => Promise<void>;
}) {
  const [tab, setTab] = useState<Tab>('Tổng quan'),
    [state, setState] = useState<State | null>(null),
    [backups, setBackups] = useState<
      { id: string; name: string; createdTime?: string }[]
    >([]),
    [exports, setExports] = useState<{ sha256: string; bytes: number }[]>([]),
    [error, setError] = useState('');
  useEffect(() => {
    if (!api || !active) return;
    let live = true;
    setError('');
    api
      .call<State>('drive')
      .then((value) => {
        if (live) setState(value);
      })
      .catch((e) => {
        if (live) setError(e.message);
      });
    return () => {
      live = false;
    };
  }, [api, active, tab]);
  useEffect(() => {
    if (!api || !active) return;
    let live = true;
    if (tab === 'Bản sao lưu' && state?.connected)
      api
        .call<typeof backups>('drive/backups')
        .then((v) => {
          if (live) setBackups(v);
        })
        .catch((e) => {
          if (live) setError(e.message);
        });
    if (tab === 'MP4 khôi phục')
      api
        .call<typeof exports>('drive/exports')
        .then((v) => {
          if (live) setExports(v);
        })
        .catch((e) => {
          if (live) setError(e.message);
        });
    return () => {
      live = false;
    };
  }, [api, active, tab, state?.connected]);
  const tabs: Tab[] = ['Tổng quan', 'Bản sao lưu', 'MP4 khôi phục', 'Cấu hình'];
  return (
    <section className="storage-workspace">
      <h1>Kho lưu trữ</h1>
      <div className="storage-tabs" role="tablist" aria-label="Kho lưu trữ">
        {tabs.map((name) => (
          <button
            key={name}
            role="tab"
            aria-selected={tab === name}
            onClick={() => setTab(name)}
          >
            {name}
          </button>
        ))}
      </div>
      {error && <p role="alert">{error}</p>}
      {tab === 'Tổng quan' && (
        <section>
          <h2>Google Drive</h2>
          <p>
            {state?.connected
              ? `Đã kết nối · ${state.folderName || 'Thư mục chưa có tên'}`
              : 'Chưa kết nối'}
          </p>
          <p>Tự sao lưu: {state?.autoSync ? 'Đang bật' : 'Đang tắt'}</p>
          <p>Backup: {state?.backup.message || 'Chưa có thông tin'}</p>
          <p>Restore: {state?.restore?.message || 'Chưa có thông tin'}</p>
          <button onClick={() => setTab('Cấu hình')}>
            Mở tác vụ và cấu hình Drive
          </button>
        </section>
      )}
      {tab === 'Bản sao lưu' && (
        <section>
          <h2>Bản sao lưu trên Drive</h2>
          {!state?.connected ? (
            <p>Kết nối Drive trong Cấu hình để xem bản sao lưu.</p>
          ) : backups.length ? (
            <div className="storage-snapshots">
              {backups.map((item) => (
                <article key={item.id}>
                  <strong>{item.name}</strong>
                  <p>{item.createdTime || 'Chưa có thời gian'}</p>
                </article>
              ))}
            </div>
          ) : (
            <p>Chưa có bản sao lưu hoặc chưa tải được danh sách.</p>
          )}
          <button onClick={() => setTab('Cấu hình')}>
            Sao lưu hoặc khôi phục
          </button>
        </section>
      )}
      {tab === 'MP4 khôi phục' && (
        <section>
          <h2>MP4 đã khôi phục</h2>
          {exports.length ? (
            exports.map((file) => (
              <article key={file.sha256}>
                <a
                  href={`/api/v1/drive/exports/${file.sha256}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  MP4 {file.sha256.slice(0, 12)}
                </a>{' '}
                · {(file.bytes / 1048576).toFixed(1)} MiB
              </article>
            ))
          ) : (
            <p>Chưa có MP4 khôi phục trên máy.</p>
          )}
        </section>
      )}
      <div hidden={tab !== 'Cấu hình'}>
        <DrivePanel api={api} beforeBackup={beforeBackup} />
      </div>
    </section>
  );
}
