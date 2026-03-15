"""
copy_assets.py
--------------
Run this AFTER batch_count_videos.py to copy the annotated videos and
people_counts.json from counted/ into the Android app assets so Android
Studio / gradlew can bundle them into the APK.

Usage:
    python copy_assets.py
"""

import shutil
from pathlib import Path

COUNTED_DIR   = Path("counted")
ASSETS_VIDEOS = Path("android_app/app/src/main/assets/videos")

ASSETS_VIDEOS.mkdir(parents=True, exist_ok=True)

# Copy every .mp4 from counted/ into assets/videos/
copied = 0
for mp4 in COUNTED_DIR.glob("*.mp4"):
    dest = ASSETS_VIDEOS / mp4.name
    shutil.copy2(mp4, dest)
    print(f"  Copied  {mp4.name} -> {dest}")
    copied += 1

# Copy people_counts.json
json_src = COUNTED_DIR / "people_counts.json"
if json_src.exists():
    shutil.copy2(json_src, ASSETS_VIDEOS / "people_counts.json")
    print(f"  Copied  people_counts.json -> assets/videos/")
else:
    print("  ⚠  counted/people_counts.json not found – run batch_count_videos.py first!")

# Copy map.jpg from root to assets
map_src = Path("map.jpg")
if map_src.exists():
    shutil.copy2(map_src, Path("android_app/app/src/main/assets/map.jpg"))
    print(f"  Copied  map.jpg -> android_app/app/src/main/assets/map.jpg")
else:
    print("  ⚠  map.jpg not found in root directory!")

print()
print(f"DONE. {copied} video(s) copied to {ASSETS_VIDEOS}")
print("   You can now build the APK:")
print("   cd android_app && gradlew.bat assembleDebug")
