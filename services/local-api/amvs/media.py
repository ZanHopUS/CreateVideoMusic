"""Probe managed local media; file names and client MIME never authorize reads."""

import av

from .domain import TICKS


def probe(path):
    with path.open("rb") as source:
        magic = source.read(16)
    image = magic.startswith(b"\x89PNG\r\n\x1a\n") or magic.startswith(b"\xff\xd8\xff")
    with av.open(str(path)) as container:
        videos = [
            s
            for s in container.streams.video
            if not (s.disposition & av.stream.Disposition.attached_pic)
        ]
        audios = list(container.streams.audio)
        if image:
            stream = container.streams.video[0]
            if stream.width * stream.height > 40_000_000:
                raise ValueError("Ảnh quá lớn (tối đa 40 megapixel).")
            next(container.decode(video=0))
            return {
                "kind": "image",
                "mime": "image/png" if magic.startswith(b"\x89PNG") else "image/jpeg",
                "extension": ".png" if magic.startswith(b"\x89PNG") else ".jpg",
                "width": stream.width,
                "height": stream.height,
                "durationTicks": 0,
                "codec": stream.codec_context.name,
            }
        if videos:
            stream = videos[0]
            if "mov" not in container.format.name or stream.codec_context.name != "h264":
                raise ValueError("Hiện hỗ trợ video MP4 H.264.")
            if stream.width * stream.height > 3840 * 2160:
                raise ValueError("Video nguồn vượt giới hạn 4K hiện tại.")
            duration = (
                float(container.duration / av.time_base)
                if container.duration
                else float(stream.duration * stream.time_base)
            )
            return {
                "kind": "video",
                "mime": "video/mp4",
                "extension": ".mp4",
                "width": stream.width,
                "height": stream.height,
                "durationTicks": int(duration * TICKS),
                "codec": stream.codec_context.name,
            }
        if not audios:
            raise ValueError("Không tìm thấy audio/video được hỗ trợ.")
        stream = audios[0]
        if not any(
            kind in container.format.name for kind in ("wav", "mp3", "mov")
        ) or stream.codec_context.name not in {"pcm_s16le", "mp3", "mp3float", "aac"}:
            raise ValueError("Hiện hỗ trợ WAV PCM16, MP3 và M4A AAC.")
        duration = (
            float(container.duration / av.time_base)
            if container.duration
            else float(stream.duration * stream.time_base)
        )
        ext = (
            ".wav"
            if "wav" in container.format.name
            else ".mp3"
            if "mp3" in container.format.name
            else ".m4a"
        )
        if not duration > 0:
            raise ValueError("Không đọc được thời lượng nhạc.")
        return {
            "kind": "audio",
            "mime": {".wav": "audio/wav", ".mp3": "audio/mpeg", ".m4a": "audio/mp4"}[ext],
            "extension": ext,
            "width": 0,
            "height": 0,
            "durationTicks": int(duration * TICKS),
            "codec": stream.codec_context.name,
        }
