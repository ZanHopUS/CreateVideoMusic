"""Compare real UI Player screenshots with independently decoded MP4 frames.

No NumPy/Pillow dependency; compact RGB buffers and tile errors. Thresholds are
fixture regression bounds, not perceptual/lyrics-quality acceptance.
"""

import argparse
import json
from pathlib import Path

import av
from av.video.reformatter import Interpolation

ROOT = Path(__file__).resolve().parents[1]


def rgb(frame):
    frame = frame.reformat(format="rgb24")
    plane = memoryview(frame.planes[0])
    stride = frame.planes[0].line_size
    return b"".join(plane[y * stride : y * stride + frame.width * 3] for y in range(frame.height))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    assert run.is_relative_to((ROOT / ".local/e2e").resolve())
    cases = json.loads((run / "preview-frame-cases.json").read_text(encoding="utf-8"))
    results = []
    for case in cases:
        screenshot = (run / case["screenshot"]).resolve()
        assert screenshot.is_relative_to(run)
        output = Path(case["output"]).resolve()
        assert output.is_relative_to((ROOT / ".local/evidence/s6").resolve())
        with av.open(str(screenshot)) as image:
            expected_frame = next(image.decode(video=0))
            width, height = expected_frame.width, expected_frame.height
            expected = rgb(expected_frame)
        with av.open(str(output)) as media:
            final = None
            for index, frame in enumerate(media.decode(video=0)):
                if index == case["frame"]:
                    final = frame
                    break
        if final is None:
            raise ValueError("Requested output frame missing")
        final = final.reformat(
            width=width, height=height, format="rgb24", interpolation=Interpolation.BILINEAR
        )
        actual = rgb(final)
        global_mae = sum(abs(a - b) for a, b in zip(expected, actual)) / len(expected)
        tiles = []
        for row in range(8):
            for column in range(6):
                errors = []
                for y in range(row * height // 8, (row + 1) * height // 8):
                    start = (y * width + column * width // 6) * 3
                    end = (y * width + (column + 1) * width // 6) * 3
                    errors.extend(
                        abs(a - b) for a, b in zip(expected[start:end], actual[start:end])
                    )
                tiles.append(sum(errors) / len(errors))
        ordered = sorted(tiles)
        p95 = ordered[45]
        passed = global_mae <= 8 and p95 <= 15
        results.append(
            {
                **case,
                "width": width,
                "height": height,
                "globalMeanAbsoluteError": global_mae,
                "tileP95MeanAbsoluteError": p95,
                "tileErrors": tiles,
                "passed": passed,
            }
        )
    report = {
        "allPassed": all(r["passed"] for r in results),
        "bounds": {"globalMAE": 8, "tileP95MAE": 15},
        "scope": "UI screenshot versus H.264 decoded and bilinearly resized frame; short generated fixtures, not human perceptual review",
        "cases": results,
    }
    (run / "preview-render-comparison.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "allPassed": report["allPassed"],
                "cases": len(results),
                "maxGlobalMAE": max(r["globalMeanAbsoluteError"] for r in results),
                "maxTileP95MAE": max(r["tileP95MeanAbsoluteError"] for r in results),
            }
        )
    )
    return 0 if report["allPassed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
