from fastapi import APIRouter, HTTPException, status


def stub_router(resource: str, phase: int) -> APIRouter:
    """Router whose list endpoint answers 501 until `phase` implements it."""
    router = APIRouter(prefix=f"/{resource}", tags=[resource])

    @router.get("", summary=f"List {resource} (phase {phase})")
    def list_items() -> None:
        raise HTTPException(
            status.HTTP_501_NOT_IMPLEMENTED, f"/{resource} is implemented in phase {phase}"
        )

    return router
