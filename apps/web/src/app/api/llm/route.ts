import { NextResponse } from "next/server";

type Provider = "openai" | "deepseek" | "claude";

type RequestBody = {
  provider: Provider;
  apiKey: string;
  baseUrl?: string;
  model: string;
  temperature?: number;
  maxTokens?: number;
  anthropicVersion?: string;
  prompt: string;
};

const DEFAULT_BASE_URLS: Record<Provider, string> = {
  openai: "https://api.openai.com/v1",
  deepseek: "https://api.deepseek.com",
  claude: "https://api.anthropic.com",
};

function joinUrl(base: string, path: string) {
  const trimmedBase = base.replace(/\/+$/, "");
  const trimmedPath = path.replace(/^\/+/, "");
  return `${trimmedBase}/${trimmedPath}`;
}

async function callOpenAICompatible(body: RequestBody) {
  const baseUrl = (body.baseUrl || DEFAULT_BASE_URLS[body.provider]).trim();
  const url = joinUrl(baseUrl, "chat/completions");

  const payload: Record<string, unknown> = {
    model: body.model,
    messages: [{ role: "user", content: body.prompt }],
  };

  if (Number.isFinite(body.temperature)) {
    payload.temperature = body.temperature;
  }
  if (Number.isFinite(body.maxTokens)) {
    payload.max_tokens = body.maxTokens;
  }

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${body.apiKey}`,
    },
    body: JSON.stringify(payload),
  });

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const message = data?.error?.message || data?.error || res.statusText;
    throw new Error(message || `Request failed (${res.status})`);
  }

  const text =
    data?.choices?.[0]?.message?.content ??
    data?.choices?.[0]?.text ??
    "";

  if (!text) {
    throw new Error("Empty response from LLM provider");
  }

  return text as string;
}

async function callAnthropic(body: RequestBody) {
  const baseUrl = (body.baseUrl || DEFAULT_BASE_URLS.claude).trim();
  const url = joinUrl(baseUrl, "v1/messages");
  const payload: Record<string, unknown> = {
    model: body.model,
    max_tokens: Number.isFinite(body.maxTokens) ? body.maxTokens : 800,
    temperature: Number.isFinite(body.temperature) ? body.temperature : 0.2,
    messages: [{ role: "user", content: body.prompt }],
  };

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": body.apiKey,
      "anthropic-version": body.anthropicVersion || "2023-06-01",
    },
    body: JSON.stringify(payload),
  });

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const message = data?.error?.message || data?.error || res.statusText;
    throw new Error(message || `Request failed (${res.status})`);
  }

  const parts = Array.isArray(data?.content)
    ? data.content
        .filter((item: { type?: string }) => item.type === "text")
        .map((item: { text?: string }) => item.text)
    : [];
  const text = parts.join("").trim();

  if (!text) {
    throw new Error("Empty response from LLM provider");
  }

  return text;
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as RequestBody;

    if (!body.prompt) {
      return NextResponse.json({ error: "prompt is required" }, { status: 400 });
    }
    if (!body.apiKey || !body.model) {
      return NextResponse.json(
        { error: "apiKey and model are required" },
        { status: 400 },
      );
    }

    let text = "";

    if (body.provider === "claude") {
      text = await callAnthropic(body);
    } else {
      text = await callOpenAICompatible(body);
    }

    return NextResponse.json({ text });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "LLM request failed";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
