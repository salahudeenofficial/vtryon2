# Microservice Architecture Analysis

## Current Architecture Issues & Missing Components

### 1. LATENT_ENCODER Service
**Architecture Document Definition:**
- Input: image1 (image path)
- Output: img1_enc (latent encoding)

**Issues Found:**
- ✓ Architecture correctly identifies: LoadImage → ImageScaleToTotalPixels → VAEEncode
- ✗ Missing: VAE model loading specification (vaeloader needs to be initialized)
- ✗ Missing: Image scaling step not clearly documented as part of latent_encoder
- ✗ Missing: Output format specification (tensor format, shape, serialization method)

**Current Implementation:**
```python
loadimage_78 = loadimage.load_image(image=masked_person_path)
imagescaletototalpixels_93 = imagescaletototalpixels.EXECUTE_NORMALIZED(...)
vaeencode_88 = vaeencode.encode(pixels=..., vae=vaeloader_39, ...)
img1_enc = get_value_at_index(vaeencode_88, 0)
```

**Required Changes:**
- Add VAE model initialization as dependency
- Clarify image scaling is part of latent_encoder
- Specify output format (pickle, numpy, tensor file, etc.)

---

### 2. TEXT_ENCODER Service
**Architecture Document Definition:**
- Input: image1, image2, prompt
- Output: t_en_out1 (positive encoding), t_en_out2 (negative encoding)

**Issues Found:**
- ✗ Architecture shows image loading inside text_encoder (should receive pre-processed images)
- ✗ Missing: CLIP model loading specification
- ✗ Missing: VAE model requirement (needed for text encoding in this architecture)
- ✗ Missing: Image scaling/preprocessing requirement not documented
- ✗ Missing: Output format specification
- ✗ Architecture shows image1 needs to be scaled (same as latent_encoder), but this is duplicated

**Current Implementation:**
```python
loadimage_78 = loadimage.load_image(image=masked_person_path)
loadimage_106 = loadimage.load_image(image=cloth_path)
imagescaletototalpixels_93 = imagescaletototalpixels.EXECUTE_NORMALIZED(...)
textencodeqwenimageeditplus_111 = textencodeqwenimageeditplus.EXECUTE_NORMALIZED(
    prompt="...",
    clip=cliploader_38,
    vae=vaeloader_39,
    image1=imagescaletototalpixels_93,
    image2=loadimage_106
)
```

**Required Changes:**
- Clarify: Should receive image paths OR pre-processed images?
- If image paths: Need to specify image preprocessing steps
- Add CLIP model initialization as dependency
- Add VAE model as dependency (architecture shows it)
- Specify output format

---

### 3. SAMPLING Service
**Architecture Document Definition:**
- Input: t_en_out1 (positive text encoding), t_en_out2 (negative text encoding), img1_enc (latent)
- Output: k_out (sampled latent)

**Issues Found:**
- ✗ CRITICAL: Missing model inputs - needs UNET model, LoRA model, and model transformations
- ✗ Missing: Sampling parameters (seed, steps, cfg, sampler_name, scheduler, denoise)
- ✗ Missing: ModelSamplingAuraFlow and CFGNorm transformations
- ✗ Missing: LoraLoaderModelOnly requirement
- ✗ Architecture shows it uses `loraloadermodelonly_89` but doesn't specify as input
- ✗ Missing: Output format specification

**Current Implementation:**
```python
loraloadermodelonly_89 = loraloadermodelonly.load_lora_model_only(...)
modelsamplingauraflow_66 = modelsamplingauraflow.patch_aura(
    shift=3, model=get_value_at_index(loraloadermodelonly_89, 0)
)
cfgnorm_75 = cfgnorm.EXECUTE_NORMALIZED(
    strength=1, model=get_value_at_index(modelsamplingauraflow_66, 0)
)
ksampler_3 = ksampler.sample(
    seed=random.randint(1, 2**64),
    steps=4,
    cfg=1,
    sampler_name="euler",
    scheduler="simple",
    denoise=1,
    model=get_value_at_index(cfgnorm_75, 0),
    positive=t_en_out1,
    negative=t_en_out2,
    latent_image=img1_enc
)
```

**Required Changes:**
- Add model inputs: UNET model, LoRA model path/name
- Add sampling parameters as inputs
- Add model transformation parameters (shift, strength)
- Specify output format

---

### 4. DECODING Service
**Architecture Document Definition:**
- Input: k_out (sampled latent)
- Output: file_name.jpg (decoded image file)

**Issues Found:**
- ✗ Missing: VAE model requirement (needed for decoding)
- ✗ Missing: Output filename specification as input
- ✗ Missing: Output directory specification
- ✓ Architecture correctly identifies: VAEDecode → SaveImage

**Current Implementation:**
```python
vaedecode_8 = vaedecode.decode(
    samples=get_value_at_index(ksampler_3, 0),
    vae=get_value_at_index(vaeloader_39, 0)
)
saveimage_60 = saveimage.save_images(
    filename_prefix=output_filename,
    images=get_value_at_index(vaedecode_8, 0)
)
```

**Required Changes:**
- Add VAE model as dependency
- Add output filename as input parameter
- Add output directory as input parameter
- Specify output format (JPEG, PNG, etc.)

---

## Missing Services

### 5. MODEL_LOADER Service (NEW - Required)
**Purpose:** Load and initialize all AI models needed by other services

**Should Handle:**
- UNETLoader: Load diffusion model
- CLIPLoader: Load CLIP text encoder
- VAELoader: Load VAE encoder/decoder
- LoraLoaderModelOnly: Load LoRA weights

**Issues:**
- Currently models are loaded in main() but should be a separate service
- Models are shared across multiple services - need model registry/cache
- Model loading happens once but used multiple times

**Proposed Architecture:**
- Input: Model configuration (model names/paths)
- Output: Model registry/handle that can be referenced by other services
- OR: Each service loads its own models (less efficient but more isolated)

---

## Shared Dependencies Analysis

### Currently Shared (Need to Determine Strategy):

1. **VAE Model** - Used by:
   - latent_encoder (VAEEncode)
   - text_encoder (TextEncodeQwenImageEditPlus needs VAE)
   - decoding (VAEDecode)

2. **Image Scaling** - Used by:
   - latent_encoder (needs scaled image)
   - text_encoder (needs scaled image1)

3. **Model Loading Infrastructure:**
   - All services need ComfyUI nodes
   - All services need custom nodes initialization
   - All services need sys.path setup

4. **Utility Functions:**
   - get_value_at_index() - used by all services
   - find_path() - used for setup
   - add_comfyui_directory_to_sys_path() - setup

---

## Recommendations

### Option 1: Model Registry Service
Create a separate MODEL_REGISTRY service that:
- Loads all models once
- Exposes models via API/interface
- Other services request models from registry

### Option 2: Model Loading Per Service
Each service loads its own models:
- More isolated
- Less efficient (duplicate loading)
- More independent

### Option 3: Shared Library
Create a shared Python package with:
- Model loading utilities
- Common functions (get_value_at_index, etc.)
- Shared dependencies

---

## Input/Output Format Specifications Needed

For each service, specify:
1. **Input Format:**
   - File paths (strings)
   - Pre-processed tensors (pickle/numpy/torch files)
   - JSON/REST API format
   - Message queue format

2. **Output Format:**
   - File paths (where outputs are saved)
   - Serialized tensors (format: pickle/numpy/torch)
   - JSON responses
   - Standardized data format

3. **Error Handling:**
   - Error response format
   - Validation failures
   - Model loading failures

---

## Architecture Document Corrections Needed

1. **latent_encoder:**
   - Add: VAE model dependency
   - Specify: Output format (tensor file path or serialized tensor)
   - Clarify: Image scaling is part of this service

2. **text_encoder:**
   - Fix: Input should be image paths, not loaded images
   - Add: CLIP model dependency
   - Add: VAE model dependency (for image encoding in text encoder)
   - Add: Image preprocessing steps
   - Specify: Output format

3. **sampling:**
   - Add: UNET model dependency
   - Add: LoRA model dependency
   - Add: Sampling parameters (seed, steps, cfg, etc.)
   - Add: Model transformation parameters
   - Specify: Output format

4. **decoding:**
   - Add: VAE model dependency
   - Add: Output filename parameter
   - Add: Output directory parameter
   - Specify: Output format

5. **Add: MODEL_LOADER service** (new)

---

## Next Steps

1. Create microservice directory structure
2. Extract each service into separate Python module
3. Define input/output contracts (interfaces)
4. Create requirements.txt for each service
5. Create shared utilities library
6. Document API contracts for each service

