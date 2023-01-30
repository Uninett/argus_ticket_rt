# argus_ticket_rt

This is a plugin to create tickets in Request Tracker from [Argus](https://github.com/Uninett/argus-server)

## Settings

* `TICKET_ENDPOINT`: Link to instance, absolute URL
* `TICKET_AUTHENTICATION_SECRET`: Standard username/password or token:

    ```
    {
        "username": username,
        "password": password
    }
    ```
    
    or

    ```
    {
        "token": token
    }
    ```

* `TICKET_INFORMATION`: Queue (obligatory)

    ```
    {
        "queue": queue_name
    }
    ```

## Library

The library was changed from rt_client to rt since rt_client did not support token authentication.