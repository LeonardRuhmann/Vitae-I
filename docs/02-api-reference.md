# 📡 API Reference

> Back to [main README](../README.md)

---

## Batch API — Upload Resumes

**Endpoint:** `POST /upload-batch`

Upload up to 10 PDF resumes for batch NLP processing. Returns a `job_id` to track progress.

**Headers:**

| Header | Required | Description |
|---|---|---|
| `X-Session-ID` | Yes | A unique session identifier (UUID recommended) |

**Example:**

```bash
curl -X POST "http://localhost:8000/upload-batch" \
     -H "X-Session-ID: my-session-123" \
     -F "files=@resume1.pdf" \
     -F "files=@resume2.pdf"
# Returns: {"job_id": "uuid-here"}
```

---

## Results API — Fetch Job Results

**Endpoint:** `GET /jobs/{job_id}`

Retrieve the full results payload for a completed (or in-progress) batch job.

**Example:**

```bash
curl "http://localhost:8000/jobs/{job_id}"
```

**Response:**

```json
{
  "job_id": "1c0ecf4d-8a09-470a-bc12-13c3b57962e1",
  "status": "COMPLETED",
  "total_files": 2,
  "processed_files": 2,
  "results": [
    {
      "file_name": "resume1.pdf",
      "status": "SUCCESS",
      "skills": ["Python", "React", "FastAPI"],
      "people": ["Leonardo Ruhmann"],
      "info": ["Universidade de Brasília"]
    }
  ]
}
```

---

## WebSocket — Real-Time Progress

**Endpoint:** `ws://localhost:8000/ws/jobs/{job_id}`

Connect after uploading a batch to receive real-time `progress` events as each resume is processed by spaCy. The frontend listens for a `completed` event to know when to fetch final results via `GET /jobs/{job_id}`.
