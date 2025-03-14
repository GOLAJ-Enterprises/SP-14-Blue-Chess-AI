def require_init(method):
    def wrapper(self, *args, **kwargs):
        if not getattr(self, "_initialized", False):
            raise RuntimeError(
                f"{self.__class__.__name__}.init() must be called before using '{method.__name__}'"
            )
        return method(self, *args, **kwargs)

    return wrapper
