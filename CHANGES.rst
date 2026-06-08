***************
Release history
***************

.. Changelog entries should follow this format:

   version (release date)
   ======================

   **section**

   - One-line description of change (link to Github issue/PR)

.. Changes should be organized in one of several sections:

   - Added
   - Changed
   - Deprecated
   - Removed
   - Fixed

0.1.3 (unreleased)
==================

**Added**

- Added ``.webp`` support for card images.
- Refactored ``BunnyPalette`` into a ``StrEnum`` with a dynamic colour grid
  and added more colours.

**Changed**

- Reveal each card's owner with a coloured bunny and name label below the
  card, and outline the clue maker's card in their colour, instead of tinting
  the whole card.
- Prevented players from voting for their own card during the vote phase.
- Migrated to uv and Python 3.13, switched to ruff and GitHub Actions, and
  added Docker support.

**Removed**

- Removed the colour overlay that tinted and faded cards on reveal.
- Stopped drawing a vote token for the clue maker, who does not vote.
- Removed the magnifying-glass hover effect on cards.

**Fixed**

- Made the player's hand horizontally scrollable when the window is too
  narrow to show every card.


0.1.2 (December 29, 2023)
=========================

**Added**

- Added the ability for hosts to hide their games from the table.
  (`#11 <https://github.com/arvoelke/Dixit/pull/11>`__)
- Configuration settings may be overriden by another config file.
  (`#10 <https://github.com/arvoelke/Dixit/pull/10>`__)
- Default to looking for .png extensions in card directories.
  (`#21 <https://github.com/arvoelke/Dixit/pull/21>`__)


0.1.1 (July 10, 2020)
=====================

**Changed**

- Patched the license and readme to add disclaimers.
  (`#9 <https://github.com/arvoelke/Dixit/pull/9>`__)


0.1.0 (July 9, 2020)
====================

Initial alpha release expected to undergo significant changes.

Thank you to all the developers who have helped so far!
