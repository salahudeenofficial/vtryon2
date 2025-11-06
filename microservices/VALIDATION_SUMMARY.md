# Architecture Validation Summary

## Issues Found in microservice_archetecture.txt

### 1. LATENT_ENCODER Service
**Missing Components:**
- ✗ VAE model loading specification (vaeloader initialization)
- ✗ Output format specification (how latent is saved/transmitted)
- ✗ Error handling specification

**Found in Code:**
- ✓ Image loading (LoadImage)
- ✓ Image scaling (ImageScaleToTotalPixels)
- ✓ VAE encoding (VAEEncode)

---

### 2. TEXT_ENCODER Service
**Missing Components:**
- ✗ CLIP model loading specification
- ✗ VAE model dependency (required but not documented)
- ✗ Image preprocessing steps (scaling) not clearly documented
- ✗ Input format specification (paths vs pre-processed images)
- ✗ Output format specification

**Found in Code:**
- ✓ Image loading (LoadImage for both images)
- ✓ Image scaling (ImageScaleToTotalPixels for image1)
- ✓ Text encoding (TextEncodeQwenImageEditPlus)

**Issues:**
- Architecture shows image loading inside service, but should specify if it receives paths or pre-processed images
- Image scaling is duplicated (same as latent_encoder) - needs clarification

---

### 3. SAMPLING Service
**CRITICAL Missing Components:**
- ✗ **UNET model dependency** (required but not in inputs)
- ✗ **LoRA model dependency** (required but not in inputs)
- ✗ **Model transformation steps** (ModelSamplingAuraFlow, CFGNorm)
- ✗ **Sampling parameters** (seed, steps, cfg, sampler_name, scheduler, denoise)
- ✗ **Model transformation parameters** (shift, strength)
- ✗ Output format specification

**Found in Code:**
- ✓ Model transformations (ModelSamplingAuraFlow.patch_aura, CFGNorm.EXECUTE_NORMALIZED)
- ✓ Sampling (KSampler.sample)
- ✓ LoRA loading (LoraLoaderModelOnly)

**Issues:**
- Architecture shows `loraloadermodelonly_89` used but doesn't specify as input
- Missing all sampling parameters in architecture document

---

### 4. DECODING Service
**Missing Components:**
- ✗ VAE model dependency (required but not documented)
- ✗ Output filename parameter
- ✗ Output directory parameter
- ✗ Output format specification (JPEG, PNG, etc.)

**Found in Code:**
- ✓ VAE decoding (VAEDecode.decode)
- ✓ Image saving (SaveImage.save_images)

---

## Shared Dependencies Analysis

### Models Required:
1. **VAE Model** (`qwen_image_vae.safetensors`)
   - Used by: latent_encoder, text_encoder, decoding
   - Strategy: Load once, share via service registry OR load per service

2. **CLIP Model** (`qwen_2.5_vl_7b_fp8_scaled.safetensors`)
   - Used by: text_encoder only
   - Strategy: Load in text_encoder service

3. **UNET Model** (`qwen_image_edit_2509_fp8_e4m3fn.safetensors`)
   - Used by: sampling service
   - Strategy: Load in sampling service

4. **LoRA Model** (`Qwen-Image-Lightning-4steps-V2.0.safetensors`)
   - Used by: sampling service
   - Strategy: Load in sampling service

### Common Utilities:
- `get_value_at_index()` - Used by all services
- `find_path()` - Setup utility
- ComfyUI path setup - Required by all services
- Custom nodes initialization - Required by all services

---

## Architecture Document Corrections Needed

### Service 1: latent_encoder
**Add to Inputs:**
- vae_model_name (str, optional): VAE model filename

**Add to Outputs:**
- output_format (str): "tensor_file" or "serialized"
- latent_file_path (str): Path to saved latent
- metadata_file (str): Path to JSON metadata

---

### Service 2: text_encoder
**Add to Inputs:**
- clip_model_name (str): CLIP model filename
- vae_model_name (str): VAE model filename (required for this architecture)
- image1_preprocessed (bool, optional): Whether image1 is already scaled

**Fix:**
- Clarify: Input should be image paths, not loaded images
- Document: Image scaling happens inside service for image1

---

### Service 3: sampling
**Add to Inputs:**
- unet_model_name (str): UNET model filename
- lora_model_name (str): LoRA model filename
- lora_strength (float): LoRA strength
- sampling_params (dict): seed, steps, cfg, sampler_name, scheduler, denoise
- model_transform_params (dict): shift, strength

**Add to Outputs:**
- sampled_latent_file (str): Path to saved latent
- metadata_file (str): Path to JSON metadata

---

### Service 4: decoding
**Add to Inputs:**
- vae_model_name (str): VAE model filename
- output_filename (str): Base name for output
- output_dir (str): Output directory
- output_format (str): Image format (jpg, png, webp)

**Add to Outputs:**
- image_file_path (str): Path to saved image
- image_shape (tuple): Image dimensions

---

## Additional Service Needed

### Service 5: model_loader (Optional)
**Purpose:** Centralized model loading and caching

**Why:**
- Models are large and expensive to load
- Multiple services need same models
- Can reduce memory usage with shared instances

**Alternative:** Each service loads its own models (simpler but less efficient)

---

## Recommended Next Steps

1. ✅ Created directory structure
2. ✅ Created API documentation for each service
3. ✅ Created requirements.txt for each service
4. ⏳ Implement each microservice
5. ⏳ Create shared_utils package
6. ⏳ Define inter-service communication protocol
7. ⏳ Create Dockerfiles for each service
8. ⏳ Set up orchestration configuration

