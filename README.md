# argus_ticket_rt

This is a plugin to create tickets in Request Tracker from [Argus](https://github.com/Uninett/argus-server)

## Settings

* `TICKET_ENDPOINT`: Link to instance, absolute URL
* `TICKET_AUTHENTICATION_SECRET`: Standard username/password:

    ```
    {
        "username": username,
        "password": password
    }
    ```

* `TICKET_INFORMATION`: Queue (obligatory)

    ```
    {
        "queue": queue_name
    }
    ```
