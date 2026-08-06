from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root() -> dict:
    return {"message": "Welcome to SUPPORTFORGE!"}
@router.get("/health")
async def health() -> dict:
    return {"status": "SUPPORTFORGE is WORKING FINE"}