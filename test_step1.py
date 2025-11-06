"""
Test Step 1: Compare latent encoder output tensors

This script compares:
1. Expected tensor from workflow_script_serial_test.py (test_outputs/latent_encoder_output.pt)
2. Actual tensor from latent_encoder microservice

It validates that the microservice produces the same output as the reference implementation.
"""
import sys
import torch
from pathlib import Path
import numpy as np
from typing import Optional


def load_expected_tensor(expected_path: str = "./test_outputs/latent_encoder_output.pt") -> Optional[torch.Tensor]:
    """Load expected tensor from workflow_script_serial_test.py output."""
    expected_file = Path(expected_path)
    
    if not expected_file.exists():
        print(f"❌ Expected tensor file not found: {expected_path}")
        print("   Please run workflow_script_serial_test.py first to generate expected outputs.")
        return None
    
    try:
        tensor = torch.load(expected_file)
        print(f"✓ Loaded expected tensor from: {expected_path}")
        print(f"  Shape: {tensor.shape}")
        print(f"  Dtype: {tensor.dtype}")
        return tensor
    except Exception as e:
        print(f"❌ Error loading expected tensor: {e}")
        return None


def get_actual_tensor_from_service(
    image_path: str = "input/masked_person.png",
    vae_model_name: str = "qwen_image_vae.safetensors",
    output_dir: str = "./test_outputs_actual"
) -> Optional[torch.Tensor]:
    """Get actual tensor from latent_encoder microservice."""
    # Add microservice directory to path
    microservice_dir = Path(__file__).parent / "microservices" / "latent_encoder"
    comfyui_dir = Path(__file__).parent
    
    # Add both microservice and ComfyUI to path
    sys.path.insert(0, str(microservice_dir))
    sys.path.insert(0, str(comfyui_dir))
    
    try:
        # Import service module
        import importlib.util
        service_path = microservice_dir / "service.py"
        spec = importlib.util.spec_from_file_location("service", service_path)
        service_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(service_module)
        
        encode_image_to_latent = service_module.encode_image_to_latent
        
        print(f"\nRunning latent_encoder microservice...")
        print(f"  Image: {image_path}")
        print(f"  VAE Model: {vae_model_name}")
        
        # Check if image exists
        image_path_obj = Path(image_path)
        if not image_path_obj.exists():
            # Try alternative paths
            alt_paths = [
                Path("input") / "masked_person.png",
                Path("masked_person.png"),
                Path("input") / "masked_person.jpg",
            ]
            found = False
            for alt_path in alt_paths:
                if alt_path.exists():
                    image_path = str(alt_path)
                    print(f"  Using alternative path: {image_path}")
                    found = True
                    break
            if not found:
                print(f"❌ Image file not found: {image_path}")
                print("   Tried:")
                for alt_path in alt_paths:
                    print(f"     - {alt_path}")
                return None
        
        # Call the service with save_tensor=False to get tensor directly
        result = encode_image_to_latent(
            image_path=image_path,
            vae_model_name=vae_model_name,
            output_dir=output_dir,
            upscale_method="lanczos",
            megapixels=1.0,
            save_tensor=False  # Return tensor instead of saving
        )
        
        if result["status"] != "success":
            print(f"❌ Service returned error: {result.get('error_code')}")
            print(f"   Error message: {result.get('error_message')}")
            return None
        
        tensor = result.get("latent_tensor")
        if tensor is None:
            print("❌ Service did not return tensor")
            print(f"   Result keys: {result.keys()}")
            return None
        
        print(f"✓ Got actual tensor from service")
        print(f"  Shape: {tensor.shape}")
        print(f"  Dtype: {tensor.dtype}")
        return tensor
        
    except ImportError as e:
        print(f"❌ Error importing service: {e}")
        print("   Make sure you're running from the ComfyUI root directory")
        print(f"   Microservice dir: {microservice_dir}")
        import traceback
        traceback.print_exc()
        return None
    except Exception as e:
        print(f"❌ Error running service: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_tensors(
    expected: torch.Tensor,
    actual: torch.Tensor,
    tolerance: float = 1e-5,
    rtol: float = 1e-4
) -> dict:
    """
    Compare two tensors and return detailed comparison results.
    
    Args:
        expected: Expected tensor
        actual: Actual tensor
        tolerance: Absolute tolerance for comparison
        rtol: Relative tolerance for comparison
    
    Returns:
        dict with comparison results
    """
    results = {
        "shapes_match": False,
        "dtypes_match": False,
        "values_match": False,
        "max_absolute_error": None,
        "mean_absolute_error": None,
        "max_relative_error": None,
        "mean_relative_error": None,
        "within_tolerance": False,
        "details": {}
    }
    
    # Check shapes
    results["shapes_match"] = expected.shape == actual.shape
    results["details"]["expected_shape"] = list(expected.shape)
    results["details"]["actual_shape"] = list(actual.shape)
    
    if not results["shapes_match"]:
        print(f"\n❌ Shape mismatch!")
        print(f"   Expected: {expected.shape}")
        print(f"   Actual:   {actual.shape}")
        return results
    
    print(f"\n✓ Shapes match: {expected.shape}")
    
    # Check dtypes
    results["dtypes_match"] = expected.dtype == actual.dtype
    results["details"]["expected_dtype"] = str(expected.dtype)
    results["details"]["actual_dtype"] = str(actual.dtype)
    
    if not results["dtypes_match"]:
        print(f"\n⚠️  Dtype mismatch (converting actual to expected dtype)")
        print(f"   Expected: {expected.dtype}")
        print(f"   Actual:   {actual.dtype}")
        actual = actual.to(expected.dtype)
    
    # Ensure same device
    if expected.device != actual.device:
        actual = actual.to(expected.device)
    
    # Calculate errors
    diff = (expected - actual).abs()
    results["max_absolute_error"] = float(diff.max().item())
    results["mean_absolute_error"] = float(diff.mean().item())
    
    # Calculate relative errors (avoid division by zero)
    with np.errstate(divide='ignore', invalid='ignore'):
        relative_diff = diff / (expected.abs() + 1e-8)
        results["max_relative_error"] = float(relative_diff.max().item())
        results["mean_relative_error"] = float(relative_diff.mean().item())
    
    # Check if within tolerance
    absolute_ok = results["max_absolute_error"] <= tolerance
    relative_ok = results["max_relative_error"] <= rtol
    results["within_tolerance"] = absolute_ok and relative_ok
    results["values_match"] = results["within_tolerance"]
    
    return results


def print_comparison_results(results: dict):
    """Print formatted comparison results."""
    print("\n" + "=" * 60)
    print("COMPARISON RESULTS")
    print("=" * 60)
    
    print(f"\nShapes Match: {'✓' if results['shapes_match'] else '❌'}")
    print(f"Dtypes Match: {'✓' if results['dtypes_match'] else '⚠️'}")
    print(f"Values Match: {'✓' if results['values_match'] else '❌'}")
    
    if results["max_absolute_error"] is not None:
        print(f"\nError Metrics:")
        print(f"  Max Absolute Error:  {results['max_absolute_error']:.2e}")
        print(f"  Mean Absolute Error: {results['mean_absolute_error']:.2e}")
        print(f"  Max Relative Error:  {results['max_relative_error']:.2e}")
        print(f"  Mean Relative Error: {results['mean_relative_error']:.2e}")
    
    print(f"\nWithin Tolerance: {'✓ YES' if results['within_tolerance'] else '❌ NO'}")
    
    print("\n" + "=" * 60)


def main():
    """Main test function."""
    print("=" * 60)
    print("Test Step 1: Latent Encoder Tensor Comparison")
    print("=" * 60)
    
    # Load expected tensor
    print("\n[1/3] Loading expected tensor...")
    expected = load_expected_tensor()
    if expected is None:
        return 1
    
    # Get actual tensor from service
    print("\n[2/3] Getting actual tensor from latent_encoder microservice...")
    actual = get_actual_tensor_from_service()
    if actual is None:
        return 1
    
    # Compare tensors
    print("\n[3/3] Comparing tensors...")
    results = compare_tensors(expected, actual)
    
    # Print results
    print_comparison_results(results)
    
    # Return exit code
    if results["values_match"] and results["shapes_match"]:
        print("\n✅ TEST PASSED: Tensors match!")
        return 0
    else:
        print("\n❌ TEST FAILED: Tensors do not match!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

