# API Specification

## Base URL
All endpoints are prefixed with `/api/v1`

## Correlation ID

All API requests and responses include a correlation ID for request tracking:
- **Request Header:** `X-Correlation-ID` (optional) — if provided, this ID will be used; otherwise, a new UUID will be generated
- **Response Header:** `X-Correlation-ID` — the correlation ID for this request
- **Error Responses:** All error responses include `correlation_id` in the response body

The correlation ID is also included in all log messages, allowing you to trace a request through the system by searching logs for the correlation ID.

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

**Response Headers:**
- `X-Correlation-ID`: Correlation ID for this request

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

### Logout
**Method:** `POST`  
**Path:** `/api/v1/auth/logout`

**Response Body:**
```json
{
  "detail": "logged out"
}
```

**Notes:**
- JWT tokens are stateless, so this endpoint currently just returns a success message
- The client should discard the token on their side
- Future implementation may include token blacklist/revocation mechanism

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
- Valid status values: `"draft"`, `"ongoing"`, `"closed"`, `"archived"`
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

### Get Study
**Method:** `GET`  
**Path:** `/api/v1/studies/{study_id}`

**Path Parameters:**
- `study_id` (integer, required): The ID of the study

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
- Only members of the study can view it
- Returns 404 if study doesn't exist
- Returns 403 if user is not a member of the study

**Error Responses:**
- `403`: Access denied (user is not a member of the study)
- `404`: Study not found

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
- `member_id` (integer, required): The user ID of the study member to remove (note: this is the user_id, not the StudyMember record ID)

**Response Body:**
- No content (204 No Content)

**Notes:**
- Only study owners can remove members
- Cannot remove the last owner of the study
- The `member_id` parameter is actually the `user_id` of the member to remove

**Error Responses:**
- `400`: Cannot remove the last owner of the study
- `403`: Access denied (only owners can remove members)
- `404`: Member not found

---

## CSR Endpoints

> **Authorization:** Requires `Authorization: Bearer <token>` header. User must be a member of the study.  
> **⚠️ DEPRECATED**: These endpoints are deprecated. Use the `/api/v1/output/...` endpoints instead. The CSR endpoints will be removed in a future major version but currently behave identically to the OutputDocument endpoints.

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
- This endpoint uses the same normalized CSR loading logic as `GET /api/v1/csr/document/{document_id}`, ensuring consistent behavior.
- Internally, it finds or creates a default `Document` of type "csr" for the study, then ensures the linked `OutputDocument` exists.
- The returned CSR document may have a `document_id` field linking it to the `Document` model for navigation consistency.

**Error Responses:**
- `404`: Study not found

### Get CSR Document by Document ID
**Method:** `GET`  
**Path:** `/api/v1/csr/document/{document_id}`

**Path Parameters:**
- `document_id` (integer, required): The ID of the Document (must be type "csr")

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
- Loads the Document by ID, ensures user has access to its study, and checks that `document.type == "csr"`
- Returns the linked OutputDocument structure for editing
- If the OutputDocument doesn't exist for the Document, it will be automatically created with default sections
- The frontend can navigate by `document_id` instead of only by `study_id`
- If an OutputDocument already exists for the study but is not linked to the Document, it will be linked automatically
- This endpoint uses the same normalized CSR loading logic as `GET /api/v1/csr/{study_id}`, ensuring consistent behavior
- The returned `document_id` can be used consistently across CSR, QC, and RAG endpoints

**Error Responses:**
- `400`: Document type is not "csr"
- `403`: User is not a member of the study
- `404`: Document or study not found

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
- The response includes `template_id` field linking to the template used

**Error Responses:**
- `400`: Section does not belong to the specified study
- `401/403`: Missing or invalid token, or user is not a member of the study
- `404`: Section, study, or template not found

### Export CSR Document to DOCX
**Method:** `GET`  
**Path:** `/api/v1/csr/{study_id}/export/docx`

**Path Parameters:**
- `study_id` (integer, required): The ID of the study

**Response:**
- Content-Type: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Content-Disposition: `attachment; filename="csr_{study_code}.docx"`
- Body: Binary DOCX file content

**Notes:**
- Requires authentication (user must be a member of the study)
- If the CSR document doesn't exist, it will be automatically created with default sections
- Exports the CSR document with all sections and their latest versions
- Document structure:
  - Document title as main heading (centered)
  - Section titles as level 1 headings
  - Section text as paragraphs
- Filename is generated as `csr_{study_code}.docx` or `csr_{study_id}.docx` if code is not available

**Error Responses:**
- `401/403`: Missing or invalid token, or user is not a member of the study
- `404`: Study not found, or CSR document not found (after creation attempt)

---

## OutputDocument Endpoints

> **Authorization:** Requires `Authorization: Bearer <token>` header. User must be a member of the study.

The OutputDocument endpoints expose the OutputDocument domain, which represents structured editable documents (currently used for CSR/Clinical Study Reports). These endpoints replace the deprecated `/api/v1/csr/...` endpoints and use OutputDocument terminology.

### Get Output Document
**Method:** `GET`  
**Path:** `/api/v1/output/{study_id}`

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
- If the Output Document doesn't exist for the study, it will be automatically created with default sections.
- This endpoint uses the same normalized OutputDocument loading logic as `GET /api/v1/output/document/{document_id}`, ensuring consistent behavior.
- Internally, it finds or creates a default `Document` of type "csr" for the study, then ensures the linked `OutputDocument` exists.
- The returned Output Document may have a `document_id` field linking it to the `Document` model for navigation consistency.

**Error Responses:**
- `404`: Study not found

### Get Output Document by Document ID
**Method:** `GET`  
**Path:** `/api/v1/output/document/{document_id}`

**Path Parameters:**
- `document_id` (integer, required): The ID of the Document (must be type "csr")

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
- Loads the Document by ID, ensures user has access to its study, and checks that `document.type == "csr"`
- Returns the linked OutputDocument structure for editing
- If the OutputDocument doesn't exist for the Document, it will be automatically created with default sections
- The frontend can navigate by `document_id` instead of only by `study_id`
- If an OutputDocument already exists for the study but is not linked to the Document, it will be linked automatically
- This endpoint uses the same normalized OutputDocument loading logic as `GET /api/v1/output/{study_id}`, ensuring consistent behavior
- The returned `document_id` can be used consistently across OutputDocument, QC, and RAG endpoints

**Error Responses:**
- `400`: Document type is not "csr"
- `403`: User is not a member of the study
- `404`: Document or study not found

### Get Output Document Sections
**Method:** `GET`  
**Path:** `/api/v1/output/{study_id}/sections`

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
- Returns all sections for the Output Document of the study, ordered by `order_index`.
- If the Output Document doesn't exist for the study, it will be automatically created with default sections.

**Error Responses:**
- `404`: Study not found

### Get Latest Section Version
**Method:** `GET`  
**Path:** `/api/v1/output/sections/{section_id}/versions/latest`

**Path Parameters:**
- `section_id` (integer, required): The ID of the Output Document section

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
**Path:** `/api/v1/output/sections/{section_id}/versions`

**Path Parameters:**
- `section_id` (integer, required): The ID of the Output Document section

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
**Path:** `/api/v1/output/sections/{section_id}/apply-template`

**Path Parameters:**
- `section_id` (integer, required): The ID of the Output Document section

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
- The response includes `template_id` field linking to the template used

**Error Responses:**
- `400`: Section does not belong to the specified study
- `401/403`: Missing or invalid token, or user is not a member of the study
- `404`: Section, study, or template not found

### Export Output Document to DOCX
**Method:** `GET`  
**Path:** `/api/v1/output/{study_id}/export/docx`

**Path Parameters:**
- `study_id` (integer, required): The ID of the study

**Response:**
- Content-Type: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Content-Disposition: `attachment; filename="csr_{study_code}.docx"`
- Body: Binary DOCX file content

**Notes:**
- Requires authentication (user must be a member of the study)
- If the Output Document doesn't exist, it will be automatically created with default sections
- Exports the Output Document with all sections and their latest versions
- Document structure:
  - Document title as main heading (centered)
  - Section titles as level 1 headings
  - Section text as paragraphs
- Filename is generated as `csr_{study_code}.docx` or `csr_{study_id}.docx` if code is not available

**Error Responses:**
- `401/403`: Missing or invalid token, or user is not a member of the study
- `404`: Study not found, or Output Document not found (after creation attempt)

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
- Uses prompt templates if available for the section, otherwise builds prompt using `ai_prompt_builder`
- Includes current section text (if exists) in the prompt for context-aware generation
- Supports two AI modes controlled by `AI_MODE` configuration:
  - `"stub"` (default): Returns placeholder text for development/testing
  - `"real"`: Calls external LLM API via HTTP (requires `AI_ENDPOINT` and optionally `AI_API_KEY` environment variables)
- All AI calls are logged in the database with the mode used (`mode` field)
- The effective prompt (after template rendering or prompt building) is logged in `ai_call_logs`

**Error Responses:**
- `400`: Section does not belong to study
- `401/403`: Missing or invalid token, or user is not a member of the study
- `404`: Section or study not found
- `500`: AI generation failed (includes error details in `ai_call_logs` with `success=false`)

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
- `type` (string, required): The type/category of the source document (e.g., "protocol", "sap", "tlf", "csr_prev")
- `language` (string, optional): Language code ("ru" or "en"), default "ru"
- `version_label` (string, optional): Version label for the document

**Response Body:**
```json
{
  "id": 0,
  "study_id": 0,
  "type": "string",
  "file_name": "string",
  "uploaded_at": "2024-01-01T00:00:00Z",
  "uploaded_by": "string | null",
  "language": "string",
  "version_label": "string | null",
  "status": "string",
  "is_current": true,
  "is_rag_enabled": true,
  "index_status": "string"
}
```

**Notes:**
- When uploading a new document with the same `type` and `language`, previous documents are automatically marked as `is_current=false`
- The uploaded document is automatically indexed for RAG if `is_rag_enabled=true` (default)
- `index_status` is set to "not_indexed" initially, then updated to "indexed" after successful RAG ingestion
- RAG ingestion runs as a background task, so the response may return before indexing is complete
- The document is immediately available after upload, but RAG chunks may not be available until indexing completes

**Error Responses:**
- `400`: File must have a filename, or language must be 'ru' or 'en'
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
    "uploaded_by": "string | null",
    "language": "string",
    "version_label": "string | null",
    "status": "string",
    "is_current": true,
    "is_rag_enabled": true,
    "index_status": "string"
  }
]
```

**Notes:**
- Documents are ordered by `uploaded_at` in descending order (most recent first)
- After upload, the document is automatically indexed for RAG (text extraction and chunking) if `is_rag_enabled=true`
- `index_status` indicates the indexing state: "not_indexed", "indexed", or "error"

**Error Responses:**
- `401/403`: Missing or invalid token, or user is not a member of the study
- `404`: Study not found

### Delete Source Document
**Method:** `DELETE`  
**Path:** `/api/v1/sources/{source_document_id}`

**Path Parameters:**
- `source_document_id` (integer, required): The ID of the source document to delete

**Response Body:**
- No content (204 No Content)

**Notes:**
- Performs a soft delete of the source document
- Sets `status="archived"`, `is_current=false`, `is_rag_enabled=false`, and `index_status="not_indexed"`
- Deletes all associated RAG chunks for the document
- Only study owners and editors can delete documents (viewers are not allowed)
- The file is not physically deleted from storage
- The document record remains in the database with archived status

**Error Responses:**
- `403`: Access denied (user is not a member of the study, or user is a viewer)
- `404`: Source document not found

### Permanently Delete Source Document
**Method:** `DELETE`  
**Path:** `/api/v1/sources/{source_document_id}/permanent`

**Path Parameters:**
- `source_document_id` (integer, required): The ID of the source document to permanently delete

**Response Body:**
- No content (204 No Content)

**Notes:**
- Permanently deletes a source document, its RAG chunks and stored file
- Only study owners can perform permanent delete (editors and viewers are not allowed)
- This action is irreversible:
  - Deletes all associated RAG chunks from the database
  - Physically deletes the file from storage
  - Removes the SourceDocument record from the database
- If file deletion fails, the database record is still deleted (error is logged)

**Error Responses:**
- `403`: Access denied (user is not a member of the study, or user is not an owner)
- `404`: Source document not found

### Restore Source Document
**Method:** `POST`  
**Path:** `/api/v1/sources/{source_document_id}/restore`

**Path Parameters:**
- `source_document_id` (integer, required): The ID of the source document to restore

**Response Body:**
```json
{
  "id": 0,
  "study_id": 0,
  "type": "string",
  "file_name": "string",
  "uploaded_at": "2024-01-01T00:00:00Z",
  "uploaded_by": "string | null",
  "language": "string",
  "version_label": "string | null",
  "status": "active",
  "is_current": false,
  "is_rag_enabled": true,
  "index_status": "not_indexed"
}
```

**Notes:**
- Restores a previously archived source document back to active state
- Sets `status="active"`, `is_rag_enabled=true`, `index_status="not_indexed"`
- `is_current` is set to `false` by default, or `true` if there are no other active documents of the same (study_id, type, language)
- Automatically triggers RAG ingestion to re-index the document
- Only study owners and editors can restore documents (viewers are not allowed)
- The document will become usable for RAG queries again once re-indexed

**Error Responses:**
- `400`: Document is not archived
- `403`: Access denied (user is not a member of the study, or user is a viewer)
- `404`: Source document not found

---

## Documents Endpoints

> **Authorization:** Requires `Authorization: Bearer <token>` header. User must be a member of the study.

### List Documents for Study
**Method:** `GET`  
**Path:** `/api/v1/studies/{study_id}/documents`

**Path Parameters:**
- `study_id` (integer, required): The ID of the study

**Query Parameters:**
- `ensure_default_csr` (boolean, optional): If `true`, automatically creates a default CSR document if none exists for the study. Default: `false`

**Response Body:**
```json
[
  {
    "id": 0,
    "study_id": 0,
    "type": "string",
    "title": "string",
    "template_code": "string | null",
    "status": "string",
    "current_version_label": "string | null",
    "created_by": 0,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

**Notes:**
- Returns all documents for the study, ordered by `type` first, then by `created_at` in ascending order
- Only study members can view documents
- Valid document types: `"csr"`, `"protocol"`, `"ib"`, `"sap"`, `"tlf"`
- Valid document statuses: `"draft"`, `"in_qc"`, `"ready_for_submission"`, `"archived"`
- If `ensure_default_csr=true` and no CSR document exists, a default CSR document is created with:
  - `title` = "CSR for {study.code}" (or "CSR for Study {study_id}" if code is not available)
  - `status` = "draft"
  - `created_by` = current user

**Error Responses:**
- `401/403`: Missing or invalid token, or user is not a member of the study
- `404`: Study not found

### Create Document for Study
**Method:** `POST`  
**Path:** `/api/v1/studies/{study_id}/documents`

**Path Parameters:**
- `study_id` (integer, required): The ID of the study

**Request Body:**
```json
{
  "type": "string",
  "title": "string",
  "template_code": "string | null",
  "status": "string"
}
```

**Response Body:**
```json
{
  "id": 0,
  "study_id": 0,
  "type": "string",
  "title": "string",
  "template_code": "string | null",
  "status": "string",
  "current_version_label": "string | null",
  "created_by": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Notes:**
- `status` defaults to `"draft"` if not provided
- Valid document types: `"csr"`, `"protocol"`, `"ib"`, `"sap"`, `"tlf"`
- Valid status values: `"draft"`, `"in_qc"`, `"ready_for_submission"`, `"archived"`
- Only study owners and editors can create documents (viewers are not allowed)
- The `created_by` field is automatically set to the current user's ID
- Returns status code `201 Created`

**Error Responses:**
- `400`: Invalid request data (e.g., invalid `type` or `status` value)
- `401/403`: Missing or invalid token, or user is not a member of the study, or user is a viewer
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
- `q` (string, optional): Search query (case-insensitive substring search in chunk text using `ilike`)
- `limit` (integer, optional): Maximum number of chunks to return (default: 50, max: 500, min: 1)
- `offset` (integer, optional): Number of chunks to skip (default: 0, min: 0)

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
      "text_preview": "string",
      "source_document_file_name": "string | null",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Notes:**
- Diagnostic endpoint to inspect RAG chunks
- Chunks are ordered by `source_type` and `order_index`
- Supports pagination with `limit` and `offset`
- Returns `total_chunks` for implementing pagination on the client side
- Text search (`q`) performs case-insensitive substring matching
- `text_preview` contains a truncated version of the text (first 200 characters) for list views
- `source_document_file_name` contains the file name of the source document for convenience

**Error Responses:**
- `401/403`: Missing or invalid token, or user is not a member of the study
- `404`: Study not found

---

## QC (Quality Control) Endpoints

> **Authorization:** Requires `Authorization: Bearer <token>` header. User must be a member of the study.

### Run QC Check for Document
**Method:** `POST`  
**Path:** `/api/v1/qc/documents/{document_id}/run`

**Path Parameters:**
- `document_id` (integer, required): The ID of the Document (must be type "csr")

**Response Body:**
```json
{
  "document_id": 0,
  "issues_created": 0,
  "message": "string"
}
```

**Notes:**
- Accepts a `Document.id` (the Document with `type="csr"`)
- Automatically resolves the linked `OutputDocument` and runs QC rules on it
- If the `OutputDocument` doesn't exist for the Document, it will be automatically created
- Requires access to the study that owns the document
- Returns the number of issues created
- The same `document_id` can be used across CSR, QC, and RAG endpoints for consistent navigation

**Error Responses:**
- `400`: Document type is not "csr"
- `401/403`: Missing or invalid token, or user is not a member of the study
- `404`: Document not found

### Get QC Issues
**Method:** `GET`  
**Path:** `/api/v1/qc/issues/{study_id}`

**Path Parameters:**
- `study_id` (integer, required): The ID of the study

**Query Parameters:**
- `status` (string, optional): Filter by status (`open`, `resolved`, `wont_fix`)
- `severity` (string, optional): Filter by severity (`info`, `warning`, `error`)

**Response Body:**
```json
{
  "issues": [
    {
      "id": 0,
      "study_id": 0,
      "document_id": 0,
      "section_id": 0,
      "rule_id": 0,
      "severity": "string",
      "status": "string",
      "message": "string",
      "created_at": "2024-01-01T00:00:00Z",
      "resolved_at": "string | null",
      "resolved_by": "string | null"
    }
  ],
  "total": 0
}
```

**Notes:**
- Returns all QC issues for the study with optional filtering
- Issues are ordered by `created_at` in descending order (most recent first)
- Valid status values: `open`, `resolved`, `wont_fix`
- Valid severity values: `info`, `warning`, `error`

**Error Responses:**
- `400`: Invalid status or severity filter value
- `401/403`: Missing or invalid token, or user is not a member of the study
- `404`: Study not found

### Get QC Issues for Study
**Method:** `GET`  
**Path:** `/api/v1/qc/studies/{study_id}/issues`

**Path Parameters:**
- `study_id` (integer, required): The ID of the study

**Query Parameters:**
- `document_id` (integer, optional): Filter by document ID
- `status` (string, optional): Filter by status (`open`, `resolved`, `wont_fix`)
- `severity` (string, optional): Filter by severity (`info`, `warning`, `error`)

**Response Body:**
```json
{
  "issues": [
    {
      "id": 0,
      "study_id": 0,
      "document_id": 0,
      "section_id": 0,
      "rule_id": 0,
      "severity": "string",
      "status": "string",
      "message": "string",
      "created_at": "2024-01-01T00:00:00Z",
      "resolved_at": "string | null",
      "resolved_by": "string | null"
    }
  ],
  "total": 0
}
```

**Notes:**
- Returns all QC issues for the study with optional filtering
- Issues are ordered by `created_at` in descending order (most recent first)
- `document_id` filter allows filtering issues by a specific CSR document
- Valid status values: `open`, `resolved`, `wont_fix`
- Valid severity values: `info`, `warning`, `error`

**Error Responses:**
- `400`: Invalid status or severity filter value
- `401/403`: Missing or invalid token, or user is not a member of the study
- `404`: Study not found

---

## Navigation and Document Structure

### Terminology

**OutputDocument Terminology**: The structured editable document for documents of type `"csr"` is called `OutputDocument` in the codebase and API. The term "CSR" (Clinical Study Report) refers specifically to the document type (`Document.type == "csr"`), while `OutputDocument` is the structured representation used for editing sections and versions. The `/api/v1/output/*` endpoints are the official API for OutputDocument operations. The deprecated `/api/v1/csr/*` endpoints are thin wrappers that delegate to the output endpoints and will be removed in a future major version.

### Document-Based Navigation

The frontend can navigate by `document_id` for CSR, QC, and RAG operations. This provides a consistent identifier across all endpoints.

**Key Concepts:**

1. **Document Model**: The `Document` model represents a document in the system with fields:
   - `id`: Unique document identifier
   - `type`: Document type (e.g., `"csr"`, `"protocol"`, `"ib"`, `"sap"`, `"tlf"`)
   - `study_id`: The study this document belongs to
   - `title`, `status`, etc.

2. **OutputDocument Model**: The `OutputDocument` model represents the structured document for documents of type `"csr"` with:
   - `id`: Unique OutputDocument identifier
   - `study_id`: The study this OutputDocument belongs to
   - `document_id`: Link to the `Document` (nullable, for backward compatibility)
   - `sections`: List of OutputDocument sections

3. **Relationship**: 
   - A `Document` with `type="csr"` can have a linked `OutputDocument`
   - The `OutputDocument.document_id` field links to `Document.id`
   - When accessing OutputDocument endpoints by `document_id`, the system automatically:
     - Finds the `Document` with `type="csr"`
     - Gets or creates the linked `OutputDocument`
     - Returns the OutputDocument structure for editing

**Navigation Flow:**

1. **Frontend gets Document list**: `GET /api/v1/studies/{study_id}/documents`
   - Returns all documents for the study, including CSR documents
   - Each CSR document has a `Document.id` that can be used for navigation

2. **Frontend navigates to OutputDocument**: `GET /api/v1/output/document/{document_id}`
   - Uses the `Document.id` from step 1
   - Backend automatically resolves the linked `OutputDocument`
   - Returns OutputDocument structure with sections

3. **Frontend runs QC**: `POST /api/v1/qc/documents/{document_id}/run`
   - Uses the same `Document.id`
   - Backend resolves `OutputDocument` and runs QC rules

4. **Frontend gets QC issues**: `GET /api/v1/qc/studies/{study_id}/issues?document_id={document_id}`
   - Filters issues by the same `Document.id`

**Backward Compatibility:**

- Deprecated study-based endpoints (`GET /api/v1/csr/{study_id}`) still work and use the same internal logic
- They automatically find or create a default `Document` of type "csr" for the study
- Both study-based and document-based endpoints use the same normalized OutputDocument loading function internally
- The `/api/v1/csr/*` endpoints are deprecated wrappers that delegate to `/api/v1/output/*` endpoints

**Consistent Behavior:**

Both `GET /api/v1/output/{study_id}` and `GET /api/v1/output/document/{document_id}` use the same internal logic:
- Find or create a `Document` of type "csr" for the study
- Get or create the linked `OutputDocument`
- Ensure default sections exist
- Return the OutputDocument structure

This ensures that regardless of which endpoint the frontend uses, the same OutputDocument structure is returned and the same `document_id` can be used for subsequent operations.

---

## Notes

- All datetime fields are in ISO 8601 format (UTC)
- All endpoints return JSON responses unless otherwise specified (e.g., token form data input)
- Error responses follow the format: `{"detail": "error message"}`

