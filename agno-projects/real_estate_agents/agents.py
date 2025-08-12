from agno.agent import Agent
from agno.models.openai import OpenAIChat
from firecrawl import FirecrawlApp
from models import PropertyListing

class DirectFirecrawlAgent:
    """Agent with direct Firecrawl integration for property search"""
    
    def __init__(self, firecrawl_api_key: str, openai_api_key: str, model_id: str = "gpt-4o"):
        self.agent = Agent(
            model=OpenAIChat(id=model_id, api_key=openai_api_key),
            markdown=True,
            description="I am a real estate expert who helps find and analyze properties based on user preferences."
        )
        self.firecrawl = FirecrawlApp(api_key=firecrawl_api_key)

    def find_properties_direct(self, city: str, state: str, user_criteria: dict, selected_websites: list) -> dict:
        """Direct Firecrawl integration for property search"""
        city_formatted = city.replace(' ', '-').lower()
        state_upper = state.upper() if state else ''
        
        # Create URLs for selected websites
        state_lower = state.lower() if state else ''
        city_trulia = city.replace(' ', '_')  # Trulia uses underscores for spaces
        search_urls = {
            "Zillow": f"https://www.zillow.com/homes/for_sale/{city_formatted}-{state_upper}/",
            "Realtor.com": f"https://www.realtor.com/realestateandhomes-search/{city_formatted}_{state_upper}/pg-1",
            "Trulia": f"https://www.trulia.com/{state_upper}/{city_trulia}/",
            "Homes.com": f"https://www.homes.com/homes-for-sale/{city_formatted}-{state_lower}/"
        }
        
        # Filter URLs based on selected websites
        urls_to_search = [url for site, url in search_urls.items() if site in selected_websites]
        
        print(f"Selected websites: {selected_websites}")
        print(f"URLs to search: {urls_to_search}")
        
        if not urls_to_search:
            return {"error": "No websites selected"}
        
        # Create comprehensive prompt with specific schema guidance
        prompt = f"""You are extracting property listings from real estate websites. Extract EVERY property listing you can find on the page.

USER SEARCH CRITERIA:
- Budget: {user_criteria.get('budget_range', 'Any')}
- Property Type: {user_criteria.get('property_type', 'Any')}
- Bedrooms: {user_criteria.get('bedrooms', 'Any')}
- Bathrooms: {user_criteria.get('bathrooms', 'Any')}
- Min Square Feet: {user_criteria.get('min_sqft', 'Any')}
- Special Features: {user_criteria.get('special_features', 'Any')}

EXTRACTION INSTRUCTIONS:
1. Find ALL property listings on the page (usually 20-40 per page)
2. For EACH property, extract these fields:
   - address: Full street address (required)
   - price: Listed price with $ symbol (required) 
   - bedrooms: Number of bedrooms (required)
   - bathrooms: Number of bathrooms (required)
   - square_feet: Square footage if available
   - property_type: House/Condo/Townhouse/Apartment etc.
   - description: Brief property description if available
   - listing_url: Direct link to property details if available
   - agent_contact: Agent name/phone if visible

3. CRITICAL REQUIREMENTS:
   - Extract AT LEAST 10 properties if they exist on the page
   - Do NOT skip properties even if some fields are missing
   - Use "Not specified" for missing optional fields
   - Ensure address and price are always filled
   - Look for property cards, listings, search results

4. RETURN FORMAT:
   - Return JSON with "properties" array containing all extracted properties
   - Each property should be a complete object with all available fields
   - Set "total_count" to the number of properties extracted
   - Set "source_website" to the main website name (Zillow/Realtor/Trulia/Homes)

EXTRACT EVERY VISIBLE PROPERTY LISTING - DO NOT LIMIT TO JUST A FEW!
        """
        
        try:
            # Direct Firecrawl call - using correct API format
            print(f"Calling Firecrawl with {len(urls_to_search)} URLs")
            raw_response = self.firecrawl.extract(
                urls_to_search,
                prompt=prompt,
                schema=PropertyListing.model_json_schema()
            )
            
            print("Raw Firecrawl Response:", raw_response)
            
            if hasattr(raw_response, 'success') and raw_response.success:
                # Handle Firecrawl response object
                properties = raw_response.data.get('properties', []) if hasattr(raw_response, 'data') else []
                total_count = raw_response.data.get('total_count', 0) if hasattr(raw_response, 'data') else 0
                print(f"Response data keys: {list(raw_response.data.keys()) if hasattr(raw_response, 'data') else 'No data'}")
            elif isinstance(raw_response, dict) and raw_response.get('success'):
                # Handle dictionary response
                properties = raw_response['data'].get('properties', [])
                total_count = raw_response['data'].get('total_count', 0)
                print(f"Response data keys: {list(raw_response['data'].keys())}")
            else:
                properties = []
                total_count = 0
                print(f"Response failed or unexpected format: {type(raw_response)}")
            
            print(f"Extracted {len(properties)} properties from {total_count} total found")
            
            # Debug: Print first property if available
            if properties:
                print(f"First property sample: {properties[0]}")
                return {
                    'success': True,
                    'properties': properties,
                    'total_count': len(properties),
                    'source_websites': selected_websites
                }
            else:
                # Enhanced error message with debugging info
                error_msg = f"""No properties extracted despite finding {total_count} listings.
                
                POSSIBLE CAUSES:
                1. Website structure changed - extraction schema doesn't match
                2. Website blocking or requiring interaction (captcha, login)
                3. Properties don't match specified criteria too strictly
                4. Extraction prompt needs refinement for this website
                
                SUGGESTIONS:
                - Try different websites (Zillow, Realtor.com, Trulia, Homes.com)
                - Broaden search criteria (Any bedrooms, Any type, etc.)
                - Check if website requires specific user interaction
                
                Debug Info: Found {total_count} listings but extraction returned empty array."""
                
                return {"error": error_msg}
                
        except Exception as e:
            return {"error": f"Firecrawl extraction failed: {str(e)}"}

def create_sequential_agents(llm, user_criteria):
    """Create agents for sequential manual execution"""
    
    property_search_agent = Agent(
        name="Property Search Agent",
        model=llm,
        instructions="""
        You are a property search expert. Your role is to find and extract property listings.
        
        WORKFLOW:
        1. SEARCH FOR PROPERTIES:
           - Use the provided Firecrawl data to extract property listings
           - Focus on properties matching user criteria
           - Extract detailed property information
        
        2. EXTRACT PROPERTY DATA:
           - Address, price, bedrooms, bathrooms, square footage
           - Property type, features, listing URLs
           - Agent contact information
        
        3. PROVIDE STRUCTURED OUTPUT:
           - List properties with complete details
           - Include all listing URLs
           - Rank by match quality to user criteria
        
        IMPORTANT: 
        - Focus ONLY on finding and extracting property data
        - Do NOT provide market analysis or valuations
        - Your output will be used by other agents for analysis
        """,
    )
    
    market_analysis_agent = Agent(
        name="Market Analysis Agent",
        model=llm,
        instructions="""
        You are a market analysis expert. Provide CONCISE market insights.
        
        REQUIREMENTS:
        - Keep analysis brief and to the point
        - Focus on key market trends only
        - Provide 2-3 bullet points per area
        - Avoid repetition and lengthy explanations
        
        COVER:
        1. Market Condition: Buyer's/seller's market, price trends
        2. Key Neighborhoods: Brief overview of areas where properties are located
        3. Investment Outlook: 2-3 key points about investment potential
        
        FORMAT: Use bullet points and keep each section under 100 words.
        """,
    )
    
    property_valuation_agent = Agent(
        name="Property Valuation Agent",
        model=llm,
        instructions="""
        You are a property valuation expert. Provide CONCISE property assessments.
        
        REQUIREMENTS:
        - Keep each property assessment brief (2-3 sentences max)
        - Focus on key points only: value, investment potential, recommendation
        - Avoid lengthy analysis and repetition
        - Use bullet points for clarity
        
        FOR EACH PROPERTY, PROVIDE:
        1. Value Assessment: Fair price, over/under priced
        2. Investment Potential: High/Medium/Low with brief reason
        3. Key Recommendation: One actionable insight
        
        FORMAT: 
        - Use bullet points
        - Keep each property under 50 words
        - Focus on actionable insights only
        """,
    )
    
    return property_search_agent, market_analysis_agent, property_valuation_agent
