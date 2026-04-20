document.addEventListener("DOMContentLoaded", function () {
  const textarea = document.querySelector("#id_content");
  if (!textarea) {
    return;
  }

  const wrapper = document.createElement("div");
  wrapper.className = "local-wysiwyg";

  const tabs = document.createElement("div");
  tabs.className = "local-wysiwyg__tabs";
  tabs.setAttribute("role", "tablist");
  tabs.setAttribute("aria-label", "Editor mode");

  const toolbar = document.createElement("div");
  toolbar.className = "local-wysiwyg__toolbar";

  const editor = document.createElement("div");
  editor.className = "local-wysiwyg__editor";
  editor.contentEditable = "true";
  editor.innerHTML = textarea.value || "";
  editor.setAttribute("role", "tabpanel");
  editor.setAttribute("aria-label", "Post content editor");

  const status = document.createElement("p");
  status.className = "local-wysiwyg__status";
  status.setAttribute("aria-live", "polite");

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

  function setStatus(message, isError = false) {
    status.textContent = message;
    status.classList.toggle("local-wysiwyg__status--error", isError);
  }

  function updateToolbarState() {
    toolbar.querySelectorAll("[data-command-state]").forEach((button) => {
      const command = button.dataset.commandState;
      let isActive = false;
      try {
        isActive = document.queryCommandState(command);
      } catch (error) {
        isActive = false;
      }
      button.classList.toggle("local-wysiwyg__button--active", isActive);
      button.setAttribute("aria-pressed", String(isActive));
    });
  }

  function setEditorMode(nextMode) {
    if (nextMode === "html" && !htmlMode) {
      editor.textContent = editor.innerHTML;
      htmlMode = true;
    }

    if (nextMode === "visual" && htmlMode) {
      editor.innerHTML = editor.textContent;
      htmlMode = false;
    }

    wrapper.classList.toggle("local-wysiwyg--html", htmlMode);
    visualTab.setAttribute("aria-selected", String(!htmlMode));
    htmlTab.setAttribute("aria-selected", String(htmlMode));
    editor.setAttribute("aria-label", htmlMode ? "Post content HTML editor" : "Post content visual editor");
    syncTextarea();
    editor.focus();
  }

  function runCommand(command, value = null) {
    if (htmlMode) {
      return;
    }
    restoreSelection();
    document.execCommand(command, false, value);
    syncTextarea();
    updateToolbarState();
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

  function addTab(label, mode) {
    const tab = document.createElement("button");
    tab.type = "button";
    tab.className = "local-wysiwyg__tab";
    tab.textContent = label;
    tab.setAttribute("role", "tab");
    tab.setAttribute("aria-selected", mode === "visual" ? "true" : "false");
    tab.addEventListener("click", function () {
      setEditorMode(mode);
    });
    tabs.appendChild(tab);
    return tab;
  }

  function addButton(label, title, command, value = null, tracksState = false) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "local-wysiwyg__button";
    button.textContent = label;
    button.title = title;
    button.setAttribute("aria-label", title);
    if (tracksState) {
      button.dataset.commandState = command;
      button.setAttribute("aria-pressed", "false");
    }
    button.addEventListener("click", function () {
      runCommand(command, value);
    });
    toolbar.appendChild(button);
    return button;
  }

  function addIconButton(icon, title, command, value = null, tracksState = false) {
    const button = addButton("", title, command, value, tracksState);
    button.classList.add("local-wysiwyg__button--icon");
    button.innerHTML = icon;
    return button;
  }

  function addDivider() {
    const divider = document.createElement("span");
    divider.className = "local-wysiwyg__divider";
    divider.setAttribute("aria-hidden", "true");
    toolbar.appendChild(divider);
  }

  const visualTab = addTab("Visual", "visual");
  const htmlTab = addTab("HTML", "html");

  const formatSelect = document.createElement("select");
  formatSelect.className = "local-wysiwyg__select";
  formatSelect.title = "Text style";
  formatSelect.setAttribute("aria-label", "Text style");
  [
    ["p", "Paragraph"],
    ["h2", "Heading 2"],
    ["h3", "Heading 3"],
    ["blockquote", "Quote"],
  ].forEach(([value, label]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    formatSelect.appendChild(option);
  });
  formatSelect.addEventListener("change", function () {
    runCommand("formatBlock", formatSelect.value);
  });
  toolbar.appendChild(formatSelect);

  addDivider();
  addButton("B", "Bold", "bold", null, true);
  addButton("I", "Italic", "italic", null, true);
  addDivider();
  addIconButton(
    '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="6" cy="7" r="1.4"></circle><circle cx="6" cy="12" r="1.4"></circle><circle cx="6" cy="17" r="1.4"></circle><path d="M10 7h8"></path><path d="M10 12h8"></path><path d="M10 17h8"></path></svg>',
    "Bulleted list",
    "insertUnorderedList",
    null,
    true
  );
  addIconButton(
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 8h1.5V4.5L5 5.4"></path><path d="M4.8 13.2c0-1 2.8-1.1 2.8.2 0 .9-1.5 1.3-2.8 2.8h3"></path><path d="M5 19.4c.4.5 2.7.7 2.7-.7 0-.8-.7-1.1-1.4-1.1.7 0 1.2-.4 1.2-1.1 0-1.1-1.8-1.2-2.4-.6"></path><path d="M11 7h7"></path><path d="M11 12h7"></path><path d="M11 17h7"></path></svg>',
    "Numbered list",
    "insertOrderedList",
    null,
    true
  );
  addDivider();
  addIconButton(
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 7H4v5"></path><path d="M4 7l5-5"></path><path d="M5 7h8a5 5 0 1 1 0 10h-3"></path></svg>',
    "Undo",
    "undo"
  );
  addIconButton(
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 7h5v5"></path><path d="M20 7l-5-5"></path><path d="M19 7h-8a5 5 0 1 0 0 10h3"></path></svg>',
    "Redo",
    "redo"
  );
  addDivider();

  const linkButton = document.createElement("button");
  linkButton.type = "button";
  linkButton.className = "local-wysiwyg__button local-wysiwyg__button--icon";
  linkButton.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.1 0l2-2a5 5 0 0 0-7.1-7.1l-1.1 1.1"></path><path d="M14 11a5 5 0 0 0-7.1 0l-2 2A5 5 0 0 0 12 20.1l1.1-1.1"></path></svg>';
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
  imageButton.className = "local-wysiwyg__button local-wysiwyg__button--icon local-wysiwyg__button--primary";
  imageButton.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v14H4z"></path><path d="M8 13l2.5-2.5L16 16"></path><path d="M14 14l2-2 4 4"></path><circle cx="8.5" cy="8.5" r="1.5"></circle></svg>';
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

  wrapper.appendChild(tabs);
  wrapper.appendChild(toolbar);
  wrapper.appendChild(editor);
  wrapper.appendChild(status);
  textarea.parentNode.insertBefore(wrapper, textarea.nextSibling);
  textarea.classList.add("local-wysiwyg__textarea");

  editor.addEventListener("keyup", function () {
    saveSelection();
    updateToolbarState();
  });
  editor.addEventListener("mouseup", function () {
    saveSelection();
    updateToolbarState();
  });
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
  document.addEventListener("selectionchange", updateToolbarState);
  textarea.form?.addEventListener("submit", syncTextarea);
});
