// See app.js for why local module imports are versioned with ?v=__VERSION__.
import { getHandles, updateCropFromDrag } from "./geometry.js?v=__VERSION__"

export function startDrag(e, state, canvas, requestRender) {
  const pos = getPos(e, canvas)
  state.pointer = pos
  e.preventDefault()

  state.dragging = null

  let bestHandle = null
  let bestDist = Infinity

  for (const h of getHandles(state.crop)) {
    const dx = pos.x - h.x
    const dy = pos.y - h.y
    const dist = Math.sqrt(dx * dx + dy * dy)

    if (dist < 50 && dist < bestDist) {
      bestDist = dist
      bestHandle = h
    }
  }

  if (bestHandle) {
    state.dragging = bestHandle.name
  }

  requestRender()
}

export function onDrag(e, state, canvas, requestRender) {
  if (e.buttons === 0) {
    state.dragging = null
    return
  }

  if (!state.dragging) return
  
  const pos = getPos(e, canvas)
  state.pointer = pos

  e.preventDefault()
  updateCropFromDrag(state, pos)

  requestRender()
}

export function endDrag(state) {
  state.dragging = null
}

function getPos(e, canvas) {
  const rect = canvas.getBoundingClientRect()

  let clientX = e.touches ? e.touches[0].clientX : e.clientX
  let clientY = e.touches ? e.touches[0].clientY : e.clientY

  const canvasRatio = canvas.width / canvas.height
  const rectRatio = rect.width / rect.height

  let drawWidth, drawHeight, offsetX, offsetY

  if (canvasRatio > rectRatio) {
    drawWidth = rect.width
    drawHeight = rect.width / canvasRatio
    offsetX = 0
    offsetY = (rect.height - drawHeight) / 2
  } else {
    drawHeight = rect.height
    drawWidth = rect.height * canvasRatio
    offsetX = (rect.width - drawWidth) / 2
    offsetY = 0
  }

  const x = (clientX - rect.left - offsetX) * (canvas.width / drawWidth)
  const y = (clientY - rect.top - offsetY) * (canvas.height / drawHeight)

  return { x, y }
}