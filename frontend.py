"""
X-Ray Dashboard - Streamlit Frontend for X-Ray API
"""
import streamlit as st
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


# Page configuration
st.set_page_config(
    page_title="X-Ray Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .step-card {
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f8f9fa;
    }
    </style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'api_url' not in st.session_state:
        st.session_state.api_url = "http://localhost:8000"
    if 'execution_id' not in st.session_state:
        st.session_state.execution_id = None
    if 'current_trail' not in st.session_state:
        st.session_state.current_trail = None


def make_api_request(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """Make API request and handle errors"""
    try:
        url = f"{st.session_state.api_url}{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Could not connect to API at {st.session_state.api_url}. Make sure the server is running.")
        return None
    except requests.exceptions.Timeout:
        st.error("❌ Request timed out. Please try again.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ HTTP Error: {e}")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None


def get_trail(execution_id: str) -> Optional[Dict]:
    """Get trail by execution ID"""
    return make_api_request(f"/xray/trail/{execution_id}")


def list_trails(limit: int = 10) -> Optional[List[Dict]]:
    """List all trails"""
    result = make_api_request("/xray/trails", params={"limit": limit})
    if result:
        return result.get("trails", [])
    return None


def call_related_products(keywords: str, price: float) -> Optional[Dict]:
    """Call the related-products endpoint"""
    return make_api_request(
        "/related-products",
        params={"keywords": keywords, "price": price}
    )


def format_timestamp(timestamp_str: str) -> str:
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str


def render_step_card(step: Dict, step_num: int):
    """Render a step card with all details"""
    with st.expander(f"Step {step_num}: {step['step_name'].replace('_', ' ').title()}", expanded=step_num == 1):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Step ID:** `{step['step_id']}`")
            st.markdown(f"**Timestamp:** {format_timestamp(step['timestamp'])}")
        
        with col2:
            if step.get('reasoning'):
                st.markdown(f"**Reasoning:** {step['reasoning']}")
        
        # Inputs
        if step.get('inputs'):
            st.markdown("#### 📥 Inputs")
            st.json(step['inputs'])
        
        # Candidates
        if step.get('candidates'):
            st.markdown(f"#### 🎯 Candidates ({len(step['candidates'])})")
            candidates_df = pd.DataFrame(step['candidates'])
            st.dataframe(candidates_df, use_container_width=True)
            
            # Visualize candidates if they have numeric fields
            if 'price' in candidates_df.columns:
                fig = px.bar(
                    candidates_df,
                    x='id',
                    y='price',
                    title="Candidate Prices",
                    labels={'id': 'Product ID', 'price': 'Price ($)'}
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        
        # Filters
        if step.get('filters_applied'):
            st.markdown("#### 🔍 Filters Applied")
            for filter_data in step['filters_applied']:
                with st.container():
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Filter Name", filter_data['name'])
                    with col2:
                        st.metric("Passed", filter_data.get('passed_count', 0))
                    with col3:
                        st.metric("Rejected", filter_data.get('rejected_count', 0))
                    
                    if filter_data.get('config'):
                        st.json(filter_data['config'])
                    
                    if filter_data.get('reasoning'):
                        st.info(f"💡 {filter_data['reasoning']}")
                    
                    # Show passed/rejected items
                    if filter_data.get('passed'):
                        with st.expander("✅ Passed Items"):
                            st.json(filter_data['passed'])
                    
                    if filter_data.get('rejected'):
                        with st.expander("❌ Rejected Items"):
                            rejected_df = pd.DataFrame(filter_data['rejected'])
                            st.dataframe(rejected_df, use_container_width=True)
        
        # Outcomes
        if step.get('outcomes'):
            st.markdown("#### 📊 Outcomes")
            st.json(step['outcomes'])


def render_trail_dashboard(trail: Dict):
    """Render the main trail dashboard"""
    st.markdown(f"<div class='main-header'>🔍 X-Ray Decision Trail</div>", unsafe_allow_html=True)
    
    # Header metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Execution ID", trail['execution_id'][:8] + "...")
    with col2:
        st.metric("Total Steps", trail['total_steps'])
    with col3:
        st.metric("Created At", format_timestamp(trail['created_at']))
    with col4:
        if trail.get('metadata'):
            endpoint = trail['metadata'].get('endpoint', 'N/A')
            st.metric("Endpoint", endpoint)
    
    # Metadata
    if trail.get('metadata'):
        st.markdown("#### 📋 Execution Metadata")
        st.json(trail['metadata'])
    
    # Steps overview
    st.markdown("---")
    st.markdown("## 📈 Steps Overview")
    
    # Step timeline visualization
    steps_data = []
    for i, step in enumerate(trail['steps'], 1):
        steps_data.append({
            'Step': f"Step {i}",
            'Name': step['step_name'].replace('_', ' ').title(),
            'Candidates': len(step.get('candidates', [])),
            'Filters': len(step.get('filters_applied', [])),
            'Has Outcomes': 1 if step.get('outcomes') else 0
        })
    
    steps_df = pd.DataFrame(steps_data)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            steps_df,
            x='Step',
            y='Candidates',
            title="Candidates per Step",
            color='Candidates',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            steps_df,
            x='Step',
            y='Filters',
            title="Filters Applied per Step",
            color='Filters',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed steps
    st.markdown("---")
    st.markdown("## 🔬 Detailed Steps")
    
    for i, step in enumerate(trail['steps'], 1):
        render_step_card(step, i)
    
    # Summary statistics
    st.markdown("---")
    st.markdown("## 📊 Summary Statistics")
    
    # Collect all candidates across steps
    all_candidates = []
    for step in trail['steps']:
        if step.get('candidates'):
            all_candidates.extend(step['candidates'])
    
    if all_candidates:
        candidates_df = pd.DataFrame(all_candidates)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'price' in candidates_df.columns:
                st.markdown("### Price Distribution")
                fig = px.histogram(
                    candidates_df,
                    x='price',
                    nbins=20,
                    title="Price Distribution of Candidates"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'rating' in candidates_df.columns:
                st.markdown("### Rating Distribution")
                fig = px.histogram(
                    candidates_df,
                    x='rating',
                    nbins=20,
                    title="Rating Distribution of Candidates"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Statistics table
        numeric_cols = candidates_df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            st.markdown("### Statistical Summary")
            st.dataframe(candidates_df[numeric_cols].describe(), use_container_width=True)


def main():
    """Main application"""
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        api_url = st.text_input(
            "API URL",
            value=st.session_state.api_url,
            help="Base URL of your FastAPI server"
        )
        st.session_state.api_url = api_url
        
        st.markdown("---")
        st.markdown("## 🚀 Quick Actions")
        
        if st.button("🔄 Refresh Trails List"):
            st.rerun()
        
        st.markdown("---")
        st.markdown("## 📝 Make New Request")
        
        with st.form("new_request_form"):
            keywords = st.text_input("Keywords", value="water,bottle", help="Comma-separated keywords")
            price = st.number_input("Price", value=29.99, min_value=0.01, step=0.01)
            
            if st.form_submit_button("🚀 Call API"):
                with st.spinner("Calling API..."):
                    result = call_related_products(keywords, price)
                    if result:
                        st.session_state.execution_id = result.get('execution_id')
                        st.success(f"✅ Request successful! Execution ID: {st.session_state.execution_id[:8]}...")
                        st.rerun()
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["🔍 View Trail", "📋 List All Trails", "📊 Analytics"])
    
    # Tab 1: View Trail
    with tab1:
        st.markdown("## View Decision Trail")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            execution_id = st.text_input(
                "Execution ID",
                value=st.session_state.execution_id or "",
                placeholder="Enter execution ID or select from list",
                help="Enter an execution ID to view its trail"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔍 Load Trail", type="primary"):
                if execution_id:
                    with st.spinner("Loading trail..."):
                        trail = get_trail(execution_id)
                        if trail:
                            st.session_state.current_trail = trail
                            st.session_state.execution_id = execution_id
                            st.success("✅ Trail loaded successfully!")
                        else:
                            st.error("❌ Trail not found")
                else:
                    st.warning("⚠️ Please enter an execution ID")
        
        # Display trail if available
        if st.session_state.current_trail:
            render_trail_dashboard(st.session_state.current_trail)
        elif st.session_state.execution_id:
            # Try to load if we have an execution_id
            trail = get_trail(st.session_state.execution_id)
            if trail:
                st.session_state.current_trail = trail
                render_trail_dashboard(trail)
    
    # Tab 2: List All Trails
    with tab2:
        st.markdown("## All Decision Trails")
        
        limit = st.number_input("Limit", value=20, min_value=1, max_value=100, step=5)
        
        if st.button("🔄 Load Trails"):
            with st.spinner("Loading trails..."):
                trails = list_trails(limit=limit)
                if trails:
                    st.session_state.trails_list = trails
                    st.success(f"✅ Loaded {len(trails)} trails")
                else:
                    st.error("❌ Could not load trails")
        
        if 'trails_list' in st.session_state and st.session_state.trails_list:
            trails = st.session_state.trails_list
            
            st.markdown(f"### Found {len(trails)} trails")
            
            # Create trails dataframe
            trails_data = []
            for trail in trails:
                trails_data.append({
                    'Execution ID': trail['execution_id'],
                    'Created At': format_timestamp(trail['created_at']),
                    'Total Steps': trail['total_steps'],
                    'Endpoint': trail.get('metadata', {}).get('endpoint', 'N/A'),
                    'Keywords': trail.get('metadata', {}).get('keywords', 'N/A'),
                    'Price': trail.get('metadata', {}).get('price', 'N/A')
                })
            
            trails_df = pd.DataFrame(trails_data)
            st.dataframe(trails_df, use_container_width=True)
            
            # Trail selection
            st.markdown("### Select Trail to View")
            selected_idx = st.selectbox(
                "Choose a trail",
                range(len(trails)),
                format_func=lambda x: f"{trails[x]['execution_id'][:8]}... - {format_timestamp(trails[x]['created_at'])}"
            )
            
            if st.button("👁️ View Selected Trail"):
                selected_trail = trails[selected_idx]
                st.session_state.execution_id = selected_trail['execution_id']
                st.session_state.current_trail = selected_trail
                st.rerun()
    
    # Tab 3: Analytics
    with tab3:
        st.markdown("## Analytics Dashboard")
        
        limit = st.number_input("Trails to Analyze", value=10, min_value=1, max_value=50, step=5, key="analytics_limit")
        
        if st.button("📊 Generate Analytics", type="primary"):
            with st.spinner("Loading trails for analysis..."):
                trails = list_trails(limit=limit)
                if trails:
                    # Overall statistics
                    st.markdown("### Overall Statistics")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    total_trails = len(trails)
                    total_steps = sum(t.get('total_steps', 0) for t in trails)
                    avg_steps = total_steps / total_trails if total_trails > 0 else 0
                    
                    with col1:
                        st.metric("Total Trails", total_trails)
                    with col2:
                        st.metric("Total Steps", total_steps)
                    with col3:
                        st.metric("Avg Steps/Trail", f"{avg_steps:.2f}")
                    with col4:
                        total_candidates = sum(
                            len(step.get('candidates', []))
                            for trail in trails
                            for step in trail.get('steps', [])
                        )
                        st.metric("Total Candidates", total_candidates)
                    
                    # Steps distribution
                    st.markdown("### Steps Distribution")
                    steps_dist = {}
                    for trail in trails:
                        for step in trail.get('steps', []):
                            step_name = step['step_name']
                            steps_dist[step_name] = steps_dist.get(step_name, 0) + 1
                    
                    if steps_dist:
                        fig = px.pie(
                            values=list(steps_dist.values()),
                            names=list(steps_dist.keys()),
                            title="Step Types Distribution"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Timeline
                    st.markdown("### Execution Timeline")
                    timeline_data = []
                    for trail in trails:
                        timeline_data.append({
                            'Date': trail['created_at'][:10],
                            'Count': 1
                        })
                    
                    if timeline_data:
                        timeline_df = pd.DataFrame(timeline_data)
                        timeline_df = timeline_df.groupby('Date').sum().reset_index()
                        timeline_df['Date'] = pd.to_datetime(timeline_df['Date'])
                        timeline_df = timeline_df.sort_values('Date')
                        
                        fig = px.line(
                            timeline_df,
                            x='Date',
                            y='Count',
                            title="Trails Created Over Time",
                            markers=True
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("❌ Could not load trails for analysis")


if __name__ == "__main__":
    main()

