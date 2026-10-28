document.addEventListener("DOMContentLoaded", () => {
  const escapeHtml = (value) =>
    String(value).replace(/[&<>"']/g, (ch) => (
      { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]
    ));

  // Toast notifications
  let toastTimer;
  const toast = document.querySelector("#toast");
  const TOAST_SHOWN = ["opacity-100", "translate-y-0"];
  const TOAST_HIDDEN = ["opacity-0", "translate-y-2.5"];
  const showToast = (message) => {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add(...TOAST_SHOWN);
    toast.classList.remove(...TOAST_HIDDEN);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.classList.add(...TOAST_HIDDEN);
      toast.classList.remove(...TOAST_SHOWN);
    }, 3000);
  };

  // Modal functions — backdrops start hidden and are shown with display:flex.
  const openModal = (id) => {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.remove("hidden");
    modal.classList.add("flex");
    document.body.style.overflow = "hidden";
    modal.querySelector(".close-button")?.focus();
  };

  const closeModal = (id) => {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.add("hidden");
    modal.classList.remove("flex");
    if (!document.querySelector(".modal-backdrop.flex, .modal-backdrop:not(.hidden)")) {
      document.body.style.overflow = "";
    }
  };

  // Delegated clicks so listeners keep working for content swapped in via AJAX.
  document.addEventListener("click", (event) => {
    const closer = event.target.closest("[data-close]");
    if (closer) {
      closeModal(closer.dataset.close);
      return;
    }

    if (event.target.classList?.contains("modal-backdrop")) {
      closeModal(event.target.id);
      return;
    }

    if (event.target.closest("#open-members-modal")) {
      openModal("members-modal");
      return;
    }

    if (event.target.closest("#open-invite-modal")) {
      openModal("invite-modal");
      return;
    }

    if (event.target.closest("#open-add-suggestion")) {
      openModal("add-suggestion-modal");
      return;
    }

    const editButton = event.target.closest("[data-edit]");
    if (editButton) {
      openModal(`edit-modal-${editButton.dataset.edit}`);
      return;
    }

    const summaryButton = event.target.closest(".agree-summary[data-voters]");
    if (summaryButton && !summaryButton.disabled) {
      renderVoters(votersFor(summaryButton));
      openModal("voters-modal");
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      const open = document.querySelector(".modal-backdrop:not(.hidden)");
      if (open) closeModal(open.id);
    }
  });

  // Copy link
  document.addEventListener("click", async (event) => {
    if (!event.target.closest("#copy-link")) return;
    const input = document.querySelector("#invite-link");
    if (!input) return;
    try {
      await navigator.clipboard.writeText(input.value);
      showToast("لینک کپی شد.");
    } catch {
      input.select();
      showToast("کپی لینک ممکن نشد؛ آن را دستی کپی کنید.");
    }
  });

  // Share link
  document.addEventListener("click", async (event) => {
    if (!event.target.closest("#share-link")) return;
    const url = document.querySelector("#invite-link")?.value;
    if (!url) return;
    if (navigator.share) {
      try {
        await navigator.share({ title: "دعوت به دورهمی", text: "بیا برای دورهمی برنامه‌ریزی کنیم!", url });
      } catch (e) {
        if (e.name !== "AbortError") showToast("اشتراک‌گذاری انجام نشد.");
      }
    } else {
      try {
        await navigator.clipboard.writeText(url);
        showToast("این مرورگر اشتراک‌گذاری مستقیم ندارد؛ لینک کپی شد.");
      } catch {
        showToast("لینک را کپی کنید و برای دوستتان بفرستید.");
      }
    }
  });

  // Voters modal — names live in a JSON script tag inside each suggestion card,
  // so they are read at click time and stay fresh after AJAX swaps.
  const votersFor = (button) => {
    const card = button.closest("[data-suggestion]");
    const script = card?.querySelector('script[type="application/json"]');
    if (!script) return [];
    try {
      return JSON.parse(script.textContent);
    } catch {
      return [];
    }
  };

  const renderVoters = (names) => {
    const list = document.querySelector("#voter-list");
    if (!list) return;
    list.innerHTML = names.length
      ? names.map((name) => `
          <div class="flex items-center gap-[13px] border-b border-line py-3 last:border-b-0">
            <span class="grid size-10.5 shrink-0 place-items-center rounded-full bg-[linear-gradient(145deg,#f7e8f0,#ead0df)] text-xs font-bold text-primary-dark" aria-hidden="true">${escapeHtml(String(name).slice(0, 1))}</span>
            <div>
              <div class="text-[13px] font-semibold text-ink">${escapeHtml(name)}</div>
              <div class="text-[11px] text-muted">موافق این پیشنهاد</div>
            </div>
          </div>`).join("")
      : '<div class="px-3 py-7 text-center text-[13px] text-muted">هنوز کسی موافق نیست.</div>';
    const subtitle = document.querySelector("#voters-subtitle");
    if (subtitle) {
      subtitle.textContent = names.length === 0
        ? "هنوز کسی موافق نیست."
        : `${names.length} موافق`;
    }
  };

  // Add suggestion form AJAX submission
  document.querySelector("#add-suggestion-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = "در حال ثبت…";
    form.querySelectorAll(".errorlist").forEach((el) => el.remove());

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
        },
      });

      if (response.ok) {
        showToast("پیشنهاد با موفقیت ثبت شد.");
        closeModal("add-suggestion-modal");
        form.reset();
        // Reload page to show new suggestion
        window.location.reload();
      } else {
        const data = await response.json();
        if (data.errors) {
          // Display form errors, creating the error list the first time it is needed
          Object.entries(data.errors).forEach(([field, errors]) => {
            const input = form.querySelector(`[name="${field}"]`);
            if (!input) return;
            const fieldDiv = input.closest(".mb-4") || input.parentElement;
            let errorDiv = fieldDiv.querySelector(".errorlist");
            if (!errorDiv) {
              errorDiv = document.createElement("ul");
              errorDiv.className = "errorlist";
              fieldDiv.appendChild(errorDiv);
            }
            errorDiv.innerHTML = errors.map((err) => `<li>${escapeHtml(err)}</li>`).join("");
          });
        }
        showToast("خطا در ثبت پیشنهاد.");
      }
    } catch {
      showToast("خطا در ارتباط با سرور.");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "ثبت پیشنهاد";
    }
  });

  // Delegated submits: confirmation prompts and the AJAX agreement toggle.
  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;

    if (form.dataset.confirm && !confirm(form.dataset.confirm)) {
      event.preventDefault();
      return;
    }

    if (form.classList.contains("agreement-form")) {
      event.preventDefault();
      toggleAgreement(form);
    }
  });

  // Agreement toggle — the server answers with freshly rendered sections and
  // the new agreement state; swapping them keeps counts, leading marks and
  // the organizer's finalize box in sync with the database.
  const toggleAgreement = async (form) => {
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn?.textContent;
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "در حال ثبت…";
    }

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]")?.value,
        },
      });
      if (!response.ok) throw new Error("Agreement failed");
      const data = await response.json();

      const suggestionsSlot = document.querySelector("#suggestions-slot");
      if (data.suggestions_html && suggestionsSlot) {
        suggestionsSlot.innerHTML = data.suggestions_html;
      }
      const sidebarSlot = document.querySelector("#sidebar-slot");
      if (data.sidebar_html && sidebarSlot) {
        sidebarSlot.innerHTML = data.sidebar_html;
      }

      showToast(data.agreed ? "موافقت شما ثبت شد." : "موافقت شما پس گرفته شد.");
    } catch {
      showToast("ثبت موافقت انجام نشد. لطفاً دوباره تلاش کنید.");
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }
    }
  };
});
