"""Custom exceptions for decoding service."""


class DecodingError(Exception):
    """Base exception for decoding service."""
    pass


class VAEModelNotFoundError(DecodingError):
    """Raised when VAE model file is not found."""
    pass


class LatentFileNotFoundError(DecodingError):
    """Raised when input latent file is not found."""
    pass


class DecodingFailedError(DecodingError):
    """Raised when VAE decoding process fails."""
    pass


class OutputDirNotWritableError(DecodingError):
    """Raised when output directory is not writable."""
    pass


class InvalidImageFormatError(DecodingError):
    """Raised when image format is invalid."""
    pass


class ComfyUIInitializationError(DecodingError):
    """Raised when ComfyUI initialization fails."""
    pass


class InvalidTensorFormatError(DecodingError):
    """Raised when tensor format is invalid."""
    pass



