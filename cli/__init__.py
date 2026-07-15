"""TungDevAI CLI — terminal coding assistant (local)."""

__all__ = ["main"]


def main() -> None:
    from cli.main import main as _main

    _main()
