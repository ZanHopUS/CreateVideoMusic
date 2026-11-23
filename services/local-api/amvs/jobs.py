"""Persistent jobs and owned subprocess tree supervision; no PoC imports."""

import json
import os
import queue
import shutil
import subprocess
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import av
import imageio_ffmpeg
import psutil

from .domain import ROOT, TICKS, content_hash, validate, validate_job
from .store import contained, digest_file

TERMINAL = {"succeeded", "failed", "cancelled", "interrupted"}


class Jobs:
    def __init__(self, store, headroom=4):
        self.store = store
        self.headroom = headroom
        self.lock = threading.RLock()
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.rows = store.jobs()
        self.cancelled = set()
        self.stopping = False
        for job in self.rows.values():
            if job["status"] not in TERMINAL:
                job.update(
                    status="interrupted", message="Ứng dụng đã đóng; hãy tạo lượt render mới."
                )
                store.put_job(job)

    def public(self, id):
        with self.lock:
            job = self.rows[id]
            result = {
                k: v for k, v in job.items() if k not in {"project", "grant", "outputFile", "pid"}
            }
            validate_job(result)
            return result

    def patch(self, id, **changes):
        with self.lock:
            self.rows[id].update(changes)
            self.store.put_job(self.rows[id])

    def start(self, project, grant):
        validate(project, self.store.assets())
        if (
            project["templateRef"]["id"] != "TPL-01"
            or project["lyrics"]
            or any(i["type"] not in {"image", "audio", "text"} for i in project["items"])
        ):
            raise ValueError("Lượt đầu chỉ hỗ trợ mẫu Ảnh + Caption + Nhạc.")
        if project["preset"] != {"width": 720, "height": 1280, "fps": 30}:
            raise ValueError("Lượt đầu hỗ trợ 720p30 dọc.")
        if not any(i["type"] == "image" for i in project["items"]) or not any(
            i["type"] == "audio" for i in project["items"]
        ):
            raise ValueError("Hãy thêm ảnh và nhạc trước khi xuất.")
        id = uuid.uuid4().hex
        job = {
            "schemaVersion": "amvs-job/1",
            "id": id,
            "kind": "render",
            "projectId": project["id"],
            "status": "queued",
            "phase": "queued",
            "progress": 0,
            "snapshotHash": content_hash(project),
            "project": json.loads(json.dumps(project)),
            "grant": str(grant),
            "message": "Đang chờ lượt render.",
        }
        with self.lock:
            if self.stopping or sum(j["status"] not in TERMINAL for j in self.rows.values()) >= 10:
                raise ValueError("Hàng đợi đã đầy.")
            self.rows[id] = job
            self.store.put_job(job)
        self.pool.submit(self.run, id)
        return self.public(id)

    def cancel(self, id):
        with self.lock:
            if self.rows[id]["status"] not in TERMINAL:
                self.cancelled.add(id)
                self.patch(id, status="cancelling", message="Đang hủy…")
        return self.public(id)

    def check(self, id):
        with self.lock:
            if id in self.cancelled or self.stopping:
                raise InterruptedError("Đã hủy render.")

    def kill(self, process):
        if process.poll() is not None:
            return
        try:
            parent = psutil.Process(process.pid)
            children = parent.children(recursive=True)
            for member in reversed(children + [parent]):
                try:
                    member.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            psutil.wait_procs(children + [parent], timeout=5)
        except psutil.NoSuchProcess:
            pass
        process.wait(timeout=10)

    def command(self, id, args, folder, phase):
        lines = queue.Queue()
        samples = []
        low = None
        began = time.monotonic()
        with (folder / f"{phase}.stderr.log").open("w", encoding="utf-8") as stderr:
            process = subprocess.Popen(
                args, cwd=ROOT, stdout=subprocess.PIPE, stderr=stderr, text=True, encoding="utf-8"
            )

            def read():
                for line in process.stdout:
                    lines.put(line)

            reader = threading.Thread(target=read, daemon=True)
            reader.start()
            try:
                while process.poll() is None:
                    self.check(id)
                    while not lines.empty():
                        line = lines.get_nowait()
                        try:
                            event = json.loads(line)
                            if "progress" in event:
                                self.patch(
                                    id,
                                    progress=max(
                                        self.rows[id]["progress"], min(0.85, event["progress"])
                                    ),
                                )
                        except (ValueError, TypeError):
                            pass
                    available = psutil.virtual_memory().available
                    private = 0
                    try:
                        parent = psutil.Process(process.pid)
                        for child in [parent, *parent.children(recursive=True)]:
                            try:
                                mem = child.memory_info()
                                private += getattr(mem, "private", mem.rss)
                            except psutil.NoSuchProcess:
                                pass
                    except psutil.NoSuchProcess:
                        pass
                    now = time.monotonic()
                    low = (low or now) if available < 2 * 1024**3 else None
                    samples.append(
                        {
                            "elapsed_s": now - began,
                            "private_bytes": private,
                            "system_available_bytes": available,
                        }
                    )
                    if private > 12 * 1024**3 or (low and now - low >= 10):
                        raise MemoryError("RAM thấp; render đã dừng để bảo vệ dữ liệu.")
                    if now - began > 3000:
                        raise TimeoutError("Render vượt thời gian cho phép.")
                    time.sleep(0.25)
                reader.join(timeout=2)
                if process.returncode:
                    raise RuntimeError("Tiến trình render không hoàn tất; xem chẩn đoán local.")
            except BaseException:
                self.kill(process)
                raise
            finally:
                if process.stdout:
                    process.stdout.close()
                (folder / f"{phase}.resources.json").write_text(
                    json.dumps({"samples": samples}, indent=2), encoding="utf-8"
                )
        return samples

    def run(self, id):
        try:
            with self.lock:
                job = dict(self.rows[id])
            self.check(id)
            folder = contained(self.store.root / "jobs" / id, self.store.root)
            folder.mkdir(parents=True)
            consecutive = 0
            admission_samples = []
            self.patch(id, phase="waiting-resources", message="Chờ đủ RAM trống để xuất video…")
            while consecutive < 10:
                self.check(id)
                available = psutil.virtual_memory().available
                consecutive = consecutive + 1 if available >= self.headroom * 1024**3 else 0
                admission_samples.append(
                    {"system_available_bytes": available, "monotonic_s": time.monotonic()}
                )
                admission_samples = admission_samples[-60:]
                (folder / "admission.json").write_text(
                    json.dumps(
                        {
                            "minimumGiB": self.headroom,
                            "requiredSamples": 10,
                            "allowed": consecutive >= 10,
                            "samples": admission_samples,
                        }
                    ),
                    encoding="utf-8",
                )
                if consecutive < 10:
                    time.sleep(1)
            public = folder / "public"
            public.mkdir()
            assets = self.store.assets()
            mapping = {}
            self.patch(id, status="preparing", phase="preparing", message="Chuẩn bị bản dựng…")
            for key in job["project"]["assetRefs"]:
                self.check(id)
                source = self.store.asset_path(assets[key])
                if digest_file(source) != key:
                    raise ValueError("Media đã thay đổi hoặc bị hỏng.")
                name = assets[key]["file"]
                shutil.copy2(source, public / name)
                mapping[key] = name
            (folder / "input.json").write_text(
                json.dumps({"project": job["project"], "assets": mapping}), encoding="utf-8"
            )
            if shutil.disk_usage(folder).free < 2 * 1024**3:
                raise OSError("Không đủ dung lượng trống.")
            self.patch(id, status="running", phase="running", message="Đang dựng video…")
            samples = self.command(
                id, ["node", str(ROOT / "workers/render/render.mjs"), str(folder)], folder, "render"
            )
            self.check(id)
            self.patch(
                id,
                status="finalizing",
                phase="finalizing",
                progress=0.88,
                message="Hoàn thiện âm thanh…",
            )
            seconds = job["project"]["durationTicks"] / TICKS
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            samples += self.command(
                id,
                [
                    ffmpeg,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-n",
                    "-i",
                    str(folder / "raw.mp4"),
                    "-map",
                    "0:v:0",
                    "-map",
                    "0:a:0",
                    "-c:v",
                    "copy",
                    "-c:a",
                    "aac",
                    "-ar",
                    "48000",
                    "-b:a",
                    "192k",
                    "-af",
                    f"apad=whole_dur={seconds},atrim=duration={seconds},asetpts=PTS-STARTPTS",
                    "-t",
                    str(seconds),
                    "-movflags",
                    "+faststart",
                    str(folder / "bounded.mp4"),
                ],
                folder,
                "finalize",
            )
            self.check(id)
            self.patch(
                id,
                status="validating",
                phase="validating",
                progress=0.95,
                message="Kiểm tra video…",
            )
            with av.open(str(folder / "bounded.mp4")) as media:
                video, audio = media.streams.video[0], media.streams.audio[0]
                if (
                    video.codec_context.name != "h264"
                    or audio.codec_context.name != "aac"
                    or abs(media.duration / av.time_base - seconds) > 1 / 30
                ):
                    raise ValueError("Video xuất không đạt kiểm tra metadata.")
                frames = 0
                for frame in media.decode(video=0):
                    if frames % 30 == 0:
                        self.check(id)
                    frames += 1
                if frames != round(seconds * 30):
                    raise ValueError("Video xuất thiếu frame.")
            self.check(id)
            target = contained(
                Path(job["grant"]) / f"{job['project']['id']}-{id}.mp4", job["grant"]
            )
            stage = contained(target.with_suffix(".stage"), job["grant"])
            with (folder / "bounded.mp4").open("rb") as source, stage.open("xb") as output:
                shutil.copyfileobj(source, output, 1024 * 1024)
                output.flush()
                os.fsync(output.fileno())
            with self.lock:
                self.check(id)
                contained(target, job["grant"])
                os.replace(stage, target)
                self.patch(
                    id,
                    status="succeeded",
                    phase="succeeded",
                    progress=1,
                    outputFile=str(target),
                    resourceSampledPass=bool(samples)
                    and all(
                        s["system_available_bytes"] >= 2 * 1024**3
                        and s["private_bytes"] <= 12 * 1024**3
                        for s in samples
                    ),
                    resourceScope="render-and-finalize-children-only",
                    message="Video đã sẵn sàng.",
                )
        except InterruptedError:
            self.patch(id, status="cancelled", phase="cancelled", message="Đã hủy render.")
        except Exception as error:
            # Public errors never include raw exception paths, argv or private content.
            self.patch(
                id,
                status="failed",
                phase="failed",
                message="Không thể xuất video. Dữ liệu project được giữ nguyên.",
            )
            folder = contained(self.store.root / "jobs" / id, self.store.root)
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "failure.json").write_text(
                json.dumps({"type": type(error).__name__, "message": str(error)}), encoding="utf-8"
            )

    def shutdown(self):
        self.stopping = True
        self.pool.shutdown(wait=True, cancel_futures=True)
