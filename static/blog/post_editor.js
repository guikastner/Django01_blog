document.addEventListener("DOMContentLoaded", function () {
  const textarea = document.querySelector("#id_content");
  if (!textarea) {
    return;
  }

  const wrapper = document.createElement("div");
  wrapper.className = "local-wysiwyg";

  const toolbar = document.createElement("div");
  toolbar.className = "local-wysiwyg__toolbar";

  const editor = document.createElement("div");
  editor.className = "local-wysiwyg__editor";
  editor.contentEditable = "true";
  editor.innerHTML = textarea.value || "";

  const htmlToggle = document.createElement("button");
  htmlToggle.type = "button";
  htmlToggle.className = "local-wysiwyg__button";
  htmlToggle.textContent = "HTML";

  let htmlMode = false;
  let savedRange = null;

  function getCookie(name) {
    return (
      document.cookie
        .split(";")
        .map((cookie) => cookie.trim())
        .find((cookie) => cookie.startsWith(`${name}=`))
        ?.split("=")
        .slice(1)
        .join("=") || ""
    );
  }

  function saveSelection() {
    const selection = window.getSelection();
    if (selection && selection.rangeCount > 0 && editor.contains(selection.anchorNode)) {
      savedRange = selection.getRangeAt(0).cloneRange();
    }
  }

  function restoreSelection() {
    if (!savedRange) {
      editor.focus();
      return;
    }
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(savedRange);
  }

  function syncTextarea() {
    textarea.value = htmlMode ? editor.textContent : editor.innerHTML;
  }

  function runCommand(command, value = null) {
    editor.focus();
    document.execCommand(command, false, value);
    syncTextarea();
  }

  function insertImage(url) {
    if (htmlMode) {
      return;
    }
    restoreSelection();
    const image = document.createElement("img");
    image.src = url;
    image.alt = "";
    const selection = window.getSelection();
    const range = selection.rangeCount ? selection.getRangeAt(0) : null;
    if (range) {
      range.deleteContents();
      range.insertNode(image);
      range.setStartAfter(image);
      range.setEndAfter(image);
      selection.removeAllRanges();
      selection.addRange(range);
    } else {
      editor.appendChild(image);
    }
    syncTextarea();
  }

  function setStatus(message, isError = false) {
    status.textContent = message;
    status.classList.toggle("local-wysiwyg__status--error", isError);
  }

  async function uploadImage(file) {
    const uploadUrl = textarea.dataset.uploadUrl;
    if (!uploadUrl) {
      setStatus("Media upload endpoint is not configured.", true);
      return;
    }

    const formData = new FormData();
    formData.append("image", file);
    setStatus("Uploading media...");

    try {
      const response = await fetch(uploadUrl, {
        method: "POST",
        body: formData,
        credentials: "same-origin",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
      });

      const payload = await response.json();
      if (!response.ok) {
        setStatus(payload.error || "Media upload failed.", true);
        return;
      }

      insertImage(payload.url);
      setStatus("");
    } catch (error) {
      setStatus("Media upload failed.", true);
    }
  }

  function addButton(label, title, command, value = null) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "local-wysiwyg__button";
    button.textContent = label;
    button.title = title;
    button.setAttribute("aria-label", title);
    button.addEventListener("click", function () {
      if (!htmlMode) {
        runCommand(command, value);
      }
    });
    toolbar.appendChild(button);
  }

  function addDivider() {
    const divider = document.createElement("span");
    divider.className = "local-wysiwyg__divider";
    divider.setAttribute("aria-hidden", "true");
    toolbar.appendChild(divider);
  }

  addButton("B", "Bold", "bold");
  addButton("I", "Italic", "italic");
  addDivider();
  addButton("H2", "Heading 2", "formatBlock", "h2");
  addButton("P", "Paragraph", "formatBlock", "p");
  addDivider();
  addButton("ul", "Bulleted list", "insertUnorderedList");
  addButton("ol", "Numbered list", "insertOrderedList");
  addDivider();

  const linkButton = document.createElement("button");
  linkButton.type = "button";
  linkButton.className = "local-wysiwyg__button";
  linkButton.textContent = "Link";
  linkButton.title = "Create link";
  linkButton.setAttribute("aria-label", "Create link");
  linkButton.addEventListener("click", function () {
    if (htmlMode) {
      return;
    }
    const url = window.prompt("Link URL");
    if (url) {
      runCommand("createLink", url);
    }
  });
  toolbar.appendChild(linkButton);

  const imageInput = document.createElement("input");
  imageInput.type = "file";
  imageInput.accept = "image/jpeg,image/png,image/webp";
  imageInput.hidden = true;

  const imageButton = document.createElement("button");
  imageButton.type = "button";
  imageButton.className = "local-wysiwyg__button";
  imageButton.textContent = "Media";
  imageButton.title = "Upload media";
  imageButton.setAttribute("aria-label", "Upload media");
  imageButton.addEventListener("click", function () {
    if (!htmlMode) {
      imageInput.click();
    }
  });
  imageInput.addEventListener("change", function () {
    const file = imageInput.files?.[0];
    if (file) {
      uploadImage(file);
    }
    imageInput.value = "";
  });
  toolbar.appendChild(imageButton);
  toolbar.appendChild(imageInput);

  htmlToggle.title = "Edit HTML";
  htmlToggle.setAttribute("aria-label", "Edit HTML");
  htmlToggle.addEventListener("click", function () {
    htmlMode = !htmlMode;
    htmlToggle.classList.toggle("local-wysiwyg__button--active", htmlMode);
    editor.textContent = htmlMode ? editor.innerHTML : editor.textContent;
    syncTextarea();
  });
  toolbar.appendChild(htmlToggle);

  const status = document.createElement("p");
  status.className = "local-wysiwyg__status";
  status.setAttribute("aria-live", "polite");

  wrapper.appendChild(toolbar);
  wrapper.appendChild(editor);
  wrapper.appendChild(status);
  textarea.parentNode.insertBefore(wrapper, textarea.nextSibling);
  textarea.classList.add("local-wysiwyg__textarea");

  editor.addEventListener("keyup", saveSelection);
  editor.addEventListener("mouseup", saveSelection);
  editor.addEventListener("focus", saveSelection);
  editor.addEventListener("input", syncTextarea);
  editor.addEventListener("paste", function (event) {
    if (htmlMode) {
      return;
    }

    const files = Array.from(event.clipboardData?.items || [])
      .filter((item) => item.kind === "file" && item.type.startsWith("image/"))
      .map((item) => item.getAsFile())
      .filter(Boolean);

    if (files.length === 0) {
      window.setTimeout(syncTextarea, 0);
      return;
    }

    event.preventDefault();
    saveSelection();
    files.forEach((file) => uploadImage(file));
  });
  textarea.form?.addEventListener("submit", syncTextarea);
});
