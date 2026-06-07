let videoStream = null
let torchEnabled = false

// Receipt text extraction (ChatGPT/Textract) is sensitive to capture
// resolution - low-res photos lead to misread item names and prices. So we
// always want the sharpest possible capture from the rear camera.
//
// The catch: some phones' camera HALs *advertise* high-resolution modes
// (e.g. ~12MP) they can't actually deliver a *working video stream* at - the
// getUserMedia() call "succeeds" and reports the requested settings, but the
// stream comes out blank, frozen on a single (sometimes visibly corrupted)
// frame, or otherwise broken - while still "reporting" high-res settings.
//
// We tried auto-detecting a working resolution (probing presets and
// verifying frames actually flow), but that turned out to be unreliable too
// - a stalled/corrupted decoder can still produce changing timestamps and
// fool the probe. There's no signal we can trust from inside the page to
// know which mode actually works on a given device's hardware.
//
// So instead we let the user pick: expose a small set of resolution presets
// (best quality first) and a button to cycle through them. Whichever one the
// user finds actually streams properly on their device gets remembered (per
// browser, via localStorage) and used as the starting point next time.
export const RESOLUTION_PRESETS = [
  { label: "Max (4032×3024)", width: { ideal: 4032 }, height: { ideal: 3024 } },
  { label: "High (3264×2448)", width: { ideal: 3264 }, height: { ideal: 2448 } },
  { label: "Medium (1920×1080)", width: { ideal: 1920 }, height: { ideal: 1080 } },
  { label: "Low (1280×720)", width: { ideal: 1280 }, height: { ideal: 720 } }
]

const RESOLUTION_INDEX_STORAGE_KEY = "cameraResolutionIndex"

function getRememberedResolutionIndex() {
  const stored = parseInt(localStorage.getItem(RESOLUTION_INDEX_STORAGE_KEY), 10)
  if (!isNaN(stored) && stored >= 0 && stored < RESOLUTION_PRESETS.length) {
    return stored
  }
  return 0
}

function rememberResolutionIndex(index) {
  localStorage.setItem(RESOLUTION_INDEX_STORAGE_KEY, String(index))
}

export function getCurrentResolutionIndex() {
  return currentResolutionIndex
}

let currentResolutionIndex = getRememberedResolutionIndex()

export async function startCamera() {
  await openCameraWithPreset(currentResolutionIndex)
}

// Switches to the next resolution preset (wrapping around) and restarts the
// camera with it. Called from the UI button so the user can cycle through
// presets until they find one that actually streams on their device.
export async function cycleResolution() {
  const nextIndex = (currentResolutionIndex + 1) % RESOLUTION_PRESETS.length
  await openCameraWithPreset(nextIndex)
}

async function openCameraWithPreset(index) {
  const video = document.getElementById("camera")
  const preset = RESOLUTION_PRESETS[index]

  try {
    if (videoStream) {
      videoStream.getTracks().forEach((track) => track.stop())
      videoStream = null
    }

    videoStream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: { ideal: "environment" },
        width: preset.width,
        height: preset.height
      }
    })

    video.srcObject = videoStream

    currentResolutionIndex = index
    rememberResolutionIndex(index)

    const track = videoStream.getVideoTracks()[0]
    const settings = track.getSettings()
    document.getElementById("resolution").innerHTML = `${preset.label} → ${settings.width}x${settings.height}`

    // Best-effort only: not all devices support continuous autofocus, and an
    // OverconstrainedError here must not be mistaken for the camera itself
    // having failed to start (it already did, successfully, above).
    try {
      await track.applyConstraints({
        advanced: [
          { focusMode: "continuous" }
        ]
      })
    }
    catch (focusErr) {
      console.warn("Continuous autofocus not supported on this device/preset", focusErr)
    }
  }
  catch (err) {
    console.error("Could not start the camera with preset", preset, err)
    document.getElementById("resolution").innerHTML = `${preset.label} → failed`
  }
}

export function stopCamera() {
    const video = document.getElementById("camera")
    video.pause()
}

export async function toggleTorch() {
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

  document.getElementById("torchButton").innerText = torchEnabled ? "🔦 ON" : "🔦 OFF"
}

export async function turnOffTorch() {
  if (!videoStream) return

  const track = videoStream.getVideoTracks()[0]
  const capabilities = track.getCapabilities()

  if (!capabilities.torch) {
    return
  }

  await track.applyConstraints({
    advanced: [{ torch: false }]
  })

  document.getElementById("torchButton").innerText = "🔦 OFF"
}

export async function bringBackTorch() {
  if (!videoStream) return

  const track = videoStream.getVideoTracks()[0]
  const capabilities = track.getCapabilities()

  if (!capabilities.torch) {
    return
  }

  await track.applyConstraints({
    advanced: [{ torch: torchEnabled }]
  })

  document.getElementById("torchButton").innerText = torchEnabled ? "🔦 ON" : "🔦 OFF"
}

export function takePhoto(state) {
  const video = document.getElementById("camera")
  const canvas = document.createElement("canvas")
  const ctx = canvas.getContext("2d")

  canvas.width = video.videoWidth
  canvas.height = video.videoHeight

  ctx.drawImage(video, 0, 0)

  state.image = canvas
  state.crop = {
    x: canvas.width * 0.1,
    y: canvas.height * 0.1,
    w: canvas.width * 0.8,
    h: canvas.height * 0.8
  }
  state._rotated = null
  state._rotatedKey = null
}


