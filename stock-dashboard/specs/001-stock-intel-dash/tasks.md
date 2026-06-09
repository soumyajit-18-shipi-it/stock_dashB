# Tasks: Stock Intelligence Dashboard

**Input**: Design documents from `/specs/001-stock-intel-dash/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contract.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create backend directory structure: `backend/src/{core,ml,api}` and `backend/tests/{unit,integration}`
- [X] T002 Create frontend directory structure: `frontend/src/{components,services,store}` and `frontend/tests`
- [X] T003 [P] Initialize Python backend with `FastAPI`, `yfinance`, `pandas`, `scikit-learn` in `backend/requirements.txt`
- [X] T004 [P] Initialize React frontend with `Vite`, `TypeScript`, `Plotly.js` in `frontend/package.json`
- [X] T005 [P] Configure `pytest` for backend in `backend/pytest.ini` and `Vitest` for frontend in `frontend/vitest.config.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement base `StockRecord` and `CompanyProfile` models in `backend/src/core/models.py`
- [X] T007 Implement `YFinanceService` for raw data fetching in `backend/src/core/yfinance_service.py`
- [X] T008 Setup FastAPI application with CORS and basic logging in `backend/src/main.py`
- [X] T009 Create API client service in `frontend/src/services/api_client.ts`
- [X] T010 [P] Setup global state management for stock data in `frontend/src/store/stock_store.tsx`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Basic Stock Analysis (Priority: P1) 🎯 MVP

**Goal**: Fetch and visualize historical stock data and volume with Moving Averages.

**Independent Test**: Enter a ticker (e.g., AAPL), view the price chart with 7/21 MAs and volume chart.

### Implementation for User Story 1

- [X] T011 [US1] Implement data processing logic to calculate 7-day and 21-day MAs in `backend/src/core/data_processor.py`
- [X] T012 [US1] Create GET `/stock/{ticker}` endpoint in `backend/src/api/stock_router.py` (fetching history + metadata)
- [X] T013 [US1] Create `SearchBar` component in `frontend/src/components/SearchBar.tsx`
- [X] T014 [US1] Create `StockChart` component using Plotly in `frontend/src/components/StockChart.tsx`
- [X] T015 [US1] Implement `DataRangeSelector` component in `frontend/src/components/DataRangeSelector.tsx`
- [X] T016 [US1] Integrate charts and search in `frontend/src/pages/Dashboard.tsx`
- [X] T017 [US1] Implement error handling for invalid tickers in `frontend/src/components/ErrorMessage.tsx`

**Checkpoint**: User Story 1 is functional. Users can search and visualize stock trends.

---

## Phase 4: User Story 2 - Predictive Insights (Priority: P2)

**Goal**: Generate and display next-day price predictions using Linear Regression and Random Forest.

**Independent Test**: Switch between "Linear" and "Random Forest" models and see updated prediction values and trend indicators.

### Implementation for User Story 2

- [X] T018 [US2] Implement `BaseModel` abstract class and `LinearRegressionModel` in `backend/src/ml/models.py`
- [X] T019 [US2] Implement `RandomForestModel` in `backend/src/ml/models.py`
- [X] T020 [US2] Create feature engineering service (lagged prices, volume, MAs) in `backend/src/ml/features.py`
- [X] T021 [US2] Update GET `/stock/{ticker}` to include `PredictionOutcome` based on selected model in `backend/src/api/stock_router.py`
- [X] T022 [US2] Create `PredictionCard` component in `frontend/src/components/PredictionCard.tsx`
- [X] T023 [US2] Create `ModelToggle` component in `frontend/src/components/ModelToggle.tsx`
- [X] T024 [US2] Add trend direction indicators (color-coded arrows) in `frontend/src/components/TrendIndicator.tsx`

**Checkpoint**: User Story 2 is functional. Users can see ML-based insights.

---

## Phase 5: User Story 3 - Company Context (Priority: P3)

**Goal**: Display company fundamental metadata.

**Independent Test**: View company name, sector, and market cap after searching for a ticker.

### Implementation for User Story 3

- [X] T025 [US3] Implement fundamental data extraction from yfinance in `backend/src/core/yfinance_service.py`
- [X] T026 [US3] Create `CompanyProfileCard` component in `frontend/src/components/CompanyProfileCard.tsx`
- [X] T027 [US3] Integrate metadata card into the main dashboard layout in `frontend/src/pages/Dashboard.tsx`

**Checkpoint**: All user stories are functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final refinements and validation.

- [X] T028 [P] Optimize Plotly chart performance for large (5Y) datasets in `frontend/src/components/StockChart.tsx`
- [X] T029 Implement responsive CSS layout for mobile devices in `frontend/src/styles/App.css`
- [X] T030 [P] Final code cleanup and type-checking (Backend: `mypy`, Frontend: `tsc`)
- [X] T031 Run end-to-end validation as defined in `specs/001-stock-intel-dash/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** -> **Foundational (Phase 2)** -> **User Stories (Phase 3+)**
- **User Story 2 (Predictions)** depends on **User Story 1 (Data Processing)** for input features.
- **User Story 3 (Metadata)** is independent of Story 2.

### Parallel Opportunities

- Phase 1 & 2 backend vs. frontend setup tasks marked [P] can run in parallel.
- User Story 3 (Metadata) can be implemented in parallel with User Story 2 (Predictions).
- UI component styling (T029) can run in parallel with ML logic (T020).

---

## Implementation Strategy

### MVP First (User Story 1 Only)
Focus on T001-T017. This delivers a working Stock Dashboard with real-time data and charts.

### Incremental Delivery
1. Foundation (T006-T010)
2. Basic Analysis (US1: T011-T017) -> **Deployable MVP**
3. Predictive Insights (US2: T018-T024)
4. Company Context (US3: T025-T027)
5. Final Polish (T028-T031)
