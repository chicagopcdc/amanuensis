from cdiserrors import APIError, UserError, AuthZError, AuthNError


class InternalError(APIError):
    """
    Used for logging
    revproxy will block the message from going to the user
    """

    def __init__(self, message):
        super(InternalError, self).__init__(
            message, 500, json="An internal error occurred. Please try again later."
        )


class Forbidden(APIError):
    """
    Used for logging
    """

    def __init__(self, message):
        super(Forbidden, self).__init__(
            message,
            403,
            json="Access denied. Please contact your administrator if you believe this is an error.",
        )


class NotFound(APIError):
    """
    Used for logging
    """

    def __init__(self, message):
        super(NotFound, self).__init__(message, 404)
