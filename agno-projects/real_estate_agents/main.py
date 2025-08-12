import streamlit as st
import time
from ui import (
    render_sidebar, 
    render_property_form, 
    render_progress_section,
    display_properties_professionally
)
from analysis import run_sequential_analysis

def main():
    st.set_page_config(
        page_title="AI Real Estate Agent Team", 
        page_icon="🏠", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Clean header
    st.title("🏠 AI Real Estate Agent Team")
    st.caption("Find Your Dream Home with Specialized AI Agents")
    
    # Render sidebar and get configuration
    openai_key, firecrawl_key, selected_websites = render_sidebar()
    
    # Render property form
    submitted, form_data = render_property_form()
    
    # Process form submission
    if submitted:
        # Validate all required inputs
        missing_items = []
        if not openai_key:
            missing_items.append("OpenAI API Key")
        if not firecrawl_key:
            missing_items.append("Firecrawl API Key")
        if not form_data['city']:
            missing_items.append("City")
        if not selected_websites:
            missing_items.append("At least one website selection")
        
        if missing_items:
            st.markdown(f"""
            <div class="status-error" style="text-align: center; margin: 2rem 0;">
                ⚠️ Please provide: {', '.join(missing_items)}
            </div>
            """, unsafe_allow_html=True)
            return
        
        try:
            user_criteria = {
                'budget_range': f"${form_data['min_price']:,} - ${form_data['max_price']:,}",
                'property_type': form_data['property_type'],
                'bedrooms': form_data['bedrooms'],
                'bathrooms': form_data['bathrooms'],
                'min_sqft': form_data['min_sqft'],
                'special_features': form_data['special_features'] if form_data['special_features'] else 'None specified'
            }
            
        except Exception as e:
            st.markdown(f"""
            <div class="status-error" style="text-align: center; margin: 2rem 0;">
                ❌ Error initializing: {str(e)}
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Render progress section
        update_progress = render_progress_section()
        
        try:
            start_time = time.time()
            update_progress(0.1, "Initializing...", "Starting sequential property analysis")
            
            # Run sequential analysis with manual coordination
            final_result = run_sequential_analysis(
                city=form_data['city'],
                state=form_data['state'],
                user_criteria=user_criteria,
                selected_websites=selected_websites,
                firecrawl_api_key=firecrawl_key,
                openai_api_key=openai_key,
                update_callback=update_progress
            )
            
            total_time = time.time() - start_time
            
            # Display results
            if isinstance(final_result, dict):
                # Use the new professional display
                display_properties_professionally(
                    final_result['properties'],
                    final_result['market_analysis'],
                    final_result['property_valuations'],
                    final_result['total_properties']
                )
            else:
                # Fallback to markdown display
                st.markdown("### 🏠 Comprehensive Real Estate Analysis")
                st.markdown(final_result)
            
            # Timing info in a subtle way
            st.caption(f"Analysis completed in {total_time:.1f}s")
            
        except Exception as e:
            st.markdown(f"""
            <div class="status-error" style="text-align: center; margin: 2rem 0;">
                ❌ An error occurred: {str(e)}
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
