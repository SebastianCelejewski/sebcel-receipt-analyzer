// Cache-busting note: the build replaces __VERSION__ with the build's
// timestamped version (see Makefile build-pwa). index.html already does this
// for app.js's own <script> URL, but ES module imports are resolved by their
// literal specifier strings - the browser/CDN can keep serving a stale cached
// copy of e.g. camerab.js even after a fresh app.js?v=... is fetched, since
// "./camerab.js" never changes. Appending the same ?v=__VERSION__ here forces
// each module to be re-fetched whenever a new version is deployed, so a
// version bump can never leave app.js paired with stale sibling modules
// (which would otherwise surface as "module does not provide an export"
// errors and a silently broken app on devices with cached assets).
import { render as renderFn, getRotatedCanvas } from "./render.js?v=__VERSION__"
import { rotateCrop90 } from "./geometry.js?v=__VERSION__"
import { startCamera, toggleTorch, turnOffTorch, bringBackTorch, takePhoto, listCameras, getRememberedCameraId } from "./camerab.js?v=__VERSION__"
import { startDrag, onDrag, endDrag } from "./input.js?v=__VERSION__"
import { initUpload, upload } from "./upload.js?v=__VERSION__"

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
  turnOffTorch()
}

function switchToCameraMode() {
  editorState.image = null
  editorState.rotation = 0
  editorState.fineRotation = 0
  editorState._rotated = null
  editorState._rotatedKey = null
  setState("camera")
  bringBackTorch()
  video.play()
}

function setStatus(statusText) {
  status.innerHTML = statusText
}

async function initApp() {
  initUpload()
  initCanvas()
  initCameraSelect()

  // Open the previously-picked camera (if any) right away, so a returning
  // user lands on the lens they already chose. The first call also requests
  // camera permission, which the browser needs before it will reveal device
  // labels - required to populate the picker with anything more useful than
  // "Camera 1", "Camera 2", ...
  await startCamera(getRememberedCameraId())
  await populateCameraSelect()

  loadVersion()
  switchToCameraMode()
}

function initCameraSelect() {
  document.getElementById("cameraSelect").addEventListener("change", handleCameraSelected)
}

async function handleCameraSelected(e) {
  await startCamera(e.target.value)
}

// Phones often expose multiple rear ("environment") cameras as separate
// devices (main / ultra-wide / telephoto lenses), and the browser's
// automatic pick isn't always the highest-resolution one. Rather than guess,
// let the user choose explicitly - the choice is then remembered (see
// camerab.js) so they don't have to repeat it on every visit.
async function populateCameraSelect() {
  const select = document.getElementById("cameraSelect")

  let cameras = []
  try {
    cameras = await listCameras()
  }
  catch (err) {
    console.error(err)
  }

  if (cameras.length <= 1) {
    select.classList.add("hidden")
    return
  }

  select.innerHTML = ""

  cameras.forEach((camera, index) => {
    const option = document.createElement("option")
    option.value = camera.deviceId
    option.textContent = camera.label || `Kamera ${index + 1}`
    select.appendChild(option)
  })

  const remembered = getRememberedCameraId()
  if (remembered && cameras.some((camera) => camera.deviceId === remembered)) {
    select.value = remembered
  }

  select.classList.remove("hidden")
}

function initCanvas() {
  canvas.addEventListener("mousedown", (e) => startDrag(e, editorState, canvas, requestRender))
  canvas.addEventListener("mousemove", (e) => onDrag(e, editorState, canvas, requestRender))
  canvas.addEventListener("touchstart", (e) => startDrag(e, editorState, canvas, requestRender), { passive: false })
  canvas.addEventListener("touchmove", (e) => onDrag(e, editorState, canvas, requestRender), { passive: false })

  canvas.addEventListener("mouseup", (e) => endDrag(editorState))
  canvas.addEventListener("touchend", (e) => endDrag(editorState))  
  canvas.addEventListener("touchcancel", (e) => endDrag(editorState))  
  window.addEventListener("mouseup", () => endDrag(editorState))
  window.addEventListener("touchend", () => endDrag(editorState))
  window.addEventListener("touchcancel", () => endDrag(editorState))
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
