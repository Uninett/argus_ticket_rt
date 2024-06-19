"Allow argus-server to create tickets in Request Tracker"

import logging
import requests
from urllib.parse import urljoin
from typing import List

import rt.exceptions as rt_exceptions
from rt.rest2 import Rt

from argus.incident.ticket.base import (
    TicketClientException,
    TicketCreationException,
    TicketPlugin,
    TicketPluginException,
    TicketSettingsException,
)

LOG = logging.getLogger(__name__)


__version__ = "1.1"
__all__ = [
    "RequestTrackerPlugin",
]


class RequestTrackerPlugin(TicketPlugin):
    @classmethod
    def import_settings(cls):
        try:
            endpoint, authentication, ticket_information = super().import_settings()
        except TicketSettingsException as e:
            LOG.exception(e)
            raise TicketSettingsException(f"Request Tracker: {e}")

        if "token" not in authentication.keys() and (
            "username" not in authentication.keys()
            or "password" not in authentication.keys()
        ):
            authentication_error = "Request Tracker: No authentication details (token or username/password) can be found in the authentication information. Please check and update the setting 'TICKET_AUTHENTICATION_SECRET'."
            LOG.exception(authentication_error)
            raise TicketSettingsException(authentication_error)

        if "queue" not in ticket_information.keys():
            queue_error = "Request Tracker: No queue can be found in the ticket information. Please check and update the setting 'TICKET_INFORMATION'."
            LOG.exception(queue_error)
            raise TicketSettingsException(queue_error)

        return endpoint, authentication, ticket_information

    @staticmethod
    def convert_tags_to_dict(tag_dict: dict) -> dict:
        incident_tags_list = [entry["tag"].split("=") for entry in tag_dict]
        return {key: value for key, value in incident_tags_list}

    @staticmethod
    def get_custom_fields(
        ticket_information: dict, serialized_incident: dict
    ) -> tuple[dict, List[str]]:
        serialized_incident["start_time"] = serialized_incident["start_time"][:-6]
        if serialized_incident["end_time"] != "infinity":
            serialized_incident["end_time"] = serialized_incident["end_time"][:-6]
        else:
            del serialized_incident["end_time"]

        incident_tags = RequestTrackerPlugin.convert_tags_to_dict(
            serialized_incident["tags"]
        )
        custom_fields = dict()
        custom_fields.update(ticket_information.get("custom_fields_set", {}))
        custom_fields_mapping = ticket_information.get("custom_fields_mapping", {})
        missing_fields = []

        for key, field in custom_fields_mapping.items():
            if isinstance(field, dict):
                # Information can be found in tags
                custom_field = incident_tags.get(field["tag"], None)
                if custom_field:
                    custom_fields[key] = custom_field
                else:
                    missing_fields.append(field["tag"])
            else:
                custom_field = serialized_incident.get(field, None)
                if custom_field:
                    custom_fields[key] = custom_field
                elif field != "end_time":
                    missing_fields.append(field)

        return custom_fields, missing_fields

    @staticmethod
    def create_client(endpoint, authentication):
        """Creates and returns a RT client"""
        if "token" in authentication.keys():
            try:
                client = Rt(
                    url=urljoin(endpoint, "REST/2.0"),
                    token=authentication["token"],
                )
            except Exception as e:
                client_error = "Request Tracker: Client could not be created."
                LOG.exception(client_error)
                raise TicketClientException(client_error)
            else:
                return client

        try:
            client = Rt(
                url=urljoin(endpoint, "REST/2.0"),
                http_auth=requests.auth.HTTPBasicAuth(
                    authentication["username"], authentication["password"]
                ),
            )
        except Exception as e:
            client_error = "Request Tracker: Client could not be created."
            LOG.exception(client_error)
            raise TicketClientException(client_error)
        else:
            return client

    @classmethod
    def create_ticket(cls, serialized_incident: dict):
        """
        Creates a Request Tracker ticket with the incident as template and returns the
        ticket url
        """
        endpoint, authentication, ticket_information = cls.import_settings()

        client = cls.create_client(endpoint, authentication)

        # Check if queue exists
        queue = ticket_information["queue"]
        try:
            client.get_queue(queue_id=queue)
        except (rt_exceptions.ConnectionError, ConnectionError):
            connection_error = "Request Tracker: Could not connect to Request Tracker."
            LOG.exception(connection_error)
            raise TicketClientException(connection_error)
        except rt_exceptions.AuthorizationError:
            authentication_error = "Request Tracker: The authentication details are incorrect. Please check and update the setting 'TICKET_AUTHENTICATION_SECRET'."
            LOG.exception(authentication_error)
            raise TicketSettingsException(authentication_error)
        except rt_exceptions.NotAllowedError:
            permission_error = "Request Tracker: Authenticated client does not have sufficient permissions."
            LOG.exception(permission_error)
            raise TicketCreationException(permission_error)
        except rt_exceptions.UnexpectedResponseError as e:
            if e.status_code == 403:
                permission_error = "Request Tracker: Authenticated client does not have sufficient permissions."
                LOG.exception(permission_error)
                raise TicketCreationException(permission_error)
            unexpected_error = (
                f"Request Tracker: An unexpected response was encountered: {e.message}."
            )
            LOG.exception(unexpected_error)
            raise TicketCreationException(unexpected_error)
        except rt_exceptions.NotFoundError:
            queue_error = f"Request Tracker: No queue with the name {queue} can be found. Please check and update the setting 'TICKET_INFORMATION'."
            LOG.exception(queue_error)
            raise TicketSettingsException(queue_error)
        except Exception as e:
            LOG.exception(e)
            raise TicketPluginException(e)

        custom_fields, missing_fields = cls.get_custom_fields(
            ticket_information=ticket_information,
            serialized_incident=serialized_incident,
        )
        body = cls.create_html_body(
            serialized_incident={
                "missing_fields": missing_fields,
                **serialized_incident,
            }
        )

        try:
            ticket_id = client.create_ticket(
                queue=ticket_information["queue"],
                subject=serialized_incident["description"],
                content_type="text/html",
                content=body,
                RefersTo=[
                    serialized_incident["details_url"],
                    serialized_incident["argus_url"],
                ],
                CustomFields=custom_fields,
            )
        except rt_exceptions.ConnectionError:
            connection_error = "Request Tracker: Could not connect to Request Tracker."
            LOG.exception(connection_error)
            raise TicketClientException(connection_error)
        except rt_exceptions.NotAllowedError:
            LOG.exception(permission_error)
            raise TicketCreationException(permission_error)
        except Exception as e:
            LOG.exception("Request Tracker: Ticket could not be created. %s", str(e))
            raise TicketPluginException(f"Request Tracker: {e}")
        else:
            ticket_url = urljoin(endpoint, f"Ticket/Display.html?id={ticket_id}")
            return ticket_url
