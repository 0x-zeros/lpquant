"use client";

import { useEffect, useMemo, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { useRecommendContext } from "@/context/recommend-context";
import { buildLlmPrompt } from "@/lib/llm-prompt";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

type Provider = "openai" | "deepseek" | "claude";

type ProviderSettings = {
  apiKey: string;
  baseUrl: string;
  model: string;
  temperature: number;
  maxTokens: number;
  anthropicVersion?: string;
};

type LlmSettings = {
  mode: "api" | "prompt";
  provider: Provider;
  providers: Record<Provider, ProviderSettings>;
};

const STORAGE_KEY = "lpquant.llm.settings.v1";

const DEFAULT_SETTINGS: LlmSettings = {
  mode: "prompt",
  provider: "openai",
  providers: {
    openai: {
      apiKey: "",
      baseUrl: "https://api.openai.com/v1",
      model: "",
      temperature: 0.2,
      maxTokens: 800,
    },
    deepseek: {
      apiKey: "",
      baseUrl: "https://api.deepseek.com",
      model: "",
      temperature: 0.2,
      maxTokens: 800,
    },
    claude: {
      apiKey: "",
      baseUrl: "https://api.anthropic.com",
      model: "",
      temperature: 0.2,
      maxTokens: 800,
      anthropicVersion: "2023-06-01",
    },
  },
};

function mergeSettings(next: Partial<LlmSettings>): LlmSettings {
  return {
    ...DEFAULT_SETTINGS,
    ...next,
    providers: {
      openai: {
        ...DEFAULT_SETTINGS.providers.openai,
        ...next.providers?.openai,
      },
      deepseek: {
        ...DEFAULT_SETTINGS.providers.deepseek,
        ...next.providers?.deepseek,
      },
      claude: {
        ...DEFAULT_SETTINGS.providers.claude,
        ...next.providers?.claude,
      },
    },
  };
}

export function LlmPanel() {
  const t = useTranslations("llm");
  const locale = useLocale();
  const { data, selectedKey, request } = useRecommendContext();
  const [settings, setSettings] = useState<LlmSettings>(DEFAULT_SETTINGS);
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [promptCopied, setPromptCopied] = useState(false);
  const [responseCopied, setResponseCopied] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as Partial<LlmSettings>;
      setSettings(mergeSettings(parsed));
    } catch {
      // ignore malformed storage
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }, [settings]);

  useEffect(() => {
    setResponse("");
    setError(null);
  }, [data, selectedKey, locale]);

  const promptText = useMemo(() => {
    if (!data || !selectedKey) return "";
    return buildLlmPrompt({ data, selectedKey, request, locale });
  }, [data, selectedKey, request, locale]);

  if (!data || !selectedKey) {
    return (
      <p className="text-muted-foreground text-sm">{t("empty")}</p>
    );
  }

  const provider = settings.provider;
  const active = settings.providers[provider];

  const updateProvider = (key: keyof ProviderSettings, value: string | number) => {
    setSettings((prev) => ({
      ...prev,
      providers: {
        ...prev.providers,
        [provider]: {
          ...prev.providers[provider],
          [key]: value,
        },
      },
    }));
  };

  const handleCopy = async (text: string, kind: "prompt" | "response") => {
    await navigator.clipboard.writeText(text);
    if (kind === "prompt") {
      setPromptCopied(true);
      setTimeout(() => setPromptCopied(false), 1200);
    } else {
      setResponseCopied(true);
      setTimeout(() => setResponseCopied(false), 1200);
    }
  };

  const handleRun = async () => {
    if (!promptText) return;
    if (!active.apiKey || !active.model) {
      setError(t("missingConfig"));
      return;
    }

    setLoading(true);
    setError(null);
    setResponse("");

    try {
      const res = await fetch("/api/llm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider,
          apiKey: active.apiKey,
          baseUrl: active.baseUrl,
          model: active.model,
          temperature: active.temperature,
          maxTokens: active.maxTokens,
          anthropicVersion: active.anthropicVersion,
          prompt: promptText,
        }),
      });

      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(body.error || t("requestError"));
      }

      setResponse(body.text || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("requestError"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {settings.mode === "api" && (
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">{t("apiHint")}</p>
        </div>
      )}

      <div className="grid gap-3">
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="text-sm font-medium">{t("provider")}</label>
            <Select
              value={provider}
              onValueChange={(value) =>
                setSettings((prev) => ({
                  ...prev,
                  provider: value as Provider,
                }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder={t("provider")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="openai">{t("openai")}</SelectItem>
                <SelectItem value="deepseek">{t("deepseek")}</SelectItem>
                <SelectItem value="claude">{t("claude")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium">{t("mode")}</label>
            <Tabs
              value={settings.mode}
              onValueChange={(value) =>
                setSettings((prev) => ({
                  ...prev,
                  mode: value as "api" | "prompt",
                }))
              }
            >
              <TabsList className="w-full">
                <TabsTrigger value="api" className="flex-1">
                  {t("modeApi")}
                </TabsTrigger>
                <TabsTrigger value="prompt" className="flex-1">
                  {t("modePrompt")}
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </div>

        {settings.mode === "api" && (
          <div className="grid gap-3">
            <div className="space-y-1">
              <label className="text-sm font-medium">{t("apiKey")}</label>
              <Input
                type="password"
                value={active.apiKey}
                onChange={(e) => updateProvider("apiKey", e.target.value)}
                placeholder="sk-..."
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-sm font-medium">{t("model")}</label>
                <Input
                  value={active.model}
                  onChange={(e) => updateProvider("model", e.target.value)}
                  placeholder="model-id"
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium">{t("temperature")}</label>
                <Input
                  type="number"
                  min={0}
                  max={1}
                  step={0.1}
                  value={active.temperature}
                  onChange={(e) => {
                    const next = Number(e.target.value);
                    updateProvider(
                      "temperature",
                      Number.isFinite(next) ? Math.max(0, Math.min(1, next)) : 0.2,
                    );
                  }}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-sm font-medium">{t("baseUrl")}</label>
                <Input
                  value={active.baseUrl}
                  onChange={(e) => updateProvider("baseUrl", e.target.value)}
                  placeholder="https://..."
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium">{t("maxTokens")}</label>
                <Input
                  type="number"
                  min={1}
                  step={50}
                  value={active.maxTokens}
                  onChange={(e) => {
                    const next = Number(e.target.value);
                    updateProvider(
                      "maxTokens",
                      Number.isFinite(next) && next > 0 ? next : 800,
                    );
                  }}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium">{t("prompt")}</p>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleCopy(promptText, "prompt")}
            disabled={!promptText}
          >
            {promptCopied ? t("copied") : t("copyPrompt")}
          </Button>
        </div>
        <Textarea value={promptText} readOnly className="min-h-[200px]" />
        <p className="text-xs text-muted-foreground">{t("promptHint")}</p>
      </div>

      {settings.mode === "api" && (
        <div className="space-y-3">
          <Button
            onClick={handleRun}
            disabled={loading || !promptText || !active.apiKey || !active.model}
            className="w-full"
          >
            {loading ? t("running") : t("run")}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">{t("response")}</p>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleCopy(response, "response")}
                disabled={!response}
              >
                {responseCopied ? t("copied") : t("copyResponse")}
              </Button>
            </div>
            <Textarea value={response} readOnly className="min-h-[180px]" />
          </div>
        </div>
      )}
    </div>
  );
}
