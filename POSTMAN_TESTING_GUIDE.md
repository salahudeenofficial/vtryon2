# Postman Testing Guide for Virtual Try-On API

## Step-by-Step Postman Setup

### Step 1: Create a New Request

1. Open Postman
2. Click **"New"** → **"HTTP Request"**
3. Name it: `Virtual Try-On - POST /tryon_extracted`
4. Set method to **POST**

### Step 2: Set the URL

Enter the endpoint URL:
```
http://localhost:8000/tryon_extracted
```

Or if testing on a remote server:
```
http://your-server-ip:8000/tryon_extracted
```

### Step 3: Configure Request Body

1. Go to the **"Body"** tab
2. Select **"form-data"** (NOT raw or x-www-form-urlencoded)

### Step 4: Add Form Fields

Add three fields in the form-data section:

#### Field 1: `image` (File)
- **Key**: `image`
- **Type**: Change from "Text" to **"File"** (click the dropdown next to the key)
- **Value**: Click **"Select Files"** and choose your person image (PNG or JPEG)

#### Field 2: `mask_type` (Text)
- **Key**: `mask_type`
- **Type**: Keep as **"Text"**
- **Value**: Enter one of:
  - `upper_body` (for shirts, tops)
  - `lower_body` (for pants, skirts)
  - `other` (no masking)

#### Field 3: `prompt` (Text)
- **Key**: `prompt`
- **Type**: Keep as **"Text"**
- **Value**: Enter your prompt, for example:
  ```
  by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1.
  ```

### Step 5: Send the Request

1. Click the **"Send"** button
2. Wait for the response (may take 30-75 seconds)

### Step 6: Save the Response

1. The response will be an image file
2. Click **"Save Response"** → **"Save to a file"**
3. Choose a location and filename (e.g., `tryon_result.png`)

## Visual Guide

```
┌─────────────────────────────────────────┐
│ POST  http://localhost:8000/tryon_extracted │
├─────────────────────────────────────────┤
│ Params | Authorization | Headers | Body │ ← Click "Body"
├─────────────────────────────────────────┤
│ ○ none  ○ form-data  ○ x-www-form...   │ ← Select "form-data"
│                                         │
│ Key          Value        Type          │
│ ────────────────────────────────────── │
│ image        [Select...]  File ▼        │ ← Upload image
│ mask_type    upper_body   Text          │ ← Enter mask type
│ prompt       by using...  Text          │ ← Enter prompt
│                                         │
│                    [Send]               │
└─────────────────────────────────────────┘
```

## Complete Example Configuration

### Request Details:
- **Method**: POST
- **URL**: `http://localhost:8000/tryon_extracted`
- **Body Type**: form-data

### Form Fields:
| Key | Type | Value |
|-----|------|-------|
| `image` | File | `person.jpg` (your image file) |
| `mask_type` | Text | `upper_body` |
| `prompt` | Text | `by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1.` |

## Testing Different Scenarios

### Test 1: Upper Body Try-On
```
URL: http://localhost:8000/tryon_extracted
Method: POST
Body (form-data):
  - image: [person.jpg] (File)
  - mask_type: upper_body (Text)
  - prompt: by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1. (Text)
```

### Test 2: Lower Body Try-On
```
URL: http://localhost:8000/tryon_extracted
Method: POST
Body (form-data):
  - image: [person.jpg] (File)
  - mask_type: lower_body (Text)
  - prompt: by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1. (Text)
```

### Test 3: Health Check
```
URL: http://localhost:8000/health
Method: GET
Body: None
```

## Expected Responses

### Success Response (200 OK)
- **Status**: `200 OK`
- **Content-Type**: `image/png`
- **Body**: Binary image data
- **Action**: Save the response as a PNG file

### Error Responses

#### 400 Bad Request
```json
{
  "detail": "mask_type must be one of ['upper_body', 'lower_body', 'other'], got 'invalid_type'"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Error processing request: cloth.png not found in input directory. Please provide a cloth image."
}
```

## Postman Collection Setup

### Create a Collection

1. Click **"New"** → **"Collection"**
2. Name it: `Virtual Try-On API`
3. Add the requests to this collection

### Save as Collection

You can export the collection for sharing:

1. Right-click on collection
2. Select **"Export"**
3. Choose **"Collection v2.1"**
4. Save as JSON file

### Import Collection (JSON)

Here's a Postman Collection JSON you can import:

```json
{
  "info": {
    "name": "Virtual Try-On API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Try-On - Upper Body",
      "request": {
        "method": "POST",
        "header": [],
        "body": {
          "mode": "formdata",
          "formdata": [
            {
              "key": "image",
              "type": "file",
              "src": []
            },
            {
              "key": "mask_type",
              "value": "upper_body",
              "type": "text"
            },
            {
              "key": "prompt",
              "value": "by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1.",
              "type": "text"
            }
          ]
        },
        "url": {
          "raw": "http://localhost:8000/tryon_extracted",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["tryon_extracted"]
        }
      }
    },
    {
      "name": "Try-On - Lower Body",
      "request": {
        "method": "POST",
        "header": [],
        "body": {
          "mode": "formdata",
          "formdata": [
            {
              "key": "image",
              "type": "file",
              "src": []
            },
            {
              "key": "mask_type",
              "value": "lower_body",
              "type": "text"
            },
            {
              "key": "prompt",
              "value": "by using the green masked area from Picture 3 as a reference for position place the garment from Picture 2 on the person from Picture 1.",
              "type": "text"
            }
          ]
        },
        "url": {
          "raw": "http://localhost:8000/tryon_extracted",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["tryon_extracted"]
        }
      }
    },
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/health",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["health"]
        }
      }
    }
  ]
}
```

**To import:**
1. Click **"Import"** in Postman
2. Paste the JSON above or select "Raw text"
3. Click **"Import"**

## Tips & Best Practices

### 1. Set Timeout
- Go to **Settings** → **General**
- Increase **"Request timeout"** to 300 seconds (5 minutes)
- Processing can take 30-75 seconds

### 2. Use Environment Variables
Create an environment with:
- `base_url`: `http://localhost:8000`
- Then use `{{base_url}}/tryon_extracted` in requests

### 3. Save Responses
- Right-click on response → **"Save Response"**
- Or use **Tests** tab to auto-save:
```javascript
pm.response.to.have.status(200);
const fs = require('fs');
fs.writeFileSync('result.png', pm.response.body);
```

### 4. Add Tests (Optional)
In the **Tests** tab, add:
```javascript
// Check status
pm.test("Status is 200", function () {
    pm.response.to.have.status(200);
});

// Check content type
pm.test("Content-Type is image/png", function () {
    pm.response.to.have.header("Content-Type", "image/png");
});

// Check response time
pm.test("Response time is less than 120000ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(120000);
});
```

## Troubleshooting in Postman

### Issue: "Could not get response"
- **Solution**: Check if server is running (`python api_server.py`)
- Verify URL is correct

### Issue: "Request timeout"
- **Solution**: Increase timeout in Postman settings
- Processing takes time, be patient

### Issue: "400 Bad Request"
- **Solution**: 
  - Verify `mask_type` is exactly: `upper_body`, `lower_body`, or `other`
  - Check all three fields are filled
  - Ensure image file is selected (not just text path)

### Issue: "500 Internal Server Error"
- **Solution**:
  - Check server logs for detailed error
  - Verify `input/cloth.png` exists
  - Ensure models are downloaded

### Issue: Response is not an image
- **Solution**: 
  - Check if error JSON was returned instead
  - Verify request format (must be form-data, not raw JSON)
  - Check server logs

## Quick Reference Card

```
┌─────────────────────────────────────────────┐
│ POSTMAN QUICK REFERENCE                     │
├─────────────────────────────────────────────┤
│ Method: POST                                │
│ URL: http://localhost:8000/tryon_extracted │
│ Body: form-data                             │
│                                             │
│ Fields:                                     │
│   image      → File (select image)          │
│   mask_type  → Text (upper_body/lower_body) │
│   prompt     → Text (your prompt)           │
│                                             │
│ Timeout: 300 seconds                        │
│ Expected: 200 OK, image/png                 │
└─────────────────────────────────────────────┘
```

## Video Walkthrough Steps

1. **Open Postman** → Create new request
2. **Set Method** → POST
3. **Enter URL** → `http://localhost:8000/tryon_extracted`
4. **Go to Body tab** → Select "form-data"
5. **Add image field** → Change to "File" → Select image
6. **Add mask_type** → Enter "upper_body"
7. **Add prompt** → Enter your prompt text
8. **Click Send** → Wait for response
9. **Save response** → Right-click → Save to file

That's it! You should now have a generated try-on image saved.

