"""Custom exceptions for sampling service."""


class SamplingError(Exception):
    """Base exception for sampling service."""
    pass


class UNETModelNotFoundError(SamplingError):
    """Raised when UNET model file is not found."""
    pass


class LoRAModelNotFoundError(SamplingError):
    """Raised when LoRA model file is not found."""
    pass


class InputTensorNotFoundError(SamplingError):
    """Raised when input tensor file is not found."""
    pass


class SamplingFailedError(SamplingError):
    """Raised when sampling process fails."""
    pass


class OutputDirNotWritableError(SamplingError):
    """Raised when output directory is not writable."""
    pass


class ComfyUIInitializationError(SamplingError):
    """Raised when ComfyUI initialization fails."""
    pass


class InvalidTensorFormatError(SamplingError):
    """Raised when tensor format is invalid."""
    pass



