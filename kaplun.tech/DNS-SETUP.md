# DNS Setup for kaplun.tech

## Option A: CNAME + A Records (Recommended)

1. Log into your domain registrar for kaplun.tech
2. Add these DNS records:

| Type  | Name | Value                 | TTL  |
|-------|------|-----------------------|------|
| CNAME | www  | cname.vercel-dns.com  | 3600 |
| A     | @    | 76.76.21.21           | 3600 |
| A     | @    | 76.76.21.123          | 3600 |

3. In your Vercel dashboard:
   - Go to Project Settings → Domains
   - Add `kaplun.tech` and `www.kaplun.tech`
   - Vercel will verify the DNS records

## Option B: Nameserver Transfer

1. Log into your domain registrar
2. Change nameservers to:
   - `ns1.vercel-dns.com`
   - `ns2.vercel-dns.com`
3. Wait for propagation (5 min to 48 hours)
4. Add the domain in Vercel dashboard

## Verification

After DNS propagation:
- Visit `https://kaplun.tech` — should show the coming-soon page
- Visit `https://www.kaplun.tech` — should redirect to the apex domain

## Troubleshooting

- DNS propagation can take 5 minutes to 48 hours
- Use [dnschecker.org](https://dnschecker.org) to verify propagation status
- If the site doesn't load, check that DNS records match the values above
- Ensure the domain is added to your Vercel project under Settings → Domains
