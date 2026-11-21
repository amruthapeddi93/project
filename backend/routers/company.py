from fastapi import APIRouter, Query, HTTPException
from services.company_search import search_company

router = APIRouter(
    prefix="/companies",
    tags=["Company Search"]
)


@router.get("/search")
def search_companies(q: str = Query(..., min_length=1)):

    try:
        result = search_company(q)

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Unable to fetch company search results."
        )