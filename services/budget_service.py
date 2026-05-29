import json
import logging

from models.budget import BudgetRequest, BudgetResponse, CostBreakdown
from services.gemini_service import get_model, _clean_json_text

logger = logging.getLogger(__name__)


def _build_budget_prompt(request: BudgetRequest) -> str:
    lines = [
        "Estimate realistic travel costs for a trip in India.\n",
        f"Destination: {request.destination}",
        f"Number of days: {request.days}",
        f"Budget: {request.budget} INR",
    ]

    if request.trip_type:
        lines.append(f"Trip type: {request.trip_type}")
    if request.accommodation:
        lines.append(f"Accommodation type: {request.accommodation}")

    lines.append(
        "\nProvide a cost breakdown with realistic estimates in INR."
        "\n\nReturn the response strictly as JSON with this structure:\n"
        '{\n'
        '  "stay": 14000,\n'
        '  "food": 7000,\n'
        '  "local_transport": 5000,\n'
        '  "activities": 8000,\n'
        '  "miscellaneous": 3000,\n'
        '  "total": 37000\n'
        '}\n\n'
        "The total must equal the sum of all other fields.\n"
        "Return ONLY valid JSON.\n"
        "No markdown.\n"
        "No code blocks.\n"
        "No explanation."
    )

    return "\n".join(lines)


def _parse_gemini_response(raw_text: str) -> CostBreakdown:
    text = _clean_json_text(raw_text)
    data = json.loads(text)
    return CostBreakdown(**data)


def estimate_budget(request: BudgetRequest) -> BudgetResponse:
    logger.info(f"Estimating budget for {request.destination}, {request.days} days")

    try:
        model = get_model()
        prompt = _build_budget_prompt(request)
        logger.info("Calling Gemini for budget estimation")

        response = model.generate_content(prompt)
        cost_breakdown = _parse_gemini_response(response.text)

        budget_status = "WITHIN_BUDGET" if cost_breakdown.total <= request.budget else "OVER_BUDGET"
        logger.info(f"Budget estimation complete: total={cost_breakdown.total}, status={budget_status}")

        return BudgetResponse(
            destination=request.destination,
            days=request.days,
            cost_breakdown=cost_breakdown,
            budget_status=budget_status,
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini budget response: {e}")
        raise ValueError(f"Failed to parse Gemini response: {str(e)}")
    except Exception as e:
        logger.error(f"Budget estimation failed: {e}")
        raise ValueError(f"Failed to estimate budget: {str(e)}")
