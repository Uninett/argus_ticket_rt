from unittest.mock import Mock

from argus.incident.ticket.base import TicketPluginException
from django.test import SimpleTestCase, override_settings

from argus_ticket_rt import RequestTrackerPlugin


class RequestTrackerTicketPluginTests(SimpleTestCase):
    @override_settings(
        TICKET_ENDPOINT="https://example.com/",
        TICKET_AUTHENTICATION_SECRET={"password": "value"},
        TICKET_INFORMATION={"queue": "value"},
    )
    def test_import_settings_raises_error_when_username_is_missing_from_ticket_authentication_secret(
        self,
    ):
        rt_plugin = RequestTrackerPlugin()

        with self.assertRaises(TicketPluginException):
            rt_plugin.import_settings()

    @override_settings(
        TICKET_ENDPOINT="https://example.com/",
        TICKET_AUTHENTICATION_SECRET={"username": "value"},
        TICKET_INFORMATION={"queue": "value"},
    )
    def test_import_settings_raises_error_when_password_is_missing_from_ticket_authentication_secret(
        self,
    ):
        rt_plugin = RequestTrackerPlugin()

        with self.assertRaises(TicketPluginException):
            rt_plugin.import_settings()

    @override_settings(
        TICKET_ENDPOINT="https://example.com/",
        TICKET_AUTHENTICATION_SECRET={"username": "value", "password": "value"},
        TICKET_INFORMATION={"key": "value"},
    )
    def test_import_settings_raises_error_when_queue_is_missing_from_ticket_information(
        self,
    ):
        rt_plugin = RequestTrackerPlugin()

        with self.assertRaises(TicketPluginException):
            rt_plugin.import_settings()


class GetTicketIdentifierTests(SimpleTestCase):
    def test_get_ticket_identifier_returns_ticket_id_for_valid_url(
        self,
    ):
        ticket_url = "https://example.com/Ticket/Display.html?id=123"
        rt_plugin = RequestTrackerPlugin()
        incident = Mock(ticket_url=ticket_url)

        ticket_identifier = rt_plugin.get_ticket_identifier(incident=incident)
        self.assertEqual(ticket_identifier, "123")

    def test_get_ticket_identifier_returns_ticket_url_for_url_not_following_format(
        self,
    ):
        ticket_url = "https://example.com/123"
        rt_plugin = RequestTrackerPlugin()
        incident = Mock(ticket_url=ticket_url)

        ticket_identifier = rt_plugin.get_ticket_identifier(incident=incident)
        self.assertEqual(ticket_identifier, ticket_url)
