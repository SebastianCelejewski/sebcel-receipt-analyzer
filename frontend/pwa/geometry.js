export function rotateCrop90(crop, width, height, direction) {
  // direction: +1 (right), -1 (left)

  if (direction === 1) {
    // 90° CW
    return {
      x: height - (crop.y + crop.h),
      y: crop.x,
      w: crop.h,
      h: crop.w
    }
  } else {
    // 90° CCW
    return {
      x: crop.y,
      y: width - (crop.x + crop.w),
      w: crop.h,
      h: crop.w
    }
  }
}

export function getHandles(crop) {
  return [
    { name: "tl", x: crop.x, y: crop.y },
    { name: "tr", x: crop.x + crop.w, y: crop.y },
    { name: "bl", x: crop.x, y: crop.y + crop.h },
    { name: "br", x: crop.x + crop.w, y: crop.y + crop.h }
  ]
}

export function updateCropFromDrag(state, pos) {
  const crop = state.crop

  if (state.dragging === "tl") {
    crop.w += crop.x - pos.x
    crop.h += crop.y - pos.y
    crop.x = pos.x
    crop.y = pos.y
  }

  if (state.dragging === "br") {
    crop.w = pos.x - crop.x
    crop.h = pos.y - crop.y
  }

  if (state.dragging === "tr") {
    crop.w = pos.x - crop.x
    crop.h += crop.y - pos.y
    crop.y = pos.y
  }

  if (state.dragging === "bl") {
    crop.w += crop.x - pos.x
    crop.h = pos.y - crop.y
    crop.x = pos.x
  }
}