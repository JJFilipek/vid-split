# Vid Split

A lightweight helper that turns landscape MP4 videos into vertical TikTok-ready clips and slices them into shareable segments.

## Features

- Ensures every source video is converted or padded to a 9:16 frame before processing.
- Skips the first 30 seconds (configurable) and divides the remainder into any second segments.
- Uses FFmpeg/FFprobe and a thread pool to export each chunk as an `.mp4` into the `splitted/` folder.

## Prerequisites

- Python 3.8+
- FFmpeg suite available on your `PATH` (the script invokes both `ffmpeg` and `ffprobe`).

## Usage

1. Place your source `.mp4` files inside the `tosplit/` directory.
2. Adjust `CHUNK_SECONDS` and `SKIP_SECONDS` in `main.py` if you need different timings.
3. Run:
   ```bash
   python main.py
   ```
4. Collect your processed clips from the `splitted/` directory.

## How It Works

- Each file is first passed through `ensure_tiktok_format`, which crops or pads the frame to fit 9:16 while keeping audio untouched. You can skip crop.
- After determining video length with `get_duration`, the program subtracts the initial skip window and schedules chunking tasks in parallel via `ThreadPoolExecutor`.
- Every exported segment is named `segment_<randomid>_<index>.mp4`, making it easy to group clips from the same source.

## Configuration Tips

- Increase `CHUNK_SECONDS` for longer clips per segment or decrease it for shorter social-media bites.
- Set `SKIP_SECONDS` to 0 if you need to keep the full video.
- The auto-cropping tolerance (`abs(aspect_ratio - target_ratio) < 0.01`) can be tweaked if you encounter edge cases.

## Troubleshooting

- If you see FFmpeg errors, run the script once without redirecting stdout/stderr to inspect the full command output (remove the `DEVNULL` suppressors).
- Ensure `tosplit/` is not empty; otherwise, nothing will be processed.

## License

This project is distributed under the terms of the [APACHE License](LICENSE).
