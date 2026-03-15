"""
batch_count_videos.py
---------------------
Processes every .mp4 in the records/ folder with YOLOv8 person detection,
saves annotated videos to counted/ as MP4 files (H.264 via mp4v codec),
and writes people_counts.json with a per-second count list for each video.

Usage:
    python batch_count_videos.py

Output:
    counted/<original_name>_counted.mp4   – annotated video (endless-loop ready)
    counted/people_counts.json            – per-second queue counts per lift
"""

import os
import json
import cv2
import numpy as np
from pathlib import Path
from collections import deque
from ultralytics import YOLO
import supervision as sv
import shutil # Added for copying processed video files

# ──────────────────────────────────────────────────────────────────────────────
# Lift definitions – video assignment is done here in order.
# Videos are sorted alphabetically from records/ and assigned round-robin.
# ──────────────────────────────────────────────────────────────────────────────
    # New set of 19 coordinates provided by the user (W=2623, H=759)
    # We convert them to percentages here. 
LIFTS = [
    {"id": "L1",  "name": "Lift 1",  "x_pct": 19.82, "y_pct": 79.45},
    {"id": "L2",  "name": "Lift 2",  "x_pct": 14.11, "y_pct": 73.78},
    {"id": "L3",  "name": "Lift 3",  "x_pct": 28.59, "y_pct": 59.29},
    {"id": "L4",  "name": "Lift 4",  "x_pct": 34.31, "y_pct": 54.02},
    {"id": "L5",  "name": "Lift 5",  "x_pct": 37.36, "y_pct": 55.34},
    {"id": "L6",  "name": "Lift 6",  "x_pct": 43.08, "y_pct": 59.29},
    {"id": "L7",  "name": "Lift 7",  "x_pct": 44.61, "y_pct": 57.97},
    {"id": "L8",  "name": "Lift 8",  "x_pct": 45.75, "y_pct": 46.11},
    {"id": "L9",  "name": "Lift 9",  "x_pct": 50.71, "y_pct": 56.65},
    {"id": "L10", "name": "Lift 10", "x_pct": 54.14, "y_pct": 55.34},
    {"id": "L11", "name": "Lift 11", "x_pct": 64.05, "y_pct": 72.46},
    {"id": "L12", "name": "Lift 12", "x_pct": 66.72, "y_pct": 65.88},
    {"id": "L13", "name": "Lift 13", "x_pct": 68.62, "y_pct": 60.61},
    {"id": "L14", "name": "Lift 14", "x_pct": 68.62, "y_pct": 47.43},
    {"id": "L15", "name": "Lift 15", "x_pct": 72.44, "y_pct": 51.38},
    {"id": "L16", "name": "Lift 16", "x_pct": 75.87, "y_pct": 60.61},
    {"id": "L17", "name": "Lift 17", "x_pct": 79.30, "y_pct": 73.78},
    {"id": "L18", "name": "Lift 18", "x_pct": 78.92, "y_pct": 75.10},
    {"id": "L19", "name": "Lift 19", "x_pct": 83.87, "y_pct": 65.88}
]

RECORDS_DIR = Path("records")
COUNTED_DIR = Path("counted")
COUNTED_DIR.mkdir(exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def get_queue_zone(frame_shape):
    h, w = frame_shape[:2]
    polygon = np.array([
        [0, h // 2],
        [w, h // 2],
        [w, h],
        [0, h],
    ])
    return sv.PolygonZone(polygon=polygon)


import subprocess

def compress_video(temp_path: Path, final_path: Path):
    """
    Use FFmpeg to compress the video to H.264 (AVC) for Android.
    Scales to 480p height to keep file sizes very small.
    """
    print(f"  --> Compressing & Scaling to 480p...")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(temp_path),
        "-c:v", "libx264",
        "-crf", "28",           # Constant Rate Factor (23 is default, 28 is high compression)
        "-preset", "faster",
        "-pix_fmt", "yuv420p",  # Required for Android/ExoPlayer compatibility
        "-vf", "scale=-2:480",  # Scale to 480px height, auto width (divisible by 2)
        "-an",                  # Remove audio (saves space)
        str(final_path)
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"  ⚠  FFmpeg failed: {e.stderr.decode()}")
        # Fallback: just move the temp file to final if compression fails
        shutil.move(str(temp_path), str(final_path))

def process_video(model, input_path: Path, output_path: Path) -> list[int]:
    """
    Run YOLO person counting on input_path, write annotated video to temp, 
    then compress via FFmpeg to output_path.
    Returns a list of per-second people counts.
    """
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        print(f"  ⚠  Could not open {input_path}, skipping.")
        return [0]

    fps = max(1, int(cap.get(cv2.CAP_PROP_FPS)))
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Save a temporary lightly-compressed file first
    temp_path = output_path.with_name(f"temp_{output_path.name}")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(temp_path), fourcc, fps, (width, height))

    zone           = get_queue_zone((height, width))
    zone_annotator = sv.PolygonZoneAnnotator(zone=zone, color=sv.Color.RED)
    box_annotator  = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()
    tracker        = sv.ByteTrack(lost_track_buffer=5 * max(1, fps // 3), frame_rate=fps)
    queue_history  = deque(maxlen=max(1, fps))
    
    frame_count      = 0
    detections       = sv.Detections.empty()
    people_in_queue  = 0
    counts_per_second: list[int] = []
    current_second   = -1

    while True:
        ret, frame = cap.read()
        if not ret: break

        if frame_count % 3 == 0:
            results    = model(frame, classes=0, verbose=False)[0]
            detections = sv.Detections.from_ultralytics(results)
            detections = tracker.update_with_detections(detections)
            zone_mask       = zone.trigger(detections=detections)
            people_in_queue = len(detections[zone_mask])

        queue_history.append(people_in_queue)
        smoothed = sum(queue_history) // len(queue_history) if queue_history else 0

        second = frame_count // fps
        if second != current_second:
            current_second = second
            counts_per_second.append(smoothed)

        annotated = box_annotator.annotate(scene=frame.copy(), detections=detections)
        annotated = zone_annotator.annotate(scene=annotated)

        if detections.tracker_id is not None:
            labels = [f"ID {tid}" for tid in detections.tracker_id]
        else:
            labels = [f"P{i}" for i in range(len(detections))]
        label_annotator.annotate(scene=annotated, detections=detections, labels=labels)

        colour = (0, 200, 0) if smoothed <= 5 else ((0, 200, 255) if smoothed <= 12 else (0, 0, 220))
        cv2.putText(annotated, f"Queue: {smoothed}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.8, colour, 3)

        out.write(annotated)
        frame_count += 1

    cap.release()
    out.release()

    # Now compress with FFmpeg for high efficiency
    compress_video(temp_path, output_path)
    
    # Clean up temp file
    if temp_path.exists():
        temp_path.unlink()

    return counts_per_second if counts_per_second else [0]



# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("Loading YOLOv8n model …")
    model = YOLO("yolov8n.pt")

    # Collect and sort all source videos
    video_files = sorted(
        p for p in RECORDS_DIR.iterdir()
        if p.suffix.lower() in {".mp4", ".avi", ".mov"}
    )

    if not video_files:
        print("No videos found in records/ – exiting.")
        return

    print(f"Found {len(video_files)} video(s). {len(LIFTS)} lifts defined.")
    print()

    lifts_output    = []
    processed_cache = {}    # maps src_video.name -> (counts_per_second, first_output_name)

    # ──────────────────────────────────────────────────────────────────────────
    # Resume Logic: Load existing JSON to prepopulate cache
    # ──────────────────────────────────────────────────────────────────────────
    json_path = COUNTED_DIR / "people_counts.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                for i, entry in enumerate(old_data.get("lifts", [])):
                    # We use the video field to map back to source if possible, 
                    # but simple mapping is easier: map the original video name to its counts.
                    # Since we don't store the original name in JSON, we'll infer it 
                    # from the first 14 assignments if they exist.
                    if i < len(LIFTS): # Only consider entries up to the number of defined lifts
                        # Determine the original source video for this lift assignment
                        src_video_idx = i % len(video_files)
                        src_video_name = video_files[src_video_idx].name
                        
                        # If this source video hasn't been cached yet, add it
                        if src_video_name not in processed_cache:
                            processed_cache[src_video_name] = (entry["counts_per_second"], entry["video"])
            print(f"Loaded existing metadata from {json_path}")
        except Exception as e:
            print(f"Could not load existing JSON for resume: {e}")

    for i, lift in enumerate(LIFTS):
        src_video = video_files[i % len(video_files)]
        out_name  = f"lift_{lift['id']}_counted.mp4"
        out_path  = COUNTED_DIR / out_name

        # SKIP condition: cache has the counts AND the file is already small (compressed)
        if src_video.name in processed_cache:
             reuse = True
        elif out_path.exists() and out_path.stat().st_size < 6 * 1024 * 1024:
             # If the file exists and is small, it was likely processed in a previous interrupted run
             # We still need the 'counts_per_second' for the JSON.
             # We can try to find them in the old_data if we loaded it.
             reuse = False # For now, let's just re-process if not in memory cache to be safe
        else:
             reuse = False

        if reuse or src_video.name in processed_cache:
            # Reuse existing results
            cached_counts, cached_out_name = processed_cache[src_video.name]
            print(f"[{i+1}/{len(LIFTS)}] Lift {lift['id']} ← {src_video.name} (REUSING CACHE)")
            
            if not out_path.exists():
                shutil.copy(COUNTED_DIR / cached_out_name, out_path)
            
            counts_per_second = cached_counts
        else:
            # Process for the first time
            print(f"[{i+1}/{len(LIFTS)}] Lift {lift['id']} ← {src_video.name} (PROCESSING)")
            counts_per_second = process_video(model, src_video, out_path)
            processed_cache[src_video.name] = (counts_per_second, out_name)

            # Update JSON partially after each new video is processed for safety
            temp_list = lifts_output + [{
                "id": lift["id"], "name": lift["name"], "x_pct": lift["x_pct"],
                "y_pct": lift["y_pct"], "video": out_name, "counts_per_second": counts_per_second
            }]
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({"lifts": temp_list}, f, indent=2, ensure_ascii=False)

        avg = sum(counts_per_second) // len(counts_per_second) if counts_per_second else 0
        print(f"         {len(counts_per_second)}s of counts, avg={avg}")
        print()

        lifts_output.append({
            "id":                lift["id"],
            "name":              lift["name"],
            "x_pct":             lift["x_pct"],
            "y_pct":             lift["y_pct"],
            "video":             out_name,
            "counts_per_second": counts_per_second,   # ← live per-second data
        })

    # Write JSON
    json_path = COUNTED_DIR / "people_counts.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"lifts": lifts_output}, f, indent=2, ensure_ascii=False)

    print(f"✅  Done! Annotated videos saved to counted/")
    print(f"✅  people_counts.json written to {json_path}")
    print()
    print("Summary:")
    for entry in lifts_output:
        avg = sum(entry["counts_per_second"]) // len(entry["counts_per_second"])
        colour = "🟢" if avg <= 5 else ("🟡" if avg <= 12 else "🔴")
        print(f"  Lift {entry['id']:2s}  {colour}  avg={avg:2d}  {len(entry['counts_per_second'])}s  → {entry['video']}")


if __name__ == "__main__":
    main()
