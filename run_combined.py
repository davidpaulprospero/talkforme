"""Run both listener and responder modules together."""

import subprocess
import sys
import signal
from pathlib import Path

# Get the directory containing this script
script_dir = Path(__file__).parent


class CombinedRunner:
    """Runs listener and responder modules with piped communication."""

    def __init__(self):
        """Initialize combined runner."""
        self.listener_process = None
        self.responder_process = None
        self.running = False

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\nShutting down...")
        self.stop()
        sys.exit(0)

    def start(self):
        """Start both listener and responder processes."""
        print("="*60)
        print("Talk For Me - Combined Listener & Responder")
        print("="*60)
        print("\nStarting listener and responder...")
        print("Press Ctrl+C to stop\n")

        try:
            # Start responder first (it reads from stdin)
            self.responder_process = subprocess.Popen(
                [sys.executable, str(script_dir / "responder.py")],
                stdin=subprocess.PIPE,
                stdout=sys.stdout,
                stderr=sys.stderr,
                text=True,
                bufsize=1  # Line buffered
            )

            # Start listener and pipe its output to responder
            self.listener_process = subprocess.Popen(
                [sys.executable, str(script_dir / "listener.py")],
                stdout=self.responder_process.stdin,
                stderr=sys.stderr,
                text=True,
                bufsize=1  # Line buffered
            )

            self.running = True

            # Wait for processes to finish
            self.listener_process.wait()

        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            print(f"Error: {e}")
            self.stop()

    def stop(self):
        """Stop both processes."""
        if not self.running:
            return

        self.running = False

        if self.listener_process:
            self.listener_process.terminate()
            try:
                self.listener_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.listener_process.kill()

        if self.responder_process:
            self.responder_process.terminate()
            try:
                self.responder_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.responder_process.kill()

        print("Stopped.")


def main():
    """Main entry point."""
    runner = CombinedRunner()
    runner.start()


if __name__ == "__main__":
    main()
