const API_URL = window.APP_CONFIG.API_URL
const COGNITO_DOMAIN = window.APP_CONFIG.COGNITO_DOMAIN
const CLIENT_ID = window.APP_CONFIG.CLIENT_ID
const REDIRECT_URI = window.APP_CONFIG.REDIRECT_URI

let accessToken = null

let videoStream = null
let state = "camera"
let capturedCanvas = null

let rotation = 0
let fineRotation = 0
let crop = null
let dragging = null
let torchEnabled = false

function initApp() {
  initAuth()
  initCanvas()
  startCamera()
  loadVersion()
  setState("camera")
}

function setState(newState) {
  state = newState

  document.getElementById("cameraView").classList.toggle("hidden", state !== "camera")
  document.getElementById("editView").classList.toggle("hidden", state !== "edit")
  document.getElementById("uploadView").classList.toggle("hidden", state !== "uploading")
}

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

function initCanvas() {
  const canvas = document.getElementById("canvas")

  canvas.addEventListener("mousedown", startDrag)
  canvas.addEventListener("mousemove", onDrag)
  canvas.addEventListener("mouseup", endDrag)

  canvas.addEventListener("touchstart", startDrag)
  canvas.addEventListener("touchmove", onDrag)
  canvas.addEventListener("touchend", endDrag)
}

function logout() {
  const logoutUrl = `${COGNITO_DOMAIN}/logout` +
    `?client_id=${CLIENT_ID}` +
    `&logout_uri=${encodeURIComponent(REDIRECT_URI)}`
  window.location.href = logoutUrl
}

async function startCamera() {
  try {
    videoStream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: { ideal: "environment" },

        width:  { ideal: 1920, max: 2560 },
        height: { ideal: 1080, max: 1440 }
      }
    })

    const video = document.getElementById("camera")
    video.srcObject = videoStream

    const track = videoStream.getVideoTracks()[0]
    document.getElementById("resolution").innerHTML = track.getSettings().width + "x" + track.getSettings().height;

    await track.applyConstraints({
      advanced: [
        { focusMode: "continuous" }
      ]
    })
  }
  catch (err) {
    console.error(err)
  }
}

async function toggleTorch() {
  if (!videoStream) return

  const track = videoStream.getVideoTracks()[0]
  const capabilities = track.getCapabilities()


  if (!capabilities.torch) {
    alert("Latarka niedostępna")
    return
  }

  torchEnabled = !torchEnabled

  await track.applyConstraints({
    advanced: [{ torch: torchEnabled }]
  })

  document.getElementById("torchBtn").innerText =
    torchEnabled ? "🔦 ON" : "🔦 OFF"
}

function takePhoto() {
  const video = document.getElementById("camera")

  const canvas = document.createElement("canvas")
  const ctx = canvas.getContext("2d")

  canvas.width = video.videoWidth
  canvas.height = video.videoHeight

  ctx.drawImage(video, 0, 0)

  capturedCanvas = canvas

  crop = {
    x: canvas.width * 0.1,
    y: canvas.height * 0.1,
    w: canvas.width * 0.8,
    h: canvas.height * 0.8
  }
  
  drawToCanvas()
  setState("edit")
  video.pause()
}

function retake() {
  capturedCanvas = null
  rotation = 0
  fineRotation = 0
  setState("camera")
  video.play()
}

function rotateLeft() {
  rotation = (rotation + 270) % 360
  drawToCanvas()
}

function rotateRight() {
  rotation = (rotation + 90) % 360
  drawToCanvas()
}

function setFineRotation(val) {
  fineRotation = parseFloat(val)
  drawToCanvas()
}

function drawToCanvas() {
  if (!capturedCanvas) return

  const canvas = document.getElementById("canvas")
  const ctx = canvas.getContext("2d")

  const w = capturedCanvas.width
  const h = capturedCanvas.height

  canvas.width = w
  canvas.height = h

  const angle = (rotation + fineRotation) * Math.PI / 180

  ctx.save()
  ctx.translate(w / 2, h / 2)
  ctx.rotate(angle)

  ctx.drawImage(capturedCanvas, -w / 2, -h / 2)

  ctx.restore()

  drawCropOverlay(ctx, canvas)

  const displayW = canvas.clientWidth
  const displayH = canvas.clientHeight

  const scaleX = displayW / canvas.width
  const scaleY = displayH / canvas.height
}

function drawCropOverlay(ctx, canvas) {
  if (!crop) return

  const scaleX = canvas.clientWidth / canvas.width
  const scaleY = canvas.clientHeight / canvas.height

  const x = crop.x * scaleX
  const y = crop.y * scaleY
  const w = crop.w * scaleX
  const h = crop.h * scaleY

  ctx.save()

  ctx.fillStyle = "rgba(0,0,0,0.6)"
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  ctx.globalCompositeOperation = "destination-out"
  ctx.fillRect(crop.x, crop.y, crop.w, crop.h)

  ctx.restore()

  ctx.strokeStyle = "#00ff00"
  ctx.lineWidth = 3
  ctx.strokeRect(crop.x, crop.y, crop.w, crop.h)
}

function getHandles() {
  return [
    { name: "tl", x: crop.x, y: crop.y },
    { name: "tr", x: crop.x + crop.w, y: crop.y },
    { name: "bl", x: crop.x, y: crop.y + crop.h },
    { name: "br", x: crop.x + crop.w, y: crop.y + crop.h }
  ]
}

function getFinalCanvas() {
  if (!capturedCanvas) return null

  const w = capturedCanvas.width
  const h = capturedCanvas.height

  const angle = (rotation + fineRotation) * Math.PI / 180

  // 🔹 obliczenie rozmiaru po rotacji (żeby nic nie ucinało)
  const sin = Math.abs(Math.sin(angle))
  const cos = Math.abs(Math.cos(angle))

  const rotatedW = Math.round(w * cos + h * sin)
  const rotatedH = Math.round(w * sin + h * cos)

  const rotatedCanvas = document.createElement("canvas")
  const rctx = rotatedCanvas.getContext("2d")

  rotatedCanvas.width = rotatedW
  rotatedCanvas.height = rotatedH

  rctx.save()
  rctx.translate(rotatedW / 2, rotatedH / 2)
  rctx.rotate(angle)
  rctx.drawImage(capturedCanvas, -w / 2, -h / 2)
  rctx.restore()

  if (!crop) {
    return rotatedCanvas
  }

  const cropCanvas = document.createElement("canvas")
  const cctx = cropCanvas.getContext("2d")

  const cx = Math.max(0, Math.round(crop.x))
  const cy = Math.max(0, Math.round(crop.y))
  const cw = Math.min(rotatedW - cx, Math.round(crop.w))
  const ch = Math.min(rotatedH - cy, Math.round(crop.h))

  cropCanvas.width = cw
  cropCanvas.height = ch

  cctx.drawImage(
    rotatedCanvas,
    cx, cy, cw, ch,
    0, 0, cw, ch
  )

  return cropCanvas
}

async function confirm() {
  setState("uploading")

  const finalCanvas = getFinalCanvas()

  if (!finalCanvas) {
    console.error("No final canvas")
    setState("edit")
    return
  }

  finalCanvas.toBlob(async (blob) => {
    if (!blob) {
      console.error("Blob null")
      setState("edit")
      return
    }

    await uploadBlob(blob)

    const video = document.getElementById("camera")
    video.play()

    setState("camera")

  }, "image/jpeg", 0.9)
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

    if (response.status === 401) {
      alert("401!")
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
      throw new Error("Upload failed")
    }

    status.innerText = "Skan wysłany ✔"

  }
  catch (err) {
    status.innerText = "Błąd przesyłania skanu"
  }
}

async function loadVersion() {
  try {
    const res = await fetch("version.json", { cache: "no-store" })
    const data = await res.json()

    const env = (data.env || "unknown").toUpperCase()
    const version = data.version || "?"

    const el = document.getElementById("version")
    el.textContent = `${env} | v${version}`
    if (env === "PROD") {
      el.style.color = "#00ffcc"   // spokojny
    } else if (env === "DEV") {
      el.style.color = "#ff5555"   // ostrzegawczy
    }      

  } catch (e) {
    document.getElementById("version").textContent = "version error"
  }
}

async function closeApp() {
  if (videoStream) {
    const tracks = videoStream.getTracks()
    tracks.forEach(track => track.stop())
    videoStream = null
  }

  document.getElementById("camera").srcObject = null

  const status = document.getElementById("status")
  status.innerText = "Aplikacja zatrzymana. Możesz zamknąć okno."
}

function getPos(e) {
  const canvas = document.getElementById("canvas")
  const rect = canvas.getBoundingClientRect()

  const scaleX = canvas.width / rect.width
  const scaleY = canvas.height / rect.height

  let clientX, clientY

  if (e.touches) {
    clientX = e.touches[0].clientX
    clientY = e.touches[0].clientY
  } else {
    clientX = e.clientX
    clientY = e.clientY
  }

  return {
    x: (clientX - rect.left) * scaleX,
    y: (clientY - rect.top) * scaleY
  }
}

function startDrag(e) {
  const pos = getPos(e)

  for (const h of getHandles()) {
    if (Math.abs(pos.x - h.x) < 15 && Math.abs(pos.y - h.y) < 15) {
      dragging = h.name
    }
  }
}

function onDrag(e) {
  e.preventDefault()
  if (!dragging) return

  const pos = getPos(e)

  if (dragging === "tl") {
    crop.w += crop.x - pos.x
    crop.h += crop.y - pos.y
    crop.x = pos.x
    crop.y = pos.y
  }

  if (dragging === "br") {
    crop.w = pos.x - crop.x
    crop.h = pos.y - crop.y
  }

  if (dragging === "tr") {
    crop.w = pos.x - crop.x
    crop.h += crop.y - pos.y
    crop.y = pos.y
  }

  if (dragging === "bl") {
    crop.w += crop.x - pos.x
    crop.h = pos.y - crop.y
    crop.x = pos.x
  }  

  drawToCanvas()
}

function endDrag() {
  dragging = null
}