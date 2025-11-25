from cdiserrors import APIError


class JSONAPIError(APIError):
    """
    Base error type for this service that always exposes a JSON payload.
    """

    def __init__(self, message, code=400):
        super(JSONAPIError, self).__init__(message)
        # readable text
        self.message = str(message)
        # HTTP status code
        self.code = code
        # JSON payload
        self.json = {"message": str(message)}


class AuthError(JSONAPIError):
    """
    Authentication/authorization error.
    Returns a 401 JSON response by default.
    """

    def __init__(self, message="Unauthorized"):
        super(AuthError, self).__init__(message, code=401)


class UserError(JSONAPIError):
    """
    User-facing error (bad input, invalid state, etc.).
    Returns a 400 JSON response by default.
    """

    def __init__(self, message):
        super(UserError, self).__init__(message, code=400)


class BlacklistingError(APIError):
    # TODO: Currently not pulling in parent class for JSON output.
    # This will probably switch to using JSONAPIError - Edit message when done.

    def __init__(self, message):
        super(BlacklistingError, self).__init__(message)
        self.message = str(message)
        self.code = 400


class InternalError(APIError):
    # TODO: Currently not pulling in parent class for JSON output.
    # This should stay due to logging - Edit message when done.

    def __init__(self, message):
        super(InternalError, self).__init__(message)
        self.message = str(message)
        self.code = 500


class Unauthorized(APIError):
    """
    Used for AuthN-related errors in most cases.
    """
    # TODO: Currently not pulling in parent class for JSON output.
    # This will probably switch to using JSONAPIError - Edit message when done.

    def __init__(self, message):
        super(Unauthorized, self).__init__(message)
        self.message = str(message)
        self.code = 401


class Forbidden(APIError):
    """
    Used for AuthZ-related errors in most cases.
    """
    # TODO: Currently not pulling in parent class for JSON output.
    # This will probably switch to using JSONAPIError - Edit message when done.

    def __init__(self, message):
        super(Forbidden, self).__init__(message)
        self.message = str(message)
        self.code = 403


class NotFound(APIError):
    # TODO: Currently not pulling in parent class for JSON output.
    # This will probably switch to using JSONAPIError - Edit message when done.

    def __init__(self, message):
        super(NotFound, self).__init__(message)
        self.message = str(message)
        self.code = 404


class NotSupported(APIError):
    # TODO: Currently not pulling in parent class for JSON output.
    # This will probably switch to using JSONAPIError - Edit message when done.

    def __init__(self, message):
        super(NotSupported, self).__init__(message)
        self.message = str(message)
        self.code = 400


class UnavailableError(APIError):
    # TODO: Currently not pulling in parent class for JSON output.
    # This should stay due to logging - Edit message when done.
    
    def __init__(self, message):
        super(UnavailableError, self).__init__(message)
        self.message = str(message)
        self.code = 503
