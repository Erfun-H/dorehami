document.addEventListener("DOMContentLoaded", () => {
  const escapeHtml = (value) =>
    String(value).replace(/[&<>"']/g, (ch) => (
      { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]
    ));

  // Toast notifications
  let toastTimer;
  const toast = document.querySelector("#toast");
  const showToast = (message) => {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 3000);
  };

  // Modal functions
  const openModal = (id) => {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.add("open");
    document.body.style.overflow = "hidden";
    modal.querySelector(".close-button")?.focus();
  };

  const closeModal = (id) => {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.remove("open");
    if (!document.querySelector(".modal-backdrop.open")) {
      document.body.style.overflow = "";
    }
  };

  // Close modal handlers
  document.querySelectorAll("[data-close]").forEach((btn) => {
    btn.addEventListener("click", () => closeModal(btn.dataset.close));
  });

  document.querySelectorAll(".modal-backdrop").forEach((backdrop) => {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) closeModal(backdrop.id);
    });
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      const open = document.querySelector(".modal-backdrop.open");
      if (open) closeModal(open.id);
    }
  });

  // Members modal
  document.querySelector("#open-members-modal")?.addEventListener("click", () => {
    openModal("members-modal");
  });

  // Invite modal
  document.querySelector("#open-invite-modal")?.addEventListener("click", () => {
    openModal("invite-modal");
  });

  // Copy link
  document.querySelector("#copy-link")?.addEventListener("click", async () => {
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
  document.querySelector("#share-link")?.addEventListener("click", async () => {
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

  // Voters modal — names are embedded per card as JSON and kept fresh after AJAX votes.
  const votersData = {};
  document.querySelectorAll("[data-suggestion]").forEach((card) => {
    const script = card.querySelector('script[type="application/json"]');
    if (!script) return;
    try {
      votersData[card.dataset.suggestion] = JSON.parse(script.textContent);
    } catch {
      votersData[card.dataset.suggestion] = [];
    }
  });

  const renderVoters = (names) => {
    const list = document.querySelector("#voter-list");
    if (!list) return;
    list.innerHTML = names.length
      ? names.map((name) => `
          <div class="voter-row">
            <span class="avatar" aria-hidden="true">${escapeHtml(String(name).slice(0, 1))}</span>
            <div>
              <div class="voter-name">${escapeHtml(name)}</div>
              <div class="voter-caption">موافق این پیشنهاد</div>
            </div>
          </div>`).join("")
      : '<div class="empty-state">هنوز کسی موافق نیست.</div>';
    const subtitle = document.querySelector("#voters-subtitle");
    if (subtitle) {
      subtitle.textContent = names.length === 1
        ? "۱ نفر موافق است"
        : `${names.length} نفر موافق‌اند`;
    }
  };

  document.querySelectorAll(".agree-summary[data-voters]").forEach((btn) => {
    btn.addEventListener("click", () => {
      renderVoters(votersData[btn.dataset.voters] || []);
      openModal("voters-modal");
    });
  });

    // Add suggestion button - open modal
  document.querySelector("#open-add-suggestion")?.addEventListener("click", () => {
    openModal("add-suggestion-modal");
  });

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
            const fieldDiv = input.closest(".form-field") || input.parentElement;
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

  // Edit suggestion buttons
  document.querySelectorAll("[data-edit]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const suggestionId = btn.dataset.edit;
      openModal(`edit-modal-${suggestionId}`);
    });
  });

  // Delete confirmation
  document.querySelectorAll(".delete-form").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!confirm("پیشنهاد حذف شود؟")) {
        e.preventDefault();
      }
    });
  });

  // Agreement form AJAX submission
  document.querySelectorAll(".agreement-form").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const buttons = [...document.querySelectorAll(".agreement-form button")];
      buttons.forEach((button) => { button.disabled = true; });
      showToast("در حال ثبت موافقت…");
      try {
        const response = await fetch(form.action, {
          method: "POST",
          body: new FormData(form),
          credentials: "same-origin",
          headers: {
            Accept: "application/json",
            "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]")?.value
          },
        });
        if (!response.ok) throw new Error("Agreement failed");
        const data = await response.json();
        
        // Update all suggestion cards with new agreement counts
        Object.entries(data.agreements).forEach(([id, names]) => {
          votersData[id] = names;
          const card = document.querySelector(`[data-suggestion="${id}"]`);
          if (!card) return;

          const countEl = card.querySelector(".status");
          const summaryEl = card.querySelector(".agree-summary span:last-child");
          const agreeBtn = card.querySelector(".agree-button");

          if (countEl) countEl.textContent = `${names.length} موافق`;
          const summaryBtn = card.querySelector(".agree-summary");
          if (summaryBtn) summaryBtn.disabled = names.length === 0;
          if (summaryEl) {
            summaryEl.textContent = names.length === 0
              ? "هنوز کسی موافق نیست"
              : names.length === 1
                ? "۱ نفر موافق است"
                : `${names.length} نفر موافق‌اند`;
          }
          if (agreeBtn) {
            const isAgreed = data.agreement && data.agreement.suggestion_id == id;
            agreeBtn.textContent = "موافقم";
            agreeBtn.classList.toggle("agreed", isAgreed);
          }
        });
        
        showToast("موافقت شما ثبت شد.");
      } catch {
        showToast("ثبت موافقت انجام نشد. لطفاً دوباره تلاش کنید.");
      } finally {
        buttons.forEach((button) => { button.disabled = false; });
      }
    });
  });
});
