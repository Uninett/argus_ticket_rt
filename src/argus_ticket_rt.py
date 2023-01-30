"Allow argus-server to create tickets in Request Tracker"

import logging
import requests
from urllib.parse import urljoin

from rt.rest2 import Rt

from argus.incident.ticket.base import TicketPlugin, TicketPluginException

LOG = logging.getLogger(__name__)


__version__ = "0.2"
__all__ = [
    "RequestTrackerPlugin",
]


class RequestTrackerPlugin(TicketPlugin):
    @classmethod
    def import_settings(cls):
        try:
            endpoint, authentication, ticket_information = super().import_settings()
        except ValueError as e:
            LOG.exception("Could not import settings for ticket plugin.")
            raise TicketPluginException(f"Request Tracker: {e}")

        if "token" not in authentication.keys() and (
            "username" not in authentication.keys()
            or "password" not in authentication.keys()
        ):
            LOG.error(
                "Request Tracker: No authentication details (token or username/password) can be found in the authentication information. Please update the setting 'TICKET_AUTHENTICATION_SECRET'."
            )
            raise TicketPluginException(
                "Request Tracker: No authentication details (token or username/password) can be found in the authentication information. Please update the setting 'TICKET_AUTHENTICATION_SECRET'."
            )

        if "queue" not in ticket_information.keys():
            LOG.error(
                "Request Tracker: No queue can be found in the ticket information. Please update the setting 'TICKET_INFORMATION'."
            )
            raise TicketPluginException(
                "Request Tracker: No queue can be found in the ticket information. Please update the setting 'TICKET_INFORMATION'."
            )

        return endpoint, authentication, ticket_information

    @staticmethod
    def convert_tags_to_dict(tag_dict: dict) -> dict:
        incident_tags_list = [entry["tag"].split("=") for entry in tag_dict]
        return {key: value for key, value in incident_tags_list}

    @staticmethod
    def get_custom_fields(ticket_information: dict, serialized_incident: dict) -> dict:
        incident_tags = RequestTrackerPlugin.convert_tags_to_dict(
            serialized_incident["tags"]
        )
        custom_fields = ticket_information.get("custom_fields", {})
        custom_fields_mapping = ticket_information.get("custom_fields_mapping", {})

        for key, field in custom_fields_mapping.items():
            if type(field) is dict:
                # Information can be found in tags
                custom_fields[key] = incident_tags[field["tag"]]
            else:
                # Infinity means that the incident is still open
                if serialized_incident[field] == "infinity":
                    continue
                custom_fields[key] = serialized_incident[field]

        return custom_fields

    @staticmethod
    def create_client(endpoint, authentication):
        """Creates and returns a RT client"""
        if "token" in authentication.keys:
            try:
                client = Rt(
                    url=urljoin(endpoint, "REST/2.0"),
                    token=authentication["token"],
                )
            except Exception as e:
                LOG.exception("Request Tracker: Client could not be created.")
                raise TicketPluginException(f"Request Tracker: {e}")
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
            LOG.exception("Request Tracker: Client could not be created.")
            raise TicketPluginException(f"Request Tracker: {e}")
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

        body = cls.create_html_body(serialized_incident=serialized_incident)
        custom_fields = cls.get_custom_fields(
            ticket_information=ticket_information,
            serialized_incident=serialized_incident,
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

        except Exception as e:
            LOG.exception("Request Tracker: Ticket could not be created.")
            raise TicketPluginException(f"Request Tracker: {e}")
        else:
            ticket_url = urljoin(endpoint, f"Ticket/Display.html?id={ticket_id}")
            return ticket_url
