class IridaKeyError(KeyError):
    """
    This error will only happen when there is an issue with the api itself
    It should not be able to happen based on user input

    This could happen if the HATEOAS spec changes,
    or the api has a bug in the implementation of it
    """
    pass
