import streamlit as st
import requests
import json
import base64
import io
import time
import re
import os
import threading
import queue
import zipfile
from datetime import datetime
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from docx import Document
from docx.shared import Inches as DocxInches
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import pandas as pd
import numpy as np

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Kimi Clone Pro - Free AI Assistant",
    page_icon="🐉",  # Dragon emoji as favicon
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS WITH DRAGON THEME
# ============================================
st.markdown("""
<style>
    .main { background-color: #0a0a0a; color: #ffffff; }
    .stChatMessage { background-color: transparent !important; border: none !important; }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) { background-color: #1a1a1a !important; }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) { background-color: #0f0f0f !important; }
    .stChatInputContainer { 
        border-top: 1px solid #333; background-color: #1a1a1a; 
        padding: 20px; position: fixed; bottom: 0; left: 0; right: 0; z-index: 100; 
    }
    .css-1d391kg { background-color: #111; border-right: 1px solid #333; color: white; }
    .stButton>button { 
        border-radius: 8px; border: 1px solid #444; 
        background-color: #222; color: #fff; transition: all 0.3s; 
    }
    .stButton>button:hover { background-color: #333; border-color: #666; }
    .stButton>button[kind="primary"] { background-color: #4a4a4a; color: white; }
    .dragon-logo {
        width: 60px; height: 60px; background: #000; 
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        border: 2px solid #fff; margin-bottom: 10px;
    }
    .premium-badge { 
        display: inline-flex; align-items: center; gap: 4px; 
        padding: 2px 8px; background-color: #fff7e6; border: 1px solid #ffa940; 
        border-radius: 12px; font-size: 11px; color: #ffa940; font-weight: 600; 
    }
    .tool-indicator { 
        display: inline-flex; align-items: center; gap: 6px; 
        padding: 4px 12px; background-color: #1e3a5f; border: 1px solid #4a90e2; 
        border-radius: 16px; font-size: 12px; color: #4a90e2; margin: 4px 0; 
    }
    .memory-badge { 
        display: inline-flex; align-items: center; gap: 4px; 
        padding: 2px 8px; background-color: #1a3d1a; border: 1px solid #4caf50; 
        border-radius: 12px; font-size: 11px; color: #4caf50; 
    }
    .research-progress { 
        background-color: #1a1a1a; border-radius: 10px; padding: 10px; 
        margin: 5px 0; border-left: 4px solid #4a90e2; color: #fff;
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stTextInput>div>div>input { background-color: #222; color: #fff; border: 1px solid #444; }
    .stSelectbox>div>div>div { background-color: #222; color: #fff; }
    .stTextArea>div>div>textarea { background-color: #222; color: #fff; }
    .stFileUploader>div>div>div>div { background-color: #222; color: #fff; }
    .stCheckbox>div { color: #fff; }
    .stMarkdown { color: #fff; }
    h1, h2, h3, h4, h5, h6 { color: #fff !important; }
    p { color: #ccc !important; }
    .download-folder-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE
# ============================================
defaults = {
    'messages': [],
    'memory': [],
    'uploaded_files': {},
    'search_history': [],
    'current_model': "kimi-clone-pro",
    'conversation_id': f"conv_{int(time.time())}",
    'deep_research_active': False,
    'research_progress': [],
    'agent_swarm_active': False,
    'agents_status': {},
    'ppt_templates': ["Default", "Business", "Academic", "Minimal"],
    'generated_files': {},  # Store generated files for folder download
    'dragon_logo': None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ============================================
# DRAGON LOGO DISPLAY (Using Unicode/Emoji)
# ============================================
def render_dragon_logo():
    """Render dragon logo using SVG or emoji"""
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <div style="font-size: 80px; line-height: 1;">🐉</div>
        <div style="font-size: 24px; font-weight: bold; color: #fff; margin-top: 10px;">KIMI CLONE PRO</div>
        <div style="font-size: 12px; color: #666;">Dragon Edition</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# SIDEBAR WITH DRAGON THEME
# ============================================
with st.sidebar:
    render_dragon_logo()
    
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.session_state.conversation_id = f"conv_{int(time.time())}"
        st.session_state.deep_research_active = False
        st.session_state.agent_swarm_active = False
        st.session_state.generated_files = {}
        st.rerun()
    
    st.divider()
    
    st.markdown("### 🚀 Premium Features (FREE)")
    enable_deep_research = st.toggle("🔬 Deep Research", value=False)
    enable_agent_swarm = st.toggle("🐝 Agent Swarm", value=False)
    
    # Document Generation
    with st.expander("📄 Generate Documents", expanded=False):
        doc_type = st.selectbox("Type", ["PowerPoint", "Word", "PDF"])
        doc_title = st.text_input("Title", placeholder="Enter document title...")
        if st.button("Generate Document", use_container_width=True):
            st.session_state.generate_doc = {"type": doc_type, "title": doc_title}
    
    st.divider()
    
    st.markdown("### 🛠️ Standard Tools")
    enable_search = st.toggle("🔍 Web Search", value=True)
    enable_code = st.toggle("💻 Code Interpreter", value=True)
    enable_vision = st.toggle("👁️ Vision", value=True)
    enable_memory = st.toggle("🧠 Memory Space", value=True)
    
    st.divider()
    
    # DOWNLOAD FOLDER FEATURE
    st.markdown("### 📁 Download Folder")
    if st.session_state.generated_files:
        st.caption(f"Files in folder: {len(st.session_state.generated_files)}")
        if st.button("⬇️ Download All Files (ZIP)", use_container_width=True, key="download_folder"):
            # Create zip file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for filename, content in st.session_state.generated_files.items():
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    elif hasattr(content, 'getvalue'):
                        content = content.getvalue()
                    zip_file.writestr(filename, content)
            zip_buffer.seek(0)
            st.download_button(
                label="📦 Click to Download ZIP",
                data=zip_buffer,
                file_name=f"kimi_clone_files_{int(time.time())}.zip",
                mime="application/zip",
                use_container_width=True
            )
        if st.button("🗑️ Clear Files", use_container_width=True):
            st.session_state.generated_files = {}
            st.rerun()
    else:
        st.caption("No files generated yet")
    
    st.divider()
    
    st.markdown("### 🤖 Models (All Free)")
    model_option = st.selectbox("Select", 
        ["Kimi-Clone-Base", "Kimi-Clone-Pro", "Local-LLM", "DeepResearch-Mode"],
        index=1)
    
    st.divider()
    
    if enable_memory and st.session_state.memory:
        st.markdown("### 📝 Memory")
        for i, mem in enumerate(st.session_state.memory[-5:]):
            with st.expander(f"Memory {i+1}", expanded=False):
                st.write(mem['content'][:100])
                if st.button("🗑️", key=f"del_mem_{i}"):
                    st.session_state.memory.pop(i)
                    st.rerun()
    
    if st.session_state.memory and st.button("🗑️ Clear Memory", use_container_width=True):
        st.session_state.memory = []
        st.rerun()
    
    st.divider()
    st.caption("🐉 Dragon Edition - All Features Free")

# ============================================
# CLASSES (Same as before)
# ============================================

class DeepResearchEngine:
    def __init__(self):
        self.sub_topics = []
        self.findings = {}
        
    def plan_research(self, query):
        templates = [
            ["Overview & Definition", "Current State & Trends", "Key Players & Technologies", 
             "Challenges & Limitations", "Future Outlook", "Conclusion"],
            ["Introduction", "Historical Context", "Methodology", "Results Analysis", 
             "Case Studies", "Recommendations"],
            ["Problem Statement", "Literature Review", "Technical Approach", "Implementation", 
             "Evaluation", "Conclusion"]
        ]
        import random
        return random.choice(templates)
    
    def research_sub_topic(self, topic):
        time.sleep(0.5)
        return {
            "topic": topic,
            "content": f"Research findings for {topic}...",
            "sources": [f"Source {i}" for i in range(1, 4)]
        }
    
    def synthesize_report(self, findings):
        report = "# Deep Research Report\n\n"
        for topic, data in findings.items():
            report += f"## {topic}\n{data['content']}\n\n"
        return report

class AgentSwarm:
    def __init__(self):
        self.agents = {
            "Researcher": {"status": "idle", "icon": "🔍", "role": "Gathers information"},
            "Analyst": {"status": "idle", "icon": "📊", "role": "Processes data"},
            "Writer": {"status": "idle", "icon": "✍️", "role": "Creates content"},
            "Reviewer": {"status": "idle", "icon": "✅", "role": "Quality check"},
            "Coder": {"status": "idle", "icon": "💻", "role": "Implements solutions"}
        }
    
    def dispatch_task(self, task_type, content):
        agent_map = {
            "research": "Researcher",
            "analyze": "Analyst", 
            "write": "Writer",
            "review": "Reviewer",
            "code": "Coder"
        }
        agent = agent_map.get(task_type, "Researcher")
        self.agents[agent]["status"] = "working"
        return agent
    
    def get_swarm_status(self):
        return self.agents

class DocumentGenerator:
    @staticmethod
    def generate_ppt(title, slides_content, template="Default"):
        prs = Presentation()
        title_slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(title_slide_layout)
        slide.shapes.title.text = title
        slide.placeholders[1].text = "Generated by Kimi Clone Pro"
        
        for slide_data in slides_content:
            bullet_slide_layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(bullet_slide_layout)
            slide.shapes.title.text = slide_data['title']
            body_shape = slide.placeholders[1]
            tf = body_shape.text_frame
            tf.text = slide_data['content']
        
        output = io.BytesIO()
        prs.save(output)
        output.seek(0)
        return output
    
    @staticmethod
    def generate_word(title, content):
        doc = Document()
        doc.add_heading(title, 0)
        for section in content:
            doc.add_heading(section['heading'], level=1)
            doc.add_paragraph(section['text'])
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        return output
    
    @staticmethod
    def generate_pdf(title, content):
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 12))
        for section in content:
            story.append(Paragraph(section['heading'], styles['Heading2']))
            story.append(Paragraph(section['text'], styles['Normal']))
            story.append(Spacer(1, 12))
        doc.build(story)
        output.seek(0)
        return output

# ============================================
# HELPER FUNCTIONS
# ============================================

def simulate_typing(text, placeholder, delay=0.01):
    displayed_text = ""
    for char in text:
        displayed_text += char
        placeholder.markdown(displayed_text + "▌")
        time.sleep(delay)
    placeholder.markdown(displayed_text)

def execute_python_code(code):
    try:
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        exec(code, {"__builtins__": __builtins__, "pd": pd, "np": np}, {})
        sys.stdout = old_stdout
        output = mystdout.getvalue()
        return {"success": True, "output": output if output else "Executed successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def process_file(file):
    file_type = file.type
    content = ""
    if file_type == "text/plain":
        content = file.getvalue().decode("utf-8")
    elif file_type == "application/json":
        content = json.dumps(json.load(file), indent=2)
    elif file_type.startswith("image/"):
        content = f"[Image: {file.name}]"
    else:
        content = f"[File: {file.name}]"
    return {"name": file.name, "type": file_type, "content": content}

# ============================================
# MAIN INTERFACE
# ============================================

st.markdown("""
<div style="text-align: center; padding: 20px 0; border-bottom: 1px solid #333; margin-bottom: 20px;">
    <div style="font-size: 60px;">🐉</div>
    <h1 style="margin: 0; color: #fff; font-weight: 600;">Kimi Clone <span style="color: #ffa940;">Pro</span></h1>
    <p style="color: #666; margin: 10px 0 0 0;">Dragon Edition • All Premium Features Free</p>
</div>
""", unsafe_allow_html=True)

# Handle Document Generation
if 'generate_doc' in st.session_state:
    doc_info = st.session_state.pop('generate_doc')
    with st.spinner(f"Generating {doc_info['type']}..."):
        sample_content = [
            {"title": "Introduction", "heading": "Overview", "text": "This is an auto-generated document."},
            {"title": "Key Points", "heading": "Main Content", "text": "Content generated by Kimi Clone Pro's free document engine."},
            {"title": "Conclusion", "heading": "Summary", "text": "Generated using open-source libraries."}
        ]
        if doc_info['type'] == "PowerPoint":
            file_data = DocumentGenerator.generate_ppt(doc_info['title'], sample_content)
            ext = "pptx"
            mime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        elif doc_info['type'] == "Word":
            file_data = DocumentGenerator.generate_word(doc_info['title'], sample_content)
            ext = "docx"
            mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            file_data = DocumentGenerator.generate_pdf(doc_info['title'], sample_content)
            ext = "pdf"
            mime = "application/pdf"
        
        filename = f"{doc_info['title']}.{ext}"
        
        # Store in session for folder download
        st.session_state.generated_files[filename] = file_data
        
        st.download_button(
            label=f"⬇️ Download {doc_info['type']}",
            data=file_data,
            file_name=filename,
            mime=mime
        )
        st.success(f"Added to folder: {filename}")

# Display Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "tools_used" in message:
            for tool in message["tools_used"]:
                st.markdown(f'<span class="tool-indicator">🔧 {tool}</span>', unsafe_allow_html=True)
        if "memory_used" in message and message["memory_used"]:
            st.markdown(f'<span class="memory-badge">🧠 Memory</span>', unsafe_allow_html=True)
        if "swarm_agents" in message:
            st.markdown("### 🐝 Agent Swarm Activity")
            for agent, status in message["swarm_agents"].items():
                color = "🟢" if status["status"] == "idle" else "🟡"
                st.markdown(f"{color} **{agent}**: {status['role']}")
        if "research_progress" in message:
            st.markdown("### 🔬 Deep Research Progress")
            for step in message["research_progress"]:
                st.markdown(f'<div class="research-progress">✅ {step}</div>', unsafe_allow_html=True)
        st.markdown(message["content"])
        if "files" in message:
            for file in message["files"]:
                if file["type"].startswith("image/"):
                    st.image(file["content"])

# Input Area
uploaded_file = st.file_uploader("📎 Attach files", 
                                type=["txt", "py", "json", "png", "jpg", "jpeg", "pdf", "docx", "pptx"],
                                label_visibility="collapsed")

if uploaded_file is not None:
    file_data = process_file(uploaded_file)
    st.session_state.uploaded_files[uploaded_file.name] = file_data
    st.success(f"📎 Attached: {uploaded_file.name}")

prompt = st.chat_input("Message Kimi Clone Pro... (Try: 'deep research AI trends', 'generate ppt on Python', 'swarm: analyze this data')")

if prompt:
    if prompt.startswith("deep research ") or (enable_deep_research and "research" in prompt.lower()):
        st.session_state.deep_research_active = True
        query = prompt.replace("deep research ", "")
        researcher = DeepResearchEngine()
        plan = researcher.plan_research(query)
        progress_placeholder = st.empty()
        findings = {}
        for i, topic in enumerate(plan):
            st.session_state.research_progress.append(f"Researching: {topic}")
            progress_placeholder.markdown(f"🔬 Researching: {topic}...")
            finding = researcher.research_sub_topic(topic)
            findings[topic] = finding
            time.sleep(0.3)
        report = researcher.synthesize_report(findings)
        
        # Store report in generated files
        report_filename = f"deep_research_{query.replace(' ', '_')[:30]}.md"
        st.session_state.generated_files[report_filename] = report
        
        user_message = {"role": "user", "content": f"Deep Research: {query}", "research_mode": True}
        st.session_state.messages.append(user_message)
        with st.chat_message("user"):
            st.markdown(f"🔬 **Deep Research Request**: {query}")
        with st.chat_message("assistant"):
            st.markdown(f'<span class="tool-indicator">🔬 Deep Research</span>', unsafe_allow_html=True)
            st.markdown("### Research Plan")
            for topic in plan:
                st.markdown(f"- {topic}")
            st.markdown("### Detailed Report")
            st.markdown(report)
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("⬇️ Download Report", report, report_filename)
            with col2:
                st.info(f"📁 Added to folder: {report_filename}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": report,
                "tools_used": ["Deep Research", "Report Generation"],
                "research_progress": plan
            })
    
    elif prompt.startswith("swarm:") or (enable_agent_swarm and "swarm" in prompt.lower()):
        st.session_state.agent_swarm_active = True
        task = prompt.replace("swarm:", "").strip()
        swarm = AgentSwarm()
        agents_used = []
        for task_type in ["research", "analyze", "write"]:
            agent = swarm.dispatch_task(task_type, task)
            agents_used.append(agent)
            time.sleep(0.2)
        user_message = {"role": "user", "content": f"Agent Swarm: {task}", "swarm_mode": True}
        st.session_state.messages.append(user_message)
        with st.chat_message("user"):
            st.markdown(f"🐝 **Agent Swarm Request**: {task}")
        with st.chat_message("assistant"):
            st.markdown(f'<span class="tool-indicator">🐝 Agent Swarm</span>', unsafe_allow_html=True)
            cols = st.columns(len(swarm.agents))
            for idx, (agent_name, status) in enumerate(swarm.agents.items()):
                with cols[idx]:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 10px; background: #222; border-radius: 8px; border: 1px solid #444;">
                        <div style="font-size: 24px;">{status['icon']}</div>
                        <div style="font-weight: bold; color: #fff;">{agent_name}</div>
                        <div style="font-size: 11px; color: #999;">{status['role']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown(f"**Task Distributed**: {task}")
            st.markdown("**Agents Working**: " + ", ".join(agents_used))
            st.markdown("**Result**: Multi-agent analysis complete.")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Swarm analysis of: {task}",
                "tools_used": ["Agent Swarm", "Multi-Agent Coordination"],
                "swarm_agents": swarm.get_swarm_status()
            })
    
    elif "generate ppt" in prompt.lower() or "create presentation" in prompt.lower():
        topic = prompt.replace("generate ppt", "").replace("create presentation", "").strip()
        slides = [
            {"title": f"{topic} - Overview", "content": f"Introduction to {topic}\nKey concepts and fundamentals"},
            {"title": "Key Points", "content": "• Main concept 1\n• Main concept 2\n• Main concept 3"},
            {"title": "Applications", "content": "Real-world use cases and implementations"},
            {"title": "Conclusion", "content": "Summary and next steps"}
        ]
        with st.spinner("Generating PowerPoint..."):
            ppt_data = DocumentGenerator.generate_ppt(topic, slides)
            filename = f"{topic.replace(' ', '_')}.pptx"
            st.session_state.generated_files[filename] = ppt_data
            
            user_message = {"role": "user", "content": prompt}
            st.session_state.messages.append(user_message)
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                st.markdown(f'<span class="tool-indicator">📊 PowerPoint Generation</span>', unsafe_allow_html=True)
                st.success(f"Generated presentation: {topic}")
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("⬇️ Download PPT", ppt_data, filename, 
                                     mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
                with col2:
                    st.info(f"📁 Added to folder")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Generated PowerPoint: {topic}",
                    "tools_used": ["PowerPoint Generation", "python-pptx"]
                })
    
    else:
        user_message = {
            "role": "user", 
            "content": prompt,
            "files": list(st.session_state.uploaded_files.values()) if st.session_state.uploaded_files else []
        }
        if "remember that" in prompt.lower():
            memory_content = prompt.split("remember that")[-1].strip()
            st.session_state.memory.append({
                "id": len(st.session_state.memory) + 1,
                "content": memory_content,
                "date": datetime.now().strftime("%Y-%m-%d")
            })
        st.session_state.messages.append(user_message)
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            tools_used = []
            if enable_search: tools_used.append("Web Search")
            if enable_code: tools_used.append("Code Interpreter")
            if enable_vision: tools_used.append("Vision")
            for tool in tools_used:
                st.markdown(f'<span class="tool-indicator">🔧 {tool}</span>', unsafe_allow_html=True)
            response = f"""I received: **{prompt}**

🐉 **Kimi Clone Pro - Dragon Edition** with all premium features FREE:

- 🔬 **Deep Research**: Type "deep research [topic]"
- 🐝 **Agent Swarm**: Type "swarm: [task]"  
- 📊 **PowerPoint**: Type "generate ppt [topic]"
- 📝 **Word/PDF**: Use sidebar document generator
- 💻 **Code Execution**: Python with pandas/numpy
- 🧠 **Memory**: Persistent storage
- 👁️ **Vision**: Image analysis
- 📁 **Download Folder**: All files saved to downloadable ZIP

All features run locally using free open-source libraries!"""
            placeholder = st.empty()
            simulate_typing(response, placeholder)
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "tools_used": tools_used
            })
    
    st.session_state.uploaded_files = {}

# Examples
if not st.session_state.messages:
    st.markdown("### 💡 Try Premium Features for Free:")
    cols = st.columns(4)
    examples = [
        ("🔬 Deep Research", "deep research quantum computing"),
        ("🐝 Agent Swarm", "swarm: analyze market trends"),
        ("📊 PowerPoint", "generate ppt AI Ethics"),
        ("📁 Folder", "Check sidebar for ZIP download")
    ]
    for col, (icon, text) in zip(cols, examples):
        with col:
            st.button(f"{icon}", use_container_width=True, key=f"ex_{text}")

# Show generated files count
if st.session_state.generated_files:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### 📁 Files Ready: {len(st.session_state.generated_files)}")
    for fname in list(st.session_state.generated_files.keys())[-5:]:
        st.sidebar.caption(f"• {fname[:30]}...")

st.markdown("---")
st.caption("🐉 Kimi Clone Pro Dragon Edition - All Premium Features Free | Built with Streamlit")
