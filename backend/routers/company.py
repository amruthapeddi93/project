import logging

from fastapi import APIRouter, HTTPException, Query

from services.company_search import search_company

router = APIRouter(
    prefix="/companies",
    tags=["Company Search"],
)

logger = logging.getLogger(__name__)


@router.get("/search")
def search_companies(
    q: str = Query(..., min_length=1),
):
    try:
        result = search_company(q.strip())

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    except Exception:
        logger.exception(
            "Company search failed for query: %s",
            q,
        )

        raise HTTPException(
            status_code=502,
            detail="Unable to fetch company search results.",
        ) from None
