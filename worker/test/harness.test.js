import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import worker from "../src/index.js";

const API = "https://example.test";
const json = async (response) => response.json();
const makeRequest = (path, init = {}) => new Request(API + path, init);
const pngBlob = () => new Blob([new Uint8Array(24)], { type: "image/png" });
const dbWithoutMatches = {
  prepare() {
    return {
      bind() {
        return {
          async all() { return { results: [] }; },
          async first() { return null; },
          async run() { return { success: true }; }
        };
      }
    };
  }
};

test("CORS preflight is accepted", async () => {
  const response = await worker.fetch(makeRequest("/api/ask-image", { method: "OPTIONS" }), {});
  assert.equal(response.status, 204);
  assert.equal(response.headers.get("access-control-allow-origin"), "*");
});

test("health endpoint exposes configuration flags, not secret values", async () => {
  const response = await worker.fetch(makeRequest("/health"), {});
  const data = await json(response);
  assert.equal(response.status, 200);
  assert.equal(data.ok, true);
  assert.equal(data.databaseConfigured, false);
  assert.equal(JSON.stringify(data).includes("API_KEY"), false);
});

test("empty text question is rejected before provider access", async () => {
  const response = await worker.fetch(makeRequest("/api/ask", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ question: "   " })
  }), {});
  assert.equal(response.status, 400);
});

test("image endpoint rejects a request without an image", async () => {
  const response = await worker.fetch(makeRequest("/api/ask-image", {
    method: "POST",
    body: new FormData()
  }), {});
  assert.equal(response.status, 400);
});

test("image endpoint rejects unsupported MIME types", async () => {
  const form = new FormData();
  form.append("image", new Blob(["not an image payload"], { type: "text/plain" }), "note.txt");
  const response = await worker.fetch(makeRequest("/api/ask-image", { method: "POST", body: form }), {});
  assert.equal(response.status, 400);
});

test("image endpoint enforces the 8 MiB upload limit", async () => {
  const form = new FormData();
  form.append("image", new Blob([new Uint8Array(8 * 1024 * 1024 + 1)], { type: "image/png" }), "large.png");
  const response = await worker.fetch(makeRequest("/api/ask-image", { method: "POST", body: form }), {});
  assert.equal(response.status, 413);
});

test("valid image requests fail clearly when AI is not configured", async () => {
  const form = new FormData();
  form.append("image", pngBlob(), "question.png");
  const response = await worker.fetch(makeRequest("/api/ask-image", { method: "POST", body: form }), {});
  assert.equal(response.status, 503);
});

test("general image question performs OCR extraction then answer generation", async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (_url, init) => {
    calls.push(JSON.parse(init.body));
    const content = calls.length === 1 ? "প্রশ্ন: পানির রাসায়নিক সংকেত কী?" : "পানির রাসায়নিক সংকেত H₂O।";
    return Response.json({ choices: [{ message: { content } }] });
  };
  try {
    const form = new FormData();
    form.append("image", pngBlob(), "question.png");
    form.append("question", "উত্তর দাও");
    form.append("mode", "general");
    const response = await worker.fetch(makeRequest("/api/ask-image", { method: "POST", body: form }), {
      AI_API_KEY: "test-only-placeholder",
      AI_BASE_URL: "https://provider.example/v1",
      AI_MODEL: "vision-test-model"
    });
    const data = await json(response);
    assert.equal(response.status, 200);
    assert.match(data.recognized_text, /পানির রাসায়নিক সংকেত/);
    assert.match(data.answer, /H₂O/);
    assert.equal(calls.length, 2);
    assert.equal(calls[0].messages[1].content.some(part => part.type === "image_url"), true);
    assert.equal(calls[0].model, "vision-test-model");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("book-only image question refuses to invent an answer without indexed evidence", async () => {
  const originalFetch = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => {
    calls += 1;
    return Response.json({ choices: [{ message: { content: "প্রশ্ন: বাংলাদেশের রাজধানী কী?" } }] });
  };
  try {
    const form = new FormData();
    form.append("image", pngBlob(), "question.png");
    form.append("mode", "book");
    const response = await worker.fetch(makeRequest("/api/ask-image", { method: "POST", body: form }), {
      AI_API_KEY: "test-only-placeholder",
      DB: dbWithoutMatches()
    });
    const data = await json(response);
    assert.equal(response.status, 200);
    assert.equal(data.found, false);
    assert.equal(data.sources.length, 0);
    assert.match(data.book_answer, /প্রমাণ পাওয়া যায়নি/);
    assert.equal(calls, 1, "no answer-generation call should run without book evidence");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("homepage exposes image upload, camera capture and image API wiring", async () => {
  const html = await readFile(new URL("../../index.html", import.meta.url), "utf8");
  assert.match(html, /id="image-file"/);
  assert.match(html, /capture="environment"/);
  assert.equal(html.includes("/api/ask-image"), true);
  assert.match(html, /recognized_text/);
});

test("book retrieval is restricted to ready books", async () => {
  const source = await readFile(new URL("../src/index.js", import.meta.url), "utf8");
  assert.match(source, /b\.status='ready'/);
  assert.match(source, /async function askImage\(/);
  assert.match(source, /async function ask\(/);
});
