// ===== CONFIG =====

const API_URL = "https://o5q4idu74k.execute-api.eu-central-1.amazonaws.com"
const COGNITO_DOMAIN = "https://sebcel-receipt-analyzer-dev.auth.eu-central-1.amazoncognito.com"
const CLIENT_ID = "3bdji5q53j3gbg2cbcrtlam7p9"
const REDIRECT_URI = "http://sebcel-receipt-analyzer-uploader-dev.s3-website.eu-central-1.amazonaws.com"


// ===== STATE =====

let accessToken = null


// ===== AUTH =====

function initAuth() {

  const hash = window.location.hash

  // Cognito zwraca token w URL #access_token=...
  if (hash.includes("access_token")) {

    const params = new URLSearchParams(hash.substring(1))

    accessToken = params.get("access_token")

    // usuwamy token z URL
    history.replaceState(null, "", window.location.pathname)
  }

  // jeśli brak tokena → redirect do Cognito
  if (!accessToken) {

    const loginUrl =
      `${COGNITO_DOMAIN}/login` +
      `?response_type=token` +
      `&client_id=${CLIENT_ID}` +
      `&redirect_uri=${encodeURIComponent(REDIRECT_URI)}` +
      `&scope=openid`

    window.location.href = loginUrl
  }
}


// ===== RECEIPT UPLOAD =====

async function uploadReceipt() {

  const file =
    document.getElementById("photo").files[0]

  if (!file) {
    alert("Select a receipt photo first")
    return
  }

  try {

    // 1️⃣ pobierz presigned URL z API
    const response = await fetch(
      API_URL + "/receipts/upload-url",
      {
        method: "POST",
        headers: {
          "Authorization": "Bearer " + accessToken
        }
      }
    )

    if (!response.ok) {
      throw new Error("API request failed")
    }

    const uploadData = await response.json()

    // 2️⃣ upload zdjęcia do S3
    const uploadResponse = await fetch(
      uploadData.upload_url,
      {
        method: "PUT",
        body: file,
        headers: {
          "Content-Type": "image/jpeg"
        }
      }
    )

    if (!uploadResponse.ok) {
      throw new Error("Upload failed")
    }

    alert("Receipt uploaded successfully!")

  }
  catch (error) {

    console.error(error)

    alert("Upload failed")

  }

}


// ===== OPTIONAL LOGOUT =====

function logout() {

  const logoutUrl =
    `${COGNITO_DOMAIN}/logout` +
    `?client_id=${CLIENT_ID}` +
    `&logout_uri=${encodeURIComponent(REDIRECT_URI)}`

  window.location.href = logoutUrl
}