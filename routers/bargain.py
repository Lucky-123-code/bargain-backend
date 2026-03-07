from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from schemas import BargainRequest, BargainChatRequest, BargainChatResponse, BargainMessage

router = APIRouter()


def get_llm_response(messages: List[BargainMessage], product_info: dict) -> str:
    """
    Get LLM response for bargaining conversation using litellm.
    Falls back to rule-based response if LLM fails.
    """
    try:
        import os
        import litellm
        
        # Set API key from environment or use default
        # You can set OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.
        litellm.drop_params = True
        litellm.set_verbose = False
        
        # Build the conversation context
        product_name = product_info.get("name", "this product")
        original_price = product_info.get("price", 0)
        cost = product_info.get("cost", 0)
        stock = product_info.get("stock", 0)
        minimum_price = round(cost * 1.5, 2)
        
        # System prompt for the LLM
        system_prompt = f"""You are a friendly store owner negotiating with a customer over {product_name}.
The original price is ₹{original_price}, but you can negotiate.
- Your cost is ₹{cost}
- Your minimum acceptable price is ₹{minimum_price} (that's cost + 50%)
- Current stock: {stock} units

Guidelines for negotiation:
1. Be friendly and conversational
2. You can offer discounts but never go below ₹{minimum_price}
3. If the customer offers a fair price near {minimum_price}, you can accept
4. If they offer too low, explain your constraints politely
5. Try to close the deal if they offer ₹{minimum_price} or more
6. Keep responses short and natural (1-2 sentences)

Respond as the store owner. If the user accepts your price or makes a reasonable offer, 
say the deal is done and include [ACCEPTED: ₹X] where X is the final price."""

        # Convert conversation history to litellm format
        llm_messages = [{"role": "system", "content": system_prompt}]
        
        for msg in messages:
            role = "user" if msg.role == "user" else "assistant"
            llm_messages.append({"role": role, "content": msg.content})
        
        # Add current message
        if messages:
            last_msg = messages[-1]
            if last_msg.role == "user":
                llm_messages.append({"role": "user", "content": last_msg.content})
        
        # Call LLM - try multiple providers
        try:
            # Try OpenAI first
            response = litellm.completion(
                model="gpt-4o-mini",
                messages=llm_messages,
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI failed: {e}")
            try:
                # Try Anthropic as fallback
                response = litellm.completion(
                    model="claude-3-haiku-20240307",
                    messages=llm_messages,
                    max_tokens=150,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e2:
                print(f"Anthropic failed: {e2}")
                raise Exception("LLM providers unavailable")
                
    except Exception as e:
        print(f"LLM Error: {e}")
        # Return a fallback response
        return f"I'm sorry, I'm having trouble connecting to my pricing system. My best price for this item is ₹{product_info.get('minimum_price', 'unknown')}."


def parse_offer_from_message(message: str, original_price: float) -> Optional[float]:
    """
    Extract offer amount from user message if present.
    Looks for patterns like "₹500", "500 rupees", "rs 500", etc.
    """
    import re
    
    message_lower = message.lower()
    
    # Pattern to match Indian currency formats
    patterns = [
        r'₹\s*(\d+(?:\.\d{1,2})?)',
        r'rs\.?\s*(\d+(?:\.\d{1,2})?)',
        r'rupees?\s*(\d+(?:\.\d{1,2})?)',
        r'price\s*(?:of|is|at)?\s*₹?\s*(\d+(?:\.\d{1,2})?)',
        r'(\d+(?:\.\d{1,2})?)\s*(?:rupees?|rs)',
    ]
    
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
    Looks for [ACCEPTED: ₹X] pattern.
    """
    import re
    
    pattern = r'\[ACCEPTED:\s*₹?(\d+(?:\.\d{1,2})?)\]'
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
        raise HTTPException(status_code=404, detail="Product not found")

    price, cost, stock = product

    if stock <= 0:
        return {"status": "rejected", "message": "Out of stock"}

    # Calculate profit margin percentage
    profit_margin = ((price - cost) / price) * 100 if price > 0 else 0

    # Check if profit margin is more than 50%
    if profit_margin <= 50:
        raise HTTPException(
            status_code=400,
            detail=f"Bargain not allowed: Profit margin is only {profit_margin:.1f}%. Must be more than 50% to allow bargaining."
        )

    minimum_price = round(cost * 1.5, 2)

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
        raise HTTPException(status_code=404, detail="Product not found")

    product_name, price, cost, stock = product

    if stock <= 0:
        raise HTTPException(status_code=400, detail="Product is out of stock")

    # Calculate profit margin
    profit_margin = ((price - cost) / price) * 100 if price > 0 else 0

    if profit_margin <= 50:
        raise HTTPException(
            status_code=400,
            detail=f"Bargain not allowed: Profit margin is only {profit_margin:.1f}%. Must be more than 50% to allow bargaining."
        )

    minimum_price = round(cost * 1.5, 2)

    # Build product info dict
    product_info = {
        "name": product_name,
        "price": price,
        "cost": cost,
        "stock": stock,
        "minimum_price": minimum_price,
        "original_price": price
    }

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
