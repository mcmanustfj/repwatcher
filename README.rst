==========
repwatcher
==========


.. image:: https://img.shields.io/pypi/v/repwatcher.svg
        :target: https://pypi.python.org/pypi/repwatcher


Tool to automatically upload SC:BW replays to RepMastered.com

Recommended installation is with pipx (`pip install pipx`):
 - `pipx install repwatcher`
 - `repwatcher watch`


Configuration:
`repwatcher config` will open a config file.
`replay_directory` is the directory to watch.
`authtoken` is the `authtoken` cookie from RepMastered.com. 
If you have `authtoken` in your config, uploads will be associated with your account.


* Free software: MIT license


Features
--------

This is a tool to watch a directory for new replays and upload them to RepMastered.com
It should be cross-platform, but has only been tested on Windows.

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
