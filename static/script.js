let mergeFiles = [];
let dragSourceIndex = null;
let currentPreview = null;


// =====================================
// TAB SWITCHING
// =====================================

function switchTab(tab) {

  // Reset Merge
  mergeFiles = [];
  currentPreview = null;

  document.getElementById("mergeFiles").value = "";
  document.getElementById("mergeCards").innerHTML = "";
  document.getElementById("mergePreview").innerHTML = "No PDF Selected";
  document.getElementById("mergeResult").innerHTML = "";

  // Reset Compress
  document.getElementById("pdfFile").value = "";
  document.getElementById("compressPreview").innerHTML = "No PDF Selected";
  document.getElementById("result").innerHTML = "";
  document.getElementById("size").value = "";

  // Switch tabs
  document.getElementById("tabMerge").classList.toggle("active", tab === "merge");
  document.getElementById("tabCompress").classList.toggle("active", tab === "compress");

  document.getElementById("mergeTab").style.display =
    tab === "merge" ? "block" : "none";

  document.getElementById("compressTab").style.display =
    tab === "compress" ? "block" : "none";
}


// =====================================
// PDF PREVIEW
// =====================================

function showPreview(file, containerId) {

  if (containerId === "mergePreview")
    currentPreview = file;

  const container =
    document.getElementById(containerId);

  container.innerHTML = "";

  if (!file)
    return;

  const url =
    URL.createObjectURL(file);

  const embed =
    document.createElement("embed");

  embed.src = url;
  embed.type = "application/pdf";
  embed.style.width = "100%";
  embed.style.height = "100%";

  container.appendChild(embed);
}


// =====================================
// COMPRESS PREVIEW
// =====================================

document.getElementById("pdfFile").addEventListener("change", function () {

  const file = this.files[0];

  showPreview(file, "compressPreview");

  if (file) {

    let size = file.size;
    let text = "";

    if (size >= 1024 * 1024 * 1024) {
      text = (size / (1024 * 1024 * 1024)).toFixed(2) + " GB";
    }
    else if (size >= 1024 * 1024) {
      text = (size / (1024 * 1024)).toFixed(2) + " MB";
    }
    else {
      text = (size / 1024).toFixed(2) + " KB";
    }

    document.getElementById("originalSize").value = text;
  }
  else {
    document.getElementById("originalSize").value = "";
  }

});
// =====================================
// COMPRESS
// =====================================

async function compress() {

  const file =
    document
      .getElementById("pdfFile")
      .files[0];

  const size =
    document
      .getElementById("size")
      .value;

  const result =
    document
      .getElementById("result");

  if (!file) {

    result.innerHTML =
      "<p>Select PDF first.</p>";

    return;
  }

  result.innerHTML =
    "<p>Compressing PDF...</p>";

  const formData =
    new FormData();

  formData.append(
    "pdf",
    file
  );

  formData.append(
    "size",
    size
  );

  try {

    const response =
      await fetch(
        "/compress",
        {
          method: "POST",
          body: formData
        }
      );

    const data =
      await response.json();

    if (!response.ok) {

      result.innerHTML =
        `<p>${data.error}</p>`;

      return;
    }

    result.innerHTML =
      `
            <h3>
                Compression Complete
            </h3>

            <p>
                Original :
                ${data.before} MB
            </p>

            <p>
                Output :
                ${data.after} MB
            </p>
            <p>
              DPI : ${data.dpi}
            </p>

            <p>
                ${data.message}
            </p>

            <a
                href="${data.download}"
                download>
                Download PDF
            </a>
            `;

  }
  catch (err) {

    result.innerHTML =
      `<p>${err}</p>`;
  }
}


// =====================================
// MERGE FILES
// =====================================

function handleMergeFiles(event) {

  const files =
    Array.from(
      event.target.files || []
    );

  if (!files.length)
    return;

  mergeFiles.push(
    ...files
  );

  renderMergeCards();

  // automatically preview first file
  if (
    mergeFiles.length > 0 &&
    currentPreview == null
  ) {
    showPreview(
      mergeFiles[0],
      "mergePreview"
    );
  }

  event.target.value = "";
}


// =====================================
// RENDER FILES
// =====================================

function renderMergeCards() {

  const container =
    document.getElementById(
      "mergeCards"
    );

  container.innerHTML = "";

  mergeFiles.forEach(
    (file, index) => {

      const card =
        document.createElement(
          "div"
        );

      card.className =
        "card";

      card.draggable =
        true;

      card.dataset.index =
        index;


      card.onclick =
        () =>
          showPreview(
            file,
            "mergePreview"
          );


      card.addEventListener(
        "dragstart",
        () => {

          dragSourceIndex =
            index;
        });


      card.addEventListener(
        "dragover",
        e => {

          e.preventDefault();
        });


      card.addEventListener(
        "drop",
        () => {

          const moved =
            mergeFiles.splice(
              dragSourceIndex,
              1
            )[0];

          mergeFiles.splice(
            index,
            0,
            moved
          );

          renderMergeCards();

          // preserve preview
          if (currentPreview)
            showPreview(
              currentPreview,
              "mergePreview"
            );
        });


      card.innerHTML =
        `
                <div>
                    ${index + 1}.
                    ${file.name}
                </div>
                `;


      const remove =
        document.createElement(
          "button"
        );

      remove.innerText =
        "Remove";

      remove.onclick =
        function (e) {

          e.stopPropagation();

          const removed =
            mergeFiles[index];

          mergeFiles.splice(
            index,
            1
          );

          renderMergeCards();

          // if removed file was previewed
          if (
            removed === currentPreview
          ) {

            if (
              mergeFiles.length
            ) {

              showPreview(
                mergeFiles[0],
                "mergePreview"
              );

            }
            else {

              currentPreview =
                null;

              document
                .getElementById(
                  "mergePreview"
                )
                .innerHTML =
                "No PDF Selected";
            }
          }
        };


      card.appendChild(
        remove
      );

      container.appendChild(
        card
      );
    });
}


// =====================================
// MERGE
// =====================================

async function merge() {

  const result =
    document
      .getElementById(
        "mergeResult"
      );

  if (
    mergeFiles.length < 2
  ) {

    result.innerHTML =
      "<p>Select at least 2 PDFs.</p>";

    return;
  }

  result.innerHTML =
    "<p>Merging PDFs...</p>";

  const formData =
    new FormData();

  mergeFiles.forEach(
    file =>
      formData.append(
        "pdfs",
        file
      )
  );

  try {

    const response =
      await fetch(
        "/merge",
        {
          method: "POST",
          body: formData
        }
      );

    if (!response.ok) {

      result.innerHTML =
        "<p>Merge failed.</p>";

      return;
    }

    const blob =
      await response.blob();

    const url =
      URL.createObjectURL(
        blob
      );

    result.innerHTML =
      `
            <h3>
                Merge Completed
            </h3>

            <p>
                Files :
                ${mergeFiles.length}
            </p>

            <a
                href="${url}"
                download="merged.pdf">
                Download Merged PDF
            </a>
            `;
  }

  catch (err) {

    result.innerHTML =
      `<p>${err}</p>`;
  }
}


// =====================================
// INIT
// =====================================

switchTab("merge");

document
  .getElementById("mergeFiles")
  .addEventListener(
    "change",
    handleMergeFiles
  );

// =====================================
// FEEDBACK
// =====================================

function openFeedback() {

  document.getElementById("feedbackModal").style.display = "flex";
}

function closeFeedback() {

  document.getElementById("feedbackModal").style.display = "none";

  document.getElementById("feedbackText").value = "";
}

async function sendFeedback() {

  const text = document
    .getElementById("feedbackText")
    .value
    .trim();

  if (text === "") {

    alert("Please enter your feedback.");

    return;
  }

  try {

    const response = await fetch("/feedback", {

      method: "POST",

      headers: {
        "Content-Type": "application/json"
      },

      body: JSON.stringify({
        feedback: text
      })
    });

    const data = await response.json();

    if (!response.ok) {

      alert(data.error);

      return;
    }

    document.getElementById("feedbackMessage").innerHTML =
      "<span style='color:green'>Thank you. Your feedback has been sent.</span>";

    document.getElementById("feedbackText").value = "";

    setTimeout(() => {
      closeFeedback();
      document.getElementById("feedbackMessage").innerHTML = "";
    }, 1500);
  }
  catch (err) {

    alert("Error sending feedback.");
  }
}
