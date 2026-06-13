# User Manual: Stock Intelligence Dashboard

Welcome to the Stock Intelligence Dashboard, your comprehensive tool for stock analysis and AI-driven predictions.

## Table of Contents

1.  [Installation](#installation)
2.  [Setup](#setup)
3.  [Configuration](#configuration)
4.  [Environment Variables](#environment-variables)
5.  [Usage](#usage)
    *   [Ask AI](#ask-ai)
    *   [Watchlist](#watchlist)
    *   [Charts](#charts)
    *   [AI Reports](#ai-reports)
6.  [Deployment](#deployment)

## Installation

### Prerequisites

*   Python 3.10+
*   Node.js 18+
*   NPM or Yarn
*   Supabase Account
*   Finnhub API Key

### Clone the Repository

```bash
git clone https://github.com/yourusername/stock-intelligence-dashboard.git
cd stock-intelligence-dashboard
```

## Setup

### Backend (FastAPI)

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```
2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Frontend (React)

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```

## Configuration

### Environment Variables

#### Backend (`backend/.env`)

```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_key
FINNHUB_API_KEY=your_finnhub_key
```

#### Frontend (`frontend/.env`)

```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_API_URL=http://localhost:8000/api/v1
```

## Usage

### Running the Application

1.  **Start the Backend:**
    ```bash
    cd backend
    uvicorn main:app --reload
    ```
2.  **Start the Frontend:**
    ```bash
    cd frontend
    npm run dev
    ```

### Ask AI

The "Ask AI" feature allows you to interact with an AI agent to get insights about specific stocks or market trends. Simply type your question in the drawer and receive an AI-generated response based on real-time data.

### Watchlist

You can add stocks to your personal watchlist to track their performance over time. The watchlist is persisted in Supabase.

### Charts

The dashboard provides interactive charts (powered by Plotly) for:
*   Stock Price (Historical & Predicted)
*   Volume
*   Technical Indicators (RSI, Moving Averages)

### AI Reports

Generate comprehensive AI reports for any stock ticker. These reports combine market data, technical analysis, and AI insights into a downloadable PDF.

## Deployment

### Docker

You can run the entire application using Docker:

```bash
docker-compose up --build
```

### Manual Deployment

*   **Backend:** Can be deployed to platforms like Railway, Render, or AWS App Runner.
*   **Frontend:** Can be deployed to Vercel, Netlify, or AWS Amplify.
*   **Database:** Use Supabase for managed PostgreSQL and Auth.
