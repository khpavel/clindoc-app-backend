# API Specification

## Base URL
All endpoints are prefixed with `/api/v1`

---

## CSR Endpoints

### Create Section Version
**Method:** `POST`  
**Path:** `/api/v1/csr/sections/{section_id}/versions`

**Path Parameters:**
- `section_id` (integer, required): The ID of the CSR section

**Request Body:**
```json
{
  "text": "string",
  "created_by": "string | null"
}
```

**Response Body:**
```json
{
  "id": 0,
  "text": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "created_by": "string | null",
  "source": "string"
}
```

**Error Responses:**
- `404`: Section not found

---

## AI Endpoints

### Generate Section Text
**Method:** `POST`  
**Path:** `/api/v1/ai/generate-section-text`

**Request Body:**
```json
{
  "section_id": 0,
  "prompt": "string"
}
```

**Response Body:**
```json
{
  "section_id": 0,
  "generated_text": "string",
  "model": "string"
}
```

---

## Sources Endpoints

### Upload Source Document
**Method:** `POST`  
**Path:** `/api/v1/sources/{study_id}/upload`

**Path Parameters:**
- `study_id` (integer, required): The ID of the study

**Request Body:**
- Content-Type: `multipart/form-data`
- `file` (file, required): The document file to upload
- `type` (string, required): The type/category of the source document

**Response Body:**
```json
{
  "id": 0,
  "type": "string",
  "file_name": "string"
}
```

**Error Responses:**
- `404`: Study not found
- `500`: Failed to save file

### List Source Documents
**Method:** `GET`  
**Path:** `/api/v1/sources/{study_id}`

**Path Parameters:**
- `study_id` (integer, required): The ID of the study

**Response Body:**
```json
[
  {
    "id": 0,
    "type": "string",
    "file_name": "string"
  }
]
```

**Error Responses:**
- `404`: Study not found

---

## Notes

- All datetime fields are in ISO 8601 format (UTC)
- All endpoints return JSON responses
- Error responses follow the format: `{"detail": "error message"}`

