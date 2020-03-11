class IridaConnectionError(Exception):
    """
    This error is thrown when the api cannot connect to the IRIDA api
    Either the server is unreachable or the credentials are invalid

    All calls to the api should expect this error
    """
    pass
