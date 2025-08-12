import streamlit as st
from analysis import extract_property_valuation
from config import DEFAULT_OPENAI_API_KEY, DEFAULT_FIRECRAWL_API_KEY, AVAILABLE_WEBSITES, DEFAULT_WEBSITES

def display_properties_professionally(properties, market_analysis, property_valuations, total_properties):
    """Display properties in a clean, professional UI using Streamlit components"""
    
    # Header with key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Properties Found", total_properties)
    with col2:
        # Calculate average price
        prices = []
        for p in properties:
            price_str = p.get('price', '') if isinstance(p, dict) else getattr(p, 'price', '')
            if price_str and price_str != 'Price not available':
                try:
                    price_num = ''.join(filter(str.isdigit, str(price_str)))
                    if price_num:
                        prices.append(int(price_num))
                except:
                    pass
        avg_price = f"${sum(prices) // len(prices):,}" if prices else "N/A"
        st.metric("Average Price", avg_price)
    with col3:
        types = {}
        for p in properties:
            t = p.get('property_type', 'Unknown') if isinstance(p, dict) else getattr(p, 'property_type', 'Unknown')
            types[t] = types.get(t, 0) + 1
        most_common = max(types.items(), key=lambda x: x[1])[0] if types else "N/A"
        st.metric("Most Common Type", most_common)
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["🏠 Properties", "📊 Market Analysis", "💰 Valuations"])
    
    with tab1:
        for i, prop in enumerate(properties, 1):
            # Extract property data
            data = {k: prop.get(k, '') if isinstance(prop, dict) else getattr(prop, k, '') 
                   for k in ['address', 'price', 'property_type', 'bedrooms', 'bathrooms', 'square_feet', 'description', 'listing_url']}
            
            with st.container():
                # Property header with number and price
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"#{i} 🏠 {data['address']}")
                with col2:
                    st.metric("Price", data['price'])
                
                # Property details with right-aligned button
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.markdown(f"**Type:** {data['property_type']}")
                    st.markdown(f"**Beds/Baths:** {data['bedrooms']}/{data['bathrooms']}")
                    st.markdown(f"**Area:** {data['square_feet']}")
                with col2:
                    with st.expander("💰 Investment Analysis"):
                        # Extract property-specific valuation from the full analysis
                        property_valuation = extract_property_valuation(property_valuations, i, data['address'])
                        if property_valuation:
                            st.markdown(property_valuation)
                        else:
                            st.info("Investment analysis not available for this property")
                with col3:
                    if data['listing_url'] and data['listing_url'] != '#':
                        st.markdown(
                            f"""
                            <div style="height: 100%; display: flex; align-items: center; justify-content: flex-end;">
                                <a href="{data['listing_url']}" target="_blank" 
                                   style="text-decoration: none; padding: 0.5rem 1rem; 
                                   background-color: #0066cc; color: white; 
                                   border-radius: 6px; font-size: 0.9em; font-weight: 500;">
                                    Property Link
                                </a>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                
                st.divider()
    
    with tab2:
        st.subheader("📊 Market Analysis")
        if market_analysis:
            for section in market_analysis.split('\n\n'):
                if section.strip():
                    st.markdown(section)
        else:
            st.info("No market analysis available")
    
    with tab3:
        st.subheader("💰 Investment Analysis")
        if property_valuations:
            for section in property_valuations.split('\n\n'):
                if section.strip():
                    st.markdown(section)
        else:
            st.info("No valuation data available")

def render_sidebar():
    """Render the sidebar with configuration options"""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key inputs with validation
        with st.expander("🔑 API Keys", expanded=True):
            openai_key = st.text_input(
                "OpenAI API Key", 
                value=DEFAULT_OPENAI_API_KEY, 
                type="password",
                help="Get your API key from https://platform.openai.com/api-keys",
                placeholder="sk-..."
            )
            firecrawl_key = st.text_input(
                "Firecrawl API Key", 
                value=DEFAULT_FIRECRAWL_API_KEY, 
                type="password",
                help="Get your API key from https://firecrawl.dev",
                placeholder="fc_..."
            )
            
            # Update environment variables
            if openai_key: 
                import os
                os.environ["OPENAI_API_KEY"] = openai_key
            if firecrawl_key: 
                import os
                os.environ["FIRECRAWL_API_KEY"] = firecrawl_key
        
        # Website selection
        with st.expander("🌐 Search Sources", expanded=True):
            st.markdown("**Select real estate websites to search:**")
            selected_websites = [site for site in AVAILABLE_WEBSITES if st.checkbox(site, value=site in DEFAULT_WEBSITES)]
            
            if selected_websites:
                st.markdown(f'✅ {len(selected_websites)} sources selected</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-error">⚠️ Please select at least one website</div>', unsafe_allow_html=True)
        
        # How it works
        with st.expander("🤖 How It Works", expanded=False):
            st.markdown("**🔍 Property Search Agent**")
            st.markdown("Uses direct Firecrawl integration to find properties")
            
            st.markdown("**📊 Market Analysis Agent**")
            st.markdown("Analyzes market trends and neighborhood insights")
            
            st.markdown("**💰 Property Valuation Agent**")
            st.markdown("Evaluates properties and provides investment analysis")
    
    return openai_key, firecrawl_key, selected_websites

def render_property_form():
    """Render the main property search form"""
    st.header("Your Property Requirements")
    st.info("Please provide the location, budget, and property details to help us find your ideal home.")
    
    with st.form("property_preferences"):
        # Location and Budget Section
        st.markdown("### 📍 Location & Budget")
        col1, col2 = st.columns(2)
        
        with col1:
            city = st.text_input(
                "🏙️ City", 
                placeholder="e.g., San Francisco",
                help="Enter the city where you want to buy property"
            )
            state = st.text_input(
                "🗺️ State/Province (optional)", 
                placeholder="e.g., CA",
                help="Enter the state or province (optional)"
            )
        
        with col2:
            min_price = st.number_input(
                "💰 Minimum Price ($)", 
                min_value=0, 
                value=500000, 
                step=50000,
                help="Your minimum budget for the property"
            )
            max_price = st.number_input(
                "💰 Maximum Price ($)", 
                min_value=0, 
                value=1500000, 
                step=50000,
                help="Your maximum budget for the property"
            )
        
        # Property Details Section
        st.markdown("### 🏡 Property Details")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            property_type = st.selectbox(
                "🏠 Property Type",
                ["Any", "House", "Condo", "Townhouse", "Apartment"],
                help="Type of property you're looking for"
            )
            bedrooms = st.selectbox(
                "🛏️ Bedrooms",
                ["Any", "1", "2", "3", "4", "5+"],
                help="Number of bedrooms required"
            )
        
        with col2:
            bathrooms = st.selectbox(
                "🚿 Bathrooms",
                ["Any", "1", "1.5", "2", "2.5", "3", "3.5", "4+"],
                help="Number of bathrooms required"
            )
            min_sqft = st.number_input(
                "📏 Minimum Square Feet",
                min_value=0,
                value=1000,
                step=100,
                help="Minimum square footage required"
            )
        
        with col3:
            timeline = st.selectbox(
                "⏰ Timeline",
                ["Flexible", "1-3 months", "3-6 months", "6+ months"],
                help="When do you plan to buy?"
            )
            urgency = st.selectbox(
                "🚨 Urgency",
                ["Not urgent", "Somewhat urgent", "Very urgent"],
                help="How urgent is your purchase?"
            )
        
        # Special Features
        st.markdown("### ✨ Special Features")
        special_features = st.text_area(
            "🎯 Special Features & Requirements",
            placeholder="e.g., Parking, Yard, View, Near public transport, Good schools, Walkable neighborhood, etc.",
            help="Any specific features or requirements you're looking for"
        )
        
        # Submit button with custom styling
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "🚀 Start Property Analysis",
                type="primary",
                use_container_width=True
            )
        
        return submitted, {
            'city': city,
            'state': state,
            'min_price': min_price,
            'max_price': max_price,
            'property_type': property_type,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'min_sqft': min_sqft,
            'timeline': timeline,
            'urgency': urgency,
            'special_features': special_features
        }

def render_progress_section():
    """Render the progress tracking section"""
    st.markdown("#### Property Analysis in Progress")
    st.info("AI Agents are searching for your perfect home...")
    
    status_container = st.container()
    with status_container:
        st.markdown("### 📊 Current Activity")
        progress_bar = st.progress(0)
        current_activity = st.empty()
    
    def update_progress(progress, status, activity=None):
        if activity:
            progress_bar.progress(progress)
            current_activity.text(activity)
    
    return update_progress
