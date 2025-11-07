"""Custom exceptions for latent encoder service."""


class LatentEncoderError(Exception):
    """Base exception for latent encoder service."""
    pass


class ImageNotFoundError(LatentEncoderError):
    """Raised when input image file is not found."""
    pass


class ImageInvalidError(LatentEncoderError):
    """Raised when image file is corrupted or invalid format."""
    pass


class VAEModelNotFoundError(LatentEncoderError):
    """Raised when VAE model file is not found."""
    pass


class EncodingFailedError(LatentEncoderError):
    """Raised when VAE encoding process fails."""
    pass


class OutputDirNotWritableError(LatentEncoderError):
    """Raised when output directory is not writable."""
    pass


class ScalingFailedError(LatentEncoderError):
    """Raised when image scaling process fails."""
    pass


class ComfyUIInitializationError(LatentEncoderError):
    """Raised when ComfyUI initialization fails."""
    pass



