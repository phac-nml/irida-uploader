class IridaUploadCanceledException(Exception):
    """
    This error can be thrown mid upload if the api receives the call to cancel uploads

    This should be caught and the information that the upload has been canceled should be relayed
    """
    pass
