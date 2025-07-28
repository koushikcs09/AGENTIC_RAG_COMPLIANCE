
"""
Utility functions for the Streamlit frontend application.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import base64
from io import BytesIO
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

def validate_uploaded_file(uploaded_file) -> Dict[str, Any]:
    """Validate uploaded PDF file."""
    if uploaded_file is None:
        return {"valid": False, "error": "No file uploaded"}
    
    # Check file type
    if not uploaded_file.name.lower().endswith('.pdf'):
        return {"valid": False, "error": "Only PDF files are supported"}
    
    # Check file size (50MB limit)
    max_size = 50 * 1024 * 1024  # 50MB in bytes
    file_size = len(uploaded_file.getvalue())
    
    if file_size > max_size:
        return {"valid": False, "error": f"File too large. Maximum size is 50MB, got {file_size / (1024*1024):.1f}MB"}
    
    if file_size == 0:
        return {"valid": False, "error": "File is empty"}
    
    # Basic PDF validation
    content = uploaded_file.getvalue()
    if not content.startswith(b'%PDF-'):
        return {"valid": False, "error": "Invalid PDF format"}
    
    return {
        "valid": True,
        "filename": uploaded_file.name,
        "size": file_size,
        "size_mb": round(file_size / (1024*1024), 2)
    }

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024*1024:
        return f"{size_bytes/1024:.1f} KB"
    else:
        return f"{size_bytes/(1024*1024):.1f} MB"

def create_compliance_summary_chart(results: Dict[str, Any]) -> go.Figure:
    """Create compliance summary chart."""
    if not results or "compliance_mappings" not in results:
        return go.Figure()
    
    mappings = results["compliance_mappings"]
    
    # Count compliance flags
    flag_counts = {}
    for mapping in mappings:
        flag = mapping.get("compliance_flag", "Unknown").split(' ')[-1]  # Get the text part
        flag_counts[flag] = flag_counts.get(flag, 0) + 1
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=list(flag_counts.keys()),
        values=list(flag_counts.values()),
        hole=.3,
        marker_colors=['#2ecc71', '#f39c12', '#e74c3c', '#95a5a6'][:len(flag_counts)]
    )])
    
    fig.update_layout(
        title="Compliance Status Distribution",
        font=dict(size=12),
        height=400,
        showlegend=True
    )
    
    return fig

def create_risk_level_chart(results: Dict[str, Any]) -> go.Figure:
    """Create risk level distribution chart."""
    if not results or "compliance_mappings" not in results:
        return go.Figure()
    
    mappings = results["compliance_mappings"]
    
    # Count risk levels
    risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for mapping in mappings:
        risk_level = mapping.get("risk_level", "unknown").lower()
        if risk_level in risk_counts:
            risk_counts[risk_level] += 1
    
    # Create bar chart
    fig = go.Figure(data=[go.Bar(
        x=list(risk_counts.keys()),
        y=list(risk_counts.values()),
        marker_color=['#2ecc71', '#f39c12', '#e74c3c', '#8b0000']
    )])
    
    fig.update_layout(
        title="Risk Level Distribution",
        xaxis_title="Risk Level",
        yaxis_title="Number of Items",
        font=dict(size=12),
        height=400
    )
    
    return fig

def create_compliance_score_gauge(overall_score: float) -> go.Figure:
    """Create compliance score gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=overall_score * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Overall Compliance Score"},
        delta={'reference': 80},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def format_compliance_mappings_table(mappings: List[Dict]) -> pd.DataFrame:
    """Format compliance mappings for table display."""
    if not mappings:
        return pd.DataFrame()
    
    df_data = []
    for i, mapping in enumerate(mappings):
        df_data.append({
            "T&C Reference": mapping.get("tc_reference", "N/A"),
            "Mapped Vendor Clause": mapping.get("vendor_clause", "N/A")[:100] + "..." if len(mapping.get("vendor_clause", "")) > 100 else mapping.get("vendor_clause", "N/A"),
            "Compliance Flag": mapping.get("compliance_flag", "N/A"),
            "Score": f"{mapping.get('compliance_score', 0):.0%}",
            "Risk Level": mapping.get("risk_level", "N/A").title(),
            "Suggested Action": mapping.get("suggested_action", "N/A")
        })
    
    return pd.DataFrame(df_data)

def create_download_link(data: Any, filename: str, mime_type: str = "text/plain") -> str:
    """Create download link for data."""
    if isinstance(data, pd.DataFrame):
        if filename.endswith('.csv'):
            data_str = data.to_csv(index=False)
        elif filename.endswith('.xlsx'):
            buffer = BytesIO()
            data.to_excel(buffer, index=False)
            data_str = buffer.getvalue()
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            data_str = str(data)
    elif isinstance(data, dict):
        data_str = json.dumps(data, indent=2)
    else:
        data_str = str(data)
    
    if isinstance(data_str, str):
        data_str = data_str.encode()
    
    b64 = base64.b64encode(data_str).decode()
    href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">Download {filename}</a>'
    return href

def display_progress_bar(progress: int, status: str):
    """Display progress bar with status."""
    progress_bar = st.progress(progress / 100)
    status_text = st.empty()
    
    if status == "processing":
        status_text.text(f"Processing... ({progress}%)")
    elif status == "completed":
        status_text.text("✅ Analysis completed!")
        progress_bar.progress(100)
    elif status == "failed":
        status_text.text("❌ Analysis failed")
    else:
        status_text.text(f"Status: {status}")

def display_audit_checklist(audit_checklist: List[Dict]):
    """Display audit checklist in organized format."""
    if not audit_checklist:
        st.warning("No audit checklist available")
        return
    
    st.subheader("🔍 AI-Generated Audit Checklist")
    
    for category_data in audit_checklist:
        category = category_data.get("category", "Unknown")
        items = category_data.get("items", [])
        
        with st.expander(f"📋 {category} ({len(items)} items)"):
            for i, item in enumerate(items, 1):
                st.write(f"{i}. {item}")

def create_recommendations_display(recommendations: List[str]):
    """Display recommendations in a formatted way."""
    if not recommendations:
        return
    
    st.subheader("💡 Key Recommendations")
    
    for i, rec in enumerate(recommendations, 1):
        st.write(f"**{i}.** {rec}")

def style_compliance_flag(flag: str) -> str:
    """Apply color styling to compliance flags."""
    flag_lower = flag.lower()
    if "compliant" in flag_lower and "non" not in flag_lower and "partial" not in flag_lower:
        return f'<span style="color: green; font-weight: bold;">🟢 {flag}</span>'
    elif "partial" in flag_lower:
        return f'<span style="color: orange; font-weight: bold;">🟡 {flag}</span>'
    elif "non-compliant" in flag_lower or "requires attention" in flag_lower:
        return f'<span style="color: red; font-weight: bold;">🔴 {flag}</span>'
    else:
        return f'<span style="font-weight: bold;">{flag}</span>'

def export_to_excel(results: Dict[str, Any], filename: str = None) -> BytesIO:
    """Export results to Excel format."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"compliance_report_{timestamp}.xlsx"
    
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Compliance mappings sheet
        if "compliance_mappings" in results:
            mappings_df = format_compliance_mappings_table(results["compliance_mappings"])
            mappings_df.to_excel(writer, sheet_name='Compliance Mappings', index=False)
        
        # Summary sheet
        summary_data = {
            "Metric": ["Overall Compliance Score", "High Risk Items", "Medium Risk Items", "Low Risk Items"],
            "Value": [
                f"{results.get('overall_compliance_score', 0):.0%}",
                results.get('risk_summary', {}).get('high_risk_items', 0),
                results.get('risk_summary', {}).get('medium_risk_items', 0),
                results.get('risk_summary', {}).get('low_risk_items', 0)
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Recommendations sheet
        if "recommendations" in results:
            rec_df = pd.DataFrame({"Recommendations": results["recommendations"]})
            rec_df.to_excel(writer, sheet_name='Recommendations', index=False)
    
    buffer.seek(0)
    return buffer

def get_compliance_color(score: float) -> str:
    """Get color based on compliance score."""
    if score >= 0.9:
        return "#2ecc71"  # Green
    elif score >= 0.75:
        return "#f39c12"  # Orange
    elif score >= 0.5:
        return "#e67e22"  # Dark orange
    else:
        return "#e74c3c"  # Red

def display_metrics_row(results: Dict[str, Any]):
    """Display key metrics in a row."""
    col1, col2, col3, col4 = st.columns(4)
    
    overall_score = results.get("overall_compliance_score", 0)
    risk_summary = results.get("risk_summary", {})
    
    with col1:
        st.metric(
            label="Overall Compliance",
            value=f"{overall_score:.0%}",
            delta=f"Target: 90%"
        )
    
    with col2:
        st.metric(
            label="High Risk Items",
            value=risk_summary.get("high_risk_items", 0),
            delta=None
        )
    
    with col3:
        st.metric(
            label="Medium Risk Items", 
            value=risk_summary.get("medium_risk_items", 0),
            delta=None
        )
    
    with col4:
        st.metric(
            label="Low Risk Items",
            value=risk_summary.get("low_risk_items", 0),
            delta=None
        )
