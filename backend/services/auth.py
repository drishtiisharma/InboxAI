# services/auth.py
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
import requests
import os
from db import save_user

auth_router = APIRouter(prefix="/auth", tags=["auth"])

# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "https://inboxai-backend-tb5j.onrender.com")

SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar"
]

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

@auth_router.get("/google")
async def google_login(request: Request):
    flow = Flow.from_client_secrets_file(
        "client_secret.json",
        scopes=SCOPES,
        redirect_uri=f"{BACKEND_BASE_URL}/auth/google/callback"
    )
    
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    
    request.session["oauth_state"] = state
    return RedirectResponse(url=auth_url)  

@auth_router.get("/google/callback")
async def google_callback(request: Request, code: str = None, state: str = None, error: str = None):
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    session_state = request.session.get("oauth_state")
    if not session_state or session_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    flow = Flow.from_client_secrets_file(
        "client_secret.json",
        scopes=SCOPES,
        state=state,
        redirect_uri=f"{BACKEND_BASE_URL}/auth/google/callback"
    )
    
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    # Get user info
    userinfo_res = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {credentials.token}"}
    )
    
    if userinfo_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user info")
    
    userinfo = userinfo_res.json()
    email = userinfo.get("email")
    
    if not email:
        raise HTTPException(status_code=400, detail="No email in user info")
    
    # Save refresh token
    if credentials.refresh_token:
        save_user(email, credentials.refresh_token)
    
    # Store user in session
    request.session["user"] = email
    
    return RedirectResponse(url="/auth/success")

@auth_router.get("/success")
async def auth_success():
    html_content = """
    <html>
      <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
        <h2>✅ Login successful!</h2>
        <p>You can close this window and return to the extension.</p>
        <script>
          setTimeout(() => window.close(), 2000);
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@auth_router.get("/status")
async def auth_status(request: Request):
    user_email = request.session.get("user")
    
    if not user_email:
        return JSONResponse({"authenticated": False, "email": None})
    
    return JSONResponse({
        "authenticated": True,
        "email": user_email
    })

@auth_router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return JSONResponse({"success": True})