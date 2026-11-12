export function normalizeAnswer(value) {
  return String(value ?? "")
    .normalize("NFKC")
    .toLocaleLowerCase("bn")
    .replace(/[^\\p{L}\\p{N}%/]+/gu, " ")
    .replace(/\\s+/g, " ")
    .trim();
}

function containsPhrase(answer, phrase) {
  const haystack = " " + normalizeAnswer(answer) + " ";
  const needle = " " + normalizeAnswer(phrase) + " ";
  return needle.trim().length > 0 && haystack.includes(needle);
}

export function scoreAnswer(question, answer) {
  const groups = Array.isArray(question.required_any) ? question.required_any : [];
  const hits = groups.map((alternatives) =>
    alternatives.some((candidate) => containsPhrase(answer, candidate))
  );
  const achieved = hits.filter(Boolean).length;
  const total = groups.length;
  return {
    achieved,
    total,
    coverage: total ? achieved / total : 0,
    passed: total > 0 && achieved === total,
    missed_groups: groups.filter((_, index) => !hits[index])
  };
}

export function validateDataset(dataset) {
  const errors = [];
  if (!dataset || !Array.isArray(dataset.questions)) return ["questions array missing"];
  if (dataset.questions.length !== dataset.count) errors.push("count does not match questions length");
  const seen = new Set();
  for (const q of dataset.questions) {
    if (!q.id || !q.question || !q.reference_answer) errors.push("question missing id, question or reference_answer");
    if (seen.has(q.id)) errors.push("duplicate id: " + q.id);
    seen.add(q.id);
    if (!Array.isArray(q.required_any) || q.required_any.length === 0) errors.push("missing required_any rubric: " + q.id);
    else if (q.required_any.some(group => !Array.isArray(group) || group.length === 0)) errors.push("empty fact group: " + q.id);
  }
  return errors;
}

export function summarizeResults(results) {
  const total = results.length;
  const passed = results.filter(result => result.score?.passed).length;
  const facts = results.reduce((sum, result) => sum + (result.score?.achieved || 0), 0);
  const possible = results.reduce((sum, result) => sum + (result.score?.total || 0), 0);
  const byCategory = {};
  for (const result of results) {
    const key = result.category || "অন্যান্য";
    const group = byCategory[key] ||= { total: 0, passed: 0, achieved_facts: 0, total_facts: 0 };
    group.total++;
    if (result.score?.passed) group.passed++;
    group.achieved_facts += result.score?.achieved || 0;
    group.total_facts += result.score?.total || 0;
  }
  for (const group of Object.values(byCategory)) {
    group.pass_rate = group.total ? group.passed / group.total : 0;
    group.fact_coverage = group.total_facts ? group.achieved_facts / group.total_facts : 0;
  }
  return {
    total,
    passed,
    failed: total - passed,
    pass_rate: total ? passed / total : 0,
    fact_coverage: possible ? facts / possible : 0,
    by_category: byCategory
  };
}
