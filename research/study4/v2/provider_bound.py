"""Model-level text inference reservation, not an invoice/tax or prompt-fit guarantee."""
MODEL_MAXIMUM_BOUND = {
    "kind": "provider_model_maximum_bound", "version": 1,
    "model": "gpt-5.4-mini-2026-03-17", "input_tokens": 272000, "output_tokens": 128000,
    "service_tier": "default", "billing_scope": "standard-text-single-response-no-provider-tools-v1",
}


def uses_model_maximum(plan):
    from .native_protocol import BOUND
    return plan["token_bound"] in (MODEL_MAXIMUM_BOUND, BOUND)


def reservation_output_bound(plan):
    return MODEL_MAXIMUM_BOUND["output_tokens"] if uses_model_maximum(plan) else plan["caps"]["output_tokens"]
