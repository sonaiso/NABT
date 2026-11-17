"""The external CLI retains exact source bytes and bounds reads before dispatch."""
import io
import unittest
from unittest.mock import patch

from tools import ntp as cli


class NTPCLI(unittest.TestCase):
    def invoke(self, action, raw):
        stream = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8", newline=None)
        output = io.StringIO()
        owner = patch.object(cli.gateway, "run", return_value={"status": "EXECUTED"})
        return stream, output, owner

    def test_stdin_preserves_carriage_return_and_utf8_source(self):
        source = "هَلْ كَانَ الْكَاتِبُ حَاضِرًا؟\r\n"
        stream, output, owner = self.invoke("read", source.encode())
        with stream, patch("sys.stdin", stream), patch("sys.stdout", output), \
                patch("sys.argv", ["ntp", "read"]), owner as run:
            self.assertEqual(cli.main(), 0)
            request = run.call_args.args[0]
        self.assertEqual(request["payload"]["input"]["text"].encode(), source.encode())
        self.assertEqual(request["payload"]["operation"], "think")

    def test_oversize_stdin_stops_after_one_byte_past_boundary(self):
        for action, limit in (("read", 8192), ("forward", 256)):
            with self.subTest(action=action):
                binary = io.BytesIO(b"x" * (limit + 10000))
                stream = io.TextIOWrapper(binary, encoding="utf-8")
                with patch("sys.stdin", stream), patch("sys.argv", ["ntp", action]), \
                        patch("sys.stderr", io.StringIO()), patch.object(cli.gateway, "run") as run:
                    with self.assertRaises(SystemExit) as error:
                        cli.main()
                    self.assertEqual(error.exception.code, 2)
                    self.assertEqual(binary.tell(), limit + 1)
                    run.assert_not_called()
                stream.close()

    def test_forward_accepts_exact_cell_byte_boundary_without_truncation(self):
        source = "كَ" * 64
        self.assertEqual(len(source.encode()), 256)
        stream, output, owner = self.invoke("forward", source.encode())
        with stream, patch("sys.stdin", stream), patch("sys.stdout", output), \
                patch("sys.argv", ["ntp", "forward"]), owner as run:
            self.assertEqual(cli.main(), 0)
            self.assertEqual(run.call_args.args[0]["payload"]["input"]["text"], source)

    def test_invalid_utf8_never_reaches_gateway(self):
        stream, output, owner = self.invoke("read", b"\xff")
        with stream, patch("sys.stdin", stream), patch("sys.stdout", output), \
                patch("sys.stderr", io.StringIO()), patch("sys.argv", ["ntp", "read"]), owner as run:
            with self.assertRaises(SystemExit) as error:
                cli.main()
            self.assertEqual(error.exception.code, 2)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
