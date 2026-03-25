const COGNITO_DOMAIN = window.APP_CONFIG.COGNITO_DOMAIN
const CLIENT_ID = window.APP_CONFIG.CLIENT_ID
const REDIRECT_URI = window.APP_CONFIG.REDIRECT_URI

let accessToken = null

const API_URL = window.APP_CONFIG.API_URL

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

  if (!accessToken) {
    const loginUrl =
      `${COGNITO_DOMAIN}/login` +
      `?response_type=token` +
      `&client_id=${CLIENT_ID}` +
      `&redirect_uri=${encodeURIComponent(REDIRECT_URI)}` +
      `&scope=openid+email+profile`
    window.location.href = loginUrl
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

    if (response.status === 401) {
      setStatus("Konieczne będzie ponowne zalogowanie się")
      localStorage.removeItem("access_token")
      window.location.reload()
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
