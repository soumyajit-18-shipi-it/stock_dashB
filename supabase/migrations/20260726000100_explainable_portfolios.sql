-- Persistent user portfolios for the explainable investment platform.

CREATE TABLE IF NOT EXISTS public.portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK (char_length(trim(name)) BETWEEN 1 AND 120),
    analysis_snapshot JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.portfolio_holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES public.portfolios(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    quantity NUMERIC CHECK (quantity IS NULL OR quantity > 0),
    average_cost NUMERIC CHECK (average_cost IS NULL OR average_cost >= 0),
    target_weight NUMERIC CHECK (
        target_weight IS NULL OR (target_weight > 0 AND target_weight <= 1)
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT portfolio_holding_position CHECK (
        quantity IS NOT NULL OR target_weight IS NOT NULL
    ),
    CONSTRAINT portfolio_ticker_unique UNIQUE (portfolio_id, ticker)
);

CREATE INDEX IF NOT EXISTS idx_portfolios_user_updated
    ON public.portfolios(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_holdings_portfolio
    ON public.portfolio_holdings(portfolio_id);

ALTER TABLE public.portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolio_holdings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "select_own_portfolios" ON public.portfolios
    FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "insert_own_portfolios" ON public.portfolios
    FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY "update_own_portfolios" ON public.portfolios
    FOR UPDATE TO authenticated USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);
CREATE POLICY "delete_own_portfolios" ON public.portfolios
    FOR DELETE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "select_own_portfolio_holdings" ON public.portfolio_holdings
    FOR SELECT TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.portfolios
            WHERE portfolios.id = portfolio_holdings.portfolio_id
              AND portfolios.user_id = auth.uid()
        )
    );
CREATE POLICY "insert_own_portfolio_holdings" ON public.portfolio_holdings
    FOR INSERT TO authenticated WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.portfolios
            WHERE portfolios.id = portfolio_holdings.portfolio_id
              AND portfolios.user_id = auth.uid()
        )
    );
CREATE POLICY "update_own_portfolio_holdings" ON public.portfolio_holdings
    FOR UPDATE TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.portfolios
            WHERE portfolios.id = portfolio_holdings.portfolio_id
              AND portfolios.user_id = auth.uid()
        )
    );
CREATE POLICY "delete_own_portfolio_holdings" ON public.portfolio_holdings
    FOR DELETE TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.portfolios
            WHERE portfolios.id = portfolio_holdings.portfolio_id
              AND portfolios.user_id = auth.uid()
        )
    );

CREATE OR REPLACE FUNCTION public.touch_portfolio_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS on_portfolio_updated ON public.portfolios;
CREATE TRIGGER on_portfolio_updated
    BEFORE UPDATE ON public.portfolios
    FOR EACH ROW EXECUTE FUNCTION public.touch_portfolio_updated_at();

DROP TRIGGER IF EXISTS on_portfolio_holding_updated ON public.portfolio_holdings;
CREATE TRIGGER on_portfolio_holding_updated
    BEFORE UPDATE ON public.portfolio_holdings
    FOR EACH ROW EXECUTE FUNCTION public.touch_portfolio_updated_at();
