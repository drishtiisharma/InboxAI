# services/auth.py
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
import requests
import os
import base64
import hashlib
import secrets
from db import save_user

auth_router = APIRouter(prefix="/auth", tags=["auth"])

BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://localhost:8000")

SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar"
]

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# In-memory store: state -> code_verifier
_state_store: dict = {}


def _generate_pkce_pair():
    """Generate a PKCE code_verifier and code_challenge."""
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


@auth_router.get("/google")
async def google_login(request: Request):
    flow = Flow.from_client_secrets_file(
        "client_secret.json",
        scopes=SCOPES,
        redirect_uri=f"{BACKEND_BASE_URL}/auth/google/callback"
    )

    code_verifier, code_challenge = _generate_pkce_pair()

    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        code_challenge=code_challenge,
        code_challenge_method="S256"
    )

    # Store verifier keyed by state
    _state_store[state] = code_verifier
    return RedirectResponse(url=auth_url)


@auth_router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None
):
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    if not state or state not in _state_store:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    code_verifier = _state_store.pop(state)

    # Exchange code for token manually so we can pass code_verifier
    with open("client_secret.json") as f:
        import json
        client_config = json.load(f)["web"]

    token_res = requests.post(
        client_config["token_uri"],
        data={
            "code": code,
            "client_id": client_config["client_id"],
            "client_secret": client_config["client_secret"],
            "redirect_uri": f"{BACKEND_BASE_URL}/auth/google/callback",
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,   # PKCE verifier
        }
    )

    if token_res.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Token exchange failed: {token_res.text}"
        )

    token_data = token_res.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="No access token received")

    # Get user info
    userinfo_res = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if userinfo_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user info")

    userinfo = userinfo_res.json()
    email = userinfo.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="No email in user info")

    if refresh_token:
        save_user(email, refresh_token)
    else:
        print(f"[AUTH] WARNING: No refresh token received for {email}. User may need to re-auth.")

    request.session["user"] = email
    print(f"[AUTH] Logged in: {email}")

    return RedirectResponse(url="/auth/success")


@auth_router.get("/success")
async def auth_success(request: Request):
    email = request.session.get("user")
    print(f"[AUTH] /success — session user: {email}")
    return HTMLResponse(content=f"""
    <html>
      <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
        <h2>✅ Login successful!</h2>
        <p>Signed in as <strong>{email or 'unknown'}</strong></p>
        <p>You can close this window and return to the extension.</p>
        <script>setTimeout(() => window.close(), 3000);</script>
      </body>
    </html>
    """)


@auth_router.get("/status")
async def auth_status(request: Request):
    user_email = request.session.get("user")
    print(f"[AUTH] /status — session user: {user_email}")
    if not user_email:
        return JSONResponse({"authenticated": False, "email": None})
    return JSONResponse({"authenticated": True, "email": user_email})


@auth_router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return JSONResponse({"success": True})