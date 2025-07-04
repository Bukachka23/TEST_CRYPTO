class BaseServiceException(Exception):
    status_code: int = 500
    detail: str = "Internal Server Error"


class DocumentTooLargeException(BaseServiceException):
    status_code: int = 413
    detail: str = "Document too large"


class InvalidDocumentFormatException(BaseServiceException):
    status_code = 400
    detail = "Invalid document format"


class NetworkNotSupportedException(BaseServiceException):
    status_code = 400
    detail = "Network not supported"


class VerificationFailedException(BaseServiceException):
    status_code = 422
    detail = "Document verification failed"
