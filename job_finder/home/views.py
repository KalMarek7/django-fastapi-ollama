import asyncio

import httpx
from django.shortcuts import render


def home(request):
    return render(request, "home/home.html")


async def update_view(request):
    # Use a variable for the URL from settings or environment
    fastapi_base = "http://fastapi_service:8000"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Fire both requests at once!
            # responses[0] will be the scrape, responses[1] will be the pdf
            responses = await asyncio.gather(
                client.post(f"{fastapi_base}/jobs/schedule"),
                # client.post(f"{fastapi_base}/analyze-pdf", json={"file_path": "uploads/cv.pdf"}),
                # If one fails, the others continue (optional: return_exceptions=True)
            )

            # Convert response objects to JSON
            scrape_data = responses[0].json()
        # analysis_result = responses[1].json()

        except httpx.RequestError as exc:
            return render(request, "home/partial.html", {"error": f"API Error: {exc}"})

    # Return the data to your HTMX partial
    return render(
        request,
        "home/partial.html",
        {
            "data": scrape_data,
        },
    )
