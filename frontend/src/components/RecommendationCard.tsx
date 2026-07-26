import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  Gauge,
  Loader2,
  ShieldAlert,
  Target,
} from 'lucide-react';

import type {
  InvestmentHorizon,
  RecommendationResponse,
  RiskTolerance,
} from '../types';

interface RecommendationCardProps {
  recommendation?: RecommendationResponse;
  isLoading: boolean;
  error?: Error | null;
  riskTolerance: RiskTolerance;
  horizon: InvestmentHorizon;
  onRiskToleranceChange: (value: RiskTolerance) => void;
  onHorizonChange: (value: InvestmentHorizon) => void;
  onExplain: () => void;
  isExplaining: boolean;
  llmExplanation: string;
}

const componentLabels: Record<string, string> = {
  technical: 'Technical',
  fundamental: 'Fundamentals',
  valuation: 'Valuation',
  sentiment: 'News sentiment',
  risk: 'Risk quality',
  prediction: 'ML prediction',
};

const recommendationTone = {
  BUY: {
    text: 'text-emerald-300',
    border: 'border-emerald-500/40',
    background: 'bg-emerald-500/10',
  },
  HOLD: {
    text: 'text-amber-300',
    border: 'border-amber-500/40',
    background: 'bg-amber-500/10',
  },
  SELL: {
    text: 'text-rose-300',
    border: 'border-rose-500/40',
    background: 'bg-rose-500/10',
  },
};

export function RecommendationCard({
  recommendation,
  isLoading,
  error,
  riskTolerance,
  horizon,
  onRiskToleranceChange,
  onHorizonChange,
  onExplain,
  isExplaining,
  llmExplanation,
}: RecommendationCardProps) {
  if (isLoading) {
    return (
      <section className="min-h-80 animate-pulse rounded-lg border border-slate-700 bg-slate-900/70 p-6">
        <div className="h-6 w-52 rounded bg-slate-700" />
        <div className="mt-8 h-40 rounded bg-slate-800" />
      </section>
    );
  }

  if (error || !recommendation) {
    return (
      <section className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-5 text-rose-200">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" />
          <span>{error?.message || 'Recommendation is unavailable.'}</span>
        </div>
      </section>
    );
  }

  const { decision } = recommendation;
  const tone = recommendationTone[decision.recommendation];
  const scoreAngle = `${Math.max(0, Math.min(100, decision.overall_score)) * 3.6}deg`;
  const riskWidth =
    decision.risk_level === 'high' ? 88 : decision.risk_level === 'medium' ? 58 : 28;

  return (
    <section className={`rounded-lg border ${tone.border} bg-slate-900/80 p-5 sm:p-6`}>
      <div className="flex flex-col gap-4 border-b border-slate-700 pb-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-3">
          <div className={`rounded-md p-2 ${tone.background}`}>
            <Target className={`h-6 w-6 ${tone.text}`} />
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
              Investment decision support
            </p>
            <div className="mt-1 flex items-baseline gap-3">
              <h2 className={`text-3xl font-bold ${tone.text}`}>
                {decision.recommendation}
              </h2>
              <span className="text-sm text-slate-300">
                {Math.round(decision.confidence * 100)}% confidence
              </span>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <label className="text-xs text-slate-400">
            Risk profile
            <select
              value={riskTolerance}
              onChange={(event) =>
                onRiskToleranceChange(event.target.value as RiskTolerance)
              }
              className="mt-1 block rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-white"
            >
              <option value="conservative">Conservative</option>
              <option value="balanced">Balanced</option>
              <option value="aggressive">Aggressive</option>
            </select>
          </label>
          <label className="text-xs text-slate-400">
            Horizon
            <select
              value={horizon}
              onChange={(event) =>
                onHorizonChange(event.target.value as InvestmentHorizon)
              }
              className="mt-1 block rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-white"
            >
              <option value="short">1-3 months</option>
              <option value="medium">3-12 months</option>
              <option value="long">1-5 years</option>
            </select>
          </label>
        </div>
      </div>

      <div className="grid gap-6 py-6 lg:grid-cols-[190px_1fr_1fr]">
        <div className="flex flex-col items-center justify-center">
          <div
            className="grid h-36 w-36 place-items-center rounded-full"
            style={{
              background: `conic-gradient(#10b981 0deg, #10b981 ${scoreAngle}, #334155 ${scoreAngle}, #334155 360deg)`,
            }}
          >
            <div className="grid h-28 w-28 place-items-center rounded-full bg-slate-950 text-center">
              <div>
                <div className="text-3xl font-bold text-white">
                  {Math.round(decision.overall_score)}
                </div>
                <div className="text-xs text-slate-400">Overall score</div>
              </div>
            </div>
          </div>
          <div className="mt-4 w-full">
            <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
              <span>Risk</span>
              <span className="capitalize">{decision.risk_level}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-700">
              <div
                className={`h-full ${
                  decision.risk_level === 'high'
                    ? 'bg-rose-500'
                    : decision.risk_level === 'medium'
                      ? 'bg-amber-400'
                      : 'bg-cyan-400'
                }`}
                style={{ width: `${riskWidth}%` }}
              />
            </div>
          </div>
        </div>

        <div>
          <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-100">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            Supporting evidence
          </h3>
          <ul className="mt-3 space-y-2">
            {(decision.strengths.length
              ? decision.strengths
              : ['No component has sufficiently strong positive evidence.']
            ).map((item) => (
              <li key={item} className="flex gap-2 text-sm text-slate-300">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-100">
            <ShieldAlert className="h-4 w-4 text-amber-400" />
            Risks and constraints
          </h3>
          <ul className="mt-3 space-y-2">
            {(decision.weaknesses.length
              ? decision.weaknesses
              : ['No material weakness crossed the configured threshold.']
            ).map((item) => (
              <li key={item} className="flex gap-2 text-sm text-slate-300">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="grid gap-px overflow-hidden rounded-md border border-slate-700 bg-slate-700 sm:grid-cols-3">
        <div className="bg-slate-900 p-4">
          <p className="text-xs text-slate-400">Expected return</p>
          <p className={`mt-1 text-lg font-semibold ${decision.expected_return >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
            {(decision.expected_return * 100).toFixed(1)}%
          </p>
        </div>
        <div className="bg-slate-900 p-4">
          <p className="text-xs text-slate-400">Expected downside</p>
          <p className="mt-1 text-lg font-semibold text-rose-300">
            {(decision.expected_downside * 100).toFixed(1)}%
          </p>
        </div>
        <div className="bg-slate-900 p-4">
          <p className="text-xs text-slate-400">Investment horizon</p>
          <p className="mt-1 text-lg font-semibold text-cyan-300">
            {decision.investment_horizon}
          </p>
        </div>
      </div>

      <div className="mt-6">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-100">
          <Gauge className="h-4 w-4 text-cyan-400" />
          Component contributions
        </h3>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          {Object.entries(decision.components).map(([name, component]) => (
            <div key={name}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="text-slate-300">{componentLabels[name] || name}</span>
                <span className="text-slate-400">
                  {Math.round((component.score + 1) * 50)} / 100 · {Math.round(component.confidence * 100)}%
                </span>
              </div>
              <div className="relative h-2 rounded-full bg-slate-700">
                <div className="absolute left-1/2 top-0 h-full w-px bg-slate-400" />
                <div
                  className={`absolute top-0 h-full rounded-full ${
                    component.score >= 0 ? 'bg-emerald-500' : 'bg-rose-500'
                  }`}
                  style={
                    component.score >= 0
                      ? { left: '50%', width: `${component.score * 50}%` }
                      : { right: '50%', width: `${Math.abs(component.score) * 50}%` }
                  }
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6 flex flex-col gap-3 border-t border-slate-700 pt-5">
        <div className="flex items-center justify-between gap-3">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-100">
            <Bot className="h-4 w-4 text-violet-300" />
            AI explanation
          </h3>
          <button
            type="button"
            disabled={isExplaining}
            onClick={onExplain}
            className="flex items-center gap-2 rounded-md border border-violet-500/40 bg-violet-500/10 px-3 py-2 text-sm text-violet-200 hover:bg-violet-500/20 disabled:opacity-50"
          >
            {isExplaining ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Bot className="h-4 w-4" />
            )}
            Explain
          </button>
        </div>
        {llmExplanation && (
          <p className="whitespace-pre-wrap text-sm leading-6 text-slate-300">
            {llmExplanation}
          </p>
        )}
      </div>
    </section>
  );
}
