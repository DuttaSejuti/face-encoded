class ServiceError(Exception):
    pass


class SessionNotFoundError(ServiceError):
    pass


class InvalidImageError(ServiceError):
    pass


class ImageLimitExceededError(ServiceError):
    pass
