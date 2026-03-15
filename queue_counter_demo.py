import os
import gradio as gr
import cv2
from ultralytics import YOLO
import supervision as sv
from pathlib import Path
from collections import deque

# Load the tiny fast model (open source)
model = YOLO("yolov8n.pt")  # downloads automatically first time
import numpy as np

def get_queue_zone(frame_shape):
    h, w = frame_shape[:2]
    polygon = np.array([
        [0, h//2],
        [w, h//2],
        [w, h],
        [0, h]
    ])
    return sv.PolygonZone(polygon=polygon)


def process_video(video_path: str):
    video_full_path = os.path.join("records", video_path)
    cap = cv2.VideoCapture(video_full_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_full_path}")
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    output_path = "output/" + Path(video_path).stem + "_counted.avi"

    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    zone = get_queue_zone((height, width))
    zone_annotator = sv.PolygonZoneAnnotator(zone=zone, color=sv.Color.RED)
    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()
    
    # 5-second buffer for ByteTrack (number of track updates, 1 update per 3 frames)
    tracker = sv.ByteTrack(lost_track_buffer=5 * max(1, fps // 3), frame_rate=fps)
    queue_history = deque(maxlen=max(1, 5 * fps))
    
    total_people = 0
    frame_count = 0
    
    detections = sv.Detections.empty()
    people_in_queue = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Run YOLO every 3rd frame for speed on laptop
        if frame_count % 3 == 0:
            results = model(frame, classes=0, verbose=False)[0]  # class 0 = person
            detections = sv.Detections.from_ultralytics(results)
            detections = tracker.update_with_detections(detections)
            
            # Count only in queue zone
            zone_mask = zone.trigger(detections=detections)
            people_in_queue = len(detections[zone_mask])
            total_people += people_in_queue
            
        queue_history.append(people_in_queue)
        smoothed_count = sum(queue_history) // len(queue_history) if queue_history else 0
        
        # Annotate
        annotated_frame = box_annotator.annotate(scene=frame.copy(), detections=detections)
        annotated_frame = zone_annotator.annotate(scene=annotated_frame)
        labels = [
            f"ID {tracker_id}" if tracker_id is not None else f"Person {i}"
            for i, tracker_id in enumerate(detections.tracker_id)
        ] if detections.tracker_id is not None else [f"Person {i}" for i in range(len(detections))]
        
        label_annotator.annotate(
            scene=annotated_frame,
            detections=detections,
            labels=labels
        )
        
        cv2.putText(annotated_frame, f"Queue count (5s avg): {smoothed_count}", 
                    (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        
        out.write(annotated_frame)
        frame_count += 1
    
    cap.release()
    out.release()
    
    avg_count = total_people // (frame_count // 3) if frame_count > 0 else 0
    return output_path, f"Average people in queue: {avg_count}"

# Gradio UI
def list_videos():
    return [f for f in os.listdir("records") if f.endswith((".mp4", ".mov", ".avi"))]

with gr.Blocks(title="Ski Lift Queue Counter Demo") as demo:
    gr.Markdown("# 🎿 Ski Lift Queue AI Counter (runs on your laptop)")
    gr.Markdown("Drop videos in the `records` folder → select → Process")
    
    video_dropdown = gr.Dropdown(choices=list_videos(), label="Choose video from records folder", interactive=True)
    refresh_btn = gr.Button("Refresh video list")
    
    process_btn = gr.Button("🚀 Process Video (YOLO counting)", variant="primary")
    
    output_video = gr.Video(label="Processed video with counts")
    count_text = gr.Textbox(label="Result")
    
    def refresh_list():
        return gr.Dropdown(choices=list_videos())
    
    refresh_btn.click(refresh_list, outputs=video_dropdown)
    
    process_btn.click(
        fn=process_video,
        inputs=video_dropdown,
        outputs=[output_video, count_text]
    )

demo.launch(share=False)  # opens in browser