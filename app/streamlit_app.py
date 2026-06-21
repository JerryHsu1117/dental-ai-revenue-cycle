import streamlit as st
import pandas as pd
import snowflake.connector
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv('.env'), override=True)

st.set_page_config(page_title='Dental AI Platform', layout='wide')

def get_connection():
    return snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA')
    )

def execute_query(sql):
    conn = get_connection()
    cur = conn.cursor(snowflake.connector.DictCursor)
    try:
        cur.execute(sql)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

st.sidebar.title('Dental AI Platform')
page = st.sidebar.radio('Navigate', [
    'Database Overview',
    'Patient Lookup',
    'Treatment Records',
    'Add New Patient'
])

# Page 1: Database Overview
if page == 'Database Overview':
    st.title('Database Overview')
    
    rows = execute_query('SELECT * FROM DENTAL_AI_DB.TIER1_ERP.VW_DB_SUMMARY')
    df = pd.DataFrame(rows)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    for col, row in zip([col1, col2, col3, col4, col5], rows):
        col.metric(row['TABLE_NAME'], f"{row['ROW_COUNT']:,}")
    
    st.subheader('CDT Code Distribution')
    cdt = execute_query('''
        SELECT CDT_CODE, TREATMENT_TYPE, COUNT(*) AS COUNT,
               ROUND(AVG(FEE_CHARGED),2) AS AVG_FEE
        FROM DENTAL_AI_DB.TIER1_ERP.TREATMENTS
        GROUP BY CDT_CODE, TREATMENT_TYPE ORDER BY COUNT DESC
    ''')
    st.dataframe(pd.DataFrame(cdt), use_container_width=True)

# Page 2: Patient Lookup
elif page == 'Patient Lookup':
    st.title('Patient Lookup')
    search = st.text_input('Search by last name')
    if search:
        rows = execute_query(f'''
            SELECT * FROM DENTAL_AI_DB.TIER1_ERP.VW_PATIENT_PROFILE
            WHERE UPPER(FULL_NAME) LIKE UPPER('%{search}%')
            LIMIT 20
        ''')
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
        else:
            st.warning('No patients found.')

# Page 3: Treatment Records
elif page == 'Treatment Records':
    st.title('Treatment Records')
    cdt_options = ['All'] + [
        r['CDT_CODE'] for r in execute_query(
            'SELECT DISTINCT CDT_CODE FROM DENTAL_AI_DB.TIER1_ERP.TREATMENTS ORDER BY CDT_CODE'
        )
    ]
    cdt_filter = st.selectbox('Filter by CDT Code', cdt_options)
    sql = 'SELECT * FROM DENTAL_AI_DB.TIER1_ERP.VW_TREATMENT_HISTORY'
    if cdt_filter != 'All':
        sql += f" WHERE CDT_CODE = '{cdt_filter}'"
    sql += ' LIMIT 50'
    rows = execute_query(sql)
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

# Page 4: Add New Patient
elif page == 'Add New Patient':
    st.title('Add New Patient')
    insurers = execute_query(
        'SELECT INSURANCE_COMPANY_ID, COMPANY_NAME FROM DENTAL_AI_DB.TIER1_ERP.INSURANCE_COMPANIES ORDER BY COMPANY_NAME'
    )
    insurer_map = {r['COMPANY_NAME']: r['INSURANCE_COMPANY_ID'] for r in insurers}
    
    with st.form('add_patient'):
        col1, col2 = st.columns(2)
        first  = col1.text_input('First Name')
        last   = col2.text_input('Last Name')
        dob    = st.date_input('Date of Birth')
        phone  = st.text_input('Phone')
        email  = st.text_input('Email')
        insurer_name = st.selectbox('Insurance Company', list(insurer_map.keys()))
        member_id    = st.text_input('Member ID')
        group_num    = st.text_input('Group Number')
        submitted = st.form_submit_button('Add Patient')
        
        if submitted:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO DENTAL_AI_DB.TIER1_ERP.PATIENTS
                (FIRST_NAME, LAST_NAME, DATE_OF_BIRTH, PHONE, EMAIL,
                 INSURANCE_COMPANY_ID, INSURANCE_MEMBER_ID, INSURANCE_GROUP_NUMBER)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (first, last, dob.isoformat(), phone, email,
                  insurer_map[insurer_name], member_id, group_num))
            conn.commit()
            cur.close()
            conn.close()
            st.success(f'Patient {first} {last} added successfully')
            