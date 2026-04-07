const menuToggle = document.querySelector(".menu-toggle");
const nav = document.querySelector(".nav-links");

if (menuToggle && nav) {
  menuToggle.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("open");
    menuToggle.setAttribute("aria-expanded", String(isOpen));
  });

  nav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      nav.classList.remove("open");
      menuToggle.setAttribute("aria-expanded", "false");
    });
  });
}

const liftsInput = document.getElementById("lifts");
const retainedInput = document.getElementById("retained");
const roiResult = document.getElementById("roi-result");

function formatCurrency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
}

function updateRoiEstimate() {
  if (!liftsInput || !retainedInput || !roiResult) {
    return;
  }

  const lifts = Number(liftsInput.value || 0);
  const retainedRevenue = Number(retainedInput.value || 0);

  const oneTimeCost = lifts * 400 + 2000;
  const yearlyFee = 1200;

  const firstYearTotal = oneTimeCost + yearlyFee;
  const firstYearDelta = retainedRevenue - firstYearTotal;

  const message =
    `Estimated first-year cost: ${formatCurrency(firstYearTotal)} ` +
    `(hardware + setup + annual service). ` +
    `If retained seasonal spend is ${formatCurrency(retainedRevenue)}, ` +
    `modeled year-one net effect is ${formatCurrency(firstYearDelta)}.`;

  roiResult.textContent = message;
}

if (liftsInput && retainedInput) {
  liftsInput.addEventListener("input", updateRoiEstimate);
  retainedInput.addEventListener("input", updateRoiEstimate);
  updateRoiEstimate();
}

const waitlistForm = document.getElementById("waitlist-form");
const formNote = document.getElementById("form-note");

if (waitlistForm && formNote) {
  waitlistForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const email = document.getElementById("email");
    const resort = document.getElementById("resort");

    if (!email || !resort) {
      return;
    }

    if (!email.checkValidity() || !resort.value.trim()) {
      formNote.textContent = "Please enter a valid work email and ski area name.";
      formNote.style.color = "#8b2d2d";
      return;
    }

    formNote.textContent = "Thanks. Your waitlist request has been recorded.";
    formNote.style.color = "#145736";
    waitlistForm.reset();
  });
}
