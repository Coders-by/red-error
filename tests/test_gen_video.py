import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("gen_video", Path(__file__).resolve().parents[1] / "scripts/gen-video.py")
video = importlib.util.module_from_spec(spec)
spec.loader.exec_module(video)


class VideoTaskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = self.root / "first.jpg"
        self.image.write_bytes(b"test image")
        self.prompt = self.root / "prompt.txt"
        self.prompt.write_text("Close the laptop gently.")
        self.key = self.root / "key"
        self.key.write_text("test-secret-key")
        self.output = self.root / "take.mp4"
        self.argv = ["gen-video.py", "--region", "china", "--image", str(self.image),
                     "--prompt-file", str(self.prompt), "--out", str(self.output),
                     "--key-file", str(self.key), "--wait", "0"]

    def run_cli(self, *extra):
        with patch("sys.argv", self.argv + list(extra)), patch.object(video.shutil, "which", return_value="tool"), contextlib.redirect_stdout(io.StringIO()):
            return video.main()

    def queue_task(self):
        with patch.object(video, "api", return_value={"task_id": "12345"}) as api:
            self.assertEqual(self.run_cli("--submit-only"), 0)
        self.assertEqual(api.call_args.kwargs["base"], "https://api.minimax.cn")
        return self.output.with_suffix(".json")

    def test_dry_run_does_not_read_key_write_files_or_call_api(self):
        self.key.unlink()
        with patch.object(video, "api") as api:
            self.assertEqual(self.run_cli("--dry-run"), 0)
            api.assert_not_called()
        self.assertFalse(self.output.with_suffix(".json").exists())

    def test_pending_task_resumes_without_another_post(self):
        self.queue_task()
        with patch.object(video, "api", return_value={"task": {"status": "running"}}) as api:
            self.assertEqual(self.run_cli(), 2)
        self.assertEqual(api.call_count, 1)
        self.assertEqual(api.call_args.args, ("/v2/query/video_generation/12345", "test-secret-key"))

    def test_changed_inputs_refuse_new_charge(self):
        self.queue_task()
        self.prompt.write_text("A different scene.")
        with patch.object(video, "api") as api, self.assertRaisesRegex(video.VideoError, "Inputs changed"):
            self.run_cli()
        api.assert_not_called()

    def test_ambiguous_submission_does_not_retry(self):
        with patch.object(video, "api", side_effect=TimeoutError("timeout")), self.assertRaises(TimeoutError):
            self.run_cli("--submit-only")
        with patch.object(video, "api") as api, self.assertRaisesRegex(video.VideoError, "no task ID"):
            self.run_cli("--submit-only")
        api.assert_not_called()

    def test_success_records_checksum_and_reuses_verified_video(self):
        meta = self.queue_task()

        def download(url, output):
            output.write_bytes(b"verified video")
            return {"streams": [{"codec_type": "video"}]}

        result = {"task": {"status": "succeeded", "content": {"url": "https://example.com/video.mp4"}}}
        with patch.object(video, "api", return_value=result), patch.object(video, "download", side_effect=download):
            self.assertEqual(self.run_cli(), 0)
        self.assertNotIn("test-secret-key", meta.read_text())
        self.assertIn("video_sha256", json.loads(meta.read_text()))
        with patch.object(video, "api") as api:
            self.assertEqual(self.run_cli(), 0)
            api.assert_not_called()
        self.output.write_bytes(b"corrupted")
        with self.assertRaisesRegex(video.VideoError, "checksum"):
            self.run_cli()

    def test_failed_task_does_not_download(self):
        self.queue_task()
        with patch.object(video, "api", return_value={"task": {"status": "failed"}}), patch.object(video, "download") as download, self.assertRaisesRegex(video.VideoError, "failed"):
            self.run_cli()
        download.assert_not_called()

    def test_api_redirect_refused(self):
        with self.assertRaisesRegex(video.VideoError, "redirect refused"):
            video.NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.com")


if __name__ == "__main__":
    unittest.main()
