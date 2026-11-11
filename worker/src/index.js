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
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error(`Telegram API returned HTTP ${response.status}`);
  return response.json();
}

async function sendMessage(env, chatId, text) {
  return telegramRequest(env, "sendMessage", { chat_id: chatId, text, disable_web_page_preview: true });
}

async function handleTelegram(request, env) {
  if (!env.TELEGRAM_WEBHOOK_SECRET) return json({ error: "Webhook secret is not configured" }, 503);
  if (request.headers.get("X-Telegram-Bot-Api-Secret-Token") !== env.TELEGRAM_WEBHOOK_SECRET) {
    return json({ error: "Unauthorized" }, 401);
  }

  let update;
  try { update = await request.json(); }
  catch { return json({ error: "Invalid JSON" }, 400); }

  const message = update.message;
  if (!message?.chat?.id || typeof message.text !== "string") return json({ ok: true, ignored: true });

  const text = message.text.trim();
  const chatId = message.chat.id;
  const userId = message.from?.id;

  try {
    if (text === "/start") {
      await sendMessage(env, chatId, "স্বাগতম Bengali Book AI-তে।\n\nবাংলা বইভিত্তিক প্রশ্নোত্তর ব্যবস্থা প্রস্তুত করা হচ্ছে। চালু হলে বইয়ের নাম, অধ্যায়, পৃষ্ঠা ও উদ্ধৃতিসহ উত্তর পাবেন।");
    } else if (text === "/help") {
      await sendMessage(env, chatId, "কমান্ড:\n/start — শুরু\n/help — সাহায্য\n\nবই অনুসন্ধান ব্যবস্থা এখনো চালু হয়নি।");
    } else if (text === "/admin") {
      await sendMessage(env, chatId, isAdmin(userId, env)
        ? "Admin access যাচাই হয়েছে। বই যোগ করার ব্যবস্থা পরবর্তী ধাপে যুক্ত হবে।"
        : "এই কমান্ড ব্যবহারের অনুমতি নেই।");
    } else {
      await sendMessage(env, chatId, "আপনার প্রশ্ন পেয়েছি। তবে বইয়ের searchable database এখনো যুক্ত হয়নি, তাই এখনই বইয়ের সূত্রসহ উত্তর দিতে পারছি না।");
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
    if (request.method === "GET" && url.pathname === "/health") {
      return json({
        ok: true,
        service: "Bengali Book AI API",
        phase: 1,
        telegramConfigured: Boolean(env.TELEGRAM_BOT_TOKEN),
        databaseConfigured: Boolean(env.DB)
      });
    }
    if (request.method === "POST" && url.pathname === "/telegram/webhook") return handleTelegram(request, env);
    if (request.method === "POST" && url.pathname === "/api/ask") {
      return json({ error: "Book search is not ready yet", message: "বইয়ের ডেটাবেস ও অনুসন্ধান ব্যবস্থা পরবর্তী ধাপে যুক্ত হবে।" }, 501);
    }
    return json({ error: "Not found" }, 404);
  }
};
