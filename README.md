# QueueVision | Lift Queue Intelligence for Ski Areas

### 🚀 [View Live Landing Page](https://japark10.github.io/Ski_Queue_Demo)

## Project Overview
Developed as a personal project in my free time, **QueueVision** is a conceptual platform designed to optimize guest flow and operations at ski resorts. The system uses computer vision to provide real-time, high-accuracy lift queue observation, transforming raw visual data into live wait-time intelligence. I developed this concept and a functional Android prototype to demonstrate how targeted AI deployment can solve high-friction pain points in seasonal sports infrastructure.

## Key Features
- **AI Queue Observation**: Utilizes YOLOv8 person detection to monitor lift lines and estimate queue depth.
- **Live Wait-Time Intelligence**: Converts computer vision observations into rolling wait-time predictions for guests.
- **Interactive Prototype**: An Android mobile application that allows guests to view a resort map populated with live wait times at every lift.
- **Economic Optimization**: Built-in ROI modeling for ski area operators to measure the impact of improved mountain flow.

## Technology Stack
- **Backend/AI**: Python, YOLOv8 (Ultralytics), OpenCV, Supervision.
- **Mobile Prototype**: Android (Kotlin), ExoPlayer (Media3) for video processing, Custom Interactive Map UI.
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (Responsive landing page).
- **Automation**: Custom Python scripts for batch video processing and asset bundling.

## Repository Structure
- `android_app/`: Native Android prototype source code.
- `website/`: Landing page assets, styles, and scripts.
- `records/`: Sample video footage for the AI counting engine.
- `counted/`: AI-annotated output videos and data.
- `batch_count_videos.py`: The core AI processing pipeline.
- `queue_counter_demo.py`: Gradio-based desktop demo for the counter.
- `index.html`: Main landing page (GitHub Pages compatible).

---
*Note: This is a standalone conceptual prototype developed to explore the intersection of computer vision and resort operations.*
