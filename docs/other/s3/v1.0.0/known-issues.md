# Known Issues — S3 Connector v1.0.0

## Limitations

1. **Multipart uploads not yet supported** — Files larger than ~5 GB should be uploaded directly using AWS SDK or pre-signed PUT URLs. The base64 upload endpoint is suitable for files up to a few hundred MB.

2. **No server-side encryption configuration** — SSE-S3, SSE-KMS, and SSE-C encryption headers are not yet exposed. Objects are stored with the bucket's default encryption policy.

3. **Single-page listing only** — `list_objects` returns up to `max_keys` objects (default 1000). Pagination via continuation tokens is not yet implemented.

4. **No object tagging support** — S3 object tags are not supported in this version.

5. **No lifecycle policy management** — Bucket lifecycle rules must be configured directly via the AWS Console or CLI.

## S3-compatible Storage Notes

- **MinIO**: Requires `use_path_style: true`. Some operations (e.g., bucket policy) may have slight behavioral differences.
- **Wasabi**: No data transfer fees. Some API operations (e.g., `select_object_content`) are not supported.
- **DigitalOcean Spaces**: Does not support `list_buckets` via API — bucket names must be provided explicitly.
