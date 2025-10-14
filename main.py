import os
import subprocess
import concurrent.futures
import math
import uuid

INPUT_DIR = "tosplit"
OUTPUT_DIR = "splitted"
CHUNK_SECONDS = 120  # segnemt lenght
SKIP_SECONDS = 30    # skip part of video

os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_resolution(filename):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )
    width, height = map(int, result.stdout.decode().strip().split(","))
    return width, height

def ensure_tiktok_format(input_path):
    width, height = get_resolution(input_path)
    aspect_ratio = height / width
    target_ratio = 16 / 9

    if abs(aspect_ratio - target_ratio) < 0.01:
        return input_path  # already 9:16

    new_path = input_path.replace(".mp4", "_cropped.mp4")

    if aspect_ratio < target_ratio:
        # too wide – crop sides
        new_width = int(height * 9 / 16)
        x_offset = (width - new_width) // 2
        vf_filter = f"crop={new_width}:{height}:{x_offset}:0"
    else:
        # too narrow – pad top/bottom
        new_height = int(width * 16 / 9)
        vf_filter = f"pad={width}:{new_height}:(ow-iw)/2:(oh-ih)/2"

    subprocess.run([
        "ffmpeg", "-i", input_path,
        "-vf", vf_filter,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
        "-c:a", "copy",
        new_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    os.remove(input_path)
    os.rename(new_path, input_path)

    return input_path

def get_duration(filename):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )
    return math.ceil(float(result.stdout.decode().strip()))

def cut_segment(input_path, index, start, duration, unique_id):
    output_file = os.path.join(OUTPUT_DIR, f"segment_{unique_id}_{index:03d}.mp4")
    subprocess.run([
        "ffmpeg",
        "-ss", str(start),
        "-i", input_path,
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-an",
        output_file
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def process_video(file_path):
    print(f"🎬 Processing: {os.path.basename(file_path)}")
    tiktok_ready_path = ensure_tiktok_format(file_path)
    unique_id = uuid.uuid4().hex[:8]

    total_duration = get_duration(tiktok_ready_path) - SKIP_SECONDS
    total_chunks = math.ceil(total_duration / CHUNK_SECONDS)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for i in range(total_chunks):
            start = SKIP_SECONDS + i * CHUNK_SECONDS
            duration = min(CHUNK_SECONDS, total_duration - i * CHUNK_SECONDS)
            futures.append(executor.submit(cut_segment, tiktok_ready_path, i, start, duration, unique_id))

        for future in futures:
            future.result()

    print(f"✅ Done: {os.path.basename(file_path)}")

if __name__ == "__main__":
    for file in os.listdir(INPUT_DIR):
        if file.endswith(".mp4"):
            full_path = os.path.join(INPUT_DIR, file)
            process_video(full_path)
