
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from schemas import BargainRequest, BargainChatRequest, BargainChatResponse, BargainMessage, ProductInfo
from constants import BARGAIN_SYSTEM_PROMPT_TEMPLATE, BARGAIN_CURRENCY_PATTERNS, BARGAIN_DEAL_PATTERNS, ERROR_PRODUCT_NOT_FOUND

router = APIRouter()


def get_llm_response(messages: List[BargainMessage], product_info: ProductInfo) -> str:
    """
    Get LLM response for bargaining conversation using litellm.
    Falls back to rule-based response if LLM fails.
    """
    try:
        import litellm

        # Set API key from environment or use default
        # You can set OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.
        litellm.drop_params = True

        # Build the conversation context
        product_name = product_info.name
        original_price = product_info.price
        cost = product_info.cost
        minimum_price = product_info.minimum_price

        # Calculate discount price for the example in the prompt
        discount_price = int(original_price * 0.85)

        # System prompt for the LLM - realistic Indian shopkeeper bargaining
        system_prompt = BARGAIN_SYSTEM_PROMPT_TEMPLATE.format(
            product_name=product_name, original_price=original_price,
            cost=cost, minimum_price=minimum_price, discount_price=discount_price
        )

        # Convert conversation history to litellm format
        llm_messages = [{"role": "system", "content": system_prompt}]

        for msg in messages:
            role = "user" if msg.role == "user" else "assistant"
            llm_messages.append({"role": role, "content": msg.content})

        # List of models to try in order for fallback
        models_to_try = [
            "gpt-3.5-turbo",                # OpenAI (fast, cheap, reliable)
            "claude-3-haiku-20240307",       # Anthropic (good alternative)
            "openrouter/google/gemini-flash-1.5" # Free model on OpenRouter as a last resort
        ]

        last_exception = None
        for model in models_to_try:
            try:
                print(f"Trying LLM model: {model}")
                response = litellm.completion(  # type: ignore
                    model=model,
                    messages=llm_messages,
                    max_tokens=150,
                    temperature=0.7
                )
                choices = getattr(response, 'choices', None)
                if choices:
                    content = choices[0].message.content  # type: ignore
                    if content:
                        print(f"Successfully got response from {model}")
                        return content
                raise Exception("Empty response content from model")
            except Exception as e:
                print(f"Model {model} failed: {e}")
                last_exception = e
                continue # Try next model
        
        raise Exception(f"All LLM providers failed. Last error: {last_exception}")

    except Exception as e:
        print(f"LLM Error: {e}")
        # Return a fallback response - don't reveal exact minimum price
        return "Bhaiya, aap jo bol rahe ho usse kam mein possible nahi. Thoda aur badhaiye toh dekhta hoon!"


def parse_offer_from_message(message: str, original_price: float) -> Optional[float]:
    """
    Extract offer amount from user message if present.
    Looks for patterns like "₹500", "500 rupees", "rs 500", etc.
    """
    import re
    
    message_lower = message.lower()
    
    # Pattern to match Indian currency formats
    patterns = BARGAIN_CURRENCY_PATTERNS
    
    for pattern in patterns:
        matches = re.findall(pattern, message_lower)
        if matches:
            try:
                offer = float(matches[0])
                if offer > 0 and offer <= original_price * 1.5:  # Reasonable range
                    return offer
            except ValueError:
                continue
    
    return None


def check_deal_accepted(llm_response: str) -> tuple[bool, Optional[float]]:
    """
    Check if the LLM response indicates a deal has been accepted.
    Looks for [DEAL: ₹X] pattern.
    """
    import re
    
    # Support both [DEAL: ₹X] and [ACCEPTED: ₹X] for backwards compatibility
    patterns = BARGAIN_DEAL_PATTERNS
    
    for pattern in patterns:
        match = re.search(pattern, llm_response, re.IGNORECASE)
        if match:
            try:
                return True, float(match.group(1))
            except ValueError:
                pass
    
    return False, None

@router.post("/bargain/{product_id}")
def bargain(product_id: int, data: BargainRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    product = db.execute(
        text("SELECT price, cost, stock FROM products WHERE id = :product_id"),
        {"product_id": product_id},
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail=ERROR_PRODUCT_NOT_FOUND)

    price, cost, stock = product

    if stock <= 0:
        return {"status": "rejected", "message": "Out of stock"}

    # Check if there's enough margin to allow bargaining (minimum 15% discount = 85% of price)
    if price * 0.85 <= cost:
        raise HTTPException(
            status_code=400,
            detail=f"Bargain not allowed: Not enough margin. Price is too close to cost."
        )

    minimum_price = round(price * 0.75, 2)  # Minimum 25% discount (75% of selling price)

    if data.offer >= price:
        final_price = price
    elif data.offer >= minimum_price:
        final_price = data.offer
    else:
        return {
            "status": "counter",
            "counter_price": minimum_price,
            "message": f"Minimum acceptable price is ₹{minimum_price}"
        }

    db.execute(
        text("UPDATE products SET stock = stock - 1 WHERE id = :product_id"),
        {"product_id": product_id},
    )
    db.commit()

    return {
        "status": "accepted",
        "final_price": final_price,
        "original_price": price,
        "discount": round(((price - final_price) / price) * 100, 2)
    }


# ------------------------
# LLM-POWERED BARGAIN CHAT
# ------------------------

@router.post("/bargain/chat/{product_id}", response_model=BargainChatResponse)
def bargain_chat(
    product_id: int, 
    data: BargainChatRequest, 
    db: Session = Depends(get_db)
) -> BargainChatResponse:
    """
    LLM-powered conversational bargaining endpoint.
    Uses litellm to get intelligent responses based on conversation history.
    """
    # Get product info
    product = db.execute(
        text("SELECT name, price, cost, stock FROM products WHERE id = :product_id"),
        {"product_id": product_id},
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail=ERROR_PRODUCT_NOT_FOUND)

    product_name, price, cost, stock = product

    if stock <= 0:
        raise HTTPException(status_code=400, detail="Product is out of stock")

    # Check if there's enough margin to allow bargaining (minimum 15% discount = 85% of price)
    if price * 0.85 <= cost:
        raise HTTPException(
            status_code=400,
            detail=f"Bargain not allowed: Not enough margin. Price is too close to cost."
        )

    minimum_price = round(price * 0.75, 2)  # Minimum 25% discount (75% of selling price)

    # If no messages yet, return a greeting from the shopkeeper
    if not data.message.strip() and (not data.conversation_history or len(data.conversation_history) == 0):
        greeting = f"Namaste! 🙏 Ye {product_name} ₹{price} mein hai. Best quality hai! Kya aap isme interested hain? Discount bhi de sakta hoon! 😊"
        return BargainChatResponse(
            response=greeting,
            suggested_price=None,
            is_accepted=False,
            final_price=None
        )

    # Build product info object
    product_info = ProductInfo(
        name=product_name,
        price=price,
        cost=cost,
        stock=stock,
        minimum_price=minimum_price,
        original_price=price
    )

    # Add current message to conversation history
    conversation = data.conversation_history.copy() if data.conversation_history else []
    conversation.append(BargainMessage(role="user", content=data.message))

    # Get LLM response
    llm_response = get_llm_response(conversation, product_info)

    # Check if deal was accepted
    is_accepted, final_price = check_deal_accepted(llm_response)

    # If accepted, reduce stock
    if is_accepted and final_price:
        db.execute(
            text("UPDATE products SET stock = stock - 1 WHERE id = :product_id"),
            {"product_id": product_id},
        )
        db.commit()

    # Parse offer from user message
    offer = parse_offer_from_message(data.message, price)
    suggested_price = None
    if offer and not is_accepted:
        if offer >= minimum_price:
            suggested_price = offer
        else:
            suggested_price = minimum_price

    return BargainChatResponse(
        response=llm_response,
        suggested_price=suggested_price,
        is_accepted=is_accepted,
        final_price=final_price
    )

