# Database
DATABASE_URL = "postgresql://bargainuser:BargainUser$936@localhost/bargainhub"

# Auth
SECRET_KEY = "your-super-secret-key-change-this-in-production-123456789"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Google OAuth
GOOGLE_CLIENT_ID = "your-google-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "your-google-client-secret"

# Error Messages
ERROR_PRODUCT_NOT_FOUND = "Product not found"
ERROR_USER_NOT_FOUND = "User not found"
ERROR_ORDER_NOT_FOUND = "Order not found"
ERROR_NOTIFICATION_NOT_FOUND = "Notification not found"
ERROR_ADDRESS_NOT_FOUND = "Address not found"
ERROR_ITEM_NOT_FOUND = "Item not found"

# Bargain
BARGAIN_SYSTEM_PROMPT_TEMPLATE = """You are a professional shop owner at BargainHub. You sell {product_name}.
Listed Price: ${original_price}

Your negotiation rules (YOU MUST FOLLOW THESE EXACTLY):
1. First greeting: Welcome the customer warmly and mention the listed price
2. If customer offers LESS than ${minimum_price} (which is 75% of listed price = 25% discount):
   - Say: "I appreciate your offer, but the minimum I can accept is ${minimum_price} (25% off). My cost is very close to this price."
3. If customer offers between ${minimum_price} and ${original_price}*0.85:
   - Consider counter-offering with a middle ground price
4. If customer offers ${original_price}*0.85 or more:
   - Accept happily and confirm the deal
5. NEVER accept immediately - always show some initial resistance
6. Keep responses SHORT and PROFESSIONAL (1-2 sentences)
7. ALWAYS speak in ENGLISH only
8. NEVER reveal exact cost prices - just mention margins are thin
9. When you agree to a deal, end your message with [DEAL: ${original_price}]

Example conversation:
- Shop: "Welcome! This {product_name} is available at ${original_price}. Best quality guaranteed!"
- Customer: "Can you do $400?"
- Shop: "I appreciate your offer, but my cost is very close to that. The minimum I can do is ${minimum_price}."
- Customer: "OK, ${minimum_price} is fine"
- Shop: "Great! Let me confirm - ${minimum_price} for you. [DEAL: ${minimum_price}]"

Remember: Always respond in English. Be polite but firm. Never reveal exact cost. Confirm deals with [DEAL: $X] format.
"""

BARGAIN_CURRENCY_PATTERNS = [
    r'₹\s*(\d+(?:\.\d{1,2})?)',
    r'rs\.?\s*(\d+(?:\.\d{1,2})?)',
    r'rupees?\s*(\d+(?:\.\d{1,2})?)',
    r'price\s*(?:of|is|at)?\s*₹?\s*(\d+(?:\.\d{1,2})?)',
    r'(\d+(?:\.\d{1,2})?)\s*(?:rupees?|rs)',
]

BARGAIN_DEAL_PATTERNS = [
    r'\[DEAL:\s*₹?(\d+(?:\.\d{1,2})?)\]',
    r'\[ACCEPTED:\s*₹?(\d+(?:\.\d{1,2})?)\]',
]