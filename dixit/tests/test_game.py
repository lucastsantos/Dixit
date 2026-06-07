import pytest

from dixit.codes import APIError, Codes
from dixit.core import Game, States, StringClue
from dixit.deck import CardSet
from dixit.display import BunnyPalette
from dixit.server import application
from dixit.users import User


COLOURS = [
    BunnyPalette.RED,
    BunnyPalette.ORANGE,
    BunnyPalette.YELLOW,
    BunnyPalette.GREEN,
]


def make_user(puid):
    """Creates a standalone User for testing."""
    return User(application.limits, "uid-%s" % puid, "puid-%s" % puid)


def make_game(num_players=4):
    """Builds a game with a synthetic deck and drives it into the VOTE state.

    Returns (game, players) where players[0] is the clue maker.
    """
    card_set = CardSet("test", ["fake/path/%d.jpg" % i for i in range(60)])
    users = [make_user(str(i)) for i in range(num_players)]
    game = Game(
        host=users[0],
        card_sets=[card_set],
        password="",
        name="test",
        max_players=num_players,
        max_score=application.limits.max_score,
        max_clue_length=application.limits.max_clue_length,
        limits=application.limits,
    )
    for user, colour in zip(users, COLOURS):
        game.add_player(user, colour)
    game.start_game()

    clue_maker = game.clue_maker()
    game.create_clue(clue_maker, StringClue("a clue"), game.players[clue_maker].hand[0])
    for user in game.players:
        if user != clue_maker:
            game.play_card(user, game.players[user].hand[0])

    assert game.state == States.VOTE
    # Order the returned players with the clue maker first.
    players = [clue_maker] + [u for u in game.players if u != clue_maker]
    return game, players


def test_player_cannot_vote_for_own_card():
    """A non-storyteller voting for the card they played is rejected."""
    game, players = make_game()
    voter = players[1]
    own_card = game.round.user_to_card[voter]

    with pytest.raises(APIError) as excinfo:
        game.cast_vote(voter, own_card)
    assert excinfo.value.code == Codes.VOTE_INVALID


def test_player_can_vote_for_another_card():
    """Voting for another player's card still succeeds."""
    game, players = make_game()
    voter, other = players[1], players[2]
    other_card = game.round.user_to_card[other]

    game.cast_vote(voter, other_card)
    assert game.round.has_voted(voter)
    assert voter in game.round.card_to_voted_users[other_card]
