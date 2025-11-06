"""
Test Step 4: Compare decoding output tensors

This script compares:
1. Expected tensor from workflow_script_serial_test.py:
   - test_outputs/decoding_output.pt
2. Actual tensor from decoding microservice

It validates that the microservice produces the same output as the reference implementation.
"""
import sys
import torch
from pathlib import Path
import numpy as np
from typing import Optional


def load_expected_tensor(expected_path: str = "./test_outputs/decoding_output.pt") -> Optional[torch.Tensor]:
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
        import traceback
        traceback.print_exc()
        return None


def get_actual_tensor_from_service(
    latent_path: str = "test_outputs/sampling_output.pt",
    vae_model_name: str = "qwen_image_vae.safetensors",
    output_dir: str = "./test_outputs_actual"
) -> Optional[torch.Tensor]:
    """Get actual tensor from decoding microservice."""
    # Add microservice directory to path
    microservice_dir = Path(__file__).parent / "microservices" / "decoding"
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
        
        decode_latent_to_image = service_module.decode_latent_to_image
        
        print(f"\nRunning decoding microservice...")
        print(f"  Latent: {latent_path}")
        print(f"  VAE Model: {vae_model_name}")
        
        # Check if input file exists
        latent_file = Path(latent_path)
        if not latent_file.exists():
            # Try alternative paths
            alt_paths = [
                Path("test_outputs") / latent_file.name,
                Path("input") / latent_file.name,
                latent_file.name,
            ]
            
            found = False
            for alt_path in alt_paths:
                if alt_path.exists():
                    latent_path = str(alt_path)
                    print(f"  Found latent at: {latent_path}")
                    found = True
                    break
            
            if not found:
                print(f"❌ Latent file not found: {latent_path}")
                print("   Tried paths:")
                for alt_path in alt_paths:
                    print(f"     - {alt_path}")
                return None
        
        # Call service with save_image=True to save image and get tensor
        result = decode_latent_to_image(
            latent=latent_path,
            vae_model_name=vae_model_name,
            output_filename="test_output",
            output_dir=output_dir,
            output_format="jpg",
            save_image=True  # Save image file
        )
        
        if result["status"] != "success":
            print(f"❌ Service returned error: {result.get('error_code')}")
            print(f"   Error message: {result.get('error_message')}")
            return None
        
        # Extract tensor from result
        tensor = result.get("image_tensor")
        if tensor is None:
            print("❌ Service did not return image_tensor")
            return None
        
        # Print image file info if saved
        if result.get("image_file_path"):
            print(f"✓ Image saved to: {result['image_file_path']}")
            if result.get("file_size"):
                print(f"  File size: {result['file_size']} bytes")
        
        print(f"✓ Got actual tensor from service")
        print(f"  Shape: {tensor.shape}")
        print(f"  Dtype: {tensor.dtype}")
        
        return tensor
        
    except Exception as e:
        print(f"❌ Error running service: {type(e).__name__}")
        print(f"   Error message: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_tensors(expected: torch.Tensor, actual: torch.Tensor, 
                   absolute_tolerance: float = 1e-5, 
                   relative_tolerance: float = 1e-4) -> dict:
    """
    Compare two tensors and return detailed comparison results.
    
    Args:
        expected: Expected tensor
        actual: Actual tensor
        absolute_tolerance: Absolute tolerance for comparison
        relative_tolerance: Relative tolerance for comparison
    
    Returns:
        dict: Comparison results with metrics
    """
    results = {
        "shapes_match": False,
        "dtypes_match": False,
        "values_match": False,
        "max_absolute_error": None,
        "mean_absolute_error": None,
        "max_relative_error": None,
        "mean_relative_error": None,
        "within_tolerance": False
    }
    
    # Check shapes
    results["shapes_match"] = expected.shape == actual.shape
    if not results["shapes_match"]:
        print(f"⚠️  Shape mismatch: expected {expected.shape}, got {actual.shape}")
        return results
    
    # Check dtypes
    results["dtypes_match"] = expected.dtype == actual.dtype
    if not results["dtypes_match"]:
        print(f"⚠️  Dtype mismatch: expected {expected.dtype}, got {actual.dtype}")
        # Convert to same dtype for comparison
        if expected.dtype != actual.dtype:
            # Convert to float32 for comparison
            expected = expected.float()
            actual = actual.float()
    
    # Calculate errors
    expected_np = expected.detach().cpu().numpy()
    actual_np = actual.detach().cpu().numpy()
    
    # Absolute errors
    absolute_errors = np.abs(expected_np - actual_np)
    results["max_absolute_error"] = float(np.max(absolute_errors))
    results["mean_absolute_error"] = float(np.mean(absolute_errors))
    
    # Relative errors (avoid division by zero)
    with np.errstate(divide='ignore', invalid='ignore'):
        relative_errors = np.abs((expected_np - actual_np) / (np.abs(expected_np) + 1e-10))
        results["max_relative_error"] = float(np.max(relative_errors))
        results["mean_relative_error"] = float(np.mean(relative_errors))
    
    # Check if within tolerance
    absolute_ok = results["max_absolute_error"] < absolute_tolerance
    relative_ok = results["max_relative_error"] < relative_tolerance
    
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
        print(f"  Mean Relative Error:  {results['mean_relative_error']:.2e}")
    
    print(f"\nWithin Tolerance: {'✓ YES' if results['within_tolerance'] else '❌ NO'}")
    
    print("\n" + "=" * 60)


def main():
    """Main test function."""
    print("=" * 60)
    print("Test Step 4: Decoding Tensor Comparison")
    print("=" * 60)
    
    # Load expected tensor
    print("\n[1/3] Loading expected tensor...")
    expected = load_expected_tensor()
    if expected is None:
        return 1
    
    # Get actual tensor from service
    print("\n[2/3] Getting actual tensor from decoding microservice...")
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

