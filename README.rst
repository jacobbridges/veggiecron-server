##################################################
Veggiecron Server: a healthier alternative to cron
##################################################

.. class:: no-web

    Veggiecron (inspired by the unix crontab and `celery <http://www.celeryproject.org/>`_) is a **Python server for scheduling jobs via REST API**. Standing on the shoulders of such giants as `asyncio <https://docs.python.org/dev/library/asyncio.html>`_ and `tornado <http://www.tornadoweb.org/en/stable/>`_, veggiecron is able to run thousands of jobs a minute.


    .. image:: http://i.imgur.com/yJm3tLz.gif
        :alt: live preview gif
        :width: 100%
        :align: center

.. contents::


============
Installation
============

Veggiecron will not be available via pip until we reach the version 1.0 `milestone <https://github.com/jacobbridges/veggiecron-server/milestone/1>`_ For those brave enough to run the "pre-v1" product, follow these instructions:

.. code-block:: bash

   # Ensure you have Python 3.5+
   $ python --version

   # Clone the repo
   $ git clone https://github.com/jacobbridges/veggiecron-server.git && cd veggiecron-server

   # (OPTIONAL) Create a virtual environment to run the project
   $ virtualenv venv -p python3.5
   $ ./venv/bin/activate

   # Install the dependencies
   $ pip install -r requirements.txt

=====
Usage
=====

----------------
Start the Server
----------------

Simple and clean:

.. code-block:: bash

   $ python3 start.py

The server will be started on 0.0.0.0:8118.

---------------
Register a User
---------------

.. code-block:: bash

   $ http --form POST localhost:8118/register username=test password=test
   {
       "data": {
           "date_created": 1476675574.624803,
           "date_updated": 1476675574.624803,
           "username": "test"
       },
       "description": "You are registered as \"test\"! Proceed to login.",
       "id": "success"
   }

-------------------------
Login (Get an Auth Token)
-------------------------

Auth tokens are required to perform any actions via REST on Veggiecron. These tokens can be retrieved from the ``/login`` endpoint, and are used in the request header under ``X-Auth-Token``:

.. code-block:: bash

   $ http --form POST localhost:8118/login username=test password=test
   {
       "data": {
           "token": "MmIxNTYwNOM2ZmZlNjQ4YzXkNWMyM2E1ZDEzMDZlMWU6dGVzdA=="
       },
       "description": "You have successfully generated an auth token! Check the data key.",
       "id": "success"
   }

------------
Create a Job
------------

Simple example for creating a job:

.. code-block:: bash

   $ http --form POST localhost:8118/job X-Auth-Token:<token> name=<name> type=<type> data=<data> schedule=<schedule>
   {
       "data": {
           "data": "<data>",
           "date_created": <unix-timestamp>,
           "date_updated": <unix-timestamp>,
           "name": "<name>",
           "schedule": "<schedule>",
           "type": "<type>"
       },
       "description": "Successfully created http job: \"<name>\"",
       "id": "success"
   }

The above code example will raise more questions than it answers. Here is a list of relevant links you might want to check out:

* `Job Types`_
* `Schedule String Format`_

-------------
Configuration
-------------

High-level configurations can be found in the ``config.yaml`` file. Descriptions of each config are in the following table:

========  =====================================================================
Config    Description
========  =====================================================================
app.env   Application environment. Defaults to "development".
app.name  If you don't like "veggiecron-server".
app.key   Application key used to hash passwords. Be sure to generate your own!
host      Host to run the server on.
port      Port to run the server on.
db_file   Name of the SQLite3 database file.
========  =====================================================================

=============
In-Depth Docs
=============

*This section is for more detailed documentation, while the previous sections for skimming readers.*

---------
Job Types
---------

The following job types are available:

+------+-------------------------------+-----------------------------------------------------------------------------------------+
| Type | Description                   | Data                                                                                    |
|      |                               +------------------+------+---------------------------------------------------------------+
|      |                               | Field            | Type | Description                                                   |
+======+===============================+==================+======+===============================================================+
| http | Job that makes HTTP requests. | url              | str  | URL to be requested. (must begin with "http://")              |
|      |                               +------------------+------+---------------------------------------------------------------+
|      |                               | number_of_clones | int  | Number of reqeusts made on every job run.                     |
|      |                               +------------------+------+---------------------------------------------------------------+
|      |                               | enable_shadows   | bool | Run the job again even if a previous run is still processing. |
|      |                               +------------------+------+---------------------------------------------------------------+
|      |                               | verb             | str  | HTTP method (GET, POST, DELETE, etc.)                         |
+------+-------------------------------+------------------+------+---------------------------------------------------------------+

----------------------
Schedule String Format
----------------------

A job's "schedule" property must follow the following syntax:

* every hour
* every x hours
* every minute
* every x minutes
* every x seconds
* every day @ 13:00
* every x days @ 7:30
* once @ <utc-timestamp>
