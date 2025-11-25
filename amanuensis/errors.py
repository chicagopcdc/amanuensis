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


class AuthError(APIError):
    """
    Authentication error used internally
    Not meant to be a user-facing API error.
    """
    pass


class UserError(JSONAPIError):
    """
    User-facing error (bad input, invalid state, etc.).
    Returns a 400 JSON response by default.
    """

    def __init__(self, message):
        super(UserError, self).__init__(message, code=400)


class BlacklistingError(APIError):
    # Not currently called in in amanuensis, and did not find in other
    # services, that did not already have their own defined.
    # TODO: May not be needed

    def __init__(self, message):
        super(BlacklistingError, self).__init__(message)
        self.message = str(message)
        self.code = 400


class InternalError(APIError):
    """
    Used for logging
    """

    def __init__(self, message):
        super(InternalError, self).__init__(message)
        self.message = str(message)
        self.code = 500


class Unauthorized(APIError):
    # Not currently called in in amanuensis, and did not find in other
    # services, that did not already have their own defined.
    # TODO: May not be needed

    def __init__(self, message):
        super(Unauthorized, self).__init__(message)
        self.message = str(message)
        self.code = 401


class Forbidden(APIError):
    """
    Used for logging
    """

    def __init__(self, message):
        super(Forbidden, self).__init__(message)
        self.message = str(message)
        self.code = 403


class NotFound(APIError):
    """
    Used for logging
    """

    def __init__(self, message):
        super(NotFound, self).__init__(message)
        self.message = str(message)
        self.code = 404


class NotSupported(APIError):
    # Not currently called in in amanuensis, and did not find in other
    # services, that did not already have their own defined.
    # TODO: May not be needed

    def __init__(self, message):
        super(NotSupported, self).__init__(message)
        self.message = str(message)
        self.code = 400


class UnavailableError(APIError):
    # Not currently called in in amanuensis, and did not find in other
    # services, that did not already have their own defined.
    # TODO: May not be needed
 
    def __init__(self, message):
        super(UnavailableError, self).__init__(message)
        self.message = str(message)
        self.code = 503
