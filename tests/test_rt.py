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


class ConvertTagsToListOfTuplesTests(SimpleTestCase):
    def test_given_list_of_tags_then_return_list_of_tuples(self):
        tags = RequestTrackerPlugin.convert_tags_to_list_of_tuples(
            [
                {
                    "added_by": 1,
                    "added_time": "2026-11-10T10:47:15.454401+01:00",
                    "tag": "host=switch1.example.com",
                },
                {
                    "added_by": 1,
                    "added_time": "2026-11-10T10:47:15.455349+01:00",
                    "tag": "host=switch2.example.com",
                },
                {
                    "added_by": 1,
                    "added_time": "2026-11-10T10:47:15.455925+01:00",
                    "tag": "service=CNaaS",
                },
            ]
        )
        assert tags == [
            ("host", "switch1.example.com"),
            ("host", "switch2.example.com"),
            ("service", "CNaaS"),
        ]


class GetCustomFieldsTests(SimpleTestCase):
    def setUp(self):
        self.serialized_incident = {
            "pk": 10101,
            "start_time": "2011-11-11T11:11:11+02:00",
            "end_time": "2011-11-11T11:11:12+02:00",
            "source": {
                "pk": 11,
                "name": "Uninett GW 3",
                "type": {"name": "nav"},
                "user": 12,
                "base_url": "https://somenav.somewhere.com",
            },
            "source_incident_id": "12345",
            "details_url": "https://uninett.no/api/alerts/12345/",
            "description": "Netbox 11 <12345> down.",
            "ticket_url": "https://tickettracker.com/tickets/987654/",
            "tags": [
                {
                    "added_by": 12,
                    "added_time": "2011-11-11T11:11:11.111111+02:00",
                    "tag": "object=Netbox 4",
                },
                {
                    "added_by": 12,
                    "added_time": "2011-11-11T11:11:11.111111+02:00",
                    "tag": "problem_type=boxDown",
                },
                {
                    "added_by": 200,
                    "added_time": "2020-08-10T11:26:14.550951+02:00",
                    "tag": "color=red",
                },
            ],
            "stateful": True,
            "open": False,
            "acked": False,
        }

    def test_given_set_custom_fields_then_return_set_values(self):
        ticket_information = {
            "custom_fields_set": {
                "name": "value",
            }
        }

        custom_fields, missing_fields = RequestTrackerPlugin.get_custom_fields(
            ticket_information, self.serialized_incident
        )

        assert custom_fields == {"name": "value"}
        assert not missing_fields

    def test_given_mapping_from_fields_then_return_values_from_incident(self):
        ticket_information = {
            "custom_fields_mapping": {
                "start_of_case": "start_time",
            }
        }

        custom_fields, missing_fields = RequestTrackerPlugin.get_custom_fields(
            ticket_information, self.serialized_incident
        )

        assert custom_fields == {
            "start_of_case": self.serialized_incident["start_time"]
        }
        assert not missing_fields

    def test_given_mapping_from_tags_with_single_value_then_return_single_value_from_incident(
        self,
    ):
        ticket_information = {
            "custom_fields_mapping": {
                "problem": {"tag": "problem_type"},
            }
        }

        custom_fields, missing_fields = RequestTrackerPlugin.get_custom_fields(
            ticket_information, self.serialized_incident
        )

        assert custom_fields == {"problem": "boxDown"}
        assert not missing_fields

    def test_given_mapping_from_tags_with_multiple_values_then_return_list_of_values_from_incident(
        self,
    ):
        self.serialized_incident["tags"].append(
            {
                "added_by": 200,
                "added_time": "2020-08-10T11:26:14.550951+02:00",
                "tag": "problem_type=another_problem",
            }
        )
        ticket_information = {
            "custom_fields_mapping": {
                "problem": {"tag": "problem_type"},
            }
        }

        custom_fields, missing_fields = RequestTrackerPlugin.get_custom_fields(
            ticket_information, self.serialized_incident
        )

        assert custom_fields == {"problem": ["boxDown", "another_problem"]}
        assert not missing_fields

    def test_given_mapping_from_missing_field_then_return_missing_fields(self):
        ticket_information = {
            "custom_fields_mapping": {
                "start_of_case": "non_existing_field",
            }
        }

        custom_fields, missing_fields = RequestTrackerPlugin.get_custom_fields(
            ticket_information, self.serialized_incident
        )

        assert missing_fields == ["non_existing_field"]
        assert not custom_fields

    def test_given_mapping_from_missing_tag_then_return_missing_fields(self):
        ticket_information = {
            "custom_fields_mapping": {
                "problem": {"tag": "non_existing_tag"},
            }
        }

        custom_fields, missing_fields = RequestTrackerPlugin.get_custom_fields(
            ticket_information, self.serialized_incident
        )

        assert missing_fields == ["non_existing_tag"]
        assert not custom_fields
