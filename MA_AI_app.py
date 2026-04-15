import streamlit as st
import json
import base64
import io
import time
import re
import os
import zipfile
from datetime import datetime
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from docx import Document
from docx.shared import Inches as DocxInches
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd
import numpy as np

st.set_page_config(page_title="Kimi Clone Pro", page_icon="🐉", layout="wide")

# Session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'generated_files' not in st.session_state:
    st.session_state.generated_files = {}

# CSS
st.markdown("""
<style>
    .main { background-color: #0a0a0a; color: #ffffff; }
    .stChatMessage:nth-child(odd) { background-color: #1a1a1a !important; }
    .stChatMessage:nth-child(even) { background-color: #151515 !important; }
    .zip-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; color: white !important; }
    .file-counter { background-color: #1a3d1a; color: #4caf50; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ZIP function
def create_zip(files_dict):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename, content in files_dict.items():
            if isinstance(content, str):
                content = content.encode('utf-8')
            elif hasattr(content, 'getvalue'):
                content = content.getvalue()
            zf.writestr(filename, content)
    zip_buffer.seek(0)
    return zip_buffer

# Sidebar
with st.sidebar:
    st.markdown("<div style='text-align: center;'><div style='font-size: 60px;'>🐉</div><h2>KIMI CLONE PRO</h2></div>", unsafe_allow_html=True)
    
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # ZIP Download Section
    st.markdown("### 📦 ZIP Download")
    if st.session_state.generated_files:
        st.markdown(f'<span class="file-counter">{len(st.session_state.generated_files)} files</span>', unsafe_allow_html=True)
        with st.expander("View files"):
            for f in st.session_state.generated_files.keys():
                st.caption(f"📄 {f}")
        if st.button("⬇️ DOWNLOAD ZIP", use_container_width=True):
            zip_file = create_zip(st.session_state.generated_files)
            st.download_button("📦 SAVE ZIP", zip_file, f"kimi_files_{int(time.time())}.zip", "application/zip")
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.generated_files = {}
            st.rerun()
    else:
        st.info("No files yet")
    
    st.divider()
    
    # Document Generator
    st.markdown("### 📄 Generate")
    doc_type = st.selectbox("Type", ["PowerPoint", "Word", "PDF"])
    doc_title = st.text_input("Title")
    if st.button("Generate", use_container_width=True) and doc_title:
        # Generate sample content
        if doc_type == "PowerPoint":
            prs = Presentation()
            prs.slides.add_slide(prs.slide_layouts[0]).shapes.title.text = doc_title
            output = io.BytesIO()
            prs.save(output)
            output.seek(0)
            fname = f"{doc_title}.pptx"
        elif doc_type == "Word":
            doc = Document()
            doc.add_heading(doc_title, 0)
            output = io.BytesIO()
            doc.save(output)
            output.seek(0)
            fname = f"{doc_title}.docx"
        else:
            output = io.BytesIO()
            pdf = SimpleDocTemplate(output, pagesize=A4)
            pdf.build([Paragraph(doc_title, getSampleStyleSheet()['Title'])])
            output.seek(0)
            fname = f"{doc_title}.pdf"
        
        st.session_state.generated_files[fname] = output
        st.success(f"Added {fname}")
        st.rerun()

# Main
st.markdown("<h1 style='text-align: center;'>🐉 Kimi Clone Pro</h1>", unsafe_allow_html=True)

# Display messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
prompt = st.chat_input("Type your message...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    response = f"**Echo:** {prompt}\n\nFiles in ZIP: {len(st.session_state.generated_files)}"
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)

st.markdown("---")
st.caption("🐉 Kimi Clone Pro | ZIP Ready")
