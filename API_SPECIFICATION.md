# API Specification

## Base URL
All endpoints are prefixed with `/api/v1`

---

## Health Check

### Health Check
**Method:** `GET`  
**Path:** `/health`

**Response Body:**
```json
{
  "status": "ok"
}
```

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
  "phase": "string | null",
  "status": "string",
  "indication": "string | null",
  "sponsor_name": "string | null"
}
```

**Response Body:**
```json
{
  "id": 0,
  "code": "string",
  "title": "string",
  "phase": "string | null",
  "status": "string",
  "indication": "string | null",
  "sponsor_name": "string | null"
}
```

**Notes:**
- `status` defaults to `"draft"` if not provided
- The creator is automatically added as a study member with role `"owner"`

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
    "phase": "string | null",
    "status": "string",
    "indication": "string | null",
    "sponsor_name": "string | null"
  }
]
```

**Notes:**
- Returns only studies where the current user is a member

**Error Responses:**
- `401/403`: Missing or invalid token

### List Study Members
**Method:** `GET`  
**Path:** `/api/v1/studies/{study_id}/members`

**Path Parameters:**
- `study_id` (integer, required): The ID of the study

**Response Body:**
```json
[
  {
    "id": 0,
    "study_id": 0,
    "user_id": 0,
    "role": "string",
    "created_at": "2024-01-01T00:00:00Z",
    "user": {
      "id": 0,
      "username": "string",
      "full_name": "string | null",
      "email": "string | null"
    }
  }
]
```

**Notes:**
- Only study members can view the list of members
- Roles: `"owner"`, `"editor"`, `"viewer"`

**Error Responses:**
- `403`: Access denied (user is not a member of the study)
- `404`: Study not found

### Get My Study Membership
**Method:** `GET`  
**Path:** `/api/v1/studies/{study_id}/members/me`

**Path Parameters:**
- `study_id` (integer, required): The ID of the study

**Response Body:**
```json
{
  "id": 0,
  "study_id": 0,
  "user_id": 0,
  "role": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "user": {
    "id": 0,
    "username": "string",
    "full_name": "string | null",
    "email": "string | null"
  }
}
```

**Notes:**
- Returns the current user's membership information in the specified study
- Role can be: `"owner"`, `"editor"`, or `"viewer"`

**Error Responses:**
- `403`: Access denied (user is not a member of this study)
- `404`: Study not found

### Add Study Member
**Method:** `POST`  
**Path:** `/api/v1/studies/{study_id}/members/{user_id}`

**Path Parameters:**
- `study_id` (integer, required): The ID of the study
- `user_id` (integer, required): The ID of the user to add

**Request Body:**
```json
{
  "role": "string"
}
```

**Response Body:**
```json
{
  "id": 0,
  "study_id": 0,
  "user_id": 0,
  "role": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "user": {
    "id": 0,
    "username": "string",
    "full_name": "string | null",
    "email": "string | null"
  }
}
```

**Notes:**
- Only study owners can add members
- Valid roles: `"owner"`, `"editor"`, `"viewer"`
- Cannot add the same user twice
- Cannot change study owner through this endpoint

**Error Responses:**
- `400`: User already in study, or cannot change study owner
- `403`: Access denied (only owners can add members)
- `404`: Study or user not found

### Remove Study Member
**Method:** `DELETE`  
**Path:** `/api/v1/studies/{study_id}/members/{member_id}`

**Path Parameters:**
- `study_id` (integer, required): The ID of the study
- `member_id` (integer, required): The ID of the study member record to remove

**Response Body:**
- No content (204 No Content)

**Notes:**
- Only study owners can remove members
- Cannot remove the last owner of the study

**Error Responses:**
- `400`: Cannot remove the last owner of the study
- `403`: Access denied (only owners can remove members)
- `404`: Member not found

---

## CSR Endpoints

> **Authorization:** Requires `Authorization: Bearer <token>` header. User must be a member of the study.

### Get CSR Document
**Method:** `GET`  
**Path:** `/api/v1/csr/{study_id}`

**Path Parameters:**
- `study_id` (integer, required): The ID of the study

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

**Notes:**
- If the CSR document doesn't exist for the study, it will be automatically created with default sections.

**Error Responses:**
- `404`: Study not found

### Get CSR Sections
**Method:** `GET`  
**Path:** `/api/v1/csr/{study_id}/sections`

**Path Parameters:**
- `study_id` (integer, required): The ID of the study

**Response Body:**
```json
[
  {
    "id": 0,
    "code": "string",
    "title": "string",
    "order_index": 0
  }
]
```

**Notes:**
- Returns all sections for the CSR document of the study, ordered by `order_index`.
- If the CSR document doesn't exist for the study, it will be automatically created with default sections.

**Error Responses:**
- `404`: Study not found

### Get Latest Section Version
**Method:** `GET`  
**Path:** `/api/v1/csr/sections/{section_id}/versions/latest`

**Path Parameters:**
- `section_id` (integer, required): The ID of the CSR section

**Response Body:**
```json
{
  "id": 0,
  "text": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "created_by": "string | null",
  "source": "string | null"
}
```

**Error Responses:**
- `404`: Section not found
- `404`: No versions found for this section

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
  "source": "string | null"
}
```

**Notes:**
- Creates a new version with `source="human"`.
- Returns status code `201 Created`.

**Error Responses:**
- `404`: Section not found

### Apply Template to Section
**Method:** `POST`  
**Path:** `/api/v1/csr/sections/{section_id}/apply-template`

**Path Parameters:**
- `section_id` (integer, required): The ID of the CSR section

**Request Body:**
```json
{
  "template_id": 0,
  "study_id": 0,
  "extra_context": {}
}
```

**Response Body:**
```json
{
  "id": 0,
  "text": "string",
  "created_at": "2024-01-01T00:00:00Z",
  "created_by": "string | null",
  "source": "template",
  "template_id": 0
}
```

**Notes:**
- Requires authentication
- Creates a new section version with rendered template content
- Template is rendered with context from study data and RAG chunks
- Returns status code `201 Created`

**Error Responses:**
- `400`: Section does not belong to the specified study
- `401/403`: Missing or invalid token, or user is not a member of the study
- `404`: Section, study, or template not found

---

## AI Endpoints

> **Authorization:** Requires `Authorization: Bearer <token>` header. User must be a member of the study.

### Generate Section Text
**Method:** `POST`  
**Path:** `/api/v1/ai/generate-section-text`

**Request Body:**
```json
{
  "study_id": 0,
  "section_id": 0,
  "prompt": "string | null",
  "max_tokens": 1024,
  "temperature": 0.2
}
```

**Response Body:**
```json
{
  "study_id": 0,
  "section_id": 0,
  "generated_text": "string",
  "model_name": "string | null",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Notes:**
- Automatically retrieves RAG context from source documents (protocol, SAP, TLF, previous CSR)
- Uses prompt templates if available for the section
- All AI calls are logged in the database
- Currently uses a stub implementation that will later be replaced with a real LLM call

**Error Responses:**
- `400`: Section does not belong to study
- `401/403`: Missing or invalid token, or user is not a member of the study
- `404`: Section or study not found
- `500`: AI generation failed

---

## Sources Endpoints

> **Authorization:** Requires `Authorization: Bearer <token>` header. User must be a member of the study.

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
  "study_id": 0,
  "type": "string",
  "file_name": "string",
  "uploaded_at": "2024-01-01T00:00:00Z",
  "uploaded_by": "string | null"
}
```

**Error Responses:**
- `400`: File must have a filename
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
    "study_id": 0,
    "type": "string",
    "file_name": "string",
    "uploaded_at": "2024-01-01T00:00:00Z",
    "uploaded_by": "string | null"
  }
]
```

**Notes:**
- Documents are ordered by `uploaded_at` in descending order (most recent first).
- After upload, the document is automatically indexed for RAG (text extraction and chunking)

**Error Responses:**
- `401/403`: Missing or invalid token, or user is not a member of the study
- `404`: Study not found

---

## Templates Endpoints

> **Authorization:** Not required at this time.

### Get Templates by Section Code
**Method:** `GET`  
**Path:** `/api/v1/templates/section/{section_code}`

**Path Parameters:**
- `section_code` (string, required): The code of the CSR section (e.g., `SYNOPSIS`, `OBJECTIVES`)

**Query Parameters:**
- `language` (string, optional): Filter by language (e.g., `ru`, `en`)
- `scope` (string, optional): Filter by scope (e.g., `global`, `sponsor`, `study`)

**Response Body:**
```json
[
  {
    "id": 0,
    "name": "string",
    "description": "string | null",
    "type": "section_text",
    "section_code": "string",
    "language": "string",
    "scope": "string",
    "is_default": false,
    "is_active": true,
    "version": 0,
    "content": "string",
    "variables": {},
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "created_by": "string | null"
  }
]
```

**Notes:**
- Returns only active templates of type `"section_text"`
- Templates are filtered by section code and optional language/scope

### Render Template
**Method:** `POST`  
**Path:** `/api/v1/templates/{template_id}/render`

**Path Parameters:**
- `template_id` (integer, required): The ID of the template

**Request Body:**
```json
{
  "study_id": 0,
  "section_id": 0,
  "extra_context": {}
}
```

**Response Body:**
```json
{
  "rendered_text": "string",
  "used_variables": {},
  "missing_variables": []
}
```

**Notes:**
- Renders template with context from study data and RAG chunks
- Variables in template use `{{variable_name}}` syntax
- Missing variables remain as placeholders in the rendered text

**Error Responses:**
- `404`: Template or study not found

---

## RAG Endpoints

> **Authorization:** Requires `Authorization: Bearer <token>` header for getting chunks. User must be a member of the study.

### Ingest Source Document
**Method:** `POST`  
**Path:** `/api/v1/rag/ingest/{source_document_id}`

**Path Parameters:**
- `source_document_id` (integer, required): The ID of the source document to index

**Response Body:**
```json
{
  "source_document_id": 0,
  "chunks_created": 0
}
```

**Notes:**
- Extracts text from the source document
- Splits text into chunks and stores them in the RAG system
- Replaces existing chunks for the document if re-indexing
- This is automatically called after document upload

**Error Responses:**
- `404`: Source document not found
- `500`: RAG ingestion failed

### Get Study RAG Chunks
**Method:** `GET`  
**Path:** `/api/v1/rag/{study_id}`

**Path Parameters:**
- `study_id` (integer, required): The ID of the study

**Query Parameters:**
- `source_type` (string, optional): Filter by source type (`protocol`, `sap`, `tlf`, `csr_prev`)
- `q` (string, optional): Search query (substring search in chunk text)
- `limit` (integer, optional): Maximum number of chunks to return (default: 50, max: 500)
- `offset` (integer, optional): Number of chunks to skip (default: 0)

**Response Body:**
```json
{
  "study_id": 0,
  "source_type": "string | null",
  "total_chunks": 0,
  "limit": 50,
  "offset": 0,
  "chunks": [
    {
      "id": 0,
      "study_id": 0,
      "source_document_id": 0,
      "source_type": "string",
      "order_index": 0,
      "text": "string",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Notes:**
- Diagnostic endpoint to inspect RAG chunks
- Chunks are ordered by `source_type` and `order_index`
- Supports pagination with `limit` and `offset`

**Error Responses:**
- `401/403`: Missing or invalid token, or user is not a member of the study
- `404`: Study not found

---

## Notes

- All datetime fields are in ISO 8601 format (UTC)
- All endpoints return JSON responses unless otherwise specified (e.g., token form data input)
- Error responses follow the format: `{"detail": "error message"}`

