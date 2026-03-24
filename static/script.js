let mergeFiles = []
let dragSourceIndex = null

function switchTab(tab) {
  document.getElementById("tabCompress").classList.toggle("active", tab === "compress")
  document.getElementById("tabMerge").classList.toggle("active", tab === "merge")

  document.getElementById("compressTab").style.display = tab === "compress" ? "block" : "none"
  document.getElementById("mergeTab").style.display = tab === "merge" ? "block" : "none"

  // Clear any existing results when switching tabs
  document.getElementById("result").innerHTML = ""
  document.getElementById("mergeResult").innerHTML = ""
}

async function compress() {
  const file = document.getElementById("pdfFile").files[0]
  const size = document.getElementById("size").value

  const formData = new FormData()
  formData.append("pdf", file)
  formData.append("size", size)

  const response = await fetch("/compress", {
    method: "POST",
    body: formData
  })

  const data = await response.json()

  if (!response.ok) {
    document.getElementById("result").innerHTML = `<p style="color: red;">Error: ${data.error || 'Something went wrong.'}</p>`
    return
  }

  document.getElementById("result").innerHTML = `
    <p>Original Size: ${data.before} KB</p>
    <p>Compressed Size: ${data.after} KB</p>
    <p>${data.message || ""}</p>
    <a href="${data.download}">Download PDF</a>
  `
}

function handleMergeFiles(event) {
  const files = Array.from(event.target.files || [])
  if (!files.length) return

  mergeFiles.push(...files)
  renderMergeCards()

  // Reset to allow selecting the same file again
  event.target.value = ""
}

function renderMergeCards() {
  const container = document.getElementById("mergeCards")
  container.innerHTML = ""

  mergeFiles.forEach((file, index) => {
    const card = document.createElement("div")
    card.className = "card"
    card.draggable = true
    card.dataset.index = index

    card.addEventListener("dragstart", (e) => {
      dragSourceIndex = index
      card.classList.add("dragging")
      e.dataTransfer.effectAllowed = "move"
    })

    card.addEventListener("dragend", () => {
      card.classList.remove("dragging")
    })

    card.addEventListener("dragover", (e) => {
      e.preventDefault()
      e.dataTransfer.dropEffect = "move"
      card.classList.add("drag-over")
    })

    card.addEventListener("dragleave", () => {
      card.classList.remove("drag-over")
    })

    card.addEventListener("drop", (e) => {
      e.preventDefault()
      card.classList.remove("drag-over")

      const targetIndex = Number(card.dataset.index)
      if (dragSourceIndex == null || targetIndex === dragSourceIndex) return

      const item = mergeFiles.splice(dragSourceIndex, 1)[0]
      mergeFiles.splice(targetIndex, 0, item)
      renderMergeCards()
    })

    const title = document.createElement("div")
    title.textContent = file.name

    const remove = document.createElement("button")
    remove.textContent = "Remove"
    remove.addEventListener("click", () => {
      mergeFiles.splice(index, 1)
      renderMergeCards()
    })

    card.appendChild(title)
    card.appendChild(remove)
    container.appendChild(card)
  })
}

async function merge() {
  if (!mergeFiles.length) {
    document.getElementById("mergeResult").innerHTML = `<p style="color: red;">Select at least 2 PDFs to merge.</p>`
    return
  }

  const formData = new FormData()
  mergeFiles.forEach((file) => formData.append("pdfs", file))

  const response = await fetch("/merge", {
    method: "POST",
    body: formData
  })

  if (!response.ok) {
    document.getElementById("mergeResult").innerHTML = `<p style="color: red;">Merge failed.</p>`
    return
  }

  const blob = await response.blob()
  const url = URL.createObjectURL(blob)

  document.getElementById("mergeResult").innerHTML = `
    <p>Merged ${mergeFiles.length} files.</p>
    <a href="${url}" download="merged.pdf">Download Merged PDF</a>
  `
}

// Initialize UI
switchTab("compress")
document.getElementById("mergeFiles").addEventListener("change", handleMergeFiles)
