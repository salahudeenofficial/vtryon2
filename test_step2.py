"""
Test Step 2: Compare text encoder output tensors

This script compares:
1. Expected tensors from workflow_script_serial_test.py:
   - test_outputs/text_encoder_positive_output.pt
   - test_outputs/text_encoder_negative_output.pt
2. Actual tensors from text_encoder microservice

It validates that the microservice produces the same outputs as the reference implementation.
"""
import sys
import torch
from pathlib import Path
import numpy as np
from typing import Optional, Tuple


def load_expected_tensors(
    positive_path: str = "./test_outputs/text_encoder_positive_output.pt",
    negative_path: str = "./test_outputs/text_encoder_negative_output.pt"
) -> Optional[Tuple[torch.Tensor, torch.Tensor]]:
    """Load expected tensors from workflow_script_serial_test.py output."""
    positive_file = Path(positive_path)
    negative_file = Path(negative_path)
    
    if not positive_file.exists():
        print(f"❌ Expected positive tensor file not found: {positive_path}")
        print("   Please run workflow_script_serial_test.py first to generate expected outputs.")
        return None
    
    if not negative_file.exists():
        print(f"❌ Expected negative tensor file not found: {negative_path}")
        print("   Please run workflow_script_serial_test.py first to generate expected outputs.")
        return None
    
    try:
        positive_tensor = torch.load(positive_file)
        negative_tensor = torch.load(negative_file)
        print(f"✓ Loaded expected positive tensor from: {positive_path}")
        print(f"  Shape: {positive_tensor.shape}")
        print(f"  Dtype: {positive_tensor.dtype}")
        print(f"✓ Loaded expected negative tensor from: {negative_path}")
        print(f"  Shape: {negative_tensor.shape}")
        print(f"  Dtype: {negative_tensor.dtype}")
        return positive_tensor, negative_tensor
    except Exception as e:
        print(f"❌ Error loading expected tensors: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_actual_tensors_from_service(
    image1_path: str = "input/masked_person.png",
    image2_path: str = "input/cloth.png",
    prompt: str = "by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1.",
    negative_prompt: str = "",
    clip_model_name: str = "qwen_2.5_vl_7b_fp8_scaled.safetensors",
    vae_model_name: str = "qwen_image_vae.safetensors",
    output_dir: str = "./test_outputs_actual"
) -> Optional[Tuple[torch.Tensor, torch.Tensor]]:
    """Get actual tensors from text_encoder microservice."""
    # Add microservice directory to path
    microservice_dir = Path(__file__).parent / "microservices" / "text_encoder"
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
        
        encode_text_and_images = service_module.encode_text_and_images
        
        print(f"\nRunning text_encoder microservice...")
        print(f"  Image1: {image1_path}")
        print(f"  Image2: {image2_path}")
        print(f"  Prompt: {prompt[:80]}..." if len(prompt) > 80 else f"  Prompt: {prompt}")
        print(f"  Negative Prompt: {negative_prompt if negative_prompt else '(empty)'}")
        print(f"  CLIP Model: {clip_model_name}")
        print(f"  VAE Model: {vae_model_name}")
        
        # Check if images exist
        image1_path_obj = Path(image1_path)
        image2_path_obj = Path(image2_path)
        
        # Try alternative paths for image1
        if not image1_path_obj.exists():
            alt_paths = [
                Path("input") / "masked_person.png",
                Path("masked_person.png"),
                Path("input") / "masked_person.jpg",
            ]
            found = False
            for alt_path in alt_paths:
                if alt_path.exists():
                    image1_path = str(alt_path)
                    print(f"  Using alternative path for image1: {image1_path}")
                    found = True
                    break
            if not found:
                print(f"❌ Image1 file not found: {image1_path}")
                return None
        
        # Try alternative paths for image2
        if not image2_path_obj.exists():
            alt_paths = [
                Path("input") / "cloth.png",
                Path("cloth.png"),
                Path("input") / "cloth.jpg",
            ]
            found = False
            for alt_path in alt_paths:
                if alt_path.exists():
                    image2_path = str(alt_path)
                    print(f"  Using alternative path for image2: {image2_path}")
                    found = True
                    break
            if not found:
                print(f"❌ Image2 file not found: {image2_path}")
                return None
        
        # Call the service with save_tensor=False to get tensors directly
        result = encode_text_and_images(
            image1_path=image1_path,
            image2_path=image2_path,
            prompt=prompt,
            negative_prompt=negative_prompt,
            clip_model_name=clip_model_name,
            vae_model_name=vae_model_name,
            output_dir=output_dir,
            upscale_method="lanczos",
            megapixels=1.0,
            save_tensor=False  # Return tensors instead of saving
        )
        
        if result["status"] != "success":
            print(f"❌ Service returned error: {result.get('error_code')}")
            print(f"   Error message: {result.get('error_message')}")
            return None
        
        positive_tensor = result.get("positive_encoding_tensor")
        negative_tensor = result.get("negative_encoding_tensor")
        
        if positive_tensor is None:
            print("❌ Service did not return positive tensor")
            print(f"   Result keys: {result.keys()}")
            return None
        
        if negative_tensor is None:
            print("❌ Service did not return negative tensor")
            print(f"   Result keys: {result.keys()}")
            return None
        
        print(f"✓ Got actual tensors from service")
        print(f"  Positive tensor shape: {positive_tensor.shape}")
        print(f"  Positive tensor dtype: {positive_tensor.dtype}")
        print(f"  Negative tensor shape: {negative_tensor.shape}")
        print(f"  Negative tensor dtype: {negative_tensor.dtype}")
        return positive_tensor, negative_tensor
        
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
    tensor_name: str = "tensor",
    tolerance: float = 1e-5,
    rtol: float = 1e-4
) -> dict:
    """
    Compare two tensors and return detailed comparison results.
    
    Args:
        expected: Expected tensor
        actual: Actual tensor
        tensor_name: Name of tensor for reporting
        tolerance: Absolute tolerance for comparison
        rtol: Relative tolerance for comparison
    
    Returns:
        dict with comparison results
    """
    results = {
        "tensor_name": tensor_name,
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
        print(f"\n❌ {tensor_name} shape mismatch!")
        print(f"   Expected: {expected.shape}")
        print(f"   Actual:   {actual.shape}")
        return results
    
    print(f"\n✓ {tensor_name} shapes match: {expected.shape}")
    
    # Check dtypes
    results["dtypes_match"] = expected.dtype == actual.dtype
    results["details"]["expected_dtype"] = str(expected.dtype)
    results["details"]["actual_dtype"] = str(actual.dtype)
    
    if not results["dtypes_match"]:
        print(f"\n⚠️  {tensor_name} dtype mismatch (converting actual to expected dtype)")
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


def print_comparison_results(results: dict, tensor_name: str = "Tensor"):
    """Print formatted comparison results."""
    print("\n" + "=" * 60)
    print(f"{tensor_name.upper()} COMPARISON RESULTS")
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
    print("Test Step 2: Text Encoder Tensor Comparison")
    print("=" * 60)
    
    # Load expected tensors
    print("\n[1/4] Loading expected tensors...")
    expected_tensors = load_expected_tensors()
    if expected_tensors is None:
        return 1
    
    expected_positive, expected_negative = expected_tensors
    
    # Get actual tensors from service
    print("\n[2/4] Getting actual tensors from text_encoder microservice...")
    actual_tensors = get_actual_tensors_from_service()
    if actual_tensors is None:
        return 1
    
    actual_positive, actual_negative = actual_tensors
    
    # Compare positive tensors
    print("\n[3/4] Comparing positive tensors...")
    positive_results = compare_tensors(
        expected_positive,
        actual_positive,
        tensor_name="Positive Tensor"
    )
    print_comparison_results(positive_results, "Positive Tensor")
    
    # Compare negative tensors
    print("\n[4/4] Comparing negative tensors...")
    negative_results = compare_tensors(
        expected_negative,
        actual_negative,
        tensor_name="Negative Tensor"
    )
    print_comparison_results(negative_results, "Negative Tensor")
    
    # Overall results
    print("\n" + "=" * 60)
    print("OVERALL TEST RESULTS")
    print("=" * 60)
    
    positive_pass = positive_results["values_match"] and positive_results["shapes_match"]
    negative_pass = negative_results["values_match"] and negative_results["shapes_match"]
    
    print(f"\nPositive Tensor: {'✅ PASSED' if positive_pass else '❌ FAILED'}")
    print(f"Negative Tensor: {'✅ PASSED' if negative_pass else '❌ FAILED'}")
    
    if positive_pass and negative_pass:
        print("\n✅ TEST PASSED: All tensors match!")
        return 0
    else:
        print("\n❌ TEST FAILED: Some tensors do not match!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)



