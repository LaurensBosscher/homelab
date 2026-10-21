from __future__ import annotations

import unittest

from homelab_cloudflare.cloudflare_api import (
    DnsDeleteOutcome,
    classify_dns_delete,
    delete_dns_record,
)
from homelab_cloudflare.dns_delete import dns_delete_target

_MISSING = (
    '{"result":null,"success":false,"errors":[{"code":81044,'
    '"message":"Record does not exist."}],"messages":[]}'
)


class ClassifyDnsDeleteTest(unittest.TestCase):
    def test_404_is_already_gone(self) -> None:
        self.assertIs(classify_dns_delete(404, _MISSING), DnsDeleteOutcome.ALREADY_GONE)

    def test_404_without_json_is_already_gone(self) -> None:
        self.assertIs(classify_dns_delete(404, "not found"), DnsDeleteOutcome.ALREADY_GONE)

    def test_81044_on_other_status_is_already_gone(self) -> None:
        self.assertIs(classify_dns_delete(400, _MISSING), DnsDeleteOutcome.ALREADY_GONE)

    def test_200_is_deleted(self) -> None:
        body = '{"success":true,"result":{"id":"abc"}}'
        self.assertIs(classify_dns_delete(200, body), DnsDeleteOutcome.DELETED)

    def test_auth_failure_raises(self) -> None:
        body = '{"success":false,"errors":[{"code":10000,"message":"Authentication error"}]}'
        with self.assertRaises(RuntimeError):
            classify_dns_delete(403, body)

    def test_success_false_raises(self) -> None:
        with self.assertRaises(RuntimeError):
            classify_dns_delete(200, '{"success":false,"errors":[]}')


class DeleteDnsRecordTest(unittest.TestCase):
    def test_rejects_non_ids_before_calling_api(self) -> None:
        with self.assertRaises(ValueError):
            delete_dns_record("../zones", "not-an-id")


class DnsDeleteTargetTest(unittest.TestCase):
    def test_reads_zone_and_record_id(self) -> None:
        zone, record = dns_delete_target(
            "867a0bc340f8eaf7ba313799791d3cd7",
            {"zoneId": "e32ce9cb10fafea8ee531b713afdcc10"},
            {"id": "867a0bc340f8eaf7ba313799791d3cd7"},
        )
        self.assertEqual(zone, "e32ce9cb10fafea8ee531b713afdcc10")
        self.assertEqual(record, "867a0bc340f8eaf7ba313799791d3cd7")

    def test_falls_back_to_outputs(self) -> None:
        zone, record = dns_delete_target(
            "",
            None,
            {
                "zoneId": "e32ce9cb10fafea8ee531b713afdcc10",
                "id": "867a0bc340f8eaf7ba313799791d3cd7",
            },
        )
        self.assertEqual(zone, "e32ce9cb10fafea8ee531b713afdcc10")
        self.assertEqual(record, "867a0bc340f8eaf7ba313799791d3cd7")

    def test_missing_ids_raise(self) -> None:
        with self.assertRaises(RuntimeError):
            dns_delete_target("", {}, {})


if __name__ == "__main__":
    unittest.main()
