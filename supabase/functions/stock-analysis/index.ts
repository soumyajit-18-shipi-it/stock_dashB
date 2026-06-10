/**
 * DEPRECATED: This Edge Function has been migrated to a Python FastAPI backend.
 * DO NOT USE.
 * 
 * Target: http://localhost:8000/api/v1/stock/{ticker}
 */

Deno.serve(async (req) => {
  return new Response(
    JSON.stringify({ 
      error: "This endpoint is deprecated. Please use the FastAPI backend.",
      migrated_to: "FastAPI" 
    }), 
    { 
      status: 410, 
      headers: { "Content-Type": "application/json" } 
    }
  );
});
