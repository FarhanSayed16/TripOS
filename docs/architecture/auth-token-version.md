# Auth token_version (AUDIT-004 / AUDIT-018)

## Problem

Refresh JWTs were rotated in the cookie but prior refresh tokens remained valid until `exp`.
Password-reset tokens were reusable until expiry.

## V1 solution

`users.token_version` (integer, default 0):

| Event | Behavior |
|---|---|
| Login | Mint access+refresh with current `tv` |
| Refresh | Require `tv` match → bump version → mint new pair (old refresh dead) |
| Logout | Bump version (when refresh cookie present) |
| Password reset | Reset JWT carries `tv`; on success bump version (token single-use + sessions killed) |
| Bearer access | `get_current_user` rejects if `tv` ≠ `user.token_version` |

Migration: `e5f6a7b8c9d0_add_user_token_version.py`

## Residual risk

Access tokens remain valid until their short TTL after a concurrent request race around bump; that window is `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30) only if the client already held an access token — refresh/logout still invalidate further refreshes immediately.
