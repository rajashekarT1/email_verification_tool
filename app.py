import csv
import pandas as pd
import source_code as sc
from suggestions import suggest_email_domain
import whois
import streamlit as st
from domains import emailDomains
from concurrent.futures import ThreadPoolExecutor
from streamlit_extras.metric_cards import style_metric_cards

# Caching Whois information to prevent redundant API calls
@st.cache_data
def get_whois_info(domain_part):
    try:
        return whois.whois(domain_part)
    except Exception as e:
        return None  # Handle errors gracefully

st.set_page_config(
    page_title="Email verification",
    page_icon="✅",
    layout="centered",
)

def label_email(email):
    if not sc.is_valid_email(email):
        return email, "Invalid"
    if not sc.has_valid_mx_record(email.split('@')[1]):
        return email, "Invalid"
    if not sc.verify_email(email):
        return email, "Unknown"
    if sc.is_disposable(email.split('@')[1]):
        return email, "Risky"
    return email, "Valid"

# Function to process emails in parallel
def process_emails_in_parallel(emails):
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(label_email, emails))  # Process emails concurrently
    return results

def process_csv(input_file):
    if input_file:
        df = pd.read_csv(input_file, header=None)
        emails = df[0].tolist()

        results = process_emails_in_parallel(emails)  # Parallel processing
        result_df = pd.DataFrame(results, columns=['Email', 'Label'])
        result_df.index = range(1, len(result_df) + 1)  # Starting index from 1
        return result_df
    else:
        return pd.DataFrame(columns=['Email', 'Label'])

def process_xlsx(input_file):
    df = pd.read_excel(input_file, header=None)
    emails = df[0].tolist()

    results = process_emails_in_parallel(emails)  # Parallel processing
    result_df = pd.DataFrame(results, columns=['Email', 'Label'])
    result_df.index = range(1, len(result_df) + 1)  # Starting index from 1
    
    return result_df

def process_txt(input_file):
    input_text = input_file.read().decode("utf-8").splitlines()
    results = process_emails_in_parallel(input_text)  # Parallel processing

    result_df = pd.DataFrame(results, columns=['Email', 'Label'])
    result_df.index = range(1, len(result_df) + 1)  # Starting index from 1
    return result_df

def main():
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        
    st.title("Email Verification Tool", help="This tool verifies the validity of an email address.")
  
    t1, t2 = st.tabs(["Single Email", "Bulk Email Processing"])

    with t1:
        # Single email verification
        email = st.text_input("Enter an email address:")

        if st.button("Verify"):
            with st.spinner('Verifying...'):
                result = {}

                # Syntax validation
                result['syntaxValidation'] = sc.is_valid_email(email)

                if result['syntaxValidation']:
                    domain_part = email.split('@')[1] if '@' in email else ''

                    if not domain_part:
                        st.error("Invalid email format. Please enter a valid email address.")
                    else:
                        # Additional validation for the domain part
                        if not sc.has_valid_mx_record(domain_part):
                            st.warning("Not valid: MX record not found.")
                            suggested_domains = suggest_email_domain(domain_part, emailDomains)
                            if suggested_domains:
                                st.info("Suggested Domains:")
                                for suggested_domain in suggested_domains:
                                    st.write(suggested_domain)
                            else:
                                st.warning("No suggested domains found.")
                        else:
                            # MX record validation
                            result['MXRecord'] = sc.has_valid_mx_record(domain_part)

                            # SMTP validation
                            if result['MXRecord']:
                                result['smtpConnection'] = sc.verify_email(email)
                            else:
                                result['smtpConnection'] = False

                            # Temporary domain check
                            result['is Temporary'] = sc.is_disposable(domain_part)

                            # Determine validity status and message
                            is_valid = (
                                result['syntaxValidation']
                                and result['MXRecord']
                                and result['smtpConnection']
                                and not result['is Temporary']
                            )

                            st.markdown("**Result:**")

                            # Display metric cards with reduced text size
                            col1, col2, col3 = st.columns(3)
                            col1.metric(label="Syntax", value=result['syntaxValidation'])
                            col2.metric(label="MxRecord", value=result['MXRecord'])
                            col3.metric(label="Is Temporary", value=result['is Temporary'])
            
                            
                            # Show SMTP connection status as a warning
                            if not result['smtpConnection']:
                                st.warning("SMTP connection not established.")
                            
                            # Show domain details in an expander
                            with st.expander("See Domain Information"):
                                domain_info = get_whois_info(domain_part)
                                if domain_info:
                                    st.write("Registrar:", domain_info.registrar)
                                    st.write("Server:", domain_info.whois_server)
                                    st.write("Country:", domain_info.country)
                                else:
                                    st.error("Domain information retrieval failed.")
                            
                            # Show validity message
                            if is_valid:
                                st.success(f"{email} is a Valid email")
                            else:
                                st.error(f"{email} is an Invalid email")
                                if result['is Temporary']:
                                    st.text("It is a disposable email")

    with t2:
        # Bulk email processing
        st.header("Bulk Email Processing")
        input_file = st.file_uploader("Upload a CSV, XLSX, or TXT file", type=["csv", "xlsx", "txt"])

        if input_file:
            st.write("Processing...")
            if input_file.type == 'text/plain':
                result_df = process_txt(input_file)
            elif input_file.type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                result_df = process_xlsx(input_file)
            else:
                result_df = process_csv(input_file)
            
            st.success("Processing completed. Displaying results:")
            st.dataframe(result_df)

if __name__ == "__main__":
    main()
