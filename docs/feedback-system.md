# Feedback and Issue Reporting System

This document outlines the feedback loop architecture, user issue submission system, separation from the Ask AI feature, and database configuration.

## Feature Separation

The dashboard includes two distinct interactive tools:
1.  **Ask AI Panel:** A chatbot and financial analyst assistant. Accessible via the **Ask AI** button on the top-right of the Navbar and the floating green action button at the bottom-right (`bottom-5`).
2.  **Report Issue / Request Feature Widget:** A dedicated support tool. Accessible via the floating dark button at the bottom-right (`bottom-20`), ensuring it does not overlap with Ask AI or chart controls.

## Components

The feedback system is built on:
1.  **Frontend Widget (`FeedbackWidget.tsx`):** A floating, clean widget available on every page. It allows users to write details, select categories, and capture page contexts. If the user is unauthenticated, it politely requests Google Login.
2.  **FastAPI Endpoints:**
    *   `POST /api/v1/feedback`: Creates a new feedback issue (requires authentication).
    *   `GET /api/v1/feedback/my`: Retrieves feedback submitted by the currently logged-in user.
    *   `GET /api/v1/admin/feedback`: Allows admins to list and filter all feedback.
3.  **Supabase Table (`feedback_issues`):** A database table storing categories, status updates, priority fields, and captured URLs.

## Database Setup (Main Path - No CLI Required)

To set up the `feedback_issues` and related tables:

1. Copy the entire SQL content from the root-level script [supabase_setup.sql](file:///C:/Users/soumy/stock_dashB/supabase_setup.sql).
2. Go to your **Supabase Web Dashboard**.
3. Access the **SQL Editor** from the left-hand menu.
4. Click **New Query**, paste the code, and click **Run**.

*Note: Using the Supabase CLI (`supabase db push`) is entirely optional.*

### Web-Dashboard Verification Steps
* Open the **Table Editor** in your Supabase Web Dashboard.
* Confirm that the `public.feedback_issues` table is successfully created.
* When testing issue submission, submit a mock report from the frontend UI and verify the new row appears inside `public.feedback_issues` via the Supabase Table Editor.

## Local Development Setup

Ensure the following environment configurations are set:

### Frontend Variables (`frontend/.env`)
*   `VITE_API_URL=http://localhost:8000/api/v1`
*   `VITE_SUPABASE_URL=https://your-project-ref.supabase.co`
*   `VITE_SUPABASE_ANON_KEY=your-supabase-anon-key`
*   `VITE_APP_URL=http://localhost:5173`

### Backend Variables (`backend/.env`)
*   `SUPABASE_URL=https://your-project-ref.supabase.co`
*   `SUPABASE_ANON_KEY=your-supabase-anon-key`
*   `SUPABASE_SERVICE_ROLE_KEY=your-service-role-key`

Note: In local development, the backend should be accessed at `http://localhost:8000` (not `http://0.0.0.0:8000`), and the frontend runs on `http://localhost:5173`.

## Database Schema

Feedback records are saved in `public.feedback_issues`. Row Level Security (RLS) is configured to ensure:
*   **Submitters** can only insert their own records.
*   **Users** can only read reports they created.
*   **Anonymous** users cannot submit or list reports.
*   **Admins** query feedback safely through server-side endpoints bypassing RLS.

## GitLab Issue Templates

For open-source developers, issue templates are provided at:
*   [Bug.md](file:///C:/Users/soumy/stock_dashB/.gitlab/issue_templates/Bug.md)
*   [Feature_Request.md](file:///C:/Users/soumy/stock_dashB/.gitlab/issue_templates/Feature_Request.md)
*   [Documentation.md](file:///C:/Users/soumy/stock_dashB/.gitlab/issue_templates/Documentation.md)
*   [Setup_Query.md](file:///C:/Users/soumy/stock_dashB/.gitlab/issue_templates/Setup_Query.md)
*   [Development_Query.md](file:///C:/Users/soumy/stock_dashB/.gitlab/issue_templates/Development_Query.md)
