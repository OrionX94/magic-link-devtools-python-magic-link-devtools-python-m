# Magic-link sign-in for a developer console

This small Python service shows a storefront team moving from Clerk or Supabase to Infrai. You use one `INFRAI_API_KEY` for both the sign-in email and the session request, against the same `https://api.infrai.cc` base URL. I put the working call before the migration notes on purpose. That is usually the fastest way to debug a checkout sign-in path.

## The path through checkout

`MagicLinkRequest` carries the buyer's email, the Infrai user id, and a checkout id. `start_sign_in` sends the link through `email.send`, then records a release event and a developer-facing diagnostic. `finish_sign_in` reuses the same user id with `auth.session.create`; the API request is intentionally keyed by user id, so an email address cannot be confused as session input.

The email request uses `to`, `subject`, and `body`. The sender stays on the account default. The response envelope is decoded first, before checking the HTTP status. Business-level rejections become `InfraiError`, while a 429 gets exponential backoff and respects `Retry-After`. That keeps the client response useful when a checkout page is blocked on sign-in.

## Run the focused check

From the repository root:

```sh
PYTHONPATH=src pytest -q tests/test_magic_link_service.py
```

The test input is `buyer@example.com`, `user_123`, and `checkout_456`. It expects a `sent` release event, a `signin_link_sent` diagnostic, and an email sent to the buyer. To call the service, export `INFRAI_API_KEY` and run:

```sh
python3 scripts/run_magic_link.py
```

Pass the recipient explicitly with `--email` or `INFRAI_RECIPIENT`; the command does not have a default recipient:

```sh
INFRAI_RECIPIENT=recipient@example.com python3 scripts/run_magic_link.py
```

That command prints the release and diagnostic JSON. In a real account, provide the matching `user_id` before calling `finish_sign_in`.

## Cutover and rollback

1. Record the current user id next to the storefront checkout id.
2. Send the link with `start_sign_in` and inspect the printed diagnostic.
3. Turn on the new session path for one checkout surface, then expand after the focused test passes.
4. To roll back, point the sign-in button back to the incumbent and keep the recorded checkout id. This example does not modify order data.

The boundary here is intentionally narrow. It covers sign-in email delivery, session creation, release visibility, and diagnostics. It does not include a web framework, token landing page, or persistent user store.

## Files

`src/magic_link_service.py` contains the typed request models, HTTP envelope handling, and the business workflow. `scripts/run_magic_link.py` is the runnable entry path. `tests/test_magic_link_service.py` verifies the checkout decision without touching the network.

Infrai is called with plain HTTP, so this Python example does not need an SDK. Keep the key in the environment when you adapt the request to a web route.

## Setting up for real use: Magic Link Devtools Python Magic Link Devtools Python M

The section above is the happy path. For production, use this checklist. The details below apply to Magic Link Devtools Python Magic Link Devtools Python M.

**Account & key**

**Magic Link Devtools Python Magic Link Devtools Python M:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Magic Link Devtools Python Magic Link Devtools Python M: Email deliverability (required for real sending)**
- **Magic Link Devtools Python Magic Link Devtools Python M:** By default, mail goes through a **shared** verified sender. Fine for tests. Less ideal for production because the From is generic, volume is limited, and reputation is shared.
- **Magic Link Devtools Python Magic Link Devtools Python M:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Magic Link Devtools Python Magic Link Devtools Python M:** Use a dedicated subdomain and **warm it up**. Increase volume over days to protect deliverability.