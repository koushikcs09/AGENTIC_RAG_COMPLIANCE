
"""
Main Streamlit application for the Agentic Compliance-Mapping System.
AI-powered compliance mapping for Australian mining regulations.
"""

import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Import custom modules
from config import config
from api_client import mock_api_client  # Using mock client for demonstration
from utils import (
    validate_uploaded_file, format_file_size, create_compliance_summary_chart,
    create_risk_level_chart, create_compliance_score_gauge, format_compliance_mappings_table,
    display_progress_bar, display_audit_checklist, create_recommendations_display,
    display_metrics_row, export_to_excel, create_download_link
)

# Page configuration
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-org/compliance-mapping',
        'Report a bug': 'https://github.com/your-org/compliance-mapping/issues',
        'About': f"""
        # {config.APP_TITLE}
        
        {config.APP_DESCRIPTION}
        
        Version: 1.0.0
        
        This application helps compliance officers and legal teams analyze vendor contracts 
        against Australian mining regulations using AI-powered mapping technology.
        """
    }
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4 0%, #17a2b8 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .upload-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px dashed #dee2e6;
        margin: 1rem 0;
    }
    
    .status-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .compliance-flag-compliant {
        background-color: #d4edda;
        color: #155724;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-weight: bold;
    }
    
    .compliance-flag-partial {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-weight: bold;
    }
    
    .compliance-flag-non-compliant {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-weight: bold;
    }
    
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .download-section {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 'upload'
    if 'uploaded_document' not in st.session_state:
        st.session_state.uploaded_document = None
    if 'analysis_id' not in st.session_state:
        st.session_state.analysis_id = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = None

def render_header():
    """Render the main application header."""
    st.markdown(f"""
    <div class="main-header">
        <h1>⚖️ {config.APP_TITLE}</h1>
        <p>{config.APP_DESCRIPTION}</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar with navigation and information."""
    with st.sidebar:
        st.image("https://i.ytimg.com/vi/xIc6Cz-6Zak/maxresdefault.jpg", caption="Australian Mining Compliance")
        
        st.markdown("## 📋 Process Steps")
        
        steps = [
            ("📄 Upload Document", "upload"),
            ("⚙️ Process & Analyze", "analyze"),
            ("📊 View Results", "results"),
            ("📥 Download Reports", "download")
        ]
        
        for step_name, step_key in steps:
            if st.session_state.current_step == step_key:
                st.markdown(f"**➤ {step_name}**")
            else:
                st.markdown(f"   {step_name}")
        
        st.markdown("---")
        
        st.markdown("## 🎯 Key Features")
        st.markdown("""
        - **PDF Document Upload** with validation
        - **Real-time Processing** status tracking
        - **Compliance Mapping** against Australian mining regulations
        - **AI-Generated Audit Checklist** 
        - **Multi-format Downloads** (PDF, Excel, CSV)
        - **Risk Assessment** and recommendations
        """)
        
        st.markdown("---")
        
        # System status
        st.markdown("## 🔧 System Status")
        try:
            health = mock_api_client.health_check()
            if health.get("success"):
                st.success("✅ Backend Connected")
            else:
                st.error("❌ Backend Unavailable")
        except:
            st.error("❌ Connection Error")
        
        st.markdown("---")
        
        st.markdown("## 📞 Support")
        st.markdown("""
        For technical support or questions:
        - 📧 Email: support@compliance-mapping.com
        - 📱 Phone: +61 2 9999 0000
        - 🌐 Web: compliance-mapping.com
        """)

def render_upload_section():
    """Render the document upload section."""
    st.markdown("## 📄 Document Upload")
    
    with st.container():
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        
        st.markdown("### Upload Vendor Contract PDF")
        st.markdown("Upload your vendor contract PDF for compliance analysis against Australian mining regulations.")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            accept_multiple_files=False,
            help=f"Maximum file size: {config.MAX_FILE_SIZE_MB}MB"
        )
        
        if uploaded_file is not None:
            # Validate file
            validation = validate_uploaded_file(uploaded_file)
            
            if validation["valid"]:
                st.success(f"✅ File validated successfully!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**Filename:** {validation['filename']}")
                with col2:
                    st.info(f"**Size:** {validation['size_mb']} MB")
                with col3:
                    st.info(f"**Type:** PDF Document")
                
                # Upload button
                if st.button("🚀 Upload & Start Analysis", type="primary", use_container_width=True):
                    with st.spinner("Uploading document..."):
                        # Upload document
                        upload_result = mock_api_client.upload_document(
                            uploaded_file.getvalue(),
                            uploaded_file.name,
                            "vendor_contract"
                        )
                        
                        if upload_result.get("success"):
                            st.session_state.uploaded_document = upload_result["data"]
                            
                            # Trigger analysis
                            analysis_result = mock_api_client.trigger_analysis(
                                upload_result["data"]["document_id"],
                                "full_compliance"
                            )
                            
                            if analysis_result.get("success"):
                                st.session_state.analysis_id = analysis_result["data"]["analysis_id"]
                                st.session_state.current_step = "analyze"
                                st.rerun()
                            else:
                                st.error(f"Failed to start analysis: {analysis_result.get('error', {}).get('message', 'Unknown error')}")
                        else:
                            st.error(f"Upload failed: {upload_result.get('error', {}).get('message', 'Unknown error')}")
            
            else:
                st.error(f"❌ File validation failed: {validation['error']}")
        
        st.markdown('</div>', unsafe_allow_html=True)

def render_analysis_section():
    """Render the analysis processing section."""
    st.markdown("## ⚙️ Document Analysis")
    
    if not st.session_state.analysis_id:
        st.error("No analysis in progress. Please upload a document first.")
        if st.button("← Back to Upload"):
            st.session_state.current_step = "upload"
            st.rerun()
        return
    
    st.markdown('<div class="status-card">', unsafe_allow_html=True)
    st.markdown(f"**Document:** {st.session_state.uploaded_document.get('filename', 'Unknown')}")
    st.markdown(f"**Analysis ID:** {st.session_state.analysis_id}")
    
    # Progress tracking
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Poll for results
    max_attempts = 30  # 30 attempts with 2-second intervals = 60 seconds max
    attempt = 0
    
    while attempt < max_attempts:
        result = mock_api_client.get_analysis_results(st.session_state.analysis_id)
        
        if result.get("success"):
            data = result["data"]
            status = data.get("status", "unknown")
            progress = data.get("progress", 0)
            
            # Update progress display
            with progress_placeholder.container():
                progress_bar = st.progress(progress / 100)
                
            with status_placeholder.container():
                if status == "processing":
                    st.info(f"🔄 Processing... ({progress}%)")
                elif status == "completed":
                    st.success("✅ Analysis completed successfully!")
                    st.session_state.analysis_results = data.get("results", {})
                    st.session_state.current_step = "results"
                    time.sleep(1)  # Brief pause before redirect
                    st.rerun()
                elif status == "failed":
                    st.error("❌ Analysis failed. Please try again.")
                    break
                else:
                    st.warning(f"Status: {status}")
            
            if status in ["completed", "failed"]:
                break
        
        time.sleep(2)
        attempt += 1
    
    if attempt >= max_attempts:
        st.error("⏱️ Analysis timeout. Please try again.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Upload"):
            st.session_state.current_step = "upload"
            st.rerun()
    with col2:
        if st.session_state.analysis_results:
            if st.button("View Results →"):
                st.session_state.current_step = "results"
                st.rerun()

def render_results_section():
    """Render the analysis results section."""
    st.markdown("## 📊 Compliance Analysis Results")
    
    if not st.session_state.analysis_results:
        st.error("No analysis results available. Please run an analysis first.")
        if st.button("← Back to Upload"):
            st.session_state.current_step = "upload"
            st.rerun()
        return
    
    results = st.session_state.analysis_results
    
    # Display key metrics
    st.markdown("### 📈 Key Metrics")
    display_metrics_row(results)
    
    # Charts section
    st.markdown("### 📊 Visual Summary")
    col1, col2 = st.columns(2)
    
    with col1:
        compliance_chart = create_compliance_summary_chart(results)
        st.plotly_chart(compliance_chart, use_container_width=True)
    
    with col2:
        risk_chart = create_risk_level_chart(results)
        st.plotly_chart(risk_chart, use_container_width=True)
    
    # Overall compliance score gauge
    st.markdown("### 🎯 Overall Compliance Score")
    gauge_chart = create_compliance_score_gauge(results.get("overall_compliance_score", 0))
    st.plotly_chart(gauge_chart, use_container_width=True)
    
    # Compliance mappings table
    st.markdown("### 📋 Detailed Compliance Mappings")
    if "compliance_mappings" in results and results["compliance_mappings"]:
        mappings_df = format_compliance_mappings_table(results["compliance_mappings"])
        
        # Add search/filter functionality
        search_term = st.text_input("🔍 Search mappings:", placeholder="Enter keywords to filter results...")
        
        if search_term:
            mask = mappings_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
            filtered_df = mappings_df[mask]
        else:
            filtered_df = mappings_df
        
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        # Detailed view expander
        with st.expander("🔍 View Detailed Mappings"):
            for i, mapping in enumerate(results["compliance_mappings"]):
                st.markdown(f"#### {i+1}. {mapping.get('tc_reference', 'N/A')}")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Vendor Clause:** {mapping.get('vendor_clause', 'N/A')}")
                    st.markdown(f"**Suggested Action:** {mapping.get('suggested_action', 'N/A')}")
                    
                    # Regulation references
                    if mapping.get('regulation_references'):
                        st.markdown("**Relevant Regulations:**")
                        for ref in mapping['regulation_references']:
                            st.markdown(f"- {ref}")
                
                with col2:
                    flag = mapping.get('compliance_flag', 'N/A')
                    score = mapping.get('compliance_score', 0)
                    risk = mapping.get('risk_level', 'unknown').title()
                    
                    st.markdown(f"**Status:** {flag}")
                    st.markdown(f"**Score:** {score:.0%}")
                    st.markdown(f"**Risk:** {risk}")
                
                st.markdown("---")
    
    else:
        st.warning("No compliance mappings available in results.")
    
    # Audit checklist
    if "audit_checklist" in results:
        display_audit_checklist(results["audit_checklist"])
    
    # Recommendations
    if "recommendations" in results:
        create_recommendations_display(results["recommendations"])
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Analysis"):
            st.session_state.current_step = "analyze"
            st.rerun()
    with col2:
        if st.button("Download Reports →"):
            st.session_state.current_step = "download"
            st.rerun()

def render_download_section():
    """Render the download section."""
    st.markdown("## 📥 Download Reports")
    
    if not st.session_state.analysis_results:
        st.error("No results available for download. Please run an analysis first.")
        return
    
    results = st.session_state.analysis_results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    st.markdown('<div class="download-section">', unsafe_allow_html=True)
    
    st.markdown("### Available Download Formats")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📊 Excel Report")
        st.markdown("Complete compliance report with all mappings, recommendations, and audit checklist.")
        
        # Generate Excel file
        excel_buffer = export_to_excel(results, f"compliance_report_{timestamp}.xlsx")
        
        st.download_button(
            label="📊 Download Excel Report",
            data=excel_buffer.getvalue(),
            file_name=f"compliance_report_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col2:
        st.markdown("#### 📄 CSV Data")
        st.markdown("Compliance mappings in CSV format for further analysis.")
        
        if "compliance_mappings" in results:
            mappings_df = format_compliance_mappings_table(results["compliance_mappings"])
            csv_data = mappings_df.to_csv(index=False)
            
            st.download_button(
                label="📄 Download CSV Data",
                data=csv_data,
                file_name=f"compliance_mappings_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col3:
        st.markdown("#### 📋 JSON Report")
        st.markdown("Full results in JSON format for integration with other systems.")
        
        json_data = json.dumps(results, indent=2)
        
        st.download_button(
            label="📋 Download JSON Report",
            data=json_data,
            file_name=f"compliance_results_{timestamp}.json",
            mime="application/json",
            use_container_width=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Summary section
    st.markdown("### 📈 Report Summary")
    
    summary_col1, summary_col2 = st.columns(2)
    
    with summary_col1:
        st.markdown("**Report Contents:**")
        st.markdown("- Detailed compliance mappings")
        st.markdown("- Risk assessment and scoring")
        st.markdown("- AI-generated audit checklist")
        st.markdown("- Actionable recommendations")
        st.markdown("- Regulatory references")
    
    with summary_col2:
        st.markdown("**Key Statistics:**")
        mappings_count = len(results.get("compliance_mappings", []))
        overall_score = results.get("overall_compliance_score", 0)
        high_risk = results.get("risk_summary", {}).get("high_risk_items", 0)
        
        st.markdown(f"- **Total Mappings:** {mappings_count}")
        st.markdown(f"- **Overall Score:** {overall_score:.0%}")
        st.markdown(f"- **High Risk Items:** {high_risk}")
        st.markdown(f"- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Navigation
    if st.button("← Back to Results"):
        st.session_state.current_step = "results"
        st.rerun()

def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # Render header
    render_header()
    
    # Create main layout
    col1, col2 = st.columns([1, 4])
    
    with col1:
        render_sidebar()
    
    with col2:
        # Render appropriate section based on current step
        if st.session_state.current_step == "upload":
            render_upload_section()
        elif st.session_state.current_step == "analyze":
            render_analysis_section()
        elif st.session_state.current_step == "results":
            render_results_section()
        elif st.session_state.current_step == "download":
            render_download_section()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; padding: 1rem;'>"
        f"© 2025 {config.APP_TITLE} | Version 1.0.0 | "
        "Powered by AI for Australian Mining Compliance"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
