"Allow argus-server to create tickets in Request Tracker"

import logging
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

        if ("token" not in authentication.keys()):
            LOG.error(
                "Request Tracker: No token can be found in the authentication information. Please update the setting 'TICKET_AUTHENTICATION_SECRET'."
            )
            raise TicketPluginException(
                "Request Tracker: No token can be found in the authentication information. Please update the setting 'TICKET_AUTHENTICATION_SECRET'."
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
    def create_client(endpoint, authentication):
        """Creates and returns a RT client"""
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

    @classmethod
    def create_ticket(cls, serialized_incident: dict):
        """
        Creates a Request Tracker ticket with the incident as template and returns the
        ticket url
        """
        endpoint, authentication, ticket_information = cls.import_settings()

        client = cls.create_client(endpoint, authentication)

        try:
            ticket_id = client.create_ticket(
                queue=ticket_information["queue"],
                subject=serialized_incident["description"],
                content=serialized_incident["description"],
            )

        except Exception as e:
            LOG.exception("Request Tracker: Ticket could not be created.")
            raise TicketPluginException(f"Request Tracker: {e}")
        else:
            ticket_url = urljoin(endpoint, f"Ticket/Display.html?id={ticket_id}")
            return ticket_url
