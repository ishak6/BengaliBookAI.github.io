import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { validateDataset, scoreAnswer, summarizeResults } from "../src/benchmark.js";

const dataset = JSON.parse(await readFile(new URL("../benchmark/bengali-general-50.json", import.meta.url), "utf8"));

test("benchmark contains 50 unique, rubric-backed Bengali questions", () => {
  assert.deepEqual(validateDataset(dataset), []);
  assert.equal(dataset.questions.length, 50);
  assert.equal(new Set(dataset.questions.map(q => q.id)).size, 50);
});

test("benchmark covers all five target categories", () => {
  const categories = new Set(dataset.questions.map(q => q.category));
  for (const category of ["বিজ্ঞান", "বাংলাদেশ", "গণিত", "কম্পিউটার", "সাধারণ জ্ঞান"]) {
    assert.equal(categories.has(category), true, "missing " + category);
  }
});

test("scorer recognizes Bengali numerals and normalized answer text", () => {
  const question = { required_any: [["ঢাকা", "dhaka"], ["২৬ মার্চ", "26 march"]] };
  const score = scoreAnswer(question, "বাংলাদেশের রাজধানী ঢাকা। স্বাধীনতা দিবস ২৬ মার্চ।");
  assert.equal(score.passed, true);
  assert.equal(score.coverage, 1);
});

test("scorer does not pass an incorrect answer", () => {
  const question = { required_any: [["ঢাকা"], ["২৬ মার্চ"]] };
  const score = scoreAnswer(question, "বাংলাদেশের রাজধানী চট্টগ্রাম।");
  assert.equal(score.passed, false);
  assert.equal(score.achieved, 0);
  assert.equal(score.missed_groups.length, 2);
});

test("scorer accepts equivalent H2O notation", () => {
  const question = dataset.questions.find(q => q.id === "SCI-001");
  assert.equal(scoreAnswer(question, "পানির সংকেত H2O।").passed, true);
  assert.equal(scoreAnswer(question, "পানির সংকেত CO2।").passed, false);
});

test("summary reports pass rate and fact coverage by category", () => {
  const summary = summarizeResults([
    { category: "গণিত", score: { passed: true, achieved: 2, total: 2 } },
    { category: "গণিত", score: { passed: false, achieved: 1, total: 2 } },
    { category: "বিজ্ঞান", score: { passed: true, achieved: 1, total: 1 } }
  ]);
  assert.equal(summary.total, 3);
  assert.equal(summary.passed, 2);
  assert.equal(summary.pass_rate, 2 / 3);
  assert.equal(summary.fact_coverage, 4 / 5);
  assert.equal(summary.by_category["গণিত"].pass_rate, 0.5);
});
