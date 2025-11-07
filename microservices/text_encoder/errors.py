"""Custom exceptions for text encoder service."""


class TextEncoderError(Exception):
    """Base exception for text encoder service."""
    pass


class ImageNotFoundError(TextEncoderError):
    """Raised when input image file is not found."""
    pass


class ImageInvalidError(TextEncoderError):
    """Raised when image file is corrupted or invalid format."""
    pass


class CLIPModelNotFoundError(TextEncoderError):
    """Raised when CLIP model file is not found."""
    pass


class VAEModelNotFoundError(TextEncoderError):
    """Raised when VAE model file is not found."""
    pass


class EncodingFailedError(TextEncoderError):
    """Raised when text encoding process fails."""
    pass


class OutputDirNotWritableError(TextEncoderError):
    """Raised when output directory is not writable."""
    pass


class ScalingFailedError(TextEncoderError):
    """Raised when image scaling process fails."""
    pass


class ComfyUIInitializationError(TextEncoderError):
    """Raised when ComfyUI initialization fails."""
    pass



