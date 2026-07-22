"""IQE Plugin Application."""

import datetime
import logging
import mimetypes

import attr
import pytest
from iqe.base.application.plugins import ApplicationPlugin
from iqe.base.application.plugins.service_objects import RESTPluginService
from iqe_bindings.v7.inventory_v1 import HostOut
from wait_for import TimedOutError, wait_for

mimetypes.add_type("application/vnd.redhat.advisor.payload+tgz", ".redhat-advisor-tgz")

logger = logging.getLogger(__name__)


@attr.s
class ApplicationPuptoo(ApplicationPlugin):
    """Holder for application puptoo related methods and functions."""

    plugin_app_name = "puptoo"
    plugin_real_name = "Puptoo"
    plugin_name = "puptoo"
    plugin_title = "Puptoo"
    plugin_package_name = "iqe-puptoo-plugin"
    v7_ingress_v1 = RESTPluginService.declare("v7_ingress_v1")
    v7_inventory_v1 = RESTPluginService.declare("v7_inventory_v1")

    def upload_advisor_payload(self, archive, record_property=None):
        """Uploads hosts from advisor Payload to HBI via puptoo."""
        logger.info(f"push_upload -- Attempting upload for: {archive.filename}")

        with open(archive.filename, "rb") as f:
            file_data = f.read()

        response = self.v7_ingress_v1.ingress_api.upload_post(
            file=("upload.redhat-advisor-tgz", file_data),
            metadata={"content_type": "application/vnd.redhat.advisor.payload+tgz"},
        )

        request_id = response.request_id

        if record_property:
            record_property("request_id", request_id)
        logger.info(f"push_upload -- Upload successful, obtained request id: {request_id}")

        return self._wait_for_inventory(insights_id=archive.insights_id)

    def _wait_for_inventory(self, insights_id: str) -> HostOut:
        """Wait for a host to be processed by Inventory."""

        def _verification() -> bool:
            response = self.v7_inventory_v1.hosts_api.api_host_get_host_list(
                insights_id=insights_id
            )

            if response.count == 0:
                raise LookupError("Host not found!")

            return response.results[0]

        try:
            host, _ = wait_for(
                func=_verification,
                delay=3,
                timeout=datetime.timedelta(minutes=3),
                handle_exception=True,
            )

            return host
        except TimedOutError:
            pytest.fail(f"Host not found! Insights ID: {insights_id}")
