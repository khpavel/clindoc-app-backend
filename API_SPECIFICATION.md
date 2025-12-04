# API Specification

## Base URL
All endpoints are prefixed with `/api/v1`

---

## Authentication Endpoints

### Register User
**Method:** `POST`  
**Path:** `/api/v1/auth/register`

**Request Body:**
```json
{
  "username": "string",
  "full_name": "string | null",
  "email": "string | null",
  "password": "string"
}
```

**Response Body:**
```json
{
  "id": 0,
  "username": "string",
  "full_name": "string | null",
  "email": "string | null",
  "is_active": true
}
```

**Error Responses:**
- `400`: Username (or email) already registered

### Obtain Access Token
**Method:** `POST`  
**Path:** `/api/v1/auth/token`

**Request Body:**
- Content-Type: `application/x-www-form-urlencoded`
- `username` (string, required)
- `password` (string, required)

**Response Body:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401`: Incorrect username or password
- `403`: User inactive

---

## Studies Endpoints

> **Authorization:** Requires `Authorization: Bearer <token>` header obtained from the Auth endpoints.

### Create Study
**Method:** `POST`  
**Path:** `/api/v1/studies`

**Request Body:**
```json
{
  "code": "string",
  "title": "string",
  "phase": "string | null"
}
```

**Response Body:**
```json
{
  "id": 0,
  "code": "string",
  "title": "string",
  "phase": "string | null"
}
```

**Error Responses:**
- `400`: Study with this code already exists
- `401/403`: Missing or invalid token

### List Studies
**Method:** `GET`  
**Path:** `/api/v1/studies`

**Response Body:**
```json
[
  {
    "id": 0,
    "code": "string",
    "title": "string",
    "phase": "string | null"
  }
]
```

**Error Responses:**
- `401/403`: Missing or invalid token

---

## CSR Endpoints

### Get CSR Document
**Method:** `GET`  
**Path:** `/api/v1/csr/{document_id}`

**Path Parameters:**
- `document_id` (integer, required): The ID of the CSR document

**Response Body:**
```json
{
  "id": 0,
  "study_id": 0,
  "title": "string",
  "status": "string",
  "sections": [
    {
      "id": 0,
      "code": "string",
      "title": "string",
      "order_index": 0
    }
  ]
}
```

**Error Responses:**
- `404`: Document not found

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

> **Authorization:** Not required at this time.

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
- All endpoints return JSON responses unless otherwise specified (e.g., token form data input)
- Error responses follow the format: `{"detail": "error message"}`

