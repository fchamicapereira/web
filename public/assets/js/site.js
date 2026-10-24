const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

// TV static behind everything; the 404 page turns it up through CSS.
const staticCanvas = document.getElementById("static");
const staticCtx = staticCanvas.getContext("2d");
let snow;

function sizeStatic() {
  staticCanvas.width = Math.ceil(innerWidth / 2);
  staticCanvas.height = Math.ceil(innerHeight / 2);
  snow = staticCtx.createImageData(staticCanvas.width, staticCanvas.height);
}

function drawStatic() {
  for (let i = 0; i < snow.data.length; i += 4) {
    const v = Math.random() * 255;
    snow.data[i] = snow.data[i + 1] = snow.data[i + 2] = v;
    snow.data[i + 3] = 255;
  }
  staticCtx.putImageData(snow, 0, 0);
}

sizeStatic();
drawStatic();
addEventListener("resize", () => { sizeStatic(); drawStatic(); });
if (!reduceMotion) setInterval(() => { if (!document.hidden) drawStatic(); }, 83);

// Abstract and BibTeX buttons open the panel they control.
for (const button of document.querySelectorAll("button[aria-controls]")) {
  const panel = document.getElementById(button.getAttribute("aria-controls"));
  button.addEventListener("click", () => {
    panel.hidden = !panel.hidden;
    button.setAttribute("aria-expanded", String(!panel.hidden));
  });
}

// Copy BibTeX, falling back to selecting it when the clipboard is unavailable.
for (const button of document.querySelectorAll("button[data-copy]")) {
  const source = document.getElementById(button.dataset.copy);
  const label = button.textContent;
  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(source.textContent);
      button.textContent = "Copied";
    } catch {
      const range = document.createRange();
      range.selectNodeContents(source);
      getSelection().removeAllRanges();
      getSelection().addRange(range);
      button.textContent = "Selected, press Ctrl+C";
    }
    setTimeout(() => { button.textContent = label; }, 2200);
  });
}

// Type "redrum" anywhere.
let typed = "";
addEventListener("keydown", e => {
  if (e.key.length !== 1) return;
  typed = (typed + e.key.toLowerCase()).slice(-6);
  if (typed === "redrum") {
    document.body.classList.add("mirror");
    setTimeout(() => document.body.classList.remove("mirror"), 2500);
  }
});
