# argus_ticket_rt
This is a plugin to create tickets in Request Tracker from Argus

Settings
--------

* ``TICKET_ENDPOINT``: Link to self-hosted instance
* ``TICKET_AUTHENTICATION_SECRET``:
    - token-based authentication does not work with the library used, therefore username- and password-based authentication is necessary
    - ``{"username": username, "password": password}``
* ``TICKET_INFORMATION``:
    - the only additional information needed is the queue the ticket should be added to
    - ``{"queue": queue_name}``