import csv
from tempfile import NamedTemporaryFile
import shutil
import pandas as pd
import source_code as sc
from suggestions import suggest_email_domain
import whois
from domains import emailDomains
import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards

st.set_page_config(
    page_title="Email Verification",
    page_icon="✅",
    layout="centered",
)

# Custom CSS for styling
def load_css():
    st.markdown(
        """
        <style>
        /* General Page Style */
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f9f9f9;
        }

        /* Title Styling */
        .stTitle {
            color: #333;
            font-size: 2rem;
            font-weight: bold;
            text-align: center;
        }

        /* Info Box Styling */
        .stAlert {
            background-color: #e6f7ff;
            border-left: 6px solid #1890ff;
            padding: 10px;
        }

        /* Tabs Styling */
        .stTabs [data-baseweb="tab"] {
            font-weight: bold;
            color: #1890ff;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background-color: #e6f7ff;
        }

        /* Button Styling */
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            cursor: pointer;
        }

        .stButton>button:hover {
            background-color: #45a049;
        }

        /* Metric Cards */
        .stMetric {
            border-radius: 8px;
            background-color: #f0f0f0;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
            padding: 15px;
        }

        /* DataFrame Table Styling */
        .stDataFrame table {
            border: 1px solid #ddd;
            border-collapse: collapse;
            width: 100%;
        }

        .stDataFrame th, .stDataFrame td {
            text-align: left;
            padding: 8px;
        }

        .stDataFrame tr:nth-child(even) {
            background-color: #f2f2f2;
        }

        /* File Uploader */
        .stFileUploader label {
            font-size: 1rem;
            color: #555;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
# Updated function to label emails
def label_email(email):
    if not sc.is_valid_email(email):  # Syntax validation
        return "Invalid"
    domain_part = email.split('@')[1]
    if sc.is_disposable(domain_part):  # Check if the domain is disposable
        return "Temporary/Risky"
    if not sc.has_valid_mx_record(domain_part):  # Check MX record
        return "Invalid"
    if not sc.verify_email(email):  # Verify email via SMTP
        return "Invalid"
    return "Valid"

# Updated bulk processing logic
def process_csv(input_file):
    if input_file:
        df = pd.read_csv(input_file, header=None)
        results = []
        for index, row in df.iterrows():
            email = row[0].strip()
            label = label_email(email)
            results.append([email, label])
        result_df = pd.DataFrame(results, columns=['Email', 'Label'])
        result_df.index = range(1, len(result_df) + 1)
        return result_df
    else:
        return pd.DataFrame(columns=['Email', 'Label'])
def main():
    load_css()
    st.title("Email Verification Tool")
 
    t1, t2 = st.tabs(["Single Email", "Bulk Email Processing"])

    with t1:
        email = st.text_input("Enter an email address:")
        if st.button("Verify"):
            with st.spinner('Verifying...'):
                label = label_email(email)
                if label == "Valid":
                    st.success(f"{email} is a valid email address.")
                    # Proceed with valid email logic (e.g., save to database, etc.)
                elif label == "Temporary/Risky":
                    st.warning(f"{email} is a disposable/temporary email.")
                    # Handle temporary/risky email logic (e.g., flag it or ask for confirmation)
                else:
                    st.error(f"{email} is invalid.")
                    # Handle invalid email logic (e.g., prevent submission, prompt for a new email)

    with t2:
        input_file = st.file_uploader("Upload a CSV file", type=["csv"])
        if input_file:
            with st.spinner("Processing..."):
                df = process_csv(input_file)
            st.success("Processing complete!")
            st.dataframe(df)
            st.download_button(
                label="Download Results",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="email_verification_results.csv",
                mime="text/csv",
            )

if __name__ == "__main__":
    main()
