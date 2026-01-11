# Attention
# This script was created by using ai


import argparse
import json
import os
import subprocess
import numpy as np
import random
import sys
import shutil
from pathlib import Path
import time
import re

# Define script directory
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_PATH = SCRIPT_DIR / "video_config.json"

DEFAULT_CONFIG = {
    "width": 52,
    "height": 39,
    "fps": 60,
    "frames_per_block": 16,
    "output_dir": str(SCRIPT_DIR / "out"),
    "fileType": "msvc",
    "version": 1,
    "id": None
}

def load_or_create_config(recreate_id=False):
    """Loads config from script directory or creates a new one"""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)

            # Update config to current version
            for key, default_value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = default_value

            # Validate config
            if config["width"] <= 0 or config["height"] <= 0 or config["fps"] <= 0 or config["frames_per_block"] <= 0:
                print("Invalid config parameters. Using default values.")
                config.update(DEFAULT_CONFIG)

            # Regenerate ID if needed
            old_id = config.get("id")
            if recreate_id or old_id is None:
                config["id"] = generate_id()
                if recreate_id and old_id is not None:
                    print(f"ID regenerated: {old_id} → {config['id']}")

            with open(CONFIG_PATH, 'w') as f:
                json.dump(config, f, indent=2)
            return config

        except Exception as e:
            print(f"Error reading config: {e}. Creating new config.", file=sys.stderr)

    # Create new config
    config = DEFAULT_CONFIG.copy()
    config["id"] = generate_id()
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"New config created: {CONFIG_PATH}")
    return config

def generate_id():
    """Generates a random 16-bit ID in hex format"""
    return f"{random.randint(0, 0xFFFFFFFF):08x}"

def process_frame_numpy(frame, width, height):
    """Vectorized frame processing - restored from working version"""
    # Extract channels
    r = frame[:, :, 0].astype(np.float32)
    g = frame[:, :, 1].astype(np.float32)
    b = frame[:, :, 2].astype(np.float32)

    # Vectorized transformation: 35 + (value/255)*91
    r_vals = np.floor(35 + (r / 255.0) * 91).astype(np.uint8)
    g_vals = np.floor(35 + (g / 255.0) * 91).astype(np.uint8)
    b_vals = np.floor(35 + (b / 255.0) * 91).astype(np.uint8)

    # Clamp to 35-126 range
    r_vals = np.clip(r_vals, 35, 126)
    g_vals = np.clip(g_vals, 35, 126)
    b_vals = np.clip(b_vals, 35, 126)

    # I did this to avoid a line break (\n) in the string
    r_vals[r_vals == 92] = 91
    g_vals[g_vals == 92] = 91
    b_vals[b_vals == 92] = 91


    # Create strings for each channel
    r_str = ''.join(chr(int(val)) for val in r_vals.flatten())
    g_str = ''.join(chr(int(val)) for val in g_vals.flatten())
    b_str = ''.join(chr(int(val)) for val in b_vals.flatten())

    return r_str, g_str, b_str

def escape_mlog_value(text):
    """Escapes quotes and backslashes for mlog values - restored from working version"""
    return text.replace('\\', '\\\\').replace('"', '\\"')

def get_media_duration(input_path):
    """Gets media file duration in seconds"""
    probe_cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_path
    ]

    try:
        result = subprocess.run(
            probe_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        duration = float(result.stdout.strip())
        return duration
    except (subprocess.CalledProcessError, ValueError, Exception) as e:
        print(f"Warning: failed to determine duration: {e}")
        return None

def get_frame_count(input_path):
    """Gets exact frame count in video - improved version"""
    probe_cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-count_frames',
        '-show_entries', 'stream=nb_read_frames',
        '-of', 'csv=p=0',
        input_path
    ]

    try:
        result = subprocess.run(
            probe_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        frame_count = int(result.stdout.strip())
        return frame_count

    except (subprocess.CalledProcessError, ValueError, Exception) as e:
        print(f"Warning: failed to determine frame count: {e}")
        return None

def check_ffmpeg_installed():
    """Checks if ffmpeg and ffprobe are in PATH"""
    ffmpeg_path = shutil.which('ffmpeg')
    ffprobe_path = shutil.which('ffprobe')

    if not ffmpeg_path:
        print("Error: ffmpeg not found in PATH. Please install ffmpeg.", file=sys.stderr)
        sys.exit(1)

    if not ffprobe_path:
        print("Error: ffprobe not found in PATH. Please install ffmpeg.", file=sys.stderr)
        sys.exit(1)

    print(f"ffmpeg and ffprobe found: {ffmpeg_path}, {ffprobe_path}")

def run_ffmpeg_with_progress(input_path, output_path, width, height, fps):
    """Runs FFmpeg with progress display"""
    duration = get_media_duration(input_path)
    if duration is None:
        print("Failed to determine video duration. Progress will not be displayed.")

    ffmpeg_cmd = [
        "ffmpeg",
        "-i", input_path,
        "-vf", f"scale={width}:{height}:flags=neighbor,setsar=1/1",
        "-c:v", "ffv1",
        "-r", str(fps),
        output_path,
        "-y",
        "-loglevel", "info"
    ]

    print(f"Starting FFmpeg: {' '.join(ffmpeg_cmd)}")

    process = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1
    )

    last_update = time.time()
    update_interval = 0.5
    current_time = 0.0

    # Read stderr for progress display
    while True:
        line = process.stderr.readline()
        if not line:
            break

        # Look for time information in format "time=00:00:01.23"
        time_match = re.search(r"time=(\d+):(\d+):(\d+)\.(\d+)", line)
        if time_match and duration is not None:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            seconds = int(time_match.group(3))
            ms = int(time_match.group(4))
            current_time = hours * 3600 + minutes * 60 + seconds + ms / 100.0

            # Calculate progress
            progress = min(100.0, current_time / duration * 100)
            current_time_str = time.strftime("%H:%M:%S", time.gmtime(current_time))

            # Update progress
            current_time_val = time.time()
            if current_time_val - last_update >= update_interval:
                sys.stdout.write(f"\rFFmpeg: [{progress:5.1f}%] Time: {current_time_str}/{time.strftime('%H:%M:%S', time.gmtime(duration))}")
                sys.stdout.flush()
                last_update = current_time_val

    # Wait for process completion
    process.wait()

    # Final update
    if duration is not None:
        sys.stdout.write(f"\rFFmpeg: [100.0%] Time: {time.strftime('%H:%M:%S', time.gmtime(duration))}/{time.strftime('%H:%M:%S', time.gmtime(duration))}")
        sys.stdout.flush()

    sys.stdout.write("\n")

    if process.returncode != 0:
        stderr_output = process.stderr.read()
        print(f"FFmpeg error: {stderr_output}", file=sys.stderr)
        sys.exit(1)

    return output_path

def extract_frames_from_processed_video(video_path, width, height, expected_frames=None):
    """Extracts frames from processed video - RESTORED FROM WORKING VERSION"""
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', video_path,
        '-f', 'rawvideo',
        '-pix_fmt', 'rgb24',
        '-vcodec', 'rawvideo',
        '-an', '-sn',
        '-loglevel', 'error',
        '-'
    ]

    try:
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        frame_size = width * height * 3  # RGB - 3 bytes per pixel
        frames = []
        frame_count = 0

        while True:
            raw_frame = process.stdout.read(frame_size)
            if not raw_frame:
                break

            if len(raw_frame) < frame_size:
                print(f"Incomplete frame #{frame_count}, skipping")
                continue

            # Critical fix: Ensure correct frame shape and channel order
            frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape((height, width, 3))
            frames.append(frame)
            frame_count += 1

            if frame_count % 100 == 0:
                if expected_frames and expected_frames > 0:
                    progress = min(100.0, (frame_count / expected_frames * 100))
                    sys.stdout.write(f"\rFrame extraction: [{progress:5.1f}%] ({frame_count}/{expected_frames})")
                else:
                    sys.stdout.write(f"\rFrame extraction: {frame_count} frames")
                sys.stdout.flush()

        process.wait()

        # Final progress update
        if expected_frames and expected_frames > 0:
            progress = min(100.0, (frame_count / expected_frames * 100))
            sys.stdout.write(f"\rFrame extraction: [{progress:5.1f}%] ({frame_count}/{expected_frames})")
        sys.stdout.write("\n")

        print(f"Frames loaded: {frame_count} ({width}x{height})")
        return frames

    except Exception as e:
        print(f"\nFrame extraction error: {e}", file=sys.stderr)
        try:
            process.terminate()
            process.wait(timeout=2.0)
        except:
            pass
        sys.exit(1)

def generate_mlog_files(frames, config, video_name):
    """Generates .mlog files by blocks with actual newlines - fixed version"""
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    frames_per_block = config["frames_per_block"]
    num_frames = len(frames)
    num_blocks = max(1, (num_frames + frames_per_block - 1) // frames_per_block)

    # Main file with block count
    with open(output_dir / "video_blocks.txt", "w") as f:
        f.write(str(num_blocks))

    print(f"\nCreating {num_blocks} blocks (frames per block: {frames_per_block})")

    last_update = time.time()
    update_interval = 0.1

    for block_idx in range(num_blocks):
        start_idx = block_idx * frames_per_block
        end_idx = min(start_idx + frames_per_block, num_frames)
        block_frames = frames[start_idx:end_idx]

        # Create block content with actual newlines
        lines = []

        # Metadata only for first block
        lines.append("set loaded 0")
        lines.append(f'set type "{config["fileType"]}"')
        lines.append(f'set id "{config["id"]}"')
        lines.append(f'set videoBlock {block_idx}')

        if block_idx == 0:
            lines.append(f'set iAmHeader 1')
            clean_name = video_name.replace('"', '')
            lines.append(f'set name "{escape_mlog_value(clean_name)}"')
            lines.append(f'set frames {num_frames}')
            lines.append(f'set fps {config["fps"]}')
            lines.append(f'set version {config["version"]}')

        if block_idx != 0:
            lines.append(f'set iAmHeader 0')

        # Process each frame in block
        for frame_idx_in_block, frame in enumerate(block_frames):
            r_str, g_str, b_str = process_frame_numpy(frame, config["width"], config["height"])
            # CRITICAL FIX: Apply escaping to channel data
            lines.append(f'set f{frame_idx_in_block}r "{(r_str)}"')
            lines.append(f'set f{frame_idx_in_block}g "{(g_str)}"')
            lines.append(f'set f{frame_idx_in_block}b "{(b_str)}"')

        lines.append("set loaded 1")
        lines.append("stop")

        # Save block with actual newlines
        block_path = output_dir / f"block_{block_idx}.mlog"
        with open(block_path, "w", encoding="ascii") as f:
            f.write("\n".join(lines))

        # Update progress only at specific intervals
        current_time = time.time()
        if current_time - last_update >= update_interval or block_idx == num_blocks - 1:
            progress = (block_idx + 1) / num_blocks * 100
            sys.stdout.write(f"\rGeneration: [{progress:5.1f}%] Block {block_idx+1}/{num_blocks}")
            sys.stdout.flush()
            last_update = current_time

    sys.stdout.write("\n")
    return num_blocks

def main():
    parser = argparse.ArgumentParser(description="Video to mlog converter")
    parser.add_argument("video_path", type=str, help="Path to source video")
    parser.add_argument('--regen-id', action='store_true', help='Regenerate ID in config')
    args = parser.parse_args()

    if not os.path.exists(args.video_path):
        print(f"File not found: {args.video_path}", file=sys.stderr)
        sys.exit(1)

    # Check ffmpeg and ffprobe availability
    check_ffmpeg_installed()

    # Load config with possible ID regeneration
    config = load_or_create_config(recreate_id=args.regen_id)
    width = config["width"]
    height = config["height"]
    fps = config["fps"]

    print(f"\nConfiguration:")
    print(f"   Resolution: {width}x{height}")
    print(f"   FPS: {fps}")
    print(f"   ID: {config['id']}")
    print(f"   Format version: {config['version']}")
    print(f"   Output: {Path(config['output_dir']).resolve()}\n")

    # Process video through FFmpeg with progress
    output_video = os.path.join(Path(config['output_dir']).resolve(), f"o{width}x{height}.mkv")
    run_ffmpeg_with_progress(args.video_path, output_video, width, height, fps)

    # Get frame count from the PROCESSED video (after ffmpeg conversion)
    print("\nGetting frame count from processed video...")
    expected_frames = get_frame_count(output_video)
    if expected_frames is None:
        print("Warning: Could not determine frame count from processed video. Will process all available frames.")
        expected_frames = 0
    else:
        print(f"Frames in processed video: {expected_frames}")

    # Extract frames from processed video - USING RESTORED WORKING FUNCTION
    print("\nExtracting frames from processed video...")
    frames = extract_frames_from_processed_video(output_video, width, height, expected_frames)

    # Generate mlog files
    print("\nGenerating mlog files...")
    video_name = Path(args.video_path).stem
    num_blocks = generate_mlog_files(frames, config, video_name)

    # Cleanup
    try:
        if os.path.exists(output_video):
            os.remove(output_video)
            print(f"\nTemporary file removed: {output_video}")
    except Exception as e:
        print(f"Failed to remove temporary file: {e}", file=sys.stderr)

    print(f"\nSuccessfully completed!")
    print(f"   Blocks created: {num_blocks}")
    print(f"   Files saved to: {Path(config['output_dir']).resolve()}")
    print(f"   Total frames processed: {len(frames)}")
    print(f"   Approximate playback time: {len(frames)/config['fps']:.1f} seconds")

if __name__ == "__main__":
    main()
