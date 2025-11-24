# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest
from unittest.mock import Mock, patch
import ops
from ops.testing import Harness
from charm import GatewayRouteConfiguratorCharm

class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(GatewayRouteConfiguratorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_config_changed_missing_hostname(self):
        self.harness.update_config({"hostname": ""})
        self.assertIsInstance(self.harness.charm.unit.status, ops.BlockedStatus)
        self.assertEqual(self.harness.charm.unit.status.message, "Missing 'hostname' config")

    def test_config_changed_invalid_hostname(self):
        self.harness.update_config({"hostname": "Invalid_Hostname"})
        self.assertIsInstance(self.harness.charm.unit.status, ops.BlockedStatus)
        self.assertTrue("Invalid hostname" in self.harness.charm.unit.status.message)

    def test_missing_ingress_relation(self):
        self.harness.update_config({"hostname": "valid.example.com"})
        self.assertIsInstance(self.harness.charm.unit.status, ops.BlockedStatus)
        self.assertEqual(self.harness.charm.unit.status.message, "Missing 'ingress' relation")

    @patch("charms.traefik_k8s.v2.ingress.IngressPerAppProvider.get_data")
    def test_happy_path(self, mock_get_data):
        # Mock ingress data
        class MockAppData:
            def __init__(self):
                self.name = "my-app"
                self.model = "my-model"
                self.port = 8080
                self.strip_prefix = False
                self.redirect_https = False
        
        class MockData:
            def __init__(self):
                self.app = MockAppData()
                self.units = []  # Add units list

        mock_get_data.return_value = MockData()

        # Setup relations
        ingress_rel_id = self.harness.add_relation("ingress", "workload")
        self.harness.add_relation_unit(ingress_rel_id, "workload/0")
        
        gateway_rel_id = self.harness.add_relation("gateway-route", "integrator")
        self.harness.add_relation_unit(gateway_rel_id, "integrator/0")

        # Trigger update
        self.harness.update_config({"hostname": "valid.example.com", "paths": "/foo,/bar"})

        # Verify status
        self.assertIsInstance(self.harness.charm.unit.status, ops.ActiveStatus)
        self.assertEqual(self.harness.charm.unit.status.message, "Ready")

        # Verify relation data
        relation_data = self.harness.get_relation_data(gateway_rel_id, self.harness.charm.unit.name)
        self.assertEqual(relation_data["hostname"], "valid.example.com")
        self.assertEqual(relation_data["port"], "8080")
        self.assertEqual(relation_data["application"], "my-app")
        self.assertEqual(relation_data["model"], "my-model")
        # Paths are JSON encoded
        import json
        self.assertEqual(json.loads(relation_data["paths"]), ["/foo", "/bar"])
