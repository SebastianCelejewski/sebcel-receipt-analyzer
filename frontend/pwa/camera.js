let videoStream = null
let torchEnabled = false

export async function startCamera() {
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

  document.getElementById("torchBtn").innerText =
    torchEnabled ? "🔦 ON" : "🔦 OFF"
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
}


