"""Headless test bots for driving a Dixit server with many simultaneous clients.

The Dixit server talks plain HTTP (polling), not websockets, so a "client" is
just a cookie jar that hits the same endpoints the browser does. That means we
can simulate a full table of players with lightweight threads instead of a fleet
of headless Chrome instances.

Each bot, on its turn:
  * as the clue maker, plays a random card from its hand with a random clue;
  * otherwise plays a random card, then votes for a random card that isn't its own.

Usage (server must already be running, e.g. `uv run dixit`):

    # Fill an existing game you created in the browser, then start it yourself.
    # Find the gid in the game's URL / the games list (0-indexed).
    uv run python bots.py --gid 0 --bots 8

    # Or let the bots create and run a game entirely on their own.
    uv run python bots.py --create --bots 8 --autostart

Stop everything with Ctrl-C.
"""

import argparse
import http.cookiejar
import json
import logging
import random
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

# Mirror of dixit.server.Commands and dixit.core.States so this script stays
# standalone (no import of the server package required).
GET_BOARD, JOIN_GAME, START_GAME, CREATE_CLUE, PLAY_CARD, CAST_VOTE = 0, 1, 2, 3, 4, 5
BEGIN, CLUE, PLAY, VOTE, END = 0, 1, 2, 3, 4

# Bunny colours from dixit.display.BunnyPalette (one unique colour per bot).
COLOURS = [
    "d499ff",
    "a41bf3",
    "c52828",
    "f299b1",
    "e59100",
    "e2e05d",
    "a18332",
    "b5e8c4",
    "66bd28",
    "12751b",
    "214ddc",
    "1bbdbf",
    "fafafa",
    "b5b5b5",
    "6e6e6e",
    "222222",
]

CLUE_WORDS = (
    "dream mist shadow river journey echo silent golden whisper frozen "
    "wandering hidden ancient distant burning falling gentle endless hollow "
    "crimson serene drifting fragile luminous restless"
).split()

logger = logging.getLogger("bots")


class Client:
    """A single HTTP client (one cookie jar == one server-side user)."""

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(jar)
        )

    def _open(self, path, data=None):
        url = self.base_url + path
        body = urllib.parse.urlencode(data).encode() if data is not None else None
        with self.opener.open(url, data=body, timeout=15) as resp:
            return resp.read().decode()

    def get(self, path):
        return self._open(path)

    def post(self, path, data):
        return self._open(path, data)

    def command(self, gid, cmd, **params):
        """Issues a /game/<gid>/<cmd> action. Returns True on success.

        The server raises APIError (-> HTTP 500) for illegal moves (wrong turn,
        self-vote, already played, ...); we treat those as a benign "not my move
        yet" and let the bot retry on the next poll.
        """
        query = "?" + urllib.parse.urlencode(params) if params else ""
        try:
            self.get(f"/game/{gid}/{cmd}{query}")
            return True
        except urllib.error.HTTPError as exc:
            logger.debug("command %s on game %s rejected (HTTP %s)", cmd, gid, exc.code)
            return False


class Bot:
    """Drives one Client through a game, acting whenever it's asked to."""

    def __init__(self, name, client, gid, poll=1.0, allow_start=False):
        self.name = name
        self.client = client
        self.gid = gid
        self.poll = poll
        self.allow_start = allow_start  # only the bot that owns the game may start it
        self.puid = None
        self.played_cid = None  # remembered so we never vote for our own card

    def setup(self, colour):
        """Establishes a cookie, sets the username, and joins the game."""
        self.client.get("/")  # triggers the server to mint our user cookie
        self.client.post("/setusername", {"username": self.name})
        if not self.client.command(self.gid, JOIN_GAME, colour=colour):
            logger.warning("%s could not join game %s", self.name, self.gid)

    def board(self):
        return json.loads(self.client.get(f"/game/{self.gid}/{GET_BOARD}"))

    def act(self, board):
        """Performs the single action the board says we owe, if any."""
        self.puid = board["user"]
        state = board["state"]
        if not board.get("requiresAction", {}).get(self.puid):
            return

        if state == BEGIN:
            if self.allow_start:
                logger.info("%s starting the game", self.name)
                self.client.command(self.gid, START_GAME)
        elif state == CLUE:
            self._make_clue(board)
        elif state == PLAY:
            self._play(board)
        elif state == VOTE:
            self._vote(board)

    def _hand_cids(self, board):
        return [c["cid"] for c in board.get("player", {}).get("hand", [])]

    def _make_clue(self, board):
        hand = self._hand_cids(board)
        if not hand:
            return
        cid = random.choice(hand)
        max_len = board.get("maxClueLength", 1024)
        words = random.sample(CLUE_WORDS, k=random.randint(1, 3))
        clue = " ".join(words)[:max_len] or "clue"
        if self.client.command(self.gid, CREATE_CLUE, clue=clue, cid=cid):
            self.played_cid = cid
            logger.info('%s gave clue "%s"', self.name, clue)

    def _play(self, board):
        hand = self._hand_cids(board)
        if hand and self.client.command(
            self.gid, PLAY_CARD, cid=(cid := random.choice(hand))
        ):
            self.played_cid = cid
            logger.info("%s played a card", self.name)

    def _vote(self, board):
        cards = board.get("round", {}).get("cards", [])
        candidates = [c["cid"] for c in cards if c["cid"] != self.played_cid]
        random.shuffle(candidates)
        for cid in candidates:
            if self.client.command(self.gid, CAST_VOTE, cid=cid):
                logger.info("%s voted", self.name)
                return

    def run(self, stop):
        """Polls and acts until the game ends or `stop` is set."""
        while not stop.is_set():
            try:
                board = self.board()
                self.act(board)
                if board["state"] == END:
                    logger.info("%s sees the game has ended", self.name)
                    break
            except Exception as exc:  # keep the bot alive through transient errors
                logger.warning("%s error: %s", self.name, exc)
            stop.wait(self.poll)


def monitor(client, gid, stop, poll=1.0):
    """Polls the board and prints scores + deck count whenever a round ends.

    The server bumps `turn` (and may flip to END) the instant the last vote of a
    round lands, so a change in `turn` is our signal that a round just finished.
    """
    last_turn = None
    rnd_num = 0
    while not stop.is_set():
        try:
            board = json.loads(client.get(f"/game/{gid}/{GET_BOARD}"))
            turn, state = board.get("turn"), board.get("state")
            ended = state == END
            if last_turn is not None and (turn != last_turn or ended):
                rnd_num += 1
                names = board.get("players", {})
                scores = board.get("scores", {})
                ranked = sorted(names, key=lambda p: scores.get(p, 0), reverse=True)
                line = ", ".join(f"{names[p]}: {scores.get(p, 0)}" for p in ranked)
                left, size = board.get("left", "?"), board.get("size", "?")
                label = "final" if ended else f"round {rnd_num}"
                logger.info("=== %s scores -- %s | deck %s/%s", label, line, left, size)
                if ended:
                    break
            last_turn = turn
        except Exception as exc:
            logger.warning("monitor error: %s", exc)
        stop.wait(poll)


def create_game(client, base_url, num_card_sets, max_players):
    """Creates a game via /create and returns its gid."""
    data = [("card_sets", str(i)) for i in range(num_card_sets)]
    data += [
        ("name", "Bot Test Game"),
        ("max_score", ""),  # empty == unlimited
        ("max_players", str(max_players)),
        ("max_clue_length", "1024"),
        ("password", ""),
    ]
    client.get("/")
    body = urllib.parse.urlencode(data).encode()
    with client.opener.open(base_url.rstrip("/") + "/create", data=body) as resp:
        return int(resp.read().decode())


def count_card_sets(base_url):
    """Best-effort guess at how many card sets exist (for --create)."""
    # The games list doesn't expose this; default to 4 (config.json ships 4).
    return 4


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run headless Dixit test bots.")
    parser.add_argument("--url", default="http://localhost:8888", help="server URL")
    parser.add_argument("--bots", type=int, default=8, help="number of bots")
    parser.add_argument("--gid", type=int, help="join this existing game id")
    parser.add_argument(
        "--create", action="store_true", help="create a fresh game for the bots"
    )
    parser.add_argument(
        "--autostart",
        action="store_true",
        help="with --create, the host bot starts the game once all bots join",
    )
    parser.add_argument(
        "--poll", type=float, default=1.0, help="seconds between each bot's polls"
    )
    parser.add_argument("--verbose", action="store_true", help="debug logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
    )

    if (args.gid is None) == (not args.create):
        parser.error("specify exactly one of --gid <id> or --create")

    host_client = Client(args.url)
    if args.create:
        gid = create_game(host_client, args.url, count_card_sets(args.url), args.bots)
        logger.info("Created game %s", gid)
    else:
        gid = args.gid

    bots = []
    for i in range(args.bots):
        # Reuse the host_client for bot 0 when creating, so it owns/can start it.
        client = host_client if (args.create and i == 0) else Client(args.url)
        allow_start = args.create and args.autostart and i == 0
        bots.append(
            Bot(f"Bot-{i + 1}", client, gid, poll=args.poll, allow_start=allow_start)
        )

    for bot, colour in zip(bots, COLOURS):
        bot.setup(colour)
        logger.info("%s joined game %s", bot.name, gid)

    if args.create and not args.autostart:
        logger.info(
            "Bots joined game %s. Start it from the browser as the host, "
            "or re-run with --autostart.",
            gid,
        )

    stop = threading.Event()
    threads = [threading.Thread(target=b.run, args=(stop,), daemon=True) for b in bots]
    threads.append(
        threading.Thread(
            target=monitor, args=(Client(args.url), gid, stop, args.poll), daemon=True
        )
    )
    for t in threads:
        t.start()

    logger.info("%d bots running on game %s. Ctrl-C to stop.", len(bots), gid)
    try:
        while any(t.is_alive() for t in threads):
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Stopping bots...")
        stop.set()
    for t in threads:
        t.join(timeout=2)


if __name__ == "__main__":
    sys.exit(main())
