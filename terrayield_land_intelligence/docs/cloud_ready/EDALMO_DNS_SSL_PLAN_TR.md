# edalmo.com DNS / SSL Plan - TerraYield

## Selected URLs

- Frontend: `https://terrayield.edalmo.com`
- Backend API: `https://api-terrayield.edalmo.com`
- Main site: `https://www.edalmo.com`

## DNS records

After Oracle VM public IP is known, create:

```text
A  terrayield        ORACLE_VM_PUBLIC_IP
A  api-terrayield    ORACLE_VM_PUBLIC_IP
```

If a proxy/CDN is used, equivalent CNAME records may be used, but the first Oracle VM setup expects A records.

## Reverse proxy routing

Caddyfile routes:

```text
api-terrayield.edalmo.com -> api:8010
terrayield.edalmo.com -> static frontend root
```

## SSL

Caddy will request Let’s Encrypt certificates automatically after DNS records resolve to the VM and ports 80/443 are open.

## Main site link

Add this to `www.edalmo.com` without changing the main site runtime:

```html
<a href="https://terrayield.edalmo.com" target="_blank" rel="noopener">
  TerraYield Uygulamasını Aç
</a>
```

## Verification

```text
https://terrayield.edalmo.com loads frontend
https://api-terrayield.edalmo.com/ returns backend root
frontend API requests go to https://api-terrayield.edalmo.com
```

## Safety

No secrets are required in DNS records.
