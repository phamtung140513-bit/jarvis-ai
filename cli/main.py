"""
Jarvis CMD — chat AI ngay trong terminal (cùng model/config với bot Telegram).

Chạy:
  jarvis.cmd
  python -m cli
  python -m cli "viết hàm fibonacci"
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.coder import CoderAgent
from ai.debugger import DebuggerAgent
from ai.grok import GrokClient, GrokError
from ai.memory import ConversationMemory
from ai.modes import (
    MODES,
    get_user_mode,
    list_modes_text,
    merge_prompt_layers,
    set_user_mode,
)
from ai.pipeline import AgentPipeline
from ai.planner import PlannerAgent
from ai.reviewer import ReviewerAgent
from config import ensure_directories, get_settings
from database.sqlite import Database, set_db
from logging_setup import setup_logging
from plugins.files import FilesPlugin
from product.teachings import format_teachings_for_prompt, owner_teachings

# Local CLI identity (memory/teachings owner scope)
CLI_USER_ID = 0  # reserved for CLI session memory
BANNER = r"""
     _                  _         ____ __  __ ____
    | | __ _ _ ____   _(_)___    / ___|  \/  |  _ \
 _  | |/ _` | '__\ \ / / / __|  | |   | |\/| | | | |
| |_| | (_| | |   \ V /| \__ \  | |___| |  | | |_| |
 \___/ \__,_|_|    \_/ |_|___/   \____|_|  |_|____/

  Terminal agent — chat / plan / code / workspace
  Gõ /help · /exit để thoát
"""


def _print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))


async def _owner_system_extra(session_factory, settings, user_mode_prompt: str | None) -> str | None:
    try:
        async with session_factory() as session:
            rows = await owner_teachings(session, settings.owner_ids)
            teach = format_teachings_for_prompt(rows)
    except Exception:
        teach = None
    return merge_prompt_layers(mode_prompt=user_mode_prompt, teachings=teach)


async def run_repl(one_shot: str | None = None) -> int:
    settings = get_settings()
    ensure_directories(settings)
    setup_logging(settings.log_level, settings.logs_dir)

    db = Database(settings)
    await db.init()
    set_db(db)

    grok = GrokClient(settings)
    memory = ConversationMemory(settings)
    files = FilesPlugin(settings.workspace_dir)
    await files.setup()

    planner = PlannerAgent(grok)
    coder = CoderAgent(grok)
    reviewer = ReviewerAgent(grok)
    debugger = DebuggerAgent(grok)
    pipeline = AgentPipeline(grok)

    # Load owner teachings + hydrate CLI memory
    async with db.session() as session:
        await memory.ensure_hydrated(session, CLI_USER_ID)

    mode = get_user_mode(CLI_USER_ID)

    if not one_shot:
        _print(BANNER)
        _print(
            f"  provider={settings.provider}  model={grok.active_model}\n"
            f"  mode={mode.id}  workspace={settings.workspace_dir}\n"
        )

    async def chat_once(text: str) -> None:
        nonlocal mode
        mode = get_user_mode(CLI_USER_ID)
        system = await _owner_system_extra(
            db.session, settings, mode.prompt or None
        )
        async with db.session() as session:
            await memory.add_persist(session, CLI_USER_ID, "user", text)
        _print("\n… Jarvis đang nghĩ …\n")
        try:
            reply = await grok.chat(
                memory.get_messages(CLI_USER_ID),
                system=system,
                temperature=mode.temperature,
            )
        except GrokError as exc:
            _print(f"[AI error] {exc}")
            return
        async with db.session() as session:
            await memory.add_persist(session, CLI_USER_ID, "assistant", reply)
        _print(reply)
        _print("")

    async def handle_slash(line: str) -> bool:
        """Return True if handled (including exit)."""
        nonlocal mode
        parts = line.strip().split(maxsplit=1)
        cmd = parts[0].lower().lstrip("/")
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd in {"exit", "quit", "q"}:
            _print("Bye.")
            return True

        if cmd in {"help", "h", "?"}:
            _print(
                """
Lệnh CLI:
  /help              trợ giúp
  /status            model, mode, memory, workspace
  /mode [id]         default|coder|security|sales|research
  /clear             xóa memory CLI
  /plan <task>       planner agent
  /code <spec>       coder agent
  /review <code>     reviewer
  /debug <error>     debugger
  /build <task>      plan→code→review
  /ls [path]         list workspace
  /read <file>       đọc file trong workspace/
  /write <file>      ghi file (dòng sau, kết thúc bằng dòng: ###END)
  /pwd               đường dẫn workspace
  /exit              thoát

Chat thường: gõ câu hỏi rồi Enter (không cần /).
"""
            )
            return False

        if cmd == "status":
            n = memory.snapshot(CLI_USER_ID)
            mode = get_user_mode(CLI_USER_ID)
            _print(
                f"provider={settings.provider}\n"
                f"model={grok.active_model}\n"
                f"mode={mode.id} ({mode.name})\n"
                f"memory={n}/{settings.max_history_messages}\n"
                f"workspace={settings.workspace_dir}"
            )
            return False

        if cmd == "mode":
            if not arg:
                mode = get_user_mode(CLI_USER_ID)
                _print(f"Mode: {mode.id}\n\n{list_modes_text()}")
                return False
            if arg not in MODES:
                _print(f"Không có mode '{arg}'.\n{list_modes_text()}")
                return False
            mode = set_user_mode(CLI_USER_ID, arg)
            _print(f"OK mode → {mode.id} ({mode.name})")
            return False

        if cmd == "clear":
            async with db.session() as session:
                n = await memory.clear_persist(session, CLI_USER_ID)
            _print(f"Đã xóa memory CLI ({n} tin DB).")
            return False

        if cmd == "pwd":
            _print(str(settings.workspace_dir))
            return False

        if cmd == "ls":
            rel = arg or "."
            try:
                names = await files.list_dir(rel)
            except Exception as exc:
                _print(f"ls error: {exc}")
                return False
            if not names:
                _print("(trống)")
            else:
                for name in names:
                    _print(f"  {name}")
            return False

        if cmd == "read":
            if not arg:
                _print("Dùng: /read path/trong/workspace")
                return False
            try:
                content = await files.read_text(arg)
            except Exception as exc:
                _print(f"read error: {exc}")
                return False
            _print(f"--- {arg} ---\n{content}\n--- end ---")
            return False

        if cmd == "write":
            if not arg:
                _print("Dùng: /write path.py  rồi dán nội dung, kết thúc bằng dòng ###END")
                return False
            _print(f"Nhập nội dung cho {arg} (kết thúc: ###END):")
            lines: list[str] = []
            while True:
                try:
                    row = input()
                except EOFError:
                    break
                if row.strip() == "###END":
                    break
                lines.append(row)
            body = "\n".join(lines)
            try:
                info = await files.write_text(arg, body)
            except Exception as exc:
                _print(f"write error: {exc}")
                return False
            _print(f"Wrote {info['path']} ({info['bytes']} bytes)")
            return False

        if cmd == "plan":
            if not arg:
                _print("Dùng: /plan mô tả task")
                return False
            _print("… planning …")
            try:
                out = await planner.plan(arg)
            except GrokError as exc:
                _print(f"[AI error] {exc}")
                return False
            _print(out)
            return False

        if cmd == "code":
            if not arg:
                _print("Dùng: /code spec")
                return False
            _print("… coding …")
            try:
                out = await coder.code(arg)
            except GrokError as exc:
                _print(f"[AI error] {exc}")
                return False
            _print(out)
            return False

        if cmd == "review":
            if not arg:
                _print("Dùng: /review code…")
                return False
            _print("… review …")
            try:
                out = await reviewer.review(arg)
            except GrokError as exc:
                _print(f"[AI error] {exc}")
                return False
            _print(out)
            return False

        if cmd == "debug":
            if not arg:
                _print("Dùng: /debug traceback…")
                return False
            _print("… debug …")
            try:
                out = await debugger.debug(arg)
            except GrokError as exc:
                _print(f"[AI error] {exc}")
                return False
            _print(out)
            return False

        if cmd == "build":
            if not arg:
                _print("Dùng: /build task")
                return False
            _print("… pipeline plan→code→review …")
            try:
                result = await pipeline.run(arg)
            except GrokError as exc:
                _print(f"[AI error] {exc}")
                return False
            _print(result.format_telegram().replace("*", "").replace("`", ""))
            return False

        _print(f"Lệnh không biết: /{cmd} — gõ /help")
        return False

    # One-shot mode
    if one_shot:
        if one_shot.startswith("/"):
            should_exit = await handle_slash(one_shot)
            await grok.aclose()
            await db.close()
            return 0 if not should_exit else 0
        await chat_once(one_shot)
        await grok.aclose()
        await db.close()
        return 0

    # Interactive REPL
    while True:
        try:
            line = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            _print("\nBye.")
            break
        if not line:
            continue
        if line.startswith("/"):
            if await handle_slash(line):
                break
            continue
        await chat_once(line)

    await files.teardown()
    await grok.aclose()
    await db.close()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description="Jarvis AI — terminal CMD agent (cùng config với Telegram bot)",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Câu hỏi one-shot (không có → vào REPL tương tác)",
    )
    parser.add_argument(
        "--mode",
        default=None,
        help="Mode khởi tạo: default|coder|security|sales|research",
    )
    args = parser.parse_args()
    if args.mode:
        if args.mode not in MODES:
            print(f"Mode không hợp lệ: {args.mode}")
            print("Chọn:", ", ".join(MODES))
            sys.exit(2)
        set_user_mode(CLI_USER_ID, args.mode)

    prompt = " ".join(args.prompt).strip() or None
    try:
        raise SystemExit(asyncio.run(run_repl(prompt)))
    except KeyboardInterrupt:
        print("\nBye.")
        raise SystemExit(0)


if __name__ == "__main__":
    main()
