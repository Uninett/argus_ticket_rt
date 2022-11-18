from django.test import SimpleTestCase, override_settings

from argus.incident.ticket.base import TicketPluginException
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
