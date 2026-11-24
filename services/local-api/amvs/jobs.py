"""Persistent jobs and owned subprocess tree supervision; no PoC imports."""

import json
import math
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

from .domain import ROOT, TICKS, content_hash, parse_json, validate, validate_job
from .process_group import OwnedGroup
from .providers import provider
from .storage_policy import StoragePolicy
from .store import contained, digest_file

TERMINAL = {"succeeded", "failed", "cancelled", "interrupted"}


class RenderInputError(ValueError):
    pass


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
                k: v
                for k, v in job.items()
                if k
                not in {
                    "project",
                    "grant",
                    "outputFile",
                    "pid",
                    "asr",
                    "packageInfo",
                    "packageSnapshot",
                }
            }
            validate_job(result)
            return result

    def patch(self, id, **changes):
        with self.lock:
            self.rows[id].update(changes)
            self.store.put_job(self.rows[id])

    def start(self, project, grant):
        validate(project, self.store.assets())
        if any(
            l["status"] != "reviewed"
            for l in project["lyrics"]
            if any(i.get("lyricId") == l["id"] for i in project["items"])
        ):
            raise RenderInputError("Hãy duyệt lời trước khi xuất.")
        if not any(i["type"] in {"image", "video"} for i in project["items"]) or not any(
            i["type"] == "audio" for i in project["items"]
        ):
            raise RenderInputError("Hãy thêm ảnh hoặc video và nhạc trước khi xuất.")
        if (
            project["templateRef"]["id"] == "TPL-02"
            and sum(i["type"] == "image" for i in project["items"]) < 2
        ):
            raise RenderInputError("Music Card cần ít nhất hai ảnh.")
        if project["templateRef"]["id"] == "TPL-03" and not any(
            i["type"] == "lyrics" for i in project["items"]
        ):
            raise RenderInputError(
                "Lyrics Video cần lời đã duyệt và áp dụng vào đoạn nhạc đang chọn."
            )
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
                raise RenderInputError("Hàng đợi đã đầy.")
            self.rows[id] = job
            self.store.put_job(job)
        self.pool.submit(self.run, id)
        return self.public(id)

    def start_package(self, current, grant):
        validate(current["project"], self.store.assets())
        id = uuid.uuid4().hex
        job = {
            "schemaVersion": "amvs-job/1",
            "id": id,
            "kind": "package",
            "projectId": current["project"]["id"],
            "status": "queued",
            "phase": "queued",
            "progress": 0,
            "snapshotHash": current["contentHash"],
            "message": "Đang chờ đóng gói project…",
            "project": current["project"],
            "packageSnapshot": current,
            "grant": str(grant),
        }
        with self.lock:
            if self.stopping or sum(j["status"] not in TERMINAL for j in self.rows.values()) >= 10:
                raise ValueError("Hàng đợi đã đầy.")
            self.rows[id] = job
            self.store.put_job(job)
        self.pool.submit(self.run, id)
        return self.public(id)

    def package_result(self, id):
        job = self.rows[id]
        if job["kind"] != "package" or job["status"] != "succeeded":
            raise ValueError("Package chưa sẵn sàng.")
        return job["packageInfo"]

    def start_asr(self, project, audio_id, language, model, lines=None, provider_id="local"):
        validate(project, self.store.assets())
        if language not in {"vi", "en"} or model not in {"small", "medium"}:
            raise ValueError("Ngôn ngữ/model không hợp lệ.")
        audio = next(
            (i for i in project["items"] if i["id"] == audio_id and i["type"] == "audio"), None
        )
        if not audio:
            raise ValueError("Chọn clip nhạc nguồn.")
        runtime = provider(provider_id).runtime(language, model, alignment=lines is not None)
        if lines is not None:
            if not lines:
                raise ValueError("Cần câu lời có mốc nguồn trước khi căn từ.")
            candidate = json.loads(json.dumps(project))
            candidate["items"] = [i for i in candidate["items"] if i["type"] != "lyrics"]
            candidate["lyrics"] = lines
            validate(candidate, self.store.assets())
        id = uuid.uuid4().hex
        job = {
            "schemaVersion": "amvs-job/1",
            "id": id,
            "kind": "alignment" if lines is not None else "asr",
            "projectId": project["id"],
            "snapshotHash": content_hash(project),
            "status": "queued",
            "phase": "queued",
            "progress": 0,
            "message": "Đang chờ nhận dạng local…",
            "project": json.loads(json.dumps(project)),
            "asr": {
                "audio": audio,
                "language": language,
                "model": ("align-" + language) if lines is not None else model,
                **runtime,
                "lines": lines,
            },
        }
        with self.lock:
            if self.stopping or sum(j["status"] not in TERMINAL for j in self.rows.values()) >= 10:
                raise ValueError("Hàng đợi đã đầy.")
            self.rows[id] = job
            self.store.put_job(job)
        self.pool.submit(self.run, id)
        return self.public(id)

    def run_asr(self, id, job, folder):
        config = job["asr"]
        audio = config["audio"]
        source = self.store.asset_path(self.store.assets()[audio["assetId"]])
        if digest_file(source) != audio["assetId"]:
            raise ValueError("Media nguồn bị thay đổi.")
        start = audio["sourceStartTicks"]
        duration = (
            audio["durationTicks"] * audio["speed"]["numerator"] / audio["speed"]["denominator"]
        )
        self.patch(id, status="preparing", phase="preparing", message="Chuẩn bị đoạn nhạc nguồn…")
        self.command(
            id,
            [
                imageio_ffmpeg.get_ffmpeg_exe(),
                "-hide_banner",
                "-loglevel",
                "error",
                "-n",
                "-ss",
                str(start / TICKS),
                "-i",
                str(source),
                "-t",
                str(duration / TICKS),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                str(folder / "audio.wav"),
            ],
            folder,
            "prepare-audio",
        )
        (folder / "asr-input.json").write_text(
            json.dumps(
                {**config, "sourceStartTicks": start, "sourceEndTicks": round(start + duration)}
            ),
            encoding="utf-8",
        )
        self.check(id)
        self.patch(id, status="running", phase="running", message="Đang nhận dạng lời trên CPU…")
        self.command(
            id,
            [
                config["python"],
                str(
                    ROOT
                    / (
                        "services/local-api/amvs/alignment_worker.py"
                        if job["kind"] == "alignment"
                        else "services/local-api/amvs/asr_worker.py"
                    )
                ),
                str(folder),
            ],
            folder,
            "asr",
        )
        result = parse_json((folder / "lyrics-result.json").read_bytes())
        candidate = json.loads(json.dumps(job["project"]))
        candidate["lyrics"] = result["lines"]
        candidate["items"] = [i for i in candidate["items"] if i["type"] != "lyrics"]
        validate(candidate, self.store.assets())
        self.check(id)
        self.patch(id, status="succeeded", phase="succeeded", progress=1, message=result["message"])

    def lyrics_result(self, id):
        job = self.rows[id]
        if job["kind"] not in {"asr", "alignment"} or job["status"] != "succeeded":
            raise ValueError("Bản nháp chưa sẵn sàng.")
        return parse_json(
            contained(
                self.store.root / "jobs" / id / "lyrics-result.json", self.store.root
            ).read_bytes()
        )

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
        previous_cpu = {}
        previous_sample = began
        ownership = OwnedGroup(folder / (phase + "-owner")) if os.name == "nt" else None
        with (folder / f"{phase}.stderr.log").open("w", encoding="utf-8") as stderr:
            try:
                launch = ownership.launch if ownership else subprocess.Popen
                process = launch(
                    args,
                    cwd=ROOT,
                    stdout=subprocess.PIPE,
                    stderr=stderr,
                    text=True,
                    encoding="utf-8",
                )
            except BaseException:
                if ownership:
                    ownership.close()
                raise

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
                    cpu_delta = 0
                    try:
                        parent = psutil.Process(process.pid)
                        for child in [parent, *parent.children(recursive=True)]:
                            try:
                                mem = child.memory_info()
                                private += getattr(mem, "private", mem.rss)
                                cpu = child.cpu_times()
                                total = cpu.user + cpu.system
                                if child.pid in previous_cpu:
                                    cpu_delta += max(0, total - previous_cpu[child.pid])
                                previous_cpu[child.pid] = total
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
                            "cpuPercentOfOneCore": cpu_delta
                            / max(0.001, now - previous_sample)
                            * 100,
                            "system_available_bytes": available,
                        }
                    )
                    previous_sample = now
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
                cleanup_error = None
                if ownership:
                    try:
                        ownership.close()
                    except Exception as error:
                        cleanup_error = error
                reader.join(timeout=2)
                if process.stdout:
                    process.stdout.close()
                (folder / f"{phase}.resources.json").write_text(
                    json.dumps({"samples": samples}, indent=2), encoding="utf-8"
                )
                if cleanup_error:
                    raise cleanup_error
        return samples

    def run(self, id):
        try:
            with self.lock:
                job = dict(self.rows[id])
            self.check(id)
            folder = contained(self.store.root / "jobs" / id, self.store.root)
            folder.mkdir(parents=True)
            if job["kind"] == "package":
                from .snapshots import Snapshots

                self.patch(
                    id, status="running", phase="running", message="Đang đóng gói project và media…"
                )
                current = job["packageSnapshot"]
                result = Snapshots(self.store).export(
                    job["projectId"],
                    current["revision"],
                    job["grant"],
                    snapshot=current,
                    check=lambda: self.check(id),
                )
                with self.lock:
                    self.check(id)
                    self.patch(
                        id,
                        status="succeeded",
                        phase="succeeded",
                        progress=1,
                        packageInfo=result,
                        message="Đã tạo package di chuyển có checksum.",
                    )
                return
            consecutive = 0
            admission_samples = []
            self.patch(id, phase="waiting-resources", message="Chờ đủ RAM trống để chạy tác vụ…")
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
            if job["kind"] in {"asr", "alignment"}:
                self.run_asr(id, job, folder)
                return
            public = folder / "public"
            public.mkdir()
            assets = self.store.assets()
            reserve = StoragePolicy(self.store).read()["reserveGiB"] * 1024**3
            source_bytes = sum(assets[k]["bytes"] for k in job["project"]["assetRefs"])
            estimate = source_bytes + int(
                job["project"]["durationTicks"]
                / TICKS
                * job["project"]["preset"]["width"]
                * job["project"]["preset"]["height"]
                * 0.2
            )
            if (
                shutil.disk_usage(folder).free < estimate + max(reserve, estimate // 10)
                or shutil.disk_usage(job["grant"]).free < estimate + reserve
            ):
                raise OSError("Không đủ dung lượng cho bản dựng và staging.")
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
            if shutil.disk_usage(folder).free < reserve:
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
            preset = job["project"]["preset"]
            seconds = (
                math.ceil(job["project"]["durationTicks"] * preset["fps"] / TICKS) / preset["fps"]
            )
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
                    or abs(media.duration / av.time_base - seconds)
                    > 1 / job["project"]["preset"]["fps"]
                    or video.width != job["project"]["preset"]["width"]
                    or video.height != job["project"]["preset"]["height"]
                    or video.average_rate != job["project"]["preset"]["fps"]
                ):
                    raise ValueError("Video xuất không đạt kiểm tra metadata.")
                frames = 0
                for frame in media.decode(video=0):
                    if frames % 30 == 0:
                        self.check(id)
                    frames += 1
                if frames != round(seconds * job["project"]["preset"]["fps"]):
                    raise ValueError("Video xuất thiếu frame.")
            self.check(id)
            target = contained(
                Path(job["grant"]) / f"{job['project']['id']}-{id}.mp4", job["grant"]
            )

            def published():
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

            self.publish_file(id, folder / "bounded.mp4", target, job["grant"], published)
        except InterruptedError:
            self.patch(id, status="cancelled", phase="cancelled", message="Đã hủy render.")
        except Exception as error:
            # Public errors never include raw exception paths, argv or private content.
            self.patch(
                id,
                status="failed",
                phase="failed",
                message="Tác vụ không hoàn tất. Dữ liệu project được giữ nguyên.",
            )
            folder = contained(self.store.root / "jobs" / id, self.store.root)
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "failure.json").write_text(
                json.dumps({"type": type(error).__name__, "message": str(error)}), encoding="utf-8"
            )

    def publish_file(self, id, source, target, grant, published=None):
        """Publish one owned stage atomically; discard incomplete copies on failure."""
        stage = contained(target.with_suffix(".stage"), grant)
        created = False
        try:
            with source.open("rb") as incoming, stage.open("xb") as output:
                created = True
                while chunk := incoming.read(1024 * 1024):
                    self.check(id)
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            with self.lock:
                self.check(id)
                contained(target, grant)
                os.replace(stage, target)
                if published:
                    published()
        finally:
            if created:
                contained(stage, grant).unlink(missing_ok=True)

    def temp_inventory(self):
        result = []
        with self.lock:
            for id, job in self.rows.items():
                if job["status"] not in TERMINAL:
                    continue
                folder = contained(self.store.root / "jobs" / id, self.store.root)
                entries = []
                for name in ("public", "bundle", "raw.mp4", "bounded.mp4", "audio.wav"):
                    path = contained(folder / name, folder)
                    if not path.exists():
                        continue
                    if path.is_dir():
                        files = [contained(f, folder) for f in path.rglob("*") if f.is_file()]
                        size = sum(f.stat().st_size for f in files)
                    else:
                        size = path.stat().st_size
                    entries.append({"name": name, "bytes": size})
                if entries:
                    result.append(
                        {"id": id, "bytes": sum(e["bytes"] for e in entries), "entries": entries}
                    )
        return result

    def clean_temp(self, ids):
        if (
            not isinstance(ids, list)
            or len(ids) > 1000
            or any(not isinstance(id, str) for id in ids)
        ):
            raise ValueError("Danh sách job không hợp lệ.")
        with self.lock:
            permitted = {r["id"]: r for r in self.temp_inventory()}
            if any(id not in permitted for id in ids):
                raise ValueError("Chỉ dọn temp của job đã kết thúc.")
            for id in ids:
                folder = contained(self.store.root / "jobs" / id, self.store.root)
                for entry in permitted[id]["entries"]:
                    path = contained(folder / entry["name"], folder)
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
            return {"deletedJobs": len(ids), "sourceAssetsPreserved": True}

    def shutdown(self):
        self.stopping = True
        self.pool.shutdown(wait=True, cancel_futures=True)
