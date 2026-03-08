from datetime import datetime
import uuid

const API_URL = "https://o5q4idu74k.execute-api.eu-central-1.amazonaws.com"
const COGNITO_DOMAIN = "https://sebcel-receipt-analyzer-dev.auth.eu-central-1.amazoncognito.com"
const CLIENT_ID = "3bdji5q53j3gbg2cbcrtlam7p9"
const REDIRECT_URI = "https://d1h1goxzgdb2gs.cloudfront.net"

let accessToken = null

function initAuth() {

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

function logout() {
  const logoutUrl = `${COGNITO_DOMAIN}/logout` +
    `?client_id=${CLIENT_ID}` +
    `&logout_uri=${encodeURIComponent(REDIRECT_URI)}`
  window.location.href = logoutUrl
}

async function startCamera() {
  try {
    const stream =
      await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "environment"
        }
      })

    const video = document.getElementById("camera")
    video.srcObject = stream
  }
  catch (err) {
    console.error(err)
  }
}

async function takePhoto() {
  const video = document.getElementById("camera")
  const canvas = document.getElementById("canvas")
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const ctx = canvas.getContext("2d")
  ctx.drawImage(video, 0, 0)
  canvas.toBlob(uploadBlob, "image/jpeg", 0.9)
}

async function uploadBlob(blob) {
  const status = document.getElementById("status")
  status.innerText = "Wysyłam skan paragonu..."
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

    const uploadData = await response.json()
    await fetch(uploadData.upload_url,
      {
        method: "PUT",
        body: blob,
        headers: {
          "Content-Type": "image/jpeg",
          "x-amz-meta-user": uploadData.user,
          "x-amz-meta-source": "pwa"
        }
      })

    status.innerText = "Skan wysłany ✔"

  }
  catch (err) {
    status.innerText = "Błąd przesyłania skanu"
  }

}