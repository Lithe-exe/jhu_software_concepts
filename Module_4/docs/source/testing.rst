Testing Guide
=============

This project uses ``pytest`` for unit and integration testing.

Running Tests
-------------
To run the full test suite with coverage:

.. code-block:: bash

   pytest --cov=src

Test Markers
------------
Tests are categorized by markers. You can run specific groups using ``-m``:

* ``web``: Tests Flask routes and HTML rendering.
* ``buttons``: Tests "Pull Data" and "Update Analysis" button logic.
* ``db``: Tests database schema and insertions.
* ``analysis``: Tests data formatting and math correctness.
* ``integration``: Tests the full end-to-end flow.

Example:

.. code-block:: bash

   pytest -m "web or buttons or analysis or db or integration"
