"""Video Recording and MP4 Export Pipeline for Grain of Doubt using ffmpeg.

Directly pipes indexed Pyxel screen frames (pal8 format) to ffmpeg for zero-overhead,
lossless, hardware-efficient 600x800 @ 30 FPS MP4 video encoding.
"""
import atexit
import os
import shutil
import subprocess
from typing import Optional


class VideoRecorder:
    def __init__(self, output_path: str = "borrowed_time_bot.mp4", width: int = 600, height: int = 800, fps: int = 30):
        self.base_output_path = output_path
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        self.proc: Optional[subprocess.Popen] = None
        self.palette_header: Optional[bytes] = None
        self.frames_recorded: int = 0
        self.is_recording: bool = False
        atexit.register(self.stop)

    def _has_ffmpeg(self) -> bool:
        return shutil.which("ffmpeg") is not None

    def _build_palette(self, pyxel_module) -> bytes:
        pal = bytearray(1024)
        colors = list(pyxel_module.colors)
        for i, c in enumerate(colors):
            if i >= 256:
                break
            pal[i * 4] = c & 0xFF
            pal[i * 4 + 1] = (c >> 8) & 0xFF
            pal[i * 4 + 2] = (c >> 16) & 0xFF
            pal[i * 4 + 3] = 0xFF
        return bytes(pal)

    @staticmethod
    def _resolve_unique_filename(base_path: str) -> str:
        """Ensure file does not overwrite existing recordings by incrementing _NNN suffix."""
        if not os.path.exists(base_path):
            return base_path
        name, ext = os.path.splitext(base_path)
        idx = 1
        while True:
            candidate = f"{name}_{idx:03d}{ext}"
            if not os.path.exists(candidate):
                return candidate
            idx += 1

    def start(self, pyxel_module=None, filename: Optional[str] = None) -> bool:
        if self.is_recording:
            return True
        if not self._has_ffmpeg():
            print("[VideoRecorder] Warning: ffmpeg not found on system PATH. Cannot record MP4.")
            return False

        target_base = filename or self.base_output_path
        self.output_path = self._resolve_unique_filename(target_base)

        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{self.width}x{self.height}",
            "-pix_fmt", "pal8",
            "-r", str(self.fps),
            "-i", "-",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            self.output_path
        ]

        try:
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
            if pyxel_module is not None:
                self.palette_header = self._build_palette(pyxel_module)
            self.is_recording = True
            self.frames_recorded = 0
            print(f"[VideoRecorder] Recording started -> {self.output_path}")
            return True
        except Exception as e:
            print(f"[VideoRecorder] Failed to launch ffmpeg: {e}")
            self.proc = None
            self.is_recording = False
            return False

    def record_frame(self, pyxel_module):
        if not self.is_recording or self.proc is None or self.proc.stdin is None:
            return

        try:
            if self.palette_header is None:
                self.palette_header = self._build_palette(pyxel_module)

            screen_bytes = bytes(pyxel_module.screen.data_ptr())
            frame_payload = self.palette_header + screen_bytes
            self.proc.stdin.write(frame_payload)
            self.frames_recorded += 1
        except (BrokenPipeError, OSError):
            self.stop()

    def stop(self):
        if not self.is_recording or self.proc is None:
            return

        self.is_recording = False
        try:
            if self.proc.stdin:
                self.proc.stdin.close()
            self.proc.wait(timeout=5)
            duration = self.frames_recorded / float(self.fps)
            size_kb = os.path.getsize(self.output_path) / 1024.0 if os.path.exists(self.output_path) else 0
            print(f"[VideoRecorder] Exported: {self.output_path} ({self.frames_recorded} frames, {duration:.1f}s, {size_kb:.1f} KB)")
        except Exception as e:
            print(f"[VideoRecorder] Error stopping ffmpeg: {e}")
        finally:
            self.proc = None

    def toggle(self, pyxel_module=None) -> bool:
        if self.is_recording:
            self.stop()
            return False
        else:
            return self.start(pyxel_module)
