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
import { startCamera, cycleResolution, toggleTorch, turnOffTorch, bringBackTorch, takePhoto } from "./camerab.js?v=__VERSION__"
import { startDrag, onDrag, endDrag } from "./input.js?v=__VERSION__"
import { initUpload, upload } from "./upload.js?v=__VERSION__"
import { initDebugLog } from "./debug.js?v=__VERSION__"

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
document.getElementById("resolutionButton").addEventListener("click", handleResolutionButtonClicked)
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

function handleResolutionButtonClicked() {
  cycleResolution()
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
  attemptVideoPlay()
}

// play() returns a promise that can reject with NotAllowedError on browsers
// that block autoplay before any user interaction - notably the very first
// call from initApp() on page load, before the user has tapped anything.
// The <video> is muted precisely so autoplay is generally permitted, but
// some browsers are still strict about that very first play(). If it's
// rejected, we don't just log it (that alone leaves the stream permanently
// paused/blank - "logging an intent to retry" isn't the same as retrying);
// we arm a one-shot listener for the user's next interaction and retry
// play() then, when the required user-activation is actually present.
let playRetryArmed = false

function attemptVideoPlay() {
  video.play().catch((err) => {
    console.warn("video.play() was blocked - arming retry on next user interaction", err)
    armVideoPlayRetry()
  })
}

function armVideoPlayRetry() {
  if (playRetryArmed) return
  playRetryArmed = true

  const retry = () => {
    video.play()
      .then(() => {
        playRetryArmed = false
        document.removeEventListener("pointerdown", retry)
        document.removeEventListener("touchend", retry)
        document.removeEventListener("click", retry)
      })
      .catch((err) => {
        // Still blocked - stay armed and wait for a further interaction.
        console.warn("video.play() retry was also blocked - will keep waiting for user interaction", err)
        playRetryArmed = false
        armVideoPlayRetry()
      })
  }

  document.addEventListener("pointerdown", retry, { once: true })
  document.addEventListener("touchend", retry, { once: true })
  document.addEventListener("click", retry, { once: true })
}

function setStatus(statusText) {
  status.innerHTML = statusText
}

function initApp() {
  initDebugLog()
  initUpload()
  initCanvas()
  startCamera()
  loadVersion()
  switchToCameraMode()
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
