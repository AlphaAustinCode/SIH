from app.database.models import AllocatedBlock, MaintenanceRequest
from app.schemas.api import BlockResponse, MaintenanceResponse


def maintenance_response(request: MaintenanceRequest) -> MaintenanceResponse:
    return MaintenanceResponse.model_validate(request)


def block_response(block: AllocatedBlock) -> BlockResponse:
    requests = list(block.maintenance_requests)
    return BlockResponse(
        id=block.id,
        track_section_id=block.track_section_id,
        section_name=block.track_section.section_name,
        start_time=block.start_time,
        end_time=block.end_time,
        duration_minutes=int((block.end_time - block.start_time).total_seconds() / 60),
        status=block.status.value,
        departments=sorted({request.department.value for request in requests}),
        power_cutoff_required=any(
            request.power_isolation_required for request in requests
        ),
        traffic_halted=any(request.traffic_block_required for request in requests),
        bundled_requests=[maintenance_response(request) for request in requests],
    )