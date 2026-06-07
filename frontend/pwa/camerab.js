let videoStream = null
let torchEnabled = false

// Some phones expose several rear ("environment") cameras as separate
// devices (e.g. main + ultra-wide + telephoto lenses). `facingMode:
// "environment"` lets the browser pick one for us, and on some devices it
// picks a lower-resolution lens than the user would expect. Remembering the
// last manually-picked camera lets us reopen the same (good) one next time,
// and re-select it automatically without asking again.
const SELECTED_CAMERA_STORAGE_KEY = "selected_camera_device_id"

export function getRememberedCameraId() {
  return localStorage.getItem(SELECTED_CAMERA_STORAGE_KEY)
}

// Returns the available video-input devices. Device labels are only
// populated by the browser once camera permission has been granted, so this
// is best called after the first startCamera() resolves.
export async function listCameras() {
  const devices = await navigator.mediaDevices.enumerateDevices()
  return devices.filter((device) => device.kind === "videoinput")
}

export async function startCamera(deviceId) {
  try {
    if (videoStream) {
      videoStream.getTracks().forEach((track) => track.stop())
    }

    const resolutionConstraints = {
      width:  { ideal: 1920, max: 2560 },
      height: { ideal: 1080, max: 1440 }
    }

    const videoConstraints = deviceId
      ? { deviceId: { exact: deviceId }, ...resolutionConstraints }
      : { facingMode: { ideal: "environment" }, ...resolutionConstraints }

    videoStream = await navigator.mediaDevices.getUserMedia({ video: videoConstraints })

    const video = document.getElementById("camera")
    video.srcObject = videoStream

    const track = videoStream.getVideoTracks()[0]
    const settings = track.getSettings()

    const usedDeviceId = settings.deviceId || deviceId || null
    if (usedDeviceId) {
      localStorage.setItem(SELECTED_CAMERA_STORAGE_KEY, usedDeviceId)
    }

    document.getElementById("resolution").innerHTML = settings.width + "x" + settings.height;

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

  document.getElementById("torchBtn").innerText = torchEnabled ? "🔦 ON" : "🔦 OFF"
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

  document.getElementById("torchBtn").innerText = "🔦 OFF"
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

  document.getElementById("torchBtn").innerText = torchEnabled ? "🔦 ON" : "🔦 OFF"
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


