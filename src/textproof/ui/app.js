/* TextProof (字证) local single-page UI — T008.
 *
 * Zero external dependencies: only same-origin /api/v1/* calls and
 * same-origin static files. No remote font, no third-party
 * script, no external image URL, and no browser storage of any kind:
 * this file never reads or writes any persistent browser store,
 * every in-memory reference to the image and the report.
 *
 * Wording rule (PROJECT_BOOK.md §3.3): the UI says "检测到差异 /
 * 疑似不一致 / 需要复核" and never claims the image is proven wrong.
 * REVIEW_REQUIRED, low confidence and OCR_FAILED are labelled
 * "待确认 / 不确定", never presented as confirmed errors.
 */

(function () {
  "use strict";

  var CHECK_URL = "/api/v1/check";
  var VERSION_URL = "/api/v1/version";
  var ACCEPTED_MIMES = ["image/png", "image/jpeg", "image/webp"];

  /* Verdict wording: every non-MATCH verdict is framed as a
   * difference against the current OCR output, or as "待确认". */
  var VERDICT_TEXT = {
    MATCH: "一致：未检测到差异",
    MISMATCH:
      "检测到差异：期望文本与当前 OCR 输出存在差异（疑似不一致，需要复核）",
    REVIEW_REQUIRED:
      "待确认：存在低置信度、对齐歧义或需要复核的内容，不是确定的错误",
    OCR_FAILED:
      "OCR 失败（待确认）：识别引擎未能产生可用结果，这不是已确认的图片错误",
  };

  var WARNING_TEXT = {
    LOW_OCR_CONFIDENCE:
      "识别结果不确定，需要人工查看原图片区域",
    OCR_EMPTY:
      "识别结果不确定：OCR 未能识别出可用文字，需要人工查看原图片",
  };

  /* In-memory state only. Nothing here is persisted anywhere. */
  var state = {
    imageFile: null, // File chosen by the user
    imageMime: "",
    imageBase64: "", // base64 payload for POST /api/v1/check
    objectUrl: "", // URL.createObjectURL preview URL (revoked on clear)
    imageWidth: 0,
    imageHeight: 0,
    report: null, // last textproof.report/v1 dict (or null)
    selectedErrorId: "",
    checkCount: 0,
  };

  function $(id) {
    return document.getElementById(id);
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined && text !== null) n.textContent = text;
    return n;
  }

  function setStatus(text) {
    $("status").textContent = text;
  }

  function showErrorBanner(text) {
    var b = $("error-banner");
    if (!text) {
      b.hidden = true;
      b.textContent = "";
      return;
    }
    b.hidden = false;
    b.textContent = text;
  }

  function refreshButtons() {
    var hasImage = !!state.imageFile;
    var hasText = $("expected-text").value.trim().length > 0;
    $("btn-check").disabled = !(hasImage && hasText);
    $("btn-recheck").disabled = !(hasImage && hasText && state.report !== null);
    $("btn-download").disabled = state.report === null;
    $("btn-copy").disabled = state.report === null;
  }

  /* --- upload ------------------------------------------------------- */

  function onFileChosen() {
    var input = $("file-input");
    var file = input.files && input.files[0];
    if (!file) return;
    if (ACCEPTED_MIMES.indexOf(file.type) === -1) {
      showErrorBanner(
        "不支持的图片格式：仅接受 PNG / JPEG / WebP，请重新选择。"
      );
      input.value = "";
      return;
    }
    showErrorBanner("");
    // Revoke any previous preview URL before replacing it.
    if (state.objectUrl) {
      URL.revokeObjectURL(state.objectUrl);
      state.objectUrl = "";
    }
    state.imageFile = file;
    state.imageMime = file.type;
    var url = URL.createObjectURL(file);
    state.objectUrl = url;
    var img = $("preview-img");
    img.onload = function () {
      state.imageWidth = img.naturalWidth;
      state.imageHeight = img.naturalHeight;
      $("image-info").textContent =
        "图片：" + file.name + "（" + file.type + "，" + file.size +
        " 字节，" + state.imageWidth + " × " + state.imageHeight + " px）";
      refreshButtons();
    };
    img.onerror = function () {
      showErrorBanner("图片预览加载失败，请重新选择图片。");
    };
    img.src = url;
    img.hidden = false;
    $("preview-stage").hidden = false;
    $("empty-state").hidden = true;
    setStatus("已选择图片，输入期望文本后点击“开始核对”。");
    refreshButtons();
    // Read the bytes for the API call (FileReader, in-memory only).
    var reader = new FileReader();
    reader.onload = function () {
      var dataUrl = String(reader.result || "");
      var comma = dataUrl.indexOf(",");
      state.imageBase64 = comma >= 0 ? dataUrl.slice(comma + 1) : "";
      refreshButtons();
    };
    reader.onerror = function () {
      showErrorBanner("读取图片失败，请重新选择图片。");
    };
    reader.readAsDataURL(file);
  }

  /* --- check -------------------------------------------------------- */

  function check() {
    if (!state.imageFile || !state.imageBase64) {
      setStatus("请先上传图片。");
      return Promise.resolve(false);
    }
    var expected = $("expected-text").value;
    if (!expected.trim()) {
      setStatus("期望文本为空，请输入期望文本。");
      return Promise.resolve(false);
    }
    setStatus("正在核对…（本机处理，不上传到任何外部服务）");
    showErrorBanner("");
    return fetch(CHECK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image_mime: state.imageMime,
        image_base64: state.imageBase64,
        expected_text: expected,
      }),
    })
      .then(function (resp) {
        return resp.json().then(function (body) {
          return { status: resp.status, body: body };
        });
      })
      .then(function (pair) {
        if (pair.status === 200 && pair.body && pair.body.schema) {
          state.report = pair.body;
          state.checkCount += 1;
          renderReport(pair.body);
          setStatus("核对完成（第 " + state.checkCount + " 次）。");
          return true;
        }
        // API error envelope: {error: {code, message, detail}}.
        var code = pair.body && pair.body.error ? pair.body.error.code : "";
        if (code === "OCR_FAILED") {
          state.report = null;
          renderOcrFailed();
          setStatus("OCR 失败（待确认），未生成确定结论。");
          return false;
        }
        state.report = null;
        renderEmptyResult();
        showErrorBanner(
          "核对未完成（" + (code || "HTTP " + pair.status) +
          "）：请检查图片与期望文本后重试。"
        );
        setStatus("核对未完成。");
        return false;
      })
      .catch(function () {
        state.report = null;
        renderEmptyResult();
        showErrorBanner("无法连接本机服务，请确认服务正在运行后重试。");
        setStatus("无法连接本机服务。");
        return false;
      })
      .then(function (ok) {
        refreshButtons();
        return ok;
      });
  }

  /* --- rendering ---------------------------------------------------- */

  function verdictClass(verdict) {
    if (verdict === "MATCH") return "verdict verdict-match";
    if (verdict === "MISMATCH") return "verdict verdict-mismatch";
    if (verdict === "REVIEW_REQUIRED") return "verdict verdict-review";
    if (verdict === "OCR_FAILED") return "verdict verdict-failed";
    return "verdict verdict-empty";
  }

  function renderOcrFailed() {
    var v = $("verdict");
    v.className = verdictClass("OCR_FAILED");
    v.textContent = VERDICT_TEXT.OCR_FAILED;
    $("error-count").textContent = "错误数量：—（未生成报告）";
    var list = $("error-list");
    list.textContent = "";
    list.appendChild(el("li", "empty-item", "OCR 未能产生可用结果，未列出确定错误。"));
    var warns = $("warning-list");
    warns.textContent = "";
    warns.appendChild(el("li", "", "OCR 失败（待确认）：请重试，或检查图片是否清晰、文字是否水平。"));
    $("error-detail").textContent = "未选中任何错误项。";
    $("overlay").hidden = true;
    $("overlay").textContent = "";
    $("report-json").textContent = "尚未生成报告。";
  }

  function renderEmptyResult() {
    var v = $("verdict");
    v.className = "verdict verdict-empty";
    v.textContent = "尚未核对";
    $("error-count").textContent = "错误数量：—";
    var list = $("error-list");
    list.textContent = "";
    list.appendChild(el("li", "empty-item", "暂无错误清单。"));
    var warns = $("warning-list");
    warns.textContent = "";
    warns.appendChild(el("li", "empty-item", "暂无复核提示。"));
    $("error-detail").textContent = "未选中任何错误项。";
    $("overlay").hidden = true;
    $("overlay").textContent = "";
    $("report-json").textContent = "尚未生成报告。";
  }

  function renderReport(report) {
    var verdict = report.verdict || "";
    var v = $("verdict");
    v.className = verdictClass(verdict);
    v.textContent = VERDICT_TEXT[verdict] || ("待确认：未知核对结果（" + verdict + "）");
    var errors = Array.isArray(report.errors) ? report.errors : [];
    var warnings = Array.isArray(report.warnings) ? report.warnings : [];
    $("error-count").textContent = "错误数量：" + errors.length;

    renderOverlay(report);
    renderErrorList(errors);
    renderWarnings(warnings);
    $("error-detail").textContent = "未选中任何错误项。";
    state.selectedErrorId = "";
    $("report-json").textContent = JSON.stringify(report, null, 2);
  }

  function renderOverlay(report) {
    var overlay = $("overlay");
    overlay.textContent = "";
    var lines = Array.isArray(report.ocr_lines) ? report.ocr_lines : [];
    var img = state.imageWidth > 0 && state.imageHeight > 0;
    if (!img || lines.length === 0) {
      overlay.hidden = true;
      return;
    }
    overlay.hidden = false;
    lines.forEach(function (line) {
      var box = line.bbox_xyxy;
      if (!Array.isArray(box) || box.length !== 4) return;
      var d = document.createElement("div");
      d.className = "ocr-box";
      d.dataset.lineIndex = String(line.line_index);
      d.style.left = (box[0] / state.imageWidth * 100) + "%";
      d.style.top = (box[1] / state.imageHeight * 100) + "%";
      d.style.width = ((box[2] - box[0]) / state.imageWidth * 100) + "%";
      d.style.height = ((box[3] - box[1]) / state.imageHeight * 100) + "%";
      d.title = "OCR 行 " + line.line_index + "：" + line.text;
      overlay.appendChild(d);
    });
  }

  function highlightBox(ocrLineIndex) {
    var boxes = $("overlay").querySelectorAll(".ocr-box");
    boxes.forEach(function (b) {
      b.classList.toggle(
        "selected",
        String(ocrLineIndex) !== "" &&
          b.dataset.lineIndex === String(ocrLineIndex)
      );
    });
  }

  function renderErrorList(errors) {
    var list = $("error-list");
    list.textContent = "";
    if (errors.length === 0) {
      list.appendChild(el("li", "empty-item", "未检测到差异。"));
      return;
    }
    errors.forEach(function (err) {
      var item = document.createElement("li");
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "error-item";
      btn.dataset.errorId = err.id || "";
      var label =
        (err.id || "?") + " · " + (err.type || "?") +
        " — 期望“" + (err.expected_fragment || "") + "” / 识别“" +
        (err.recognized_fragment || "") + "”";
      btn.textContent = label;
      btn.addEventListener("click", function () {
        selectError(err.id);
      });
      item.appendChild(btn);
      list.appendChild(item);
    });
  }

  function renderWarnings(warnings) {
    var list = $("warning-list");
    list.textContent = "";
    if (warnings.length === 0) {
      list.appendChild(el("li", "empty-item", "暂无复核提示。"));
      return;
    }
    warnings.forEach(function (w) {
      var text = WARNING_TEXT[w.code] || "待确认：需要人工复核（" + (w.code || "?") + "）。";
      var item = el("li", "", text);
      if (w.detail) {
        item.appendChild(document.createElement("br"));
        item.appendChild(document.createTextNode(String(w.detail)));
      }
      list.appendChild(item);
    });
  }

  function selectError(errorId) {
    if (!state.report) return;
    var errors = state.report.errors || [];
    var err = null;
    errors.forEach(function (e) {
      if (e.id === errorId) err = e;
    });
    if (!err) return;
    state.selectedErrorId = errorId;
    var items = $("error-list").querySelectorAll(".error-item");
    items.forEach(function (b) {
      b.classList.toggle("selected", b.dataset.errorId === errorId);
    });
    var hasBox = Array.isArray(err.bbox_xyxy) && err.bbox_xyxy.length === 4;
    highlightBox(hasBox ? err.ocr_line_index : "");
    var detail = $("error-detail");
    detail.textContent = "";
    var lines = [
      "类型：" + (err.type || "?"),
      "期望片段：“" + (err.expected_fragment || "") + "” " +
        "期望区间 " + JSON.stringify(err.expected_span || null),
      "识别片段：“" + (err.recognized_fragment || "") + "” " +
        "识别区间 " + JSON.stringify(err.recognized_span || null),
      "置信度：" + (err.confidence === null || err.confidence === undefined
        ? "—" : String(err.confidence)),
    ];
    if (hasBox) {
      lines.push("坐标（OCR 行框）：" + JSON.stringify(err.bbox_xyxy));
    } else {
      /* Missing whole line (or otherwise no OCR box): never invent a
       * box — say so explicitly (PROJECT_BOOK.md §4.6, FR-06). */
      lines.push("坐标：无可定位 OCR 框");
    }
    lines.forEach(function (t) {
      detail.appendChild(el("div", "", t));
    });
    detail.scrollIntoView({ block: "nearest" });
  }

  /* --- download / copy / clear -------------------------------------- */

  function downloadJson() {
    if (!state.report) return;
    var blob = new Blob(
      [JSON.stringify(state.report, null, 2)],
      { type: "application/json" }
    );
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "textproof-report.json";
    document.body.appendChild(a);
    a.click();
    a.remove();
    // The blob URL is single-use for this download; revoke it at once.
    URL.revokeObjectURL(url);
    setStatus("JSON 报告已下载。");
  }

  function copySummary() {
    if (!state.report) return;
    var r = state.report;
    var text =
      "TextProof 核对摘要\n" +
      "结论：" + (VERDICT_TEXT[r.verdict] || r.verdict) + "\n" +
      "错误数量：" + (r.summary ? r.summary.error_count : r.errors.length) + "\n" +
      "复核提示数量：" + (r.summary ? r.summary.warning_count : r.warnings.length) + "\n" +
      "（本摘要只说明期望文本与当前 OCR 输出的差异，不是图片文字一定有错的证明。）";
    function done(ok) {
      $("copy-status").textContent = ok ? "报告摘要已复制。" : "复制失败，请手动选中原始 JSON 报告。";
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        function () { done(true); },
        function () { fallbackCopy(text, done); }
      );
    } else {
      fallbackCopy(text, done);
    }
  }

  function fallbackCopy(text, done) {
    try {
      var ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      var ok = document.execCommand("copy");
      ta.remove();
      done(!!ok);
    } catch (e) {
      done(false);
    }
  }

  function clearAll() {
    // Revoke the preview object URL so the browser can release it.
    if (state.objectUrl) {
      URL.revokeObjectURL(state.objectUrl);
      state.objectUrl = "";
    }
    // Drop every in-memory reference to the image and the report.
    state.imageFile = null;
    state.imageMime = "";
    state.imageBase64 = "";
    state.imageWidth = 0;
    state.imageHeight = 0;
    state.report = null;
    state.selectedErrorId = "";
    state.checkCount = 0;
    // Reset the DOM: inputs, preview, overlay, results.
    $("file-input").value = "";
    $("expected-text").value = "";
    var img = $("preview-img");
    img.removeAttribute("src");
    img.hidden = true;
    $("preview-stage").hidden = true;
    $("overlay").textContent = "";
    $("overlay").hidden = true;
    $("empty-state").hidden = false;
    $("image-info").textContent = "尚未选择图片。";
    showErrorBanner("");
    renderEmptyResult();
    $("copy-status").textContent = "";
    setStatus("已清除：图片预览 URL 已撤销，输入与核对结果已清空。");
    refreshButtons();
  }

  /* --- boot --------------------------------------------------------- */

  function loadVersion() {
    fetch(VERSION_URL)
      .then(function (resp) { return resp.json(); })
      .then(function (body) {
        if (body && body.tool_version) {
          $("version").textContent =
            "版本：" + body.tool_version + " · schema " + (body.schema || "?");
        }
      })
      .catch(function () {
        $("version").textContent = "版本：未知（本机服务未响应）";
      });
  }

  function init() {
    $("file-input").addEventListener("change", onFileChosen);
    $("expected-text").addEventListener("input", refreshButtons);
    $("btn-check").addEventListener("click", function () { check(); });
    $("btn-recheck").addEventListener("click", function () { check(); });
    $("btn-download").addEventListener("click", downloadJson);
    $("btn-copy").addEventListener("click", copySummary);
    $("btn-clear").addEventListener("click", clearAll);
    loadVersion();
    refreshButtons();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
