# Example Workflows — FTP/SFTP Integrator

## Workflow: List files on FTP/SFTP server

This workflow connects to an FTP/SFTP server and returns a list of files from a specified directory.

### Prerequisites

1. Platform running at `http://localhost:8080`
2. API key created (replace `pk_live_xxx` with your key)
3. FTP/SFTP connector credentials saved

### Step 1: Save FTP/SFTP credentials

```bash
curl -X POST http://localhost:8080/api/v1/credentials \
  -H "X-API-Key: pk_live_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "connector_name": "ftp-sftp",
    "credential_name": "my-sftp-server",
    "credentials": {
      "host": "sftp.example.com",
      "protocol": "sftp",
      "port": "22",
      "username": "myuser",
      "password": "mypassword",
      "base_path": "/data"
    }
  }'
```

### Step 2: Create the workflow

```bash
curl -X POST http://localhost:8080/api/v1/workflows \
  -H "X-API-Key: pk_live_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "FTP List Files",
    "description": "Connects to an FTP/SFTP server and returns a list of files from a given directory",
    "nodes": [
      {
        "id": "trigger_1",
        "type": "trigger",
        "label": "Manual trigger",
        "position": { "x": 250, "y": 50 },
        "config": {
          "connector_name": "ftp-sftp",
          "credential_name": "my-sftp-server",
          "event": "file.new"
        }
      },
      {
        "id": "list_files_1",
        "type": "action",
        "label": "List files on server",
        "position": { "x": 250, "y": 200 },
        "config": {
          "connector_name": "ftp-sftp",
          "credential_name": "my-sftp-server",
          "action": "file.list",
          "on_error": "stop",
          "field_mapping": [
            { "from": "__custom__", "from_custom": "/", "to": "remote_path" }
          ]
        }
      },
      {
        "id": "response_1",
        "type": "response",
        "label": "Return file list",
        "position": { "x": 250, "y": 350 },
        "config": {}
      }
    ],
    "edges": [
      {
        "id": "e_trigger_to_list",
        "source": "trigger_1",
        "target": "list_files_1",
        "sourceHandle": "default"
      },
      {
        "id": "e_list_to_response",
        "source": "list_files_1",
        "target": "response_1",
        "sourceHandle": "default"
      }
    ]
  }'
```

### Step 3: Execute the workflow (on-demand)

Replace `{workflow_id}` with the ID returned from Step 2:

```bash
curl -X POST http://localhost:8080/api/v1/workflows/{workflow_id}/test \
  -H "X-API-Key: pk_live_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_data": {
      "remote_path": "/",
      "pattern": "*"
    }
  }'
```

### Expected response

```json
{
  "id": "exec-uuid",
  "workflow_id": "workflow-uuid",
  "status": "success",
  "node_results": [
    {
      "node_id": "trigger_1",
      "node_type": "trigger",
      "status": "success"
    },
    {
      "node_id": "list_files_1",
      "node_type": "action",
      "label": "List files on server",
      "status": "success",
      "output": [
        {
          "filename": "report_2026.csv",
          "path": "/data/report_2026.csv",
          "size": 15234,
          "is_directory": false,
          "modified_at": "2026-02-20T10:30:00Z"
        },
        {
          "filename": "invoices",
          "path": "/data/invoices",
          "size": 0,
          "is_directory": true,
          "modified_at": "2026-02-18T08:00:00Z"
        }
      ]
    },
    {
      "node_id": "response_1",
      "node_type": "response",
      "status": "success"
    }
  ]
}
```

---

## Workflow: Download new files from FTP and forward to WMS

An event-driven workflow that automatically downloads new files detected by the poller and creates WMS documents.

```bash
curl -X POST http://localhost:8080/api/v1/workflows \
  -H "X-API-Key: pk_live_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "FTP New File → Download → WMS Document",
    "description": "When a new file appears on FTP, download it and create a WMS document",
    "nodes": [
      {
        "id": "trigger_ftp",
        "type": "trigger",
        "label": "New file on FTP",
        "position": { "x": 250, "y": 50 },
        "config": {
          "connector_name": "ftp-sftp",
          "credential_name": "my-sftp-server",
          "event": "file.new"
        }
      },
      {
        "id": "filter_csv",
        "type": "filter",
        "label": "Only CSV files",
        "position": { "x": 250, "y": 180 },
        "config": {
          "logic": "and",
          "conditions": [
            { "field": "filename", "operator": "ends_with", "value": ".csv" }
          ]
        }
      },
      {
        "id": "download_file",
        "type": "action",
        "label": "Download file",
        "position": { "x": 250, "y": 310 },
        "config": {
          "connector_name": "ftp-sftp",
          "credential_name": "my-sftp-server",
          "action": "file.download",
          "on_error": "stop",
          "field_mapping": [
            { "from": "path", "to": "remote_path" }
          ]
        }
      },
      {
        "id": "create_doc",
        "type": "action",
        "label": "Create WMS document",
        "position": { "x": 250, "y": 440 },
        "config": {
          "connector_name": "pinquark-wms",
          "credential_name": "wms-prod",
          "action": "document.create",
          "on_error": "stop",
          "field_mapping": [
            { "from": "nodes.download_file.filename", "to": "documentName" },
            { "from": "nodes.download_file.content_base64", "to": "content" }
          ]
        }
      }
    ],
    "edges": [
      { "id": "e1", "source": "trigger_ftp", "target": "filter_csv", "sourceHandle": "default" },
      { "id": "e2", "source": "filter_csv", "target": "download_file", "sourceHandle": "default" },
      { "id": "e3", "source": "download_file", "target": "create_doc", "sourceHandle": "default" }
    ]
  }'
```
