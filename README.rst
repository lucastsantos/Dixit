Fork Notice
-----------

This repository is a fork of `arvoelke/Dixit <https://github.com/arvoelke/Dixit/>`__.
All changes from the fork are described under ``0.1.3 (unreleased)`` in
`CHANGES.rst <CHANGES.rst>`__.

.. figure:: http://i.imgur.com/y5Zv9Az.png
   :alt: Revealing the correct card

Installation
------------

Dixit is developed with `uv <https://docs.astral.sh/uv/>`__ and targets
Python 3.13. From a checkout of this repository, install the dependencies
into a virtual environment with:

``uv sync``

Supplying Cards
---------------

Card images are not distributed with this software (see the Disclaimer
below). Place your own ``.png``, ``.jpg``, or ``.webp`` card images into
``dixit/static/cards/dixit/`` to build the default deck. See
``dixit/static/cards/dixit/README.txt``. The server starts without any
cards, but a game cannot deal a hand until enough images are present.

Starting the Server
-------------------

``uv run dixit``

Then go to http://localhost:8888/.

To start with a configuration override file (see "Configuring the Server"
below), pass it as an argument:

``uv run dixit config.local.json``

Running with Docker
-------------------

A ``Dockerfile`` and ``docker-compose.yml`` are included. To build and run:

``docker compose up --build``

Then go to http://localhost:8888/. Card images placed in a ``./cards``
directory on the host are mounted into the default deck. To use a
configuration override, create ``config.local.json`` and uncomment the
relevant lines in ``docker-compose.yml``.

Configuring the Server
----------------------

Configuration options, such as the port (default 8888), and the location of
each card deck (e.g., see ``dixit/static/cards/dixit/README.txt``), are housed
in JSON configuration files that are read when you launch the server.
Default settings are located in ``dixit/config.json``.

To override the defaults, you may create a JSON file in your working directory
that contains a subset of these configuration options. For example, to change
the port to 9000, create a new file named ``config.local.json`` that contains:

.. code-block:: JSON

   {
       "port": 9000
   }

Then pass in this file name when you launch the server, as in:
``dixit config.local.json``. This will override the default configuration with
the values in ``config.local.json``.

Alternatively, directly edit ``dixit/config.json``, to for instance, specify
which port to use, or to point to the location of each card deck that you have.

Disclaimer
----------

This software is solely the work of several fans of the Dixit board
game. It is not intended to replace nor compete with the original
board game, Dixit (a registered trademark of Libellud Company), and
likewise does not represent the works, views, nor opinions of Libellud.
This software is provided as is, without warranty of any kind, express
or implied.

Please support the creators, designers, and artists behind Dixit by
purchasing the original board game and its expansions.

We do not currently, nor do we plan to, distribute copywritten artwork.
Currently all cards must be supplied by you, the user. This server is
provided for personal use only (there is no license for commercial use).

Please contact the maintainer if there are any concerns.

Notes
-----

This is an alpha release and may therefore undergo significant changes.
Please request features or submit changes to
https://github.com/arvoelke/Dixit/.

Thank you to all the developers who have helped so far!
