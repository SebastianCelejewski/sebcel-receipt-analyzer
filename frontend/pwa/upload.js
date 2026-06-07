const COGNITO_DOMAIN = window.APP_CONFIG.COGNITO_DOMAIN
const CLIENT_ID = window.APP_CONFIG.CLIENT_ID
const REDIRECT_URI = window.APP_CONFIG.REDIRECT_URI

let accessToken = null

const API_URL = window.APP_CONFIG.API_URL

// The PWA uses Cognito's implicit OAuth flow (response_type=token), which
// returns only a short-lived access token — no refresh token. There is no
// API call that can "refresh" such a token. The practical equivalent of a
// refresh is to redirect back to Cognito's /login endpoint: if the user
// still has an active Cognito Hosted UI session (its own session cookie,
// independent of our access token), the redirect completes near-instantly
// and a fresh token comes back without asking the user to type credentials
// again. That's what redirectToLogin() below relies on.

function decodeJwtPayload(token) {
  try {
    const payload = token.split(".")[1]
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/")
    return JSON.parse(atob(normalized))
  } catch (err) {
    return null
  }
}

// A small safety margin avoids the edge case where the token is still valid
// when we check it, but expires moments later while the request is in flight.
const TOKEN_EXPIRY_SAFETY_MARGIN_SECONDS = 30

function isTokenValid(token) {
  if (!token) {
    return false
  }

  const payload = decodeJwtPayload(token)
  if (!payload || !payload.exp) {
    return false
  }

  const nowSeconds = Date.now() / 1000
  return payload.exp - TOKEN_EXPIRY_SAFETY_MARGIN_SECONDS > nowSeconds
}

function redirectToLogin() {
  localStorage.removeItem("access_token")
  accessToken = null

  const loginUrl =
    `${COGNITO_DOMAIN}/login` +
    `?response_type=token` +
    `&client_id=${CLIENT_ID}` +
    `&redirect_uri=${encodeURIComponent(REDIRECT_URI)}` +
    `&scope=openid+email+profile`
  window.location.href = loginUrl
}

export function initUpload() {

  const hash = window.location.hash

  if (hash.includes("access_token")) {
    const params = new URLSearchParams(hash.substring(1))
    accessToken = params.get("access_token")
    localStorage.setItem("access_token", accessToken)
    history.replaceState(null, "", window.location.pathname)
  }

  if (!accessToken) {
    accessToken = localStorage.getItem("access_token")
  }

  // Validate the stored session right away rather than waiting for an
  // upload to fail: a stale/expired token in localStorage would otherwise
  // look like "we're logged in" until the very moment the user tries to
  // send a receipt. Redirecting now (instead of on first upload attempt)
  // also means the silent re-login round trip happens up front, before the
  // user has invested time framing/cropping a photo.
  if (!isTokenValid(accessToken)) {
    redirectToLogin()
  }
}


export async function upload(state, setStatus) {
  const finalCanvas = getFinalCanvas(state)

  if (!finalCanvas) {
    console.error("No final canvas")
    setStatus("No final canvas")
    return
  }

  finalCanvas.toBlob(async (blob) => {
    if (!blob) {
      console.error("Blob is null")
      setStatus("Blob is null")
      return
    }

    return await uploadBlob(blob, setStatus)
  }, "image/jpeg", 0.9)
}

async function uploadBlob(blob, setStatus) {
  const status = document.getElementById("status")
  setStatus("Wysyłam skan paragonu...")

  // Defense in depth: the token could have expired while the PWA stayed
  // open (e.g. a receipt was framed/cropped slowly). Re-check right before
  // sending it, instead of relying solely on the API's response.
  if (!isTokenValid(accessToken)) {
    setStatus("Sesja wygasła — logowanie...")
    redirectToLogin()
    return
  }

  try {
    const response = await fetch(
      API_URL + "/receipts/upload-url",
      {
        method: "POST",
        headers: {
          "Authorization": "Bearer " + accessToken
        }
      }
    )

    // Treat any authorization-related failure (not just 401 — API Gateway's
    // JWT authorizer can also surface 403) as an expired/invalid session and
    // re-authenticate, instead of leaving the user with a dead-end error and
    // a stale token still sitting in localStorage.
    if (response.status === 401 || response.status === 403) {
      setStatus("Sesja wygasła — logowanie...")
      redirectToLogin()
      return
    }

    const uploadData = await response.json()

    const uploadResponse = await fetch(uploadData.upload_url,
      {
        method: "PUT",
        body: blob,
        headers: {
          "Content-Type": "image/jpeg",
          "x-amz-meta-user": uploadData.user,
          "x-amz-meta-source": "pwa"
        }
      })

    const text = await uploadResponse.text()

    if (!uploadResponse.ok) {
      const text = await uploadResponse.text()
      console.error("Błąd przesyłania skanu: ", text)
      setStatus("Błąd przesyłania skanu: " + text)
      return
    }

    setStatus("Skan wysłany ✔")
  }
  catch (err) {
    // A network-level failure here (fetch rejecting before we get a Response)
    // can also happen when an authorization error response is blocked by the
    // browser (e.g. missing CORS headers on a 401/403). If the token looks
    // expired/invalid at this point, treat it as a session problem and
    // re-authenticate rather than showing a dead-end error.
    if (!isTokenValid(accessToken)) {
      setStatus("Sesja wygasła — logowanie...")
      redirectToLogin()
      return
    }

    console.error("Błąd przesyłania skanu: ", err)
    setStatus("Błąd przesyłania skanu: " + err)
  }
}

function getFinalCanvas(state) {
  const rotated = state._rotated || createRotatedCanvas(state)

  const { x, y, w, h } = state.crop

  const finalCanvas = document.createElement("canvas")
  finalCanvas.width = w
  finalCanvas.height = h

  const ctx = finalCanvas.getContext("2d")

  ctx.drawImage(
    rotated,
    x, y, w, h,
    0, 0, w, h
  )

  return finalCanvas
}
