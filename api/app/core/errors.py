from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Domain error converted to an HTTP response by the exception handler."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )


async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return Pydantic validation errors in the application's error format."""
    errors = []
    for err in exc.errors():
        field = ".".join(str(part) for part in err["loc"][1:])
        errors.append({"field": field, "message": err["msg"]})
    return JSONResponse(
        status_code=422,
        content={
            "code": "validation_error",
            "message": "Podaci nisu valjani",
            "errors": errors,
        },
    )
