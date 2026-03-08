const slides = Array.from(document.querySelectorAll(".slide"));
const counter = document.getElementById("slide-counter");
const progressBar = document.getElementById("progress-bar");
const slideTitle = document.getElementById("slide-title");
const notesPanel = document.getElementById("notes-panel");
const notesContent = document.getElementById("notes-content");
const closeNotes = document.getElementById("close-notes");
const overview = document.getElementById("overview");

let currentIndex = 0;
let overviewOpen = false;

function renderSlide(index) {
  currentIndex = Math.max(0, Math.min(index, slides.length - 1));

  slides.forEach((slide, idx) => {
    slide.classList.toggle("active", idx === currentIndex);
  });

  counter.textContent = `${currentIndex + 1} / ${slides.length}`;
  slideTitle.textContent = slides[currentIndex].dataset.title || `Slide ${currentIndex + 1}`;
  progressBar.style.width = `${((currentIndex + 1) / slides.length) * 100}%`;

  const notes = slides[currentIndex].querySelector(".notes");
  notesContent.innerHTML = notes ? notes.innerHTML : "<p>No notes for this slide.</p>";

  if (overviewOpen) {
    renderOverview();
  }
}

function toggleNotes(forceOpen) {
  const shouldOpen = typeof forceOpen === "boolean"
    ? forceOpen
    : !notesPanel.classList.contains("open");
  notesPanel.classList.toggle("open", shouldOpen);
}

function renderOverview() {
  const cards = slides.map((slide, idx) => `
    <article class="overview-card ${idx === currentIndex ? "active" : ""}" data-index="${idx}">
      <h3>${idx + 1}. ${slide.dataset.title || `Slide ${idx + 1}`}</h3>
      <p>${slide.querySelector("h2")?.textContent || ""}</p>
    </article>
  `).join("");

  overview.innerHTML = `
    <div class="overview-grid">
      ${cards}
    </div>
  `;

  overview.querySelectorAll(".overview-card").forEach((card) => {
    card.addEventListener("click", () => {
      renderSlide(Number(card.dataset.index));
      toggleOverview(false);
    });
  });
}

function toggleOverview(forceOpen) {
  overviewOpen = typeof forceOpen === "boolean" ? forceOpen : !overviewOpen;
  overview.classList.toggle("hidden", !overviewOpen);

  if (overviewOpen) {
    renderOverview();
  }
}

document.addEventListener("keydown", (event) => {
  if (event.key === "ArrowRight" || event.key === "PageDown" || event.key === " ") {
    event.preventDefault();
    renderSlide(currentIndex + 1);
  } else if (event.key === "ArrowLeft" || event.key === "PageUp") {
    event.preventDefault();
    renderSlide(currentIndex - 1);
  } else if (event.key === "Home") {
    event.preventDefault();
    renderSlide(0);
  } else if (event.key === "End") {
    event.preventDefault();
    renderSlide(slides.length - 1);
  } else if (event.key.toLowerCase() === "s") {
    event.preventDefault();
    toggleNotes();
  } else if (event.key.toLowerCase() === "o") {
    event.preventDefault();
    toggleOverview();
  } else if (event.key === "Escape") {
    toggleNotes(false);
    toggleOverview(false);
  }
});

closeNotes.addEventListener("click", () => toggleNotes(false));
overview.addEventListener("click", (event) => {
  if (event.target === overview) {
    toggleOverview(false);
  }
});

renderSlide(0);
