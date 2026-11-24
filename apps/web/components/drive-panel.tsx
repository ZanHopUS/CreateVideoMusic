'use client';
import { useEffect, useState } from 'react';
import type { Api } from '../lib/api';

type DriveState = {
  configured: boolean;
  connected: boolean;
  pending: boolean;
  folderId: string;
  folderName: string;
  message: string;
  backup: { status: string; message: string };
  restore: { status: string; message: string };
  autoSync: boolean;
};

export function DrivePanel({
  api,
  beforeBackup,
}: {
  api: Api | null;
  beforeBackup: () => Promise<void>;
}) {
  const [opened, setOpened] = useState(false);
  const [state, setState] = useState<DriveState | null>(null);
  const [folder, setFolder] = useState('');
  const [credentials, setCredentials] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [authUrl, setAuthUrl] = useState('');
  const [consent, setConsent] = useState(false);
  const [backups, setBackups] = useState<
    { id: string; name: string; createdTime?: string }[]
  >([]);
  const [selectedBackup, setSelectedBackup] = useState('');
  const [exports, setExports] = useState<{ sha256: string; bytes: number }[]>(
    [],
  );
  useEffect(() => {
    if (!api) return;
    let active = true;
    const refresh = () =>
      api
        .call<DriveState>('drive')
        .then((value) => {
          if (active) setState(value);
        })
        .catch((error) => {
          if (active) setMessage(error.message);
        });
    refresh();
    const timer = setInterval(refresh, 2000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [api]);

  async function perform(action: () => Promise<void>) {
    if (busy || !api) return;
    setBusy(true);
    setMessage('');
    try {
      await action();
      setState(await api.call<DriveState>('drive'));
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : 'Kết nối chưa hoàn tất.',
      );
    } finally {
      setBusy(false);
    }
  }
  const running =
    state?.backup.status === 'running' || state?.restore?.status === 'running';
  return (
    <section className="drive-panel">
      <button
        disabled={!api}
        onClick={() => setOpened(!opened)}
        aria-expanded={opened}
      >
        ☁ Kho Google Drive ·{' '}
        {state?.connected ? state.folderName || 'Đã đăng nhập' : 'Chưa kết nối'}
      </button>
      {opened && (
        <div className="drive-settings">
          <p>
            Kết nối trực tiếp Drive trên web. Media, project và MP4 được tải lên
            khi bạn bấm sao lưu; xử lý AI và render vẫn chạy trên máy.
          </p>
          <label>
            Link thư mục kho chung
            <input
              aria-label="Link thư mục Drive"
              value={
                folder ||
                (state?.folderId
                  ? `https://drive.google.com/drive/folders/${state.folderId}`
                  : '')
              }
              onChange={(event) => setFolder(event.target.value)}
              disabled={busy || running || state?.pending}
            />
          </label>
          <label>
            OAuth client JSON · loại Desktop app
            <input
              type="file"
              accept=".json,application/json"
              aria-label="OAuth client JSON"
              disabled={busy || running || state?.pending}
              onChange={async (event) => {
                const file = event.target.files?.[0];
                setCredentials(null);
                if (!file) return;
                try {
                  if (file.size > 32768) throw new Error('File OAuth quá lớn.');
                  setCredentials(JSON.parse(await file.text()));
                  setMessage(
                    'Đã chọn cấu hình OAuth. Bấm lưu cấu hình để tiếp tục.',
                  );
                } catch {
                  setMessage('Không đọc được file OAuth client JSON.');
                }
                event.target.value = '';
              }}
            />
          </label>
          <p>
            Tạo OAuth client của ứng dụng trong Google Cloud và bật Drive API
            cùng Google Picker API. Thông tin đăng nhập được bảo vệ bằng tài
            khoản Windows hiện tại.
          </p>
          <div className="actions">
            <button
              disabled={!credentials || busy || running || state?.pending}
              onClick={() =>
                perform(async () => {
                  await api!.json('drive/configure', 'POST', {
                    credentials,
                    folder: folder || state?.folderId,
                  });
                  setCredentials(null);
                  setAuthUrl('');
                })
              }
            >
              Lưu cấu hình Drive
            </button>
            <button
              disabled={!state?.configured || busy || running || state.pending}
              onClick={() =>
                perform(async () => {
                  const result = await api!.json<{ url: string }>(
                    'drive/connect',
                    'POST',
                    {},
                  );
                  setAuthUrl(result.url);
                })
              }
            >
              Đăng nhập Google
            </button>
            <button
              disabled={!state?.configured || busy || running}
              onClick={() =>
                perform(async () => {
                  await api!.json('drive/disconnect', 'POST', {});
                  setAuthUrl('');
                })
              }
            >
              Ngắt / hủy kết nối
            </button>
          </div>
          {authUrl && !state?.connected && (
            <a href={authUrl} target="_blank" rel="noreferrer">
              Mở Google để cấp quyền và chọn thư mục ↗
            </a>
          )}
          <p role="status">{message || state?.message}</p>
          <label className="rights">
            <input
              type="checkbox"
              checked={consent}
              onChange={(event) => setConsent(event.target.checked)}
            />
            Tôi đồng ý tải bản sao toàn bộ media đã nhập, project và MP4 đã xuất
            lên thư mục này.
          </label>
          <button
            className="primary"
            disabled={!state?.connected || !consent || busy || running}
            onClick={() =>
              perform(async () => {
                await beforeBackup();
                await api!.json('drive/backup', 'POST', { confirmed: true });
              })
            }
          >
            {running ? 'Đang sao lưu…' : 'Sao lưu dữ liệu lên Drive'}
          </button>
          <p aria-live="polite">{state?.backup.message}</p>
          <label className="rights">
            <input
              type="checkbox"
              checked={Boolean(state?.autoSync)}
              disabled={!state?.connected || busy || running}
              onChange={(event) =>
                perform(async () => {
                  await api!.json('drive/auto', 'POST', {
                    enabled: event.target.checked,
                    confirmed: true,
                  });
                })
              }
            />
            Tự sao lưu thay đổi lên Drive khi ứng dụng đang chạy (kiểm tra mỗi
            30 giây).
          </label>
          <div className="drive-restore">
            <button
              disabled={!state?.connected || busy || running}
              onClick={() =>
                perform(async () => {
                  const found =
                    await api!.call<
                      { id: string; name: string; createdTime?: string }[]
                    >('drive/backups');
                  setBackups(found);
                  setSelectedBackup(found[0]?.id || '');
                  if (!found.length)
                    setMessage('Chưa có bản sao lưu trong thư mục này.');
                })
              }
            >
              Tìm bản sao lưu trên Drive
            </button>
            {backups.length > 0 && (
              <label>
                Chọn bản để khôi phục
                <select
                  aria-label="Bản sao lưu Drive"
                  value={selectedBackup}
                  onChange={(event) => setSelectedBackup(event.target.value)}
                >
                  {backups.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.createdTime || item.name} · {item.name}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <button
              disabled={!selectedBackup || busy || running}
              onClick={() =>
                perform(async () => {
                  await api!.json('drive/restore', 'POST', {
                    manifestId: selectedBackup,
                    confirmed: true,
                  });
                })
              }
            >
              Khôi phục project mới từ bản đã chọn
            </button>
            <p aria-live="polite">{state?.restore?.message}</p>
            <button
              disabled={!api || busy}
              onClick={() =>
                perform(async () => {
                  setExports(
                    await api!.call<{ sha256: string; bytes: number }[]>(
                      'drive/exports',
                    ),
                  );
                })
              }
            >
              Xem MP4 đã khôi phục
            </button>
            {exports.map((file) => (
              <a
                key={file.sha256}
                href={`/api/v1/drive/exports/${file.sha256}`}
                target="_blank"
                rel="noreferrer"
              >
                Tải MP4 {file.sha256.slice(0, 10)} ·{' '}
                {(file.bytes / 1024 / 1024).toFixed(1)} MB ↗
              </a>
            ))}
          </div>
          <small>
            Bản local vẫn được giữ. Mỗi lượt tạo bản sao riêng và dùng thêm
            quota. Project đang có trên máy sẽ không bị ghi đè. Tự sao lưu cần
            bật riêng; máy phải đang chạy và có mạng.
          </small>
        </div>
      )}
    </section>
  );
}
