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

async function uploadReceipt() {
  const file = document.getElementById("photo").files[0]

  if (!file) return

  const status = document.getElementById("status")

  status.innerText = "Uploading receipt..."

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
        body: file,
        headers: {
          "Content-Type": "image/jpeg"
        }
      })

    status.innerText = "Receipt uploaded ✔"
  }
  catch (error) {
    status.innerText = "Upload failed"
  }
}


function logout() {
  const logoutUrl = `${COGNITO_DOMAIN}/logout` +
    `?client_id=${CLIENT_ID}` +
    `&logout_uri=${encodeURIComponent(REDIRECT_URI)}`
  window.location.href = logoutUrl
}