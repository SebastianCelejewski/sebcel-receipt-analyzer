import { getHandles } from "./geometry.js"

export function render(ctx, canvas, state) {
  drawCapturedImage(ctx, canvas, state)
  drawCropOverlay(ctx, canvas, state)
}

function drawCapturedImage(ctx, canvas, state) {
  const { image, rotation, fineRotation } = state
  if (!image) return

  const rotated = getRotatedCanvas(state)

  canvas.width = rotated.width
  canvas.height = rotated.height

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.drawImage(rotated, 0, 0)
}

function drawCropOverlay(ctx, canvas, state) {
  if (!state.crop) return

  ctx.save()

  // borders
  ctx.fillStyle = "rgba(0,0,0,0.6)"
  ctx.fillRect(0, 0, canvas.width, state.crop.y)
  ctx.fillRect(0, state.crop.y + state.crop.h, canvas.width, canvas.height - (state.crop.y + state.crop.h))
  ctx.fillRect(0, state.crop.y, state.crop.x, state.crop.h)
  ctx.fillRect(state.crop.x + state.crop.w, state.crop.y, canvas.width - (state.crop.x + state.crop.w), state.crop.h)
  ctx.restore()

  // frame
  ctx.strokeStyle = "#00ff00"
  ctx.lineWidth = 3
  ctx.strokeRect(state.crop.x, state.crop.y, state.crop.w, state.crop.h)

  // handles
  const size = 16
  getHandles(state.crop).forEach(h => {
    ctx.fillStyle = "white"
    ctx.fillRect(h.x - size/2, h.y - size/2, size, size)
    const text = `${Math.round(h.x)}, ${Math.round(h.y)}`
  })

  // finger/mouse position
  if (state.pointer) {
    const text = `👆 ${Math.round(state.pointer.x)}, ${Math.round(state.pointer.y)}`

    ctx.fillStyle = "red"
    ctx.beginPath()
    ctx.arc(state.pointer.x, state.pointer.y, 5, 0, Math.PI * 2)
    ctx.fill()
  }
}

export function getRotatedCanvas(state) {
  const { image, rotation, fineRotation, _rotated, _rotatedKey } = state
  const key = `${rotation}_${fineRotation}`

  if (state._rotated && state._rotatedKey === key) {
    return state._rotated
  }

  const rotated = createRotatedCanvas(image, rotation, fineRotation)

  state._rotated = rotated
  state._rotatedKey = key

  return rotated
}

function createRotatedCanvas(sourceCanvas, rotation, fineRotation) {
  const angle = (rotation - fineRotation) * Math.PI / 180

  const w = sourceCanvas.width
  const h = sourceCanvas.height

  const rotatedCanvas = document.createElement("canvas")
  const ctx = rotatedCanvas.getContext("2d")

  const sin = Math.abs(Math.sin(angle))
  const cos = Math.abs(Math.cos(angle))

  rotatedCanvas.width = Math.ceil(w * cos + h * sin)
  rotatedCanvas.height = Math.ceil(w * sin + h * cos)

  ctx.translate(rotatedCanvas.width / 2, rotatedCanvas.height / 2)
  ctx.rotate(angle)
  ctx.drawImage(sourceCanvas, -w / 2, -h / 2)

  return rotatedCanvas
}