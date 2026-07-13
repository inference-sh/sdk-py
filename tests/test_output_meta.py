"""Tests for output metadata helpers (probe_video, VideoMeta.from_file)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from inferencesh.models.output_meta import VideoMeta, probe_video


def _ffprobe_result(stdout: str, returncode: int = 0) -> MagicMock:
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    return result


class TestProbeVideo:
    def test_parses_video_stream_metadata(self):
        payload = {
            "streams": [
                {
                    "codec_type": "audio",
                    "width": 0,
                    "height": 0,
                },
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                    "nb_frames": "300",
                },
            ],
        }
        with patch("subprocess.run", return_value=_ffprobe_result(json.dumps(payload))):
            info = probe_video("/tmp/sample.mp4")

        assert info == {
            "width": 1920,
            "height": 1080,
            "fps": 30.0,
            "nb_frames": 300,
            "seconds": 10.0,
        }

    def test_seconds_uses_frame_count_over_fps_for_pricing_accuracy(self):
        """Duration must be nb_frames/fps, not container duration metadata."""
        payload = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1280,
                    "height": 720,
                    "r_frame_rate": "24/1",
                    "nb_frames": "73",
                },
            ],
        }
        with patch("subprocess.run", return_value=_ffprobe_result(json.dumps(payload))):
            info = probe_video("/tmp/clip.mp4")

        assert info["fps"] == 24.0
        assert info["nb_frames"] == 73
        assert info["seconds"] == pytest.approx(73 / 24)

    def test_returns_empty_dict_on_nonzero_exit(self):
        with patch("subprocess.run", return_value=_ffprobe_result("", returncode=1)):
            assert probe_video("/tmp/missing.mp4") == {}

    def test_returns_empty_dict_when_no_video_stream(self):
        payload = {"streams": [{"codec_type": "audio", "sample_rate": "44100"}]}
        with patch("subprocess.run", return_value=_ffprobe_result(json.dumps(payload))):
            assert probe_video("/tmp/audio_only.mp4") == {}

    def test_returns_empty_dict_on_subprocess_failure(self):
        with patch("subprocess.run", side_effect=FileNotFoundError("ffprobe")):
            assert probe_video("/tmp/sample.mp4") == {}

    def test_zero_fps_denominator_yields_zero_seconds(self):
        payload = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 640,
                    "height": 480,
                    "r_frame_rate": "0/0",
                    "nb_frames": "100",
                },
            ],
        }
        with patch("subprocess.run", return_value=_ffprobe_result(json.dumps(payload))):
            info = probe_video("/tmp/broken_fps.mp4")

        assert info["fps"] == 0.0
        assert info["seconds"] == 0.0

    def test_invokes_ffprobe_with_expected_args(self):
        with patch("subprocess.run", return_value=_ffprobe_result('{"streams":[]}')) as mock_run:
            probe_video("/videos/out.mp4")

        mock_run.assert_called_once_with(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "/videos/out.mp4"],
            capture_output=True,
            text=True,
            timeout=10,
        )


class TestVideoMetaFromFile:
    def test_populates_fields_from_probe(self):
        with patch(
            "inferencesh.models.output_meta.probe_video",
            return_value={
                "width": 1920,
                "height": 1080,
                "fps": 30.0,
                "nb_frames": 150,
                "seconds": 5.0,
            },
        ):
            meta = VideoMeta.from_file("/tmp/out.mp4")

        assert meta.width == 1920
        assert meta.height == 1080
        assert meta.fps == 30
        assert meta.seconds == 5.0
        assert meta.type == "video"

    def test_passes_through_extra_kwargs(self):
        with patch("inferencesh.models.output_meta.probe_video", return_value={"width": 1280, "height": 720, "fps": 24.0, "seconds": 2.0}):
            meta = VideoMeta.from_file(
                "/tmp/out.mp4",
                resolution="720p",
                resolution_mp=0.92,
                extra={"model": "kling"},
            )

        assert meta.resolution == "720p"
        assert meta.resolution_mp == 0.92
        assert meta.extra == {"model": "kling"}

    def test_defaults_when_probe_fails(self):
        with patch("inferencesh.models.output_meta.probe_video", return_value={}):
            meta = VideoMeta.from_file("/tmp/unreadable.mp4", resolution="1080p")

        assert meta.width == 0
        assert meta.height == 0
        assert meta.fps == 0
        assert meta.seconds == 0.0
        assert meta.resolution == "1080p"
