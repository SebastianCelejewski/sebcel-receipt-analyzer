import { getHandles, updateCropFromDrag } from "./geometry.js"

export function startDrag(e, state, canvas, requestRender) {
  const pos = getPos(e, canvas)
  state.pointer = pos
  e.preventDefault()

  for (const h of getHandles(state.crop)) {
    if (Math.abs(pos.x - h.x) < 50 && Math.abs(pos.y - h.y) < 50) {
      state.dragging = h.name;
      requestRender();
      return;
    }
  }

  state.dragging = null;
  requestRender();
}

export function onDrag(e, state, canvas, requestRender) {
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