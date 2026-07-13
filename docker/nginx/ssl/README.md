# SSL Certificates

Place your SSL certificate and key files here:

- `cert.pem` — SSL certificate
- `key.pem` — Private key

## Self-signed for development

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout key.pem -out cert.pem \
    -subj "/CN=localhost"
```

## Production

Use Let's Encrypt (certbot) or your CA's certificates.

Ensure the Nginx `server` block for port 443 is uncommented in `../nginx.conf`.
