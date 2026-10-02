"""Offline tests: python3 -m unittest discover -s tests -v"""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gen_voice", ROOT / "scripts/gen-voice.py")
voice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voice)


class FakeAPI(voice.GradioVoice):
    def __init__(self, names=None, event=b'event: complete\ndata: [{"path":"/tmp/result.wav"}]\n\n'):
        super().__init__("https://example.test")
        self.names = names or ["text", "instruct"]
        self.event = event
        self.calls = []

    def get_json(self, path, payload=None):
        self.calls.append((path, payload))
        if path == "/config":
            return {"version": "test", "api_prefix": "/gradio_api"}
        if path.endswith("/info"):
            return {"named_endpoints": {"/generate": {
                "parameters": [{"parameter_name": name} for name in self.names],
                "returns": [{"component": "Audio"}]}}}
        return {"event_id": "test-id"}

    def open(self, path, payload=None, timeout=None):
        if path.endswith("/test-id"):
            return io.BytesIO(self.event)
        return io.BytesIO(b"fake-audio-for-transport-test")


class VoiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.presets_path = ROOT / "voices.json"
        self.presets = json.loads(self.presets_path.read_text())

    def test_original_prompt_preserved(self):
        original = json.loads((ROOT / "audio/voice-preview/hello-world-soft-request.json").read_text())
        self.assertEqual(self.presets["red-error-soft"]["instruct"], original["data"][2])

    def test_two_and_three_parameter_apis(self):
        for names in (["text", "instruct"], ["text", "language", "instruct"],
                      ["text", "language", "voice_description"]):
            with self.subTest(names=names):
                api = FakeAPI(names)
                with contextlib.redirect_stderr(io.StringIO()):
                    result = api.synthesize("你好", "轻声", "Chinese", self.out / "raw")
                self.assertEqual(result["parameters"], names)
                expected = ["你好", "轻声"] if len(names) == 2 else ["你好", "Chinese", "轻声"]
                self.assertEqual(api.calls[-1][1], {"data": expected})

    def test_unknown_schema_fails_closed(self):
        with self.assertRaises(voice.VoiceError):
            FakeAPI(["text", "instruct", "unknown_required"]).discover()

    def test_fixed_speaker_routes_and_payload(self):
        api = FakeAPI(["text", "language", "speaker", "instruct", "model_size"])
        api.speaker = "Uncle_fu"
        with contextlib.redirect_stderr(io.StringIO()):
            api.synthesize("你好", "克制", "Chinese", self.out / "fixed")
        self.assertEqual(api.calls[-1][1], {"data": ["你好", "Chinese", "Uncle_fu", "克制", "1.7B"]})
        client = voice.GradioVoice("https://example.test", speaker="Uncle_fu")
        self.assertEqual(client.api_name, "generate_custom_voice")

    def test_approved_reuse_rejects_new_speaker(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(voice.main(["--reuse-approved", "--speaker", "Dylan", "--out", str(self.out / "reuse.wav")]), 1)

    def test_sse_heartbeat_then_complete(self):
        api = FakeAPI(event=b'event: heartbeat\ndata: null\n\nevent: complete\ndata: [{"path":"/tmp/a.wav"}]\n\n')
        with contextlib.redirect_stderr(io.StringIO()):
            api.synthesize("a", "b", "Chinese", self.out / "raw")
        self.assertTrue((self.out / "raw").is_file())

    def test_sse_error_and_incomplete_stream(self):
        for event in [b"event: error\ndata: null\n\n", b"event: heartbeat\ndata: null\n\n"]:
            with self.subTest(event=event), self.assertRaises(voice.VoiceError), contextlib.redirect_stderr(io.StringIO()):
                FakeAPI(event=event).synthesize("a", "b", "Chinese", self.out / "raw")
        self.assertFalse((self.out / "raw").exists())

    def test_reuse_exact_bytes_and_skip(self):
        job = voice.resolve_job(None, "red-error-soft", None, None, self.presets, reuse=True)
        client = FakeAPI()
        target = self.out / "reuse.wav"
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(voice.render(job, target, client, self.presets_path), "created")
            self.assertEqual(voice.render(job, target, client, self.presets_path), "skip")
        self.assertEqual(voice.digest(target), voice.digest(ROOT / job["approved_audio"]))
        self.assertEqual(client.calls, [])

    def test_existing_file_not_overwritten_and_corrupt_cache_rejected(self):
        job = voice.resolve_job(None, "red-error-soft", None, None, self.presets, reuse=True)
        target = self.out / "reuse.wav"
        target.write_bytes(b"keep-existing-file")
        with self.assertRaises(voice.VoiceError):
            voice.render(job, target, FakeAPI(), self.presets_path)
        self.assertEqual(target.read_bytes(), b"keep-existing-file")
        with contextlib.redirect_stdout(io.StringIO()):
            voice.render(job, target, FakeAPI(), self.presets_path, force=True)
        target.write_bytes(b"corrupted")
        with self.assertRaises(voice.VoiceError):
            voice.render(job, target, FakeAPI(), self.presets_path)

    def test_reuse_rejects_changed_text_or_instructions(self):
        for text, instruct in [("不同台词", None), ("你好，世界。", "另一种表演")]:
            with self.subTest(text=text), self.assertRaises(voice.VoiceError):
                voice.resolve_job(text, "red-error-soft", instruct, None, self.presets, reuse=True)

    def test_dry_run_has_no_files_or_network(self):
        job = voice.resolve_job("你好", "red-error-soft", None, None, self.presets)
        client = FakeAPI()
        with contextlib.redirect_stdout(io.StringIO()):
            voice.render(job, self.out / "nested/a.wav", client, self.presets_path, dry_run=True)
        self.assertEqual(list(self.out.iterdir()), [])
        self.assertEqual(client.calls, [])

    def test_transport_refuses_other_origin(self):
        client = voice.GradioVoice("https://example.test")
        with self.assertRaises(voice.VoiceError):
            client.open("https://other.test/file.wav")
        with self.assertRaises(voice.VoiceError):
            voice.GradioVoice("http://public.example.test")

    def test_batch_rejects_duplicate_and_path_traversal_ids(self):
        for rows in ["../escape\t你好\n", "same\t你好\nsame\t世界\n"]:
            tsv = self.out / "bad.tsv"
            tsv.write_text("id\ttext\n" + rows)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(voice.main(["--batch", str(tsv), "--dry-run"]), 1)

    def test_batch_selection_and_unknown_id(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(voice.main(["--batch", str(ROOT / "voices.example.tsv"), "sister_01", "--dry-run"]), 0)
        self.assertEqual(len(output.getvalue().splitlines()), 1)
        self.assertEqual(json.loads(output.getvalue())["request"]["text"], "到了发消息。")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(voice.main(["--batch", str(ROOT / "voices.example.tsv"), "missing", "--dry-run"]), 1)


if __name__ == "__main__":
    unittest.main()
