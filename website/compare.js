const mlKitDetected = {
  a: `Lift Camera Node A\nPrice: 400 EUR / lift\nInstall cost: 2000 EUR one-time\nService: 1200 EUR / year\nQueue visibility: high`,
  b: `Lift Camera Node B\nPrice: 400 EUR per lift\nSetup fee: 2000 EUR\nAnnual fee: 1200 EUR\nQueue view: clear`,
};

function heuristicLlmProcess(rawText, modelName) {
  const lower = rawText.toLowerCase();
  const hasHardware = lower.includes("400") && (lower.includes("lift") || lower.includes("per lift"));
  const hasSetup = lower.includes("2000") || lower.includes("2,000");
  const hasService = lower.includes("1200") || lower.includes("1,200");

  const normalized = [
    `Model: ${modelName}`,
    `Normalized hardware cost: ${hasHardware ? "400 EUR per lift" : "not detected"}`,
    `Normalized setup fee: ${hasSetup ? "2,000 EUR one-time" : "not detected"}`,
    `Normalized annual fee: ${hasService ? "1,200 EUR/year" : "not detected"}`,
    "Interpretation: Pricing structure is consistent with QueueVision standard package.",
    "Action: Use this extracted data for side-by-side operator offer comparison.",
  ];

  return normalized.join("\n");
}

async function processWithLlm(rawText, modelName) {
  // Optional live endpoint hook. Falls back to local processing if endpoint is not configured.
  if (window.QUEUEVISION_LLM_ENDPOINT) {
    try {
      const response = await fetch(window.QUEUEVISION_LLM_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: rawText, model: modelName }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data && typeof data.output === "string" && data.output.trim()) {
          return data.output;
        }
      }
    } catch (_error) {
      // Fall through to local processor.
    }
  }

  return heuristicLlmProcess(rawText, modelName);
}

async function initComparisonPage() {
  const rawA = document.getElementById("raw-a");
  const rawB = document.getElementById("raw-b");
  const llmA = document.getElementById("llm-a");
  const llmB = document.getElementById("llm-b");

  if (!rawA || !rawB || !llmA || !llmB) {
    return;
  }

  rawA.textContent = mlKitDetected.a;
  rawB.textContent = mlKitDetected.b;

  const [processedA, processedB] = await Promise.all([
    processWithLlm(mlKitDetected.a, "Model A"),
    processWithLlm(mlKitDetected.b, "Model B"),
  ]);

  llmA.textContent = processedA;
  llmB.textContent = processedB;
}

initComparisonPage();
