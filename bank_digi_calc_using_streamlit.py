import os
import pandas as pd
import PyPDF2
import re
import streamlit as st

# -------------------- KEYWORDS & WEIGHTS --------------------
keywords = {
    "Artificial Intelligence (AI) & Machine Learning (ML)": [
        "Artificial Intelligence", "Business Intelligence", "Image Understanding", "Investment Decision Aid System",
        "Intelligent Data Analysis", "Intelligent Robotics", "Machine Learning", "Deep Learning", "Semantic Search",
        "Biometrics", "Face Recognition", "Voice Recognition", "Identity Verification", "Autonomous Driving",
        "Natural Language Processing", "AI/ML", "Chatbots", "Credit Risk Assessment Models", "Robo-advisor", "Generative AI"
    ],
    "Blockchain Technology": [
        "Blockchain", "Digital Currency", "Cryptocurrency", "Crypto", "Distributed Computing",
        "Differential Privacy Technology", "Smart Financial Contracts", "NFT", "Web 3.0"
    ],
    "Cloud Computing & Infrastructure": [
        "Cloud Computing", "Cloud", "Cloud Technologies", "Streaming Computing", "Graph Computing",
        "In-Memory Computing", "Multi-party Secure Computing", "Brain-like Computing", "Green Computing",
        "Cognitive Computing", "Converged Architecture", "Billion-level Concurrency", "EB-level Storage",
        "APIs", "Digital Infrastructure"
    ],
    "Big Data & Analytics": [
        "Big Data", "Data Mining", "Text Mining", "Data Visualization", "Heterogeneous Data",
        "Credit Analytics", "Augmented Reality", "Mixed Reality", "Virtual Reality", "Transaction Monitoring"
    ],
    "Digital Technology Applications": [
        "Mobile Internet", "Industrial Internet", "Internet Healthcare", "E-commerce", "Mobile Payment",
        "Third-party Payment", "NFC Payment", "Smart Energy", "B2B", "B2C", "C2B", "C2C", "O2O", "Netlink",
        "Smart Wear", "Smart Agriculture", "Smart Transportation", "Smart Healthcare", "Smart Customer Service",
        "Smart Home", "Smart Investment", "Smart Cultural Tourism", "Smart Environmental Protection", "Smart Grid",
        "Smart Marketing", "Digital Marketing", "Unmanned Retail", "Internet Finance", "Digital Finance",
        "Fintech", "Quantitative Finance", "Open Banking", "Embedded Finance", "Peer-to-Peer", "Buy Now Pay Later",
        "Contactless Payments", "Request to Pay", "Payment Service Directive", "Neobank", "Mobile-first Banking",
        "Banking-as-a-Service", "Metaverse"
    ],
    "Cybersecurity & Compliance": [
        "Cyber Security", "Anti-Money Laundering", "Fraud Detection"
    ],
    "Digital Banking & Transformation": [
        "Digitization", "Digital Transformation", "Net Banking", "Internet Banking", "New-to-Digital Customers",
        "E-money", "Robotic Process Automation", "Internet of Things", "Digital Adoption", "Branch on the Move",
        "DBT", "Innovation", "Banking Technology"
    ]
}

weights = {
    "Artificial Intelligence (AI) & Machine Learning (ML)": 1,
    "Blockchain Technology": 1,
    "Cloud Computing & Infrastructure": 1,
    "Big Data & Analytics": 1,
    "Digital Technology Applications": 1,
    "Cybersecurity & Compliance": 1,
    "Digital Banking & Transformation": 1
}

# -------------------- FUNCTIONS --------------------
def extract_text_from_pdf(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.lower()
    except Exception as e:
        return ""

def compute_digitization_score(text, keywords, weights):
    total_words = len(re.findall(r'\w+', text))
    category_details = {}
    total_normalized_score = 0

    for category, keyword_list in keywords.items():
        category_score = 0
        for keyword in keyword_list:
            count = len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', text))
            category_score += count
        weighted_score = category_score * weights[category]
        normalized_score = (weighted_score / total_words) * 1000 if total_words > 0 else 0
        category_details[category] = {
            "raw_count": category_score,
            "weighted_score": weighted_score,
            "normalized_score": round(normalized_score, 2)
        }
        total_normalized_score += normalized_score

    return round(total_normalized_score, 2), category_details

# -------------------- STREAMLIT UI --------------------
st.set_page_config(page_title="Digitization Score Calculator", layout="wide")
st.title("🏦 Bank Digitization Score Calculator")

uploaded_files = st.file_uploader("Upload PDF Reports", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    results = []
    st.info(f"Found {len(uploaded_files)} PDF file(s). Processing...")
    progress_bar = st.progress(0)
    log = st.empty()

    for i, pdf_file in enumerate(uploaded_files):
        filename = pdf_file.name
        log.markdown(f"📄 **Processing:** `{filename}`")

        text = extract_text_from_pdf(pdf_file)

        if text:
            filename_parts = os.path.splitext(filename)[0].split("_")
            bank_name = filename_parts[0]

            fy = "Unknown"
            for part in filename_parts:
                if "FY" in part or re.search(r'(20\d{2})[-_](\d{2,4})', part):
                    fy = part
                    if fy.startswith("FY"):
                        fy = fy[2:]
                    break

            total_score, category_scores = compute_digitization_score(text, keywords, weights)
            
            # Create a result dictionary with bank name, FY, and total score
            result = {"FY": fy, "Name of Bank": bank_name, "Digitization Score": total_score}
            
            # Add individual category scores
            for category, details in category_scores.items():
                short_name = category.split("(")[0].strip() if "(" in category else category
                result[f"{short_name} Score"] = details["normalized_score"]
                
            results.append(result)
            st.success(f"✅ `{bank_name}` ({fy}) → Score: **{total_score}**")
        else:
            st.error(f"❌ Failed to extract from: `{filename}`")

        progress_bar.progress((i + 1) / len(uploaded_files))

    # Show Results
    if results:
        df = pd.DataFrame(results)
        st.markdown("### 📊 Final Results")
        
        # Reorder columns to group total score and individual category scores
        cols = ["FY", "Name of Bank", "Digitization Score"]
        category_cols = [col for col in df.columns if col not in cols]
        df = df[cols + sorted(category_cols)]
        
        st.dataframe(df)

        # Add visualization of category scores
        st.markdown("### 📈 Category Score Breakdown")
        if len(df) > 0:
            selected_bank = st.selectbox("Select a bank to view detailed scores:", df["Name of Bank"].unique())
            bank_data = df[df["Name of Bank"] == selected_bank].iloc[0]
            
            # Extract category scores for visualization
            category_scores = {col.replace(" Score", ""): bank_data[col] 
                              for col in bank_data.index if " Score" in col}
            
            # Create a bar chart
            chart_data = pd.DataFrame({
                "Category": list(category_scores.keys()),
                "Score": list(category_scores.values())
            })
            
            st.bar_chart(chart_data.set_index("Category"))

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Results as CSV", data=csv, file_name="Digitization_Scores.csv", mime="text/csv")

else:
    st.info("Please upload one or more PDF files to begin analysis.")