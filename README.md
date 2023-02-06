# argus_ticket_rt

This is a plugin to create tickets in Request Tracker from [Argus](https://github.com/Uninett/argus-server)

The API supported is RT V2. RT 4.4 needs [RT::Extension::REST2](https://github.com/bestpractical/rt-extension-rest2)
to support V2, while RT 5.0.0 and later has the support included.

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

* `TICKET_INFORMATION`:

    Queue (obligatory)

    ```
    {
        "queue": queue_name
    }
    ```

    Custom fields (optional)

    There are two ways of automatically filling custom fields:

    1. Custom fields that are always the same, independent of the incident. 
    These will be set in `custom_fields_set` with the name of the custom field as key and the fixed value as value.


        ```
        {
            "custom_fields_set" : {
                "name_of_custom_field": set_value,
            }
        }
        ```

    2. Custom fields that are filled by attributes of the Argus incident. These are set in `custom_fields_mapping` with the name of the custom field as key and the name of the attribute as it is returned by the API  as value (e.g. `start_time`). If the information can be found in the tags the value consists of a dictionary with `tag` as the key and the name of the tag as the value (e.g. {"tag": "host"}).

        ```
        {
            "custom_fields_mapping" : {
                "name_of_custom_field": attribute_of_incident,
                "name_of_custom_field": {"tag": name_of_tag},
            }
        }
        ```

## Library

The library was changed from [rt-client](https://pypi.org/project/rt-client/)
to [rt](https://pypi.org/project/rt/) since "rt-client" did not support token
authentication.
