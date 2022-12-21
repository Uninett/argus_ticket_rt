"Allow argus-server to create tickets in Request Tracker"

import logging
import requests
from urllib.parse import urljoin

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


__version__ = "0.2"
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
            "username" not in authentication.keys() or "password" not in authentication.keys()
        ):
            LOG.exception(
                "Request Tracker: No authentication details (token or username/password) can be found in the authentication information."
            )
            raise TicketSettingsException(
                "Request Tracker: No authentication details (token or username/password) can be found in the authentication information. Please check and update the setting 'TICKET_AUTHENTICATION_SECRET'."
            )

        if "queue" not in ticket_information.keys():
            LOG.exception("Request Tracker: No queue can be found in the ticket information.")
            raise TicketSettingsException(
                "Request Tracker: No queue can be found in the ticket information. Please check and update the setting 'TICKET_INFORMATION'."
            )

        return endpoint, authentication, ticket_information

    @staticmethod
    def create_client(endpoint, authentication):
        """Creates and returns a RT client"""
        if "token" in authentication.keys():
            return Rt(
                url=urljoin(endpoint, "REST/2.0"),
                token=authentication["token"],
            )

        return Rt(
            url=urljoin(endpoint, "REST/2.0"),
            http_auth=requests.auth.HTTPBasicAuth(authentication["username"], authentication["password"]),
        )

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
            LOG.exception("Request Tracker: Could not connect to Request Tracker.")
            raise TicketClientException("Request Tracker: Could not connect to Request Tracker.")
        except rt_exceptions.AuthorizationError:
            LOG.exception("Request Tracker: The authentication details are incorrect.")
            raise TicketSettingsException(
                "Request Tracker: The authentication details are incorrect. Please check and update the setting 'TICKET_AUTHENTICATION_SECRET'."
            )
        except rt_exceptions.NotAllowedError:
            LOG.exception("Request Tracker: Authenticated client does not have sufficient permissions.")
            raise TicketCreationException("Request Tracker: Authenticated client does not have sufficient permissions.")
        except rt_exceptions.NotFoundError:
            LOG.exception("Request Tracker: No queue with the name %s can be found.", queue)
            raise TicketSettingsException(
                f"Request Tracker: No queue with the name {queue} can be found. Please check and update the setting 'TICKET_INFORMATION'."
            )

        try:
            ticket_id = client.create_ticket(
                queue=ticket_information["queue"],
                subject=serialized_incident["description"],
                content=serialized_incident["description"],
            )
        except rt_exceptions.ConnectionError:
            LOG.exception("Request Tracker: Could not connect to Request Tracker.")
            raise TicketClientException("Request Tracker: Could not connect to Request Tracker.")
        except rt_exceptions.NotAllowedError:
            LOG.exception("Request Tracker: Authenticated client does not have sufficient permissions.")
            raise TicketCreationException("Request Tracker: Authenticated client does not have sufficient permissions.")
        except Exception as e:
            LOG.exception("Request Tracker: Ticket could not be created. %s", str(e))
            raise TicketPluginException(f"Request Tracker: {e}")
        else:
            ticket_url = urljoin(endpoint, f"Ticket/Display.html?id={ticket_id}")
            return ticket_url
