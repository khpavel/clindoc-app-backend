# Backend Endpoint Verification Report

## Summary

**Date:** Generated during verification  
**Backend Server Status:** ✅ **RUNNING** on `http://127.0.0.1:8000`

---

## ❌ Missing Endpoint

The endpoint `/api/v1/sources/{documentId}/index` **DOES NOT EXIST** in the backend implementation.

---

## ✅ Alternative Endpoints for Document Indexing

### 1. Manual RAG Ingestion Endpoint

**Endpoint:** `POST /api/v1/rag/ingest/{source_document_id}`

- **Path:** `/api/v1/rag/ingest/{source_document_id}`
- **Method:** `POST`
- **Location:** `app/api/v1/rag.py` (lines 20-44)
- **Description:** Manually trigger RAG ingestion/indexing for a source document
- **Parameters:**
  - `source_document_id` (path parameter, integer): The ID of the source document to index
- **Response:**
  ```json
  {
    "source_document_id": 123,
    "chunks_created": 45
  }
  ```
- **Authentication:** Not required (no auth dependency)
- **Example Usage:**
  ```bash
  POST http://127.0.0.1:8000/api/v1/rag/ingest/123
  ```

### 2. Automatic Indexing on Upload

**Endpoint:** `POST /api/v1/sources/{study_id}/upload`

- **Path:** `/api/v1/sources/{study_id}/upload`
- **Method:** `POST`
- **Location:** `app/api/v1/sources.py` (lines 28-96)
- **Description:** Upload a source document - indexing happens automatically after upload
- **Note:** After successful upload, the document is automatically indexed via `ingest_source_document_to_rag()` (see lines 87-94 in `sources.py`)

---

## 🔍 Available Source Document Endpoints

### List Source Documents
- **Path:** `GET /api/v1/sources/{study_id}`
- **Description:** List all source documents for a study

### Upload Source Document
- **Path:** `POST /api/v1/sources/{study_id}/upload`
- **Description:** Upload a new source document (with automatic indexing)

---

## 📋 Endpoint Path Structure

Based on the codebase analysis, the actual endpoint structure is:

1. **Sources endpoints:**
   - `POST /api/v1/sources/{study_id}/upload` - Upload document
   - `GET /api/v1/sources/{study_id}` - List documents

2. **RAG endpoints:**
   - `POST /api/v1/rag/ingest/{source_document_id}` - **Manual indexing endpoint**
   - `GET /api/v1/rag/{study_id}` - Get RAG chunks for a study

---

## 🔧 Implementation Details

### Automatic Indexing Flow

When a document is uploaded via `/api/v1/sources/{study_id}/upload`:

1. File is saved to disk (`storage/study_{study_id}/`)
2. `SourceDocument` record is created in database
3. **Automatic indexing is triggered** via `ingest_source_document_to_rag()` function
4. Text is extracted from the file
5. Text is chunked
6. `RagChunk` records are created in the database

See: `app/api/v1/sources.py` lines 87-94

### Manual Indexing

To manually re-index an existing document:

1. Use the endpoint: `POST /api/v1/rag/ingest/{source_document_id}`
2. The function will:
   - Load the source document from database
   - Read the file from disk
   - Extract text
   - Delete existing chunks for this document
   - Create new chunks

See: `app/api/v1/rag.py` lines 20-44 and `app/services/rag_ingest.py`

---

## 🌐 Server Configuration

### Backend Server Status
- ✅ **Server is RUNNING**
- **URL:** `http://127.0.0.1:8000`
- **Health Check:** `GET http://127.0.0.1:8000/health` returns `{"status":"ok"}`

### Port Configuration
- Default port: **8000**
- Host binding: `0.0.0.0` (listens on all interfaces)
- Accessible via:
  - `http://localhost:8000`
  - `http://127.0.0.1:8000`
  - `http://0.0.0.0:8000`

### Server Scripts
- Windows CMD: `run_server.bat`
- PowerShell: `run_server.ps1`
- Both scripts run: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

---

## 📝 Recommendations

### Option 1: Use Existing RAG Ingestion Endpoint

If you need to manually trigger indexing, use:

```
POST /api/v1/rag/ingest/{source_document_id}
```

Replace `{source_document_id}` with the actual document ID.

### Option 2: Create Missing Endpoint

If you need the exact endpoint path `/api/v1/sources/{documentId}/index`, you could:

1. **Add it to `app/api/v1/sources.py`:**

```python
@router.post("/{document_id}/index")
def index_source_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    """Manually trigger indexing for a source document."""
    source_doc = db.query(SourceDocument).filter(SourceDocument.id == document_id).first()
    if not source_doc:
        raise HTTPException(status_code=404, detail="Source document not found")
    
    try:
        chunks_count = ingest_source_document_to_rag(db, document_id)
        logger.info(f"Indexing completed for document_id={document_id}, created {chunks_count} chunks")
        return {"document_id": document_id, "chunks_created": chunks_count}
    except Exception as e:
        logger.error(f"Indexing failed for document_id={document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")
```

### Option 3: Check Nested Path Structure

The endpoint might be structured differently:

- ❌ `/api/v1/sources/{studyId}/documents/{documentId}/index` - **Does not exist**
- ❌ `/api/v1/sources/index` (with documentId in body) - **Does not exist**

---

## 🔗 Related Files

- **Router definition:** `app/api/v1/sources.py`
- **RAG router:** `app/api/v1/rag.py`
- **Ingestion service:** `app/services/rag_ingest.py`
- **Main application:** `app/main.py`
- **API specification:** `API_SPECIFICATION.md`

---

## ✅ Verification Checklist

- [x] Checked for `/api/v1/sources/{documentId}/index` - **NOT FOUND**
- [x] Checked for `/api/v1/sources/{studyId}/documents/{documentId}/index` - **NOT FOUND**
- [x] Checked for `/api/v1/sources/index` - **NOT FOUND**
- [x] Found alternative: `/api/v1/rag/ingest/{source_document_id}` - **EXISTS**
- [x] Verified automatic indexing on upload - **IMPLEMENTED**
- [x] Verified server is running on port 8000 - **RUNNING**
- [x] Verified server accessible at `http://127.0.0.1:8000` - **ACCESSIBLE**

---

## 📌 Next Steps

1. **If you need the exact endpoint path:**
   - Implement it in `app/api/v1/sources.py` as shown in Option 2 above
   - Update `API_SPECIFICATION.md` with the new endpoint

2. **If you can use the existing endpoint:**
   - Use `POST /api/v1/rag/ingest/{source_document_id}` instead
   - Update your frontend to call this endpoint

3. **If indexing should happen automatically:**
   - It already does! Documents are automatically indexed on upload
   - No additional action needed

---

**Generated by:** Backend Endpoint Verification  
**Backend Version:** FastAPI application (version 0.1.0)


