"""Platform maintenance refusal wire contract (e3bc718 / v0.38.9).

503 responses with ``Retry-After`` use ``ErrorCode.maintenance`` when the
platform is draining (``platform.maintenance``), distinct from
``app_maintenance`` when an app owner pauses a single app.
"""

from inferencesh.models.errors import APIError
from inferencesh.types import ErrorCode


class TestPlatformMaintenanceErrorCode:
    def test_maintenance_wire_value(self):
        assert ErrorCode.MAINTENANCE.value == "maintenance"

    def test_platform_maintenance_distinct_from_app_maintenance(self):
        assert ErrorCode.APP_MAINTENANCE.value == "app_maintenance"
        assert ErrorCode.MAINTENANCE.value != ErrorCode.APP_MAINTENANCE.value

    def test_api_error_reads_maintenance_from_problem_json(self):
        body = (
            '{"type":"https://api.inference.sh/errors/maintenance",'
            '"status":503,"detail":"Platform maintenance in progress",'
            '"meta":{"retry_after_seconds":120}}'
        )
        err = APIError(503, "Platform maintenance in progress", response_body=body)
        assert err.code == ErrorCode.MAINTENANCE

    def test_api_error_reads_app_maintenance_from_problem_json(self):
        body = (
            '{"type":"https://api.inference.sh/errors/app_maintenance",'
            '"status":503,"detail":"This app is paused by its owner"}'
        )
        err = APIError(503, "app paused", response_body=body)
        assert err.code == ErrorCode.APP_MAINTENANCE
