# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A fan-made web server (Tornado, Python 3.13) for playing the board game Dixit in the browser. It is a single-process, in-memory application — there is no database; all state lives on one `Application` object and is lost on restart. No copyrighted artwork is shipped: card images must be supplied by the user (see `dixit/static/cards/dixit/README.txt`).

## Commands

```bash
uv sync                   # create the .venv and install runtime + dev deps
uv run dixit              # run the server (entry point dixit:start), then open http://localhost:8888/
uv run dixit config.local.json   # run with a config override file (see Config below)
uv run pytest             # run the test suite
uv run pytest dixit/tests/test_server.py::TestDixitServer::test_homepage   # run a single test
uv run ruff format .      # format; CI runs `ruff format --check .` and fails on any diff
uv run ruff check .       # lint (CI also gates on this)
uv build                  # build sdist + wheel into dist/
docker compose up --build # run containerized on http://localhost:8888/
```

CI (`.github/workflows/ci.yml`, GitHub Actions) runs on push/PR: `uv sync`, then `ruff format --check .`, `ruff check .`, and `pytest`. Keep code ruff-clean (both format and lint) or CI fails. The build backend is setuptools (`pyproject.toml`); `MANIFEST.in` still drives the bundling of `static/`, `templates/`, and `config.json` into the wheel.

## Architecture

**Single global state object.** `dixit/server.py` builds one module-level `application` (an `Application`, subclass of `tornado.web.Application`) that holds everything: `users`, `games` (a plain list — a game's `gid` is its index), `chat_log`, `card_sets`, and `limits`. Handlers reach state via `self.application.*`.

**HTTP polling, not websockets.** The browser polls endpoints on fixed intervals defined at the top of `dixit/templates/main.js` (`GAMEBOARD_INTERVAL`, `CHATROOM_INTERVAL`, etc.): `/getgames`, `/getusers`, `/chat`, and `/game/<gid>/0`. To avoid re-rendering unchanged data, the server sends SHA-256 hashes (`handHash`, `cardsHash`, `votesHash` via `utils.hash_obj`) that the client compares against what it last rendered.

**Request layer is thin; logic lives in `core.py`.** Handlers in `server.py` validate/parse arguments, then delegate to methods on the `Game` object. `GameHandler` is the hub: it maps integer commands (the `Commands` class) from `/game/<gid>/<cmd>` to `Game` methods (`add_player`, `start_game`, `create_clue`, `play_card`, `cast_vote`, `kick_player`) and `_get_board` assembles the full board JSON.

**Game state machine** (`core.py` `States`): `BEGIN → CLUE → PLAY → VOTE → (CLUE | END)`. Each `Game` method enforces the expected current state and raises `APIError(Codes.X)` on any violation (wrong turn, bad state, illegal value, …); error codes live in `dixit/codes.py`. A `Round` object holds all per-turn state (who played/voted which card, scores). Dixit scoring is implemented in `Game._do_scoring` (`SCORE_FOR_TRICK/LOSS/CORRECT` = 1/2/3).

**User identity.** Each `User` has a private `uid` (stored in the `dixit_user` cookie, never sent to clients) and a public `puid` (used in all client-facing JSON); both are salted hashes from `utils.hash_obj`. `RequestHandler.prepare()` transparently creates a user from the cookie on every request, so handlers can assume `self.user`. The client only ever sees `puid`s.

**Cards and decks.** `Application.find_cards` scans `static/cards/<folder>` for `.jpg`/`.png` files to build each `CardSet`; a `Deck` (one per `Game`) is the shuffled concatenation of the chosen sets. Card directories are git-ignored and `MANIFEST.in` prunes them from the package — the repo ships only the README placeholder.

**Templates are Tornado-rendered Python.** `main.html`, `main.js`, and `main.css` are served through `tornado.web` template rendering (not as static files), with `dixit/display.py` constants and the `States`/`Commands`/`Limits` objects injected in. This keeps client-side values in sync with the server: e.g. editing a colour/path/size in `display.py` or a state enum in `core.py` automatically propagates to the rendered client — there are no duplicated literals to update.

**Config.** `dixit/config.json` is JSON that allows `//` comments (stripped by `config.py`). An optional override file passed as the single CLI argument is deep-merged over the defaults (`config._merge`). The parsed config is merged into Tornado `settings`, which is also where `port` comes from. The `limits` block is validated/normalized by `core.Limits` (`-1` means infinity, mapped to `utils.INFINITY` = `1e9`).

**Admin console.** `AdminHandler` (`/admin`) `exec`s arbitrary posted code when `admin_enable` is true and the hashed password matches. It is disabled by default (`admin_enable: false`) — treat it as a dangerous debug tool, not a feature.
