// Progressive enhancement: everything works without JS (plain form posts).
document.addEventListener("submit", async (event) => {
  const form = event.target.closest("form.js-like, form.js-follow");
  if (!form) return;
  event.preventDefault();

  let response;
  try {
    response = await fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
  } catch (err) {
    form.submit();
    return;
  }
  if (!response.ok || !(response.headers.get("content-type") || "").includes("json")) {
    form.submit();
    return;
  }
  const data = await response.json();
  const button = form.querySelector("button");

  if (form.classList.contains("js-like")) {
    button.classList.toggle("is-on", data.liked);
    button.setAttribute("aria-pressed", String(data.liked));
    button.querySelector(".count").textContent = data.count;
  } else {
    button.textContent = data.following ? "Unfollow" : "Follow";
    button.classList.toggle("btn-primary", !data.following);
    button.classList.toggle("btn-quiet", data.following);
    button.classList.toggle("is-following", data.following);
    document.querySelectorAll("[data-follower-count]").forEach((el) => (el.textContent = data.followers));
  }
});

// Composer: character counter and chosen file name.
document.querySelectorAll("[data-counter]").forEach((counter) => {
  const field = document.getElementById(counter.dataset.counter);
  if (!field) return;
  const max = Number(field.getAttribute("maxlength")) || 500;
  const update = () => (counter.textContent = max - field.value.length);
  field.addEventListener("input", update);
  update();
});

document.querySelectorAll(".file-pick input[type=file]").forEach((input) => {
  const label = input.closest(".composer-bar").querySelector("[data-file-name]");
  input.addEventListener("change", () => {
    label.textContent = input.files.length ? input.files[0].name : "";
  });
});
