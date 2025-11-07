# Sampling Tensor Difference Analysis

## Test Results Summary

- **Shapes Match**: ✓ `torch.Size([1, 16, 1, 147, 110])`
- **Dtypes Match**: ✓
- **Values Match**: ❌

### Error Metrics
- **Max Absolute Error**: 5.94e+00 (~5.94)
- **Mean Absolute Error**: 1.09e+00 (~1.09)
- **Max Relative Error**: 8.26e+04 (very high - suggests division by near-zero)
- **Mean Relative Error**: 8.62e+00 (~8.62)

## Potential Causes of Differences

### 1. **Model Loading State Differences** ⚠️ HIGH PROBABILITY

**Issue**: Models are loaded separately in the microservice vs. being loaded together in the workflow.

**Impact**: 
- Model internal state (buffers, running stats) might differ
- Device placement might differ
- Model evaluation mode might not be set consistently

**Evidence**:
- Workflow loads all models together: UNET → LoRA → AuraFlow → CFGNorm
- Microservice loads models in isolation each time
- No explicit `model.eval()` calls visible

**Recommendation**: 
- Ensure models are in eval mode: `model.eval()`
- Check if model state is preserved between calls
- Verify device placement matches workflow

### 2. **Conditioning Format Differences** ⚠️ MEDIUM PROBABILITY

**Issue**: Even though we fixed the format to `[[tensor, metadata_dict]]`, there might be subtle differences.

**Potential Issues**:
- Metadata dict content might differ (empty `{}` vs. actual metadata)
- Conditioning might need specific keys in metadata dict
- Text encoder outputs might have metadata that we're losing

**Evidence**:
- Workflow uses `t_en_out1_for_sampler` directly (original format)
- Microservice loads from `.pt` file (just tensor) and wraps as `[[tensor, {}]]`
- Missing metadata might affect sampling behavior

**Recommendation**:
- Check what metadata the text encoder actually outputs
- Preserve original metadata when loading from files
- Compare conditioning structures byte-by-byte

### 3. **Model Transformation Order/State** ⚠️ MEDIUM PROBABILITY

**Issue**: The order of model transformations might affect internal state.

**Sequence in Workflow**:
1. Load UNET
2. Apply LoRA → `loraloadermodelonly_89`
3. Apply AuraFlow → `modelsamplingauraflow_66`
4. Apply CFGNorm → `cfgnorm_75`
5. Sample

**Sequence in Microservice**:
1. Load UNET
2. Apply LoRA → `lora_model`
3. Apply AuraFlow → `auraflow_model`
4. Apply CFGNorm → `final_model`
5. Sample

**Potential Issues**:
- Model transformations might modify internal state
- State might not be reset between transformations
- Different model instances might have different internal buffers

**Recommendation**:
- Verify model transformations are deterministic
- Check if transformations modify model in-place
- Compare model states after each transformation step

### 4. **Floating Point Precision Accumulation** ⚠️ LOW-MEDIUM PROBABILITY

**Issue**: Different operation orders can accumulate floating point errors differently.

**Factors**:
- CUDA vs CPU operations
- Different CUDA versions
- Different operation order in matrix multiplications
- Non-deterministic CUDA operations (even with same seed)

**Evidence**:
- Mean absolute error is reasonable (~1.09)
- Max absolute error is moderate (~5.94)
- High relative error suggests some values are very small (near zero)

**Recommendation**:
- Check if CUDA operations are deterministic
- Verify same CUDA version is used
- Check for any non-deterministic operations

### 5. **Random Number Generation State** ⚠️ LOW PROBABILITY

**Issue**: Even with same seed, random state might differ if models are loaded in different order.

**Potential Issues**:
- PyTorch random state might be affected by model loading
- CUDA random state might differ
- Different number of operations before sampling

**Evidence**:
- Same seed (12345) is used
- But model loading happens before sampling
- Random state might be affected by model initialization

**Recommendation**:
- Set random seed right before sampling
- Use `torch.manual_seed()` and `torch.cuda.manual_seed_all()`
- Verify random state is consistent

### 6. **Input Tensor Differences** ⚠️ MEDIUM PROBABILITY

**Issue**: Input tensors (positive/negative conditioning, latent) might have subtle differences.

**Potential Issues**:
- Loading from `.pt` files might lose precision
- Tensor device placement might differ
- Tensor dtype might differ (even if shapes match)

**Evidence**:
- Tensors are saved and loaded from files
- File format might not preserve exact values
- Device placement might differ (CPU vs GPU)

**Recommendation**:
- Compare input tensors byte-by-byte
- Verify same device placement
- Check dtype preservation

### 7. **Model Device Placement** ⚠️ MEDIUM PROBABILITY

**Issue**: Models might be on different devices or moved during execution.

**Potential Issues**:
- Model might be on CPU in one case, GPU in another
- Device transfers might introduce precision differences
- CUDA operations vs CPU operations have different precision

**Evidence**:
- Workflow runs in full ComfyUI context
- Microservice runs in isolated context
- Device management might differ

**Recommendation**:
- Verify models are on same device
- Check device placement after each transformation
- Ensure consistent device usage

## Diagnostic Steps (Without Code Changes)

### Step 1: Compare Input Tensors
```python
# Load and compare:
# - positive_encoding tensors
# - negative_encoding tensors  
# - latent_image tensors
# Check: shapes, dtypes, values, devices
```

### Step 2: Compare Model States
```python
# After loading UNET:
# - Compare model parameters
# - Compare model buffers
# - Compare model device

# After each transformation:
# - Compare model state after LoRA
# - Compare model state after AuraFlow
# - Compare model state after CFGNorm
```

### Step 3: Compare Conditioning Structures
```python
# Check exact structure:
# - Workflow: t_en_out1_for_sampler structure
# - Microservice: positive_cond structure
# - Compare metadata dict contents
```

### Step 4: Check Random State
```python
# Before sampling:
# - Set explicit random seeds
# - Check PyTorch random state
# - Check CUDA random state
```

### Step 5: Compare Intermediate Outputs
```python
# After each step:
# - UNET output
# - LoRA output
# - AuraFlow output
# - CFGNorm output
# - Final model state
```

## Most Likely Root Causes (Ranked)

1. **Model State/Eval Mode** (40% probability)
   - Models might not be in eval mode
   - Internal state might differ

2. **Conditioning Metadata** (30% probability)
   - Missing metadata in conditioning dict
   - Empty `{}` vs. actual metadata

3. **Model Transformation State** (20% probability)
   - Transformations might modify state differently
   - Order of operations might matter

4. **Input Tensor Precision** (10% probability)
   - File save/load might lose precision
   - Device placement differences

## Recommendations for Investigation

1. **Add Debug Logging**:
   - Log model eval mode status
   - Log conditioning structure details
   - Log device placement at each step
   - Log random seed state

2. **Compare Intermediate States**:
   - Save model state after each transformation
   - Compare conditioning structures byte-by-byte
   - Compare input tensors exactly

3. **Verify Determinism**:
   - Run workflow twice, compare outputs
   - Run microservice twice, compare outputs
   - Check if differences are consistent

4. **Check Model Loading**:
   - Verify same model files are used
   - Check model loading parameters match exactly
   - Verify weight_dtype matches

## Expected vs Actual Behavior

**Expected**: With same seed and inputs, outputs should match exactly (or very closely).

**Actual**: Outputs differ significantly, suggesting:
- Non-deterministic operations
- Different model states
- Missing metadata or context
- Precision differences

## Next Steps

1. **Verify Inputs Match**: Compare all input tensors exactly
2. **Check Model States**: Compare model parameters and buffers
3. **Inspect Conditioning**: Compare conditioning structures in detail
4. **Test Determinism**: Run same inputs multiple times
5. **Add Debugging**: Log intermediate states for comparison



