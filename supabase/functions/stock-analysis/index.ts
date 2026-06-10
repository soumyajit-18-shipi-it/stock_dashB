import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import "std/dotenv/load.ts";
import type { CompanyProfile, StockResponse } from "../../src/shared/stockContract.ts";

// Internal types for fetching data
interface Quote {
  symbol: string;
  longName?: string;
  regularMarketPrice?: number;
  previousClose?: number;
  currency?: string;
  exchange?: string;
  week_52_high?: number;
  week_52_low?: number;
  country?: string;
}

interface ChartResult {
  meta?: {
    symbol?: string;
    longName?: string;
    regularMarketPrice?: number;
    chartPreviousClose?: number;
    exchangeName?: string;
    currency?: string;
    fiftyTwoWeekHigh?: number;
    fiftyTwoWeekLow?: number;
    country?: string;
  };
  timestamp?: number[];
  indicators?: {
    quote?: Array<{
      open?: number[];
      high?: number[];
      low?: number[];
      close?: number[];
      volume?: number[];
    }>;
  };
}

function assertProfile(profile: CompanyProfile) {
  if (!profile.ticker) throw new Error("Missing ticker");
  if (!profile.name) throw new Error("Missing name");
}

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers":
    "Content-Type, Authorization, X-Client-Info, Apikey, ticker, range, model",
};

async function fetchChart(ticker: string, range: string) {
  const chartUrl = `https://query1.finance.yahoo.com/v8/finance/chart/${ticker}?interval=1d&range=${range}`;

  const chartResponse = await fetch(chartUrl, {
    headers: {
      "User-Agent": "Mozilla/5.0",
      Accept: "application/json",
    },
  });

  if (!chartResponse.ok) {
    throw new Error(`Yahoo chart error: ${chartResponse.status}`);
  }

  const chartData = await chartResponse.json();
  const chartResult: ChartResult = chartData.chart.result[0];

  const meta = chartResult.meta || {};

  const quote: Quote = {
    symbol: meta.symbol || ticker,
    longName: meta.longName,
    regularMarketPrice: meta.regularMarketPrice,
    previousClose: meta.chartPreviousClose,
    currency: meta.currency,
    exchange: meta.exchangeName,
    week_52_high: meta.fiftyTwoWeekHigh,
    week_52_low: meta.fiftyTwoWeekLow,
    country: meta.country,
  };

  // ✅ FINNHUB FETCH (FIXED)
  let finnhub = null;

  try {
    const apiKey = Deno.env.get("FINNHUB_API_KEY");

    if (apiKey) {
      const res = await fetch(
        `https://finnhub.io/api/v1/stock/profile2?symbol=${ticker}&token=${apiKey}`
      );

      if (res.ok) {
        finnhub = await res.json();
        console.log("FINNHUB RESPONSE:", finnhub);
      } else {
        console.error("FINNHUB ERROR:", res.status);
      }
    }
  } catch (err) {
    console.error("FINNHUB FETCH FAILED:", err);
  }

  // ✅ FIXED MERGE (IMPORTANT PART)
  const mergedProfile: CompanyProfile = {
    ticker,
    name: finnhub?.name || quote.longName || ticker,
    sector: finnhub?.finnhubIndustry ?? null,
    industry: finnhub?.finnhubIndustry ?? null,
    market_cap: finnhub?.marketCapitalization ?? null,
    current_price: quote.regularMarketPrice ?? null,
    previous_close: quote.previousClose ?? null,
    exchange: finnhub?.exchange || quote.exchange || null,
    country: finnhub?.country || quote.country || null,
    currency: quote.currency ?? null,
    week_52_high: quote.week_52_high ?? null,
    week_52_low: quote.week_52_low ?? null,
    logo: finnhub?.logo ?? null,
    website: finnhub?.weburl ?? null,
  };
  console.log("FINAL PROFILE:", mergedProfile);
  assertProfile(mergedProfile);

  return { quote, chart: chartResult, mergedProfile };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const url = new URL(req.url);
    let ticker = url.searchParams.get("ticker") || req.headers.get("ticker");
    const range = url.searchParams.get("range") || "1y";
    const model = url.searchParams.get("model") || "linear";

    if (!ticker) {
      return new Response(JSON.stringify({ error: "Ticker required" }), {
        status: 400,
        headers: corsHeaders,
      });
    }

    ticker = ticker.toUpperCase();

    const { quote, chart, mergedProfile } = await fetchChart(ticker, range);

    const quoteData = chart.indicators?.quote?.[0];

    const closes = (quoteData?.close || []).filter(Boolean) as number[];

    const history = closes.map((close, i) => ({
      close,
    }));

    const lastClose = closes[closes.length - 1];

    const prediction = {
      predicted_price: lastClose,
      trend: "increase",
      confidence: 0.85,
      model_used: model,
    } as const;

    const response: StockResponse = {
      ticker,
      profile: mergedProfile,
      prediction,
      confidence: prediction.confidence,
    };

    return new Response(JSON.stringify(response), { headers: corsHeaders });
  } catch (error) {
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : "Unknown error",
      }),
      { status: 500, headers: corsHeaders }
    );
  }
});