import streamlit as st
import pandas as pd
import sqlite3

# Custom CSS for modern UI
st.markdown("""
    <style>
        .stTextInput>div>div>input, .stTextArea>div>textarea, .stDateInput>div>div>input {
            border-radius: 10px;
            border: 1px solid #bbb;
            padding: 10px;
        }
        .stSelectbox>div>div {
            border-radius: 10px;
            border: 1px solid #bbb;
            padding: 5px;
        }
        .stButton>button {
            border-radius: 8px;
            background-color: #007bff;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            border: none;
        }
        .stButton>button:hover {
            background-color: #0056b3;
        }
    </style>
""", unsafe_allow_html=True)

# Function to insert a new contract into the database
def insert_contract(vendor, start_date, end_date, terms, status):
    conn = sqlite3.connect("vendors.db")
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO contracts (vendor_id, start_date, end_date, terms, status)
        VALUES ((SELECT id FROM vendors WHERE name = ?), ?, ?, ?, ?)
    ''', (vendor, str(start_date), str(end_date), terms, status))

    conn.commit()
    conn.close()

def contracts_form():
    st.markdown("<h2 style='color: #007bff;'>📜 Create New Contract</h2>", unsafe_allow_html=True)

    # Ensure vendors exist in session state
    if 'vendors' not in st.session_state:
        st.session_state.vendors = pd.DataFrame()  # Placeholder until vendors are loaded
    
    vendor_names = st.session_state.vendors['Name'].tolist() if not st.session_state.vendors.empty else []

    # If vendors exist, proceed with form
    if vendor_names:
        col1, col2 = st.columns(2)

        with col1:
            vendor = st.selectbox("🏢 Select Vendor", vendor_names, key="vendor_select")
            start_date = st.date_input("📅 Contract Start Date", key="start_date")

        with col2:
            end_date = st.date_input("📅 Contract End Date", key="end_date")
            status = st.selectbox("📌 Contract Status", ["Active", "Completed", "Pending"], key="contract_status")

        terms = st.text_area("📝 Contract Terms", key="contract_terms")

        # Centered Button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Create Contract", key="create_contract_btn"):
            if vendor and start_date and end_date and terms:
                new_contract = {
                    'Vendor': vendor,
                    'Start Date': start_date,
                    'End Date': end_date,
                    'Terms': terms,
                    'Status': status
                }
                
                # Add contract to session state using pd.concat()
                if "contracts" not in st.session_state:
                    st.session_state.contracts = pd.DataFrame()
                
                st.session_state.contracts = pd.concat([st.session_state.contracts, pd.DataFrame([new_contract])], ignore_index=True)
                
                # Insert the contract into the database
                insert_contract(vendor, start_date, end_date, terms, status)
                
                st.success("🎉 Contract created successfully!")
                st.rerun()
            else:
                st.error("⚠️ Please fill in all fields!")
    else:
        st.warning("⚠️ No vendors available. Please add vendors first.")

def display_contracts():
    st.markdown("<h2 style='color: #007bff;'>📜 Contracts List</h2>", unsafe_allow_html=True)
    if 'contracts' in st.session_state and not st.session_state.contracts.empty:
        st.dataframe(st.session_state.contracts.style.set_properties(**{'background-color': '#f5f5f5', 'border-color': 'black'}))
    else:
        st.warning("⚠️ No contracts available.")

# Run the functions
contracts_form()
st.markdown("---")  # Divider
display_contracts()
