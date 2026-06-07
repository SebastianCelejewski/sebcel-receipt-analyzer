// On-device error/log overlay.
//
// Remote debugging a phone (especially an older one) is a hassle - plugging
// it into a computer, enabling USB debugging, etc. This module gives us a
// lightweight, always-available alternative: it captures uncaught errors,
// unhandled promise rejections, and console.error/warn calls, and renders
// them into a toggleable on-screen panel (#debugLog) so issues can be seen
// and reported directly from the device having the problem.
//
// Toggle by tapping the version/env label (#version) in the top bar.

const MAX_ENTRIES = 200

let entries = []

export function initDebugLog() {
  const panel = document.getElementById("debugLog")
  const toggleEl = document.getElementById("version")

  if (!panel) return

  if (toggleEl) {
    toggleEl.addEventListener("click", () => {
      panel.classList.toggle("hidden")
    })
  }

  window.addEventListener("error", (e) => {
    log("error", `${e.message} (${e.filename}:${e.lineno}:${e.colno})`)
  })

  window.addEventListener("unhandledrejection", (e) => {
    const reason = e.reason
    const message = reason && reason.stack ? reason.stack : String(reason)
    log("error", `Unhandled rejection: ${message}`)
  })

  wrapConsoleMethod("error")
  wrapConsoleMethod("warn")

  render(panel)
}

function wrapConsoleMethod(level) {
  const original = console[level]

  console[level] = function (...args) {
    log(level, args.map(stringifyArg).join(" "))
    original.apply(console, args)
  }
}

function stringifyArg(arg) {
  if (arg instanceof Error) return arg.stack || arg.message
  if (typeof arg === "object") {
    try {
      return JSON.stringify(arg)
    } catch (e) {
      return String(arg)
    }
  }
  return String(arg)
}

function log(level, message) {
  const timestamp = new Date().toLocaleTimeString()
  entries.push({ level, message, timestamp })

  if (entries.length > MAX_ENTRIES) {
    entries = entries.slice(entries.length - MAX_ENTRIES)
  }

  const panel = document.getElementById("debugLog")
  if (panel) render(panel)
}

function render(panel) {
  panel.innerHTML = entries
    .map((e) => `<div class="debugLogEntry debugLogEntry--${e.level}">[${e.timestamp}] ${escapeHtml(e.message)}</div>`)
    .join("")

  panel.scrollTop = panel.scrollHeight
}

function escapeHtml(text) {
  const div = document.createElement("div")
  div.textContent = text
  return div.innerHTML
}
