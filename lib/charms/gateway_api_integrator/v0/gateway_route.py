# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Library for the gateway-route relation.

This library contains the Requires and Provides classes for handling the gateway-route
interface.

The `GatewayRouteRequires` class is used by the Configurator charm to send route
configuration to the Integrator.

The `GatewayRouteProvides` class is used by the Integrator charm to receive route
configuration.
"""

import json
import logging
from typing import List, Optional

from ops.charm import CharmBase, RelationCreatedEvent, RelationJoinedEvent, RelationChangedEvent
from ops.framework import Object

# The unique Charmhub library identifier, never change it
LIBID = "1234567890abcdef1234567890abcdef"

# Increment this major API version when introducing breaking changes
LIBAPI = 0

# Increment this PATCH version before using `charmcraft publish-lib` or reset
# to 0 if you are raising the major API version
LIBPATCH = 1

logger = logging.getLogger(__name__)

RELATION_NAME = "gateway-route"


class GatewayRouteRequires(Object):
    """Requires side of the gateway-route relation."""

    def __init__(self, charm: CharmBase, relation_name: str = RELATION_NAME):
        super().__init__(charm, relation_name)
        self.charm = charm
        self.relation_name = relation_name

    def send_route_configuration(
        self,
        hostname: str,
        paths: List[str],
        port: int,
        application: str,
        model: str,
    ):
        """Send route configuration to the integrator.

        Args:
            hostname: The hostname to serve the application on.
            paths: List of paths to serve.
            port: The port of the service.
            application: The application name.
            model: The model name.
        """
        relation = self.charm.model.get_relation(self.relation_name)
        if not relation:
            logger.warning(f"Relation {self.relation_name} not found")
            return

        data = {
            "hostname": hostname,
            "paths": json.dumps(paths),
            "port": str(port),
            "application": application,
            "model": model,
        }

        relation.data[self.charm.unit].update(data)


class GatewayRouteProvides(Object):
    """Provides side of the gateway-route relation."""

    def __init__(self, charm: CharmBase, relation_name: str = RELATION_NAME):
        super().__init__(charm, relation_name)
        self.charm = charm
        self.relation_name = relation_name

    # The Integrator will use raw relation data access or a specific method to read data.
    # For now, we can leave this empty or add helper methods if needed.
