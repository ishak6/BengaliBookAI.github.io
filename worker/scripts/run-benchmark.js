import { readFile, mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { scoreAnswer, summarizeResults, validateDataset } from "../src/benchmark.js";

const here = dirname(fileURLToPath(import.meta.url));
const datasetPath = resolve(here, "../benchmark/bengali-general-50.json");
const dataset = JSON.parse(await readFile(datasetPath, "utf8"));
const validationErrors = validateDataset(dataset);
if (validationErrors.length) {
  console.error("Benchmark dataset invalid:", validationErrors.join("; "));
  process.exit(1);
}

const args = process.argv.slice(2);
const has = (flag) => args.includes(flag);
const value = (flag, fallback) => {
  const index = args.indexOf(flag);
  return index >= 0 && args[index + 1] ? args[index + 1] : fallback;
};
const limit = Math.max(1, Math.min(dataset.questions.length, Number(value("--limit", dataset.questions.length)) || dataset.questions.length));
const delayMs = Math.max(0, Math.min(10000, Number(value("--delay-ms", "1200")) || 0));
const apiBase = String(value("--api-url", process.env.BENGALI_BOOK_AI_API || "https://bengali-book-ai-api.bengalibookai.workers.dev")).replace(/\\/+$/, "");
const endpoint = apiBase.endsWith("/api/ask") ? apiBase : apiBase + "/api/ask";

if (!has("--run")) {
  console.log(JSON.stringify({
    status: "ready",
    message: "Dataset validated. Add --run to send questions to the live AI API.",
    question_count: dataset.questions.length,
    selected_count: limit,
    categories: [...new Set(dataset.questions.map(q => q.category))]
  }, null, 2));
  process.exit(0);
}

const results = [];
for (const question of dataset.questions.slice(0, limit)) {
  const started = Date.now();
  let answer = "";
  let error = null;
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question: question.question, mode: "general" }),
      signal: AbortSignal.timeout(60000)
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || !data.answer) throw new Error(data.error || "API HTTP " + response.status + " or empty answer");
    answer = String(data.answer);
  } catch (err) {
    error = String(err?.message || err);
  }
  const score = scoreAnswer(question, answer);
  results.push({
    id: question.id,
    category: question.category,
    difficulty: question.difficulty,
    question: question.question,
    reference_answer: question.reference_answer,
    answer,
    score,
    error,
    latency_ms: Date.now() - started
  });
  console.log(`[${results.length}/${limit}] ${question.id}: ${error ? "ERROR" : score.passed ? "PASS" : "REVIEW"} — ${Math.round(score.coverage * 100)}% fact coverage`);
  if (delayMs && results.length < limit) await new Promise(resolve => setTimeout(resolve, delayMs));
}

const summary = summarizeResults(results);
const report = {
  benchmark: dataset.title,
  dataset_version: dataset.schema_version,
  evaluated_at: new Date().toISOString(),
  endpoint,
  summary,
  results
};
const outputPath = resolve(here, "../benchmark/results", "benchmark-" + new Date().toISOString().replace(/[:.]/g, "-") + ".json");
await mkdir(dirname(outputPath), { recursive: true });
await writeFile(outputPath, JSON.stringify(report, null, 2) + "\\n", "utf8");
console.log("\\nSUMMARY");
console.log(JSON.stringify(summary, null, 2));
console.log("Report saved:", outputPath);
if (results.some(result => result.error)) process.exitCode = 2;
