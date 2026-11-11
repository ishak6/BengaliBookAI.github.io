const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store"
};
function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: JSON_HEADERS });
}
function isAdmin(userId, env) {
  return Boolean(env.ADMIN_TELEGRAM_ID) && String(userId) === String(env.ADMIN_TELEGRAM_ID);
}
async function telegramRequest(env, method, payload) {
  if (!env.TELEGRAM_BOT_TOKEN) throw new Error("TELEGRAM_BOT_TOKEN is not configured");
  const response = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/${method}`, {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error(`Telegram API returned HTTP ${response.status}`);
  return response.json();
}
async function sendMessage(env, chatId, text) {
  return telegramRequest(env, "sendMessage", { chat_id: chatId, text, disable_web_page_preview: true });
}
async function listBooks(env) {
  if (!env.DB) return json({ error: "Database is not configured" }, 503);
  try {
    const result = await env.DB.prepare("SELECT id, title, author, language, rights_type, rights_note, status FROM books WHERE status = 'ready' ORDER BY title COLLATE NOCASE").all();
    return json({ books: result.results || [] });
  } catch (error) {
    console.error("Book list query failed:", error);
    return json({ error: "Could not load books. Check that the D1 schema has been applied." }, 503);
  }
}
async function serveBookFile(bookId, env) {
  if (!env.DB) return json({ error: "Database is not configured" }, 503);
  const book = await env.DB.prepare("SELECT storage_key FROM books WHERE id = ? AND status = 'ready' LIMIT 1").bind(bookId).first();
  if (!book?.storage_key) return json({ error: "Book file not found" }, 404);
  let assetUrl;
  try { assetUrl = new URL(book.storage_key); } catch { return json({ error: "Invalid book storage reference" }, 500); }
  if (assetUrl.protocol !== "https:" || assetUrl.hostname !== "github.com" || !assetUrl.pathname.includes("/releases/download/")) {
    return json({ error: "Book file must use a public GitHub Release asset URL" }, 400);
  }
  const upstream = await fetch(assetUrl.toString(), { redirect: "follow" });
  if (!upstream.ok || !upstream.body) return json({ error: "Book file is unavailable from GitHub Releases" }, 502);
  const headers = new Headers();
  headers.set("content-type", upstream.headers.get("content-type") || "application/pdf");
  headers.set("cache-control", "public, max-age=3600");
  headers.set("x-content-type-options", "nosniff");
  const length = upstream.headers.get("content-length");
  if (length) headers.set("content-length", length);
  return new Response(upstream.body, { status: 200, headers });
}
async function handleTelegram(request, env) {
  if (!env.TELEGRAM_WEBHOOK_SECRET) return json({ error: "Webhook secret is not configured" }, 503);
  if (request.headers.get("X-Telegram-Bot-Api-Secret-Token") !== env.TELEGRAM_WEBHOOK_SECRET) return json({ error: "Unauthorized" }, 401);
  let update;
  try { update = await request.json(); } catch { return json({ error: "Invalid JSON" }, 400); }
  const message = update.message;
  if (!message?.chat?.id || typeof message.text !== "string") return json({ ok: true, ignored: true });
  const text = message.text.trim(), chatId = message.chat.id, userId = message.from?.id;
  try {
    if (text === "/start") {
      await sendMessage(env, chatId, "স্বাগতম Bengali Book AI-তে।\n\nপ্রস্তুত বইয়ের তালিকা দেখতে /books লিখুন। বইভিত্তিক প্রশ্নোত্তর ও উদ্ধৃতি-সহ উত্তর পরবর্তী ধাপে যুক্ত হবে।");
    } else if (text === "/help") {
      await sendMessage(env, chatId, "কমান্ড:\n/start — শুরু\n/books — প্রস্তুত বইয়ের তালিকা\n/help — সাহায্য");
    } else if (text === "/books") {
      if (!env.DB) await sendMessage(env, chatId, "বইয়ের ডেটাবেস এখনো সংযুক্ত হয়নি।");
      else {
        const result = await env.DB.prepare("SELECT title, author FROM books WHERE status = 'ready' ORDER BY title COLLATE NOCASE LIMIT 30").all();
        const rows = result.results || [];
        await sendMessage(env, chatId, rows.length ? "প্রস্তুত বই:\n" + rows.map((book, i) => `${i + 1}. ${book.title}${book.author ? " — " + book.author : ""}`).join("\n") : "এখনো কোনো প্রস্তুত বই যোগ করা হয়নি।");
      }
    } else if (text === "/admin") {
      await sendMessage(env, chatId, isAdmin(userId, env) ? "Admin access যাচাই হয়েছে। বই যোগ করার upload panel এখনো তৈরি হয়নি।" : "এই কমান্ড ব্যবহারের অনুমতি নেই।");
    } else {
      await sendMessage(env, chatId, "প্রশ্ন পেয়েছি। বইয়ের searchable page index ও AI retrieval এখনো তৈরি হয়নি; তাই অনুমান করে বইয়ের উত্তর দিচ্ছি না।");
    }
  } catch (error) {
    console.error("Telegram message handling failed:", error);
    return json({ error: "Message handling failed" }, 502);
  }
  return json({ ok: true });
}
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/health") return json({
      ok: true, service: "Bengali Book AI API", phase: 1, storage: "github-releases",
      telegramConfigured: Boolean(env.TELEGRAM_BOT_TOKEN), databaseConfigured: Boolean(env.DB)
    });
    if (request.method === "GET" && url.pathname === "/api/books") return listBooks(env);
    const fileMatch = url.pathname.match(/^\/api\/books\/([^/]+)\/file$/);
    if (request.method === "GET" && fileMatch) {
      let bookId;
      try { bookId = decodeURIComponent(fileMatch[1]); } catch { return json({ error: "Invalid book ID" }, 400); }
      return serveBookFile(bookId, env);
    }
    if (request.method === "POST" && url.pathname === "/telegram/webhook") return handleTelegram(request, env);
    if (request.method === "POST" && url.pathname === "/api/ask") return json({
      error: "Book search is not ready yet",
      message: "বইয়ের page text index ও retrieval পরবর্তী ধাপে যুক্ত হবে।"
    }, 501);
    return json({ error: "Not found" }, 404);
  }
};
