'use client';
import { useEffect, useRef, useState } from 'react';
import {
  applyLyrics,
  parseLyrics,
  TICKS,
  type LyricLine,
  type ProjectContent,
} from '@amvs/domain';
import { Api, type Asset, type Job } from '../lib/api';
export type LyricsWorkspaceDraft = {
  audioId: string;
  lines: LyricLine[];
  input: string;
  format: 'lrc' | 'srt';
  language: string;
  model: string;
};
export function LyricsPanel({
  project,
  assets,
  api,
  change,
  prepare,
  expanded,
  toggle,
  initialDraft,
  onDraftChange,
}: {
  project: ProjectContent;
  assets: Asset[];
  api: Api | null;
  change: (op: (p: ProjectContent) => void) => boolean;
  prepare: () => Promise<void>;
  expanded: boolean;
  toggle: (value: boolean) => void;
  initialDraft?: LyricsWorkspaceDraft;
  onDraftChange: (draft: LyricsWorkspaceDraft) => void;
}) {
  const music = project.items.filter((i) => i.type === 'audio');
  const [audioId, setAudioId] = useState(
    initialDraft?.audioId ?? music[0]?.id ?? '',
  );
  const [lines, setLines] = useState<LyricLine[]>(
    structuredClone(initialDraft?.lines ?? project.lyrics),
  );
  const [input, setInput] = useState(initialDraft?.input ?? ''),
    [format, setFormat] = useState<'lrc' | 'srt'>(
      initialDraft?.format ?? 'lrc',
    );
  const [message, setMessage] = useState(
    'Nhập/import lời theo thời gian bài hát nguồn, sửa rồi duyệt trước khi áp dụng.',
  );
  const [language, setLanguage] = useState(initialDraft?.language ?? 'vi'),
    [model, setModel] = useState(initialDraft?.model ?? 'small');
  useEffect(() => {
    onDraftChange({ audioId, lines, input, format, language, model });
  }, [audioId, lines, input, format, language, model, onDraftChange]);
  const [job, setJob] = useState<Job | null>(null);
  const savedLyrics = useRef(JSON.stringify(project.lyrics));
  useEffect(() => {
    const signature = JSON.stringify(project.lyrics);
    if (signature !== savedLyrics.current) {
      savedLyrics.current = signature;
      setLines(structuredClone(project.lyrics));
    }
  }, [project.lyrics]);
  const audio = music.find((i) => i.id === audioId) ?? music[0];
  const asset = assets.find((a) => a.id === audio?.assetId);
  useEffect(() => {
    if (
      !job ||
      ['failed', 'cancelled', 'interrupted', 'succeeded'].includes(job.status)
    )
      return;
    let active = true;
    const timer = setInterval(async () => {
      try {
        const next = await api!.call<Job>(`jobs/${job.id}`);
        if (!active) return;
        if (next.status === 'succeeded') {
          const result = await api!.call<{
            lines: LyricLine[];
            message: string;
          }>(`jobs/${job.id}/lyrics`);
          if (active) {
            setLines(result.lines);
            setMessage(result.message);
          }
        }
        if (active) setJob(next);
      } catch (e) {
        if (active) setMessage((e as Error).message);
      }
    }, 1000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [job, api]);
  const [previousJobs, setPreviousJobs] = useState<Job[]>([]);
  useEffect(() => {
    if (!api) return;
    let active = true;
    api
      .call<(Job & { projectId: string })[]>('jobs')
      .then((rows) => {
        if (!active) return;
        const matches = rows.filter(
          (j) =>
            j.projectId === project.id && ['asr', 'alignment'].includes(j.kind),
        );
        setPreviousJobs(matches);
        const running = matches.find(
          (j) =>
            !['succeeded', 'failed', 'cancelled', 'interrupted'].includes(
              j.status,
            ),
        );
        if (running) setJob(running);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [api, project.id]);
  function saveDraft() {
    if (
      project.lyrics.some((l) => l.status === 'reviewed') &&
      !window.confirm(
        'Thay lời hiện tại bằng bản nháp này? Lời chưa duyệt sẽ tạm ẩn khỏi preview.',
      )
    )
      return;
    const draft = lines.map(({ sourceAudioItemId: _source, ...line }) => line);
    if (
      change((p) => {
        p.lyrics = structuredClone(draft);
        p.items = p.items.filter((i) => i.type !== 'lyrics');
      })
    )
      setMessage(
        'Đã ghi bản nháp vào project. Lưu project để tạo bản lưu thủ công; duyệt rồi Áp dụng để hiển thị.',
      );
  }
  async function recognize() {
    try {
      if (!audio) throw new Error('Thêm clip nhạc trước.');
      await prepare();
      const current = await api!.call<{ revision: number }>(
        `projects/${project.id}`,
      );
      setJob(
        await api!.json<Job>('lyrics/jobs', 'POST', {
          projectId: project.id,
          revision: current.revision,
          audioItemId: audio.id,
          language,
          model,
        }),
      );
    } catch (e) {
      setMessage((e as Error).message);
    }
  }
  async function align() {
    try {
      if (!audio || !lines.length)
        throw new Error('Nhập câu lời và mốc nguồn trước.');
      await prepare();
      const current = await api!.call<{ revision: number }>(
        `projects/${project.id}`,
      );
      setJob(
        await api!.json<Job>('lyrics/alignment', 'POST', {
          projectId: project.id,
          revision: current.revision,
          audioItemId: audio.id,
          language,
          lines,
        }),
      );
    } catch (e) {
      setMessage((e as Error).message);
    }
  }
  function parse() {
    if (!asset) {
      setMessage('Thêm nhạc để kiểm tra thời lượng nguồn.');
      return;
    }
    const result = parseLyrics(input, format, asset.durationTicks);
    setLines(result.lines);
    setMessage(
      result.errors.length
        ? result.errors.join(' · ')
        : `Đã đọc ${result.lines.length} câu nháp.`,
    );
  }
  function patch(id: string, op: (line: LyricLine) => void) {
    setLines((previous) =>
      previous.map((line) => {
        if (line.id !== id) return line;
        const next = structuredClone(line);
        op(next);
        next.status = 'draft';
        return next;
      }),
    );
  }
  const active =
    job &&
    !['failed', 'cancelled', 'interrupted', 'succeeded'].includes(job.status);
  return (
    <details
      className="tool-panel"
      open={expanded}
      onToggle={(e) => toggle(e.currentTarget.open)}
    >
      <summary>Lời hát · nhập, nhận dạng và duyệt</summary>
      {previousJobs
        .filter((j) => j.status === 'succeeded')
        .map((j) => (
          <button
            key={j.id}
            onClick={async () => {
              try {
                const result = await api!.call<{
                  lines: LyricLine[];
                  message: string;
                }>(`jobs/${j.id}/lyrics`);
                setLines(result.lines);
                setMessage(result.message);
              } catch (e) {
                setMessage((e as Error).message);
              }
            }}
          >
            Mở bản nháp {j.kind === 'alignment' ? 'căn từ' : 'nhận dạng'}{' '}
            {j.id.slice(0, 6)}
          </button>
        ))}
      <label>
        Clip nhạc nguồn
        <select
          aria-label="Clip nhạc nguồn"
          value={audio?.id ?? ''}
          onChange={(e) => setAudioId(e.target.value)}
        >
          {music.map((i) => (
            <option key={i.id} value={i.id}>
              {assets.find((a) => a.id === i.assetId)?.name ?? 'Nhạc'}
            </option>
          ))}
        </select>
      </label>
      <div className="clip-actions">
        <select
          aria-label="Ngôn ngữ nhận dạng"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
        >
          <option value="vi">Tiếng Việt</option>
          <option value="en">Tiếng Anh</option>
        </select>
        <select
          aria-label="Model local"
          value={model}
          onChange={(e) => setModel(e.target.value)}
        >
          <option value="small">Small · nhẹ, cần rà soát</option>
          <option value="medium">Medium · tốn RAM hơn</option>
        </select>
        <button
          disabled={!api || !audio || Boolean(active)}
          onClick={recognize}
        >
          Nhận dạng trên máy
        </button>
        {active && (
          <button
            onClick={async () => {
              try {
                setJob(
                  await api!.json<Job>(`jobs/${job!.id}/cancel`, 'POST', {}),
                );
              } catch (e) {
                setMessage((e as Error).message);
              }
            }}
          >
            Hủy nhận dạng
          </button>
        )}
      </div>
      {job && (
        <p role="status">
          {job.message} · {Math.round(job.progress * 100)}%
        </p>
      )}
      <p>
        ASR cho bản nháp; điểm model chưa phải xác suất đúng. Có thể không nhận
        được lời với nhạc không giọng hoặc giọng không rõ. Cloud AI đang tắt.
      </p>
      <label>
        File LRC/SRT
        <input
          aria-label="Nhập file lời"
          type="file"
          accept=".lrc,.srt"
          onChange={async (e) => {
            const f = e.target.files?.[0];
            if (f) {
              if (f.size > 1024 * 1024) {
                setMessage('File vượt 1 MiB.');
                return;
              }
              setInput(await f.text());
              setFormat(f.name.toLowerCase().endsWith('.srt') ? 'srt' : 'lrc');
            }
            e.target.value = '';
          }}
        />
      </label>
      <select
        aria-label="Định dạng lời"
        value={format}
        onChange={(e) => setFormat(e.target.value as 'lrc' | 'srt')}
      >
        <option value="lrc">LRC</option>
        <option value="srt">SRT</option>
      </select>
      <textarea
        aria-label="Lời có timestamp"
        placeholder="[00:01.00]Dòng lời của bạn"
        value={input}
        onChange={(e) => setInput(e.target.value)}
      />
      <button onClick={parse}>Đọc lời thành bản nháp</button>
      <button
        onClick={() =>
          setLines((prev) => [
            ...prev,
            {
              id: crypto.randomUUID(),
              text: '',
              sourceStartTicks: 0,
              sourceEndTicks: Math.min(
                asset?.durationTicks ?? TICKS,
                TICKS * 3,
              ),
              source: 'user',
              status: 'draft',
              alignmentStatus: 'sentence',
              words: [],
            },
          ])
        }
      >
        Thêm câu thủ công
      </button>
      <button
        disabled={!api || !audio || !lines.length || Boolean(active)}
        onClick={align}
      >
        Căn từ local trong mốc câu
      </button>
      <button disabled={!lines.length} onClick={saveDraft}>
        Lưu bản nháp lời vào project
      </button>
      <p>
        Bản nháp mới chưa thay lời trên timeline. Lưu bản nháp để giữ các chỉnh
        sửa khi mở lại, rồi duyệt và áp dụng.
      </p>
      <div className="lyrics-rows">
        {lines.map((line, index) => (
          <fieldset key={line.id}>
            <legend>
              Câu {index + 1} ·{' '}
              {line.alignmentStatus === 'word' ? 'Mốc từ nháp' : 'Mốc câu'}
            </legend>
            <textarea
              aria-label={`Lời câu ${index + 1}`}
              value={line.text}
              onChange={(e) =>
                patch(line.id, (l) => {
                  l.text = e.target.value;
                  l.words = [];
                  l.alignmentStatus = 'sentence';
                })
              }
            />
            <label>
              Từ giây
              <input
                type="number"
                min="0"
                step="0.01"
                aria-label={`Bắt đầu câu ${index + 1}`}
                value={line.sourceStartTicks / TICKS}
                onChange={(e) =>
                  patch(line.id, (l) => {
                    l.sourceStartTicks = Math.round(
                      Number(e.target.value) * TICKS,
                    );
                    l.words = [];
                    l.alignmentStatus = 'sentence';
                  })
                }
              />
            </label>
            <label>
              Đến giây
              <input
                type="number"
                min="0"
                step="0.01"
                aria-label={`Kết thúc câu ${index + 1}`}
                value={line.sourceEndTicks / TICKS}
                onChange={(e) =>
                  patch(line.id, (l) => {
                    l.sourceEndTicks = Math.round(
                      Number(e.target.value) * TICKS,
                    );
                    l.words = [];
                    l.alignmentStatus = 'sentence';
                  })
                }
              />
            </label>
            <label>
              <input
                type="checkbox"
                checked={line.status === 'reviewed'}
                onChange={(e) =>
                  setLines((prev) =>
                    prev.map((l) =>
                      l.id === line.id
                        ? {
                            ...l,
                            status: e.target.checked ? 'reviewed' : 'draft',
                          }
                        : l,
                    ),
                  )
                }
              />
              Đã duyệt câu {index + 1}
            </label>
            <button
              onClick={() =>
                setLines((prev) => prev.filter((l) => l.id !== line.id))
              }
            >
              Gỡ câu {index + 1}
            </button>
          </fieldset>
        ))}
      </div>
      <button
        disabled={
          !audio || lines.some((l) => l.status !== 'reviewed') || !lines.length
        }
        onClick={() => {
          if (!audio) return;
          try {
            if (
              change((p) => Object.assign(p, applyLyrics(p, lines, audio.id)))
            )
              setMessage('Đã gắn lời đã duyệt vào timeline.');
          } catch (e) {
            setMessage((e as Error).message);
          }
        }}
      >
        Áp dụng lời đã duyệt
      </button>
      <p role="status">{message}</p>
    </details>
  );
}
