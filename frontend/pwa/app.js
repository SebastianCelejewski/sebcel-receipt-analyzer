import { render as renderFn, getRotatedCanvas } from "./render.js"
import { rotateCrop90 } from "./geometry.js"
import { startCamera, toggleTorch, takePhoto } from "./camera.js"
import { startDrag, onDrag, endDrag } from "./input.js"
import { initUpload, upload } from "./upload.js"

let state = "camera"
let renderScheduled = false

const video = document.getElementById("camera")
const canvas = document.getElementById("canvas")
const ctx = canvas.getContext("2d")
const status = document.getElementById("status")

const editorState = {
  image: null,
  rotation: 0,
  fineRotation: 0,
  crop: null,
  dragging: null,
  pointer: null,
  _rotated: null,
  _rotatedKey: null
}

window.addEventListener("DOMContentLoaded", initApp)
document.getElementById("torchButton").addEventListener("click", handleTorchButtonClicked)
document.getElementById("takePhotoButton").addEventListener("click", handleTakePhotoButtonClicked)
document.getElementById("retakeButton").addEventListener("click", handleRetakeButtonClicked)
document.getElementById("confirmButton").addEventListener("click", handleConfirmButtonClicked)
document.getElementById("rotateLeftButton").addEventListener("click", handleRotateLeftButtonClicked)
document.getElementById("rotateRightButton").addEventListener("click", handleRotateRightButtonClicked)
document.getElementById("fineRotationSlider").addEventListener("input", handleRotationSliderMoved)

function handleRotationSliderMoved(e) {
  setFineRotation(e.target.value)
}

function handleTorchButtonClicked() {
  toggleTorch()
}

function handleTakePhotoButtonClicked() {
  takePhoto(editorState)
  renderFn(ctx, canvas, editorState)
  switchToEditMode()
}

function handleRetakeButtonClicked() {
  switchToCameraMode()
}

function handleConfirmButtonClicked() {
  upload(editorState, setStatus)
  switchToCameraMode()
}

function switchToEditMode() {
  setState("edit")
  video.pause()
}

function switchToCameraMode() {
  editorState.image = null
  editorState.rotation = 0
  editorState.fineRotation = 0
  editorState._rotated = null
  editorState._rotatedKey = null
  setState("camera")
  video.play()
}

function setStatus(statusText) {
  status.innerHTML = statusText
}

function initApp() {
  initUpload()
  initCanvas()
  startCamera()
  loadVersion()
  switchToCameraMode()
}

function initCanvas() {
  canvas.addEventListener("mousedown", (e) => startDrag(e, editorState, canvas, requestRender))
  canvas.addEventListener("mousemove", (e) => onDrag(e, editorState, canvas, requestRender))
  canvas.addEventListener("mouseup", (e) => endDrag(e, editorState, canvas, requestRender))

  canvas.addEventListener("touchstart", (e) => startDrag(e, editorState, canvas, requestRender), { passive: false })
  canvas.addEventListener("touchmove", (e) => onDrag(e, editorState, canvas, requestRender), { passive: false })
  canvas.addEventListener("touchend", (e) => endDrag(e, editorState, canvas, requestRender))  
}

function requestRender() {
  if (renderScheduled) return

  renderScheduled = true

  requestAnimationFrame(() => {
    renderFn(ctx, canvas, editorState)
    renderScheduled = false
  })
}

function setState(newState) {
  state = newState

  document.getElementById("cameraView").classList.toggle("hidden", state !== "camera")
  document.getElementById("editView").classList.toggle("hidden", state !== "edit")
}

function handleRotateLeftButtonClicked() {
  const rotated = getRotatedCanvas(state)
  editorState.crop = rotateCrop90(editorState.crop,rotated.width, rotated.height, -1)
  editorState.rotation = (editorState.rotation + 270) % 360
  requestRender()
}

function handleRotateRightButtonClicked() {
  const rotated = getRotatedCanvas(state)
  editorState.crop = rotateCrop90(editorState.crop, rotated.width, rotated.height, 1)
  editorState.rotation = (editorState.rotation + 90) % 360
  requestRender()
}

function setFineRotation(val) {
  editorState.fineRotation = parseFloat(val)
  requestRender()
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

function logout() {
  const logoutUrl = `${COGNITO_DOMAIN}/logout` +
    `?client_id=${CLIENT_ID}` +
    `&logout_uri=${encodeURIComponent(REDIRECT_URI)}`
  window.location.href = logoutUrl
}
