import streamlit as st
import re
import pandas as pd
from io import StringIO
from datetime import datetime
import locale

# सिस्टम की लोकल सेटिंग को हिंदी/भारतीय प्रारूप पर सेट करने का प्रयास करें
try:
    # macOS/Linux: Use 'hi_IN.UTF-8' for Hindi month names
    locale.setlocale(locale.LC_TIME, 'hi_IN.UTF-8')
except locale.Error:
    try:
        # Windows/Fallback: Use 'en_IN.UTF-8' or similar
        locale.setlocale(locale.LC_TIME, 'en_IN.UTF-8')
    except locale.Error:
        # Final fallback
        locale.setlocale(locale.LC_TIME, 'C') 

# --- पासवर्ड और कॉन्फ़िगरेशन ---
try:
    CORRECT_PASSWORD = st.secrets["app_password"]
except:
    CORRECT_PASSWORD = "sgam@4321"

# --- सहायक कार्य (Helper Functions) ---

def get_current_time_details():
    """वर्तमान तिथि, माह और वर्ष को हिंदी और अंग्रेजी प्रारूप में प्राप्त करता है।"""
    now = datetime.now()
    current_date = now.strftime("%d.%m.%Y")
    current_month_hindi = now.strftime("%B").title() 
    current_year = now.year
    current_month_numeric = now.strftime("%Y%m") # जैसे: '202606'
    return current_date, current_month_hindi, current_year, current_month_numeric


def check_password():
    """यदि उपयोगकर्ता सही पासवर्ड दर्ज करता है तो True लौटाता है।"""
    if st.session_state.get("password_correct", False):
        return True

    st.header("लॉगिन आवश्यक है")
    st.markdown("---")

    password = st.text_input(
        "पासवर्ड डालें", type="password", 
        key="password_input", 
        placeholder=""
    )

    if st.button("लॉगिन"):
        if password == CORRECT_PASSWORD:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("पासवर्ड गलत है। कृपया पुनः प्रयास करें।")
            st.session_state["password_correct"] = False
    
    return False

def get_data_section(data_string):
    """अपलोड की गई फ़ाइल से केवल डेटा तालिका अनुभाग को निकालता है।"""
    lines = data_string.split('\n')
    data_section = []
    
    start_pattern = "______________________________________________________________________________________________________________________________________________"
    end_pattern = "Total :"
    
    start_index = -1
    end_index = -1
    
    try:
        start_index = lines.index(start_pattern)
        for i in range(start_index + 1, len(lines)):
            if lines[i].strip().startswith(end_pattern):
                end_index = i
                break
        
        if start_index != -1 and end_index != -1:
            data_section = lines[start_index:end_index] 
            
    except ValueError:
        return []

    return data_section


def extract_month_from_record(record_line):
    """रिकॉर्ड लाइन से क्लेम महीना (जैसे: Jul25, Aug25) ढूंढता है।"""
    match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d{2}\b', record_line, re.IGNORECASE)
    if match:
        return match.group(0).title()
    return "Unknown_Month"


def number_to_word(number):
    """संख्या को शब्दों में बदलने का कार्य।"""
    try:
        import num2words
        return num2words.num2words(number, lang='en').title()
    except ImportError:
        return f"Rupees {number} in Words"


def create_output_text(filtered_records, total_ta_amount_sum, total_emp_count, filter_type, claim_month):
    """फ़िल्टर किए गए रिकॉर्ड से आउटपुट टेक्स्ट फ़ाइल बनाता है, जिसमें वर्तमान महीना शामिल होता है।"""
    current_date, current_month_hindi, current_year, current_month_numeric = get_current_time_details()

    if not filtered_records:
        return ""

    # --- 1. आधिकारिक नोट का निर्माण ---
    official_note_base = f"""प0म0रे0 															कार्यालय
सरईग्राम/स्‍टॉफ - IV/TA													 वरिष्‍ठ खण्‍ड अभियंता (रेल पथ)
दिनांक/{current_date}														सरईग्राम

प्रति,
	वरिष्‍ठ मण्‍डल (वित्त प्रबंधक) 
	पमरे जबलपुर

द्वारा :-	उचित माध्‍यम 
"""
    
    # क्लेम महीने के बजाय हमेशा वर्तमान महीना और वर्ष (Current Month & Year) का ही उपयोग करें
    month_year_text = f"माह {current_month_hindi} {current_year}"
    if filter_type == 'upto':
        subject_detail = "15 दिवस तक के यात्रा भत्ता"
    else:
        subject_detail = "15 दिवस से अधिक के यात्रा भत्ता"
        
    subject_line = f"विषय:- 	{month_year_text} की वेतन में लगने वाला {subject_detail} पर प्रतिहस्‍ताक्षर एवं भुगतान की कार्यवाही बावत ।"
    
    official_note_body = f"""      उपरोक्‍त विषयानुसार इस डिपो के अधीन पदस्‍थ कर्मचारियों का {month_year_text} के वेतन पत्रक में लगने वाला यात्रा भत्ता की सूची कर्मचारीवार निम्‍नानुसार तैयार कर प्रतिहस्‍ताक्षर एवं भुगतान की अग्रिम कार्यवाही हेतु 
यात्रा भत्ता संलग्‍न सादर प्रेषित है ।
"""
    
    final_official_note = official_note_base + subject_line + "\n\n" + official_note_body
    
    # --- 2. आउटपुट लाइन्स का निर्माण ---
    output_text_lines = []
    output_text_lines.append(final_official_note)
    
    output_text_lines.extend([
        "WEST CENTRAL RAILWAY/ JABALPUR DIVISION                         PAGE NO:1",
        "PRINT DATE:   ",
        f"TA/ CONTINGENCY STATEMENT OF THE STAFF OF B.U No. 3602255    FROM PERIOD:202409    TO PERIOD:202508",
        "______________________________________________________________________________________________________________________________________________",
        "SNO    EMP NO          NAME           DESIG     GP/    MONTH           20% TA        30% TA   	      70% TA  	        100% TA  TOTAL  CONT        ",
        "                                     	        LEVEL  CLAIM           Amount        Amount   	      Amount   	         Amount  AMOUNT  AMT",
        "															         OF TA",
        "_______________________________________________________________________________________________________________________________________________"
    ])
    
    # --- 3. फ़िल्टर किए गए रिकॉर्ड जोड़ें ---
    for i, item in enumerate(filtered_records):
        new_sno = i + 1
        original_sno_pattern = r'^\s*(\d{1,4})\s+'
        new_record_line = re.sub(original_sno_pattern, f" {new_sno:<4} ", item['record_line'], 1)
        output_text_lines.append(new_record_line)
        output_text_lines.append("__________________________________________________________________________________________________________________________________________")

    # --- 4. अंत में टोटल और Rs. in Word जोड़ें ---
    # CLAIM MONTH तालिका स्तंभ में अब हमेशा वर्त्तमान महीना numeric फॉर्मेट (जैसे '202606') में प्रिंट होगा
    total_section = f"""
__________________________________________________________________________________________________________________________________________
							Total :                                                             {total_ta_amount_sum}      0
__________________________________________________________________________________________________________________________________________


 ALLOCATION			  AMOUNT      EMPCOUNT
 ----------------------------------------------------------
   04025116                      {total_ta_amount_sum}         {total_emp_count}
 ----------------------------------------------------------
            TOTAL AMT           {total_ta_amount_sum}         {total_emp_count}

CLAIM MONTH		TA		CONTIGENT	TOTALAMT    RECORD COUNT
_____________________________________________________________________________
   {current_month_numeric:<17} {total_ta_amount_sum:<23} 0         {total_ta_amount_sum:<14} {total_emp_count}
_____________________________________________________________________________
         TOTAL AMT   {total_ta_amount_sum:<23} 0         {total_ta_amount_sum:<14} {total_emp_count}

FORWARDED  IN DUPLICATE FOR VETTING OF Rs.{total_ta_amount_sum}
( Rs.{number_to_word(total_ta_amount_sum)} Only ) ONLY
& RETURN TO THIS OFFICE
FOR DRAWL IN THE REGULAR SALARY BILL.
THE BILL WAS NOT DRAWN PREVIOUSLY AND WILL NOT BE DRAWN IN FUTURE
"""
    output_text_lines.append(total_section)
    
    output_text_lines.extend([
        "",
        "                                                                                    ",
        "                                                                                  WEST CENTRAL RAILWAY   ",
        "                                                                          JABALPUR DIVISION",
        "                                                              -------------",
    ])

    return "\n".join(output_text_lines)


def process_ta_data(data_string):
    """सभी रिकॉर्ड को पार्स करता है और उन्हें 15 दिन तक और 15 दिन से अधिक के लिए अलग करता है।"""
    data_section = get_data_section(data_string)
    records = []
    current_record = ""

    # डेटा सेक्शन से रिकॉर्ड निकालें
    for line in data_section:
        line = line.strip()
        if re.match(r'^\s*(\d{1,4})\s+', line):
            if current_record:
                records.append(current_record.strip())
            current_record = line
        elif "________________" in line:
            if current_record:
                records.append(current_record.strip())
            current_record = ""
            continue
        elif current_record:
            current_record += " " + line
            
    if current_record:
        records.append(current_record.strip())

    above_15_by_month = {}
    upto_15_days_records = []
    
    for record in records:
        days_matches = re.findall(r'(\d+)\*[0-9\.]+\s*=\s*(\d+)', record)
        
        if len(days_matches) == 4:
            days_20 = int(days_matches[0][0])
            days_30 = int(days_matches[1][0])
            days_70 = int(days_matches[2][0])
            days_100 = int(days_matches[3][0])
            
            total_days = days_20 + days_30 + days_70 + days_100
            
            total_ta_amount_match = re.search(r'(\d+)\s+0$', record)
            total_ta_amount = int(total_ta_amount_match.group(1)) if total_ta_amount_match else 0

            sno_match = re.match(r'^\s*(\d{1,4})\s+', record)
            original_sno = sno_match.group(1).strip() if sno_match else "0"

            record_data = {
                'original_sno': original_sno,
                'record_line': record,
                'total_ta_amount': total_ta_amount
            }

            if total_days > 15:
                rec_month = extract_month_from_record(record)
                if rec_month not in above_15_by_month:
                    above_15_by_month[rec_month] = []
                above_15_by_month[rec_month].append(record_data)
            else:
                upto_15_days_records.append(record_data)

    # 15 दिन से अधिक वाले रिकॉर्ड्स के लिए महीना-वार आउटपुट फाइलें जनरेट करें
    above_15_outputs = {}
    for month, m_records in above_15_by_month.items():
        total_m_amount = sum(item['total_ta_amount'] for item in m_records)
        above_15_outputs[month] = create_output_text(
            m_records, total_m_amount, len(m_records), 'above', month
        )
    
    # 15 दिन तक वाले रिकॉर्ड्स के लिए (इसे एक ही फाइल में रखा गया है)
    total_upto_amount = sum(item['total_ta_amount'] for item in upto_15_days_records)
    # 15 दिन तक वाली फाइल के लिए एक सामान्य नामकरण रखें
    upto_15_output = create_output_text(
        upto_15_days_records, total_upto_amount, len(upto_15_days_records), 'upto', 'Combined_Period'
    )
    
    return above_15_outputs, upto_15_output


# --- Streamlit App Interface ---

def main_app():
    st.set_page_config(page_title="TA 15 Days Monthwise Filter", layout="centered")

    st.title("यात्रा भत्ता (TA) फ़िल्टर: 15 दिन तक और 15 दिन से अधिक")
    st.subheader("(15 दिन से अधिक वाले कर्मचारियों की माह-वार फाइलें)")
    st.markdown("---")

    st.subheader("1. TXT फ़ाइल अपलोड करें")
    uploaded_file = st.file_uploader("कृपया अपनी TA सूची वाली TXT फ़ाइल अपलोड करें।", type="txt")

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        data_string = file_bytes.decode("utf-8")
        
        st.subheader("2. फ़िल्टर किया गया डेटा")
        
        # दोनों सूचियों को प्रोसेस करें
        above_15_outputs, upto_15_output = process_ta_data(data_string)

        # --- 15 दिन से अधिक का सेक्शन (महीना-वार) ---
        st.markdown("### ➡️ **15 दिन से अधिक** TA वाले कर्मचारी (महीने के अनुसार विभाजित)")
        
        if not above_15_outputs:
            st.warning("फ़ाइल में 15 दिन से अधिक TA वाले कोई कर्मचारी नहीं पाए गए।")
        else:
            for month, output_text in above_15_outputs.items():
                emp_count_match = re.search(r'TOTAL AMT\s+[\d\s]+(\d+)', output_text)
                record_count = int(emp_count_match.group(1)) if emp_count_match else 0
                
                with st.expander(f"📅 माह: **{month}** (कुल कर्मचारी: {record_count})"):
                    st.success(f"माह **{month}** में कुल **{record_count}** कर्मचारी पाए गए।")
                    st.code(output_text, language='text')

                    st.download_button(
                        label=f"📁 {month}_Above_15_Days.txt डाउनलोड करें",
                        data=output_text.encode("utf-8"),
                        file_name=f"{month}_Above_15_Days.txt",
                        mime="text/plain",
                        key=f"btn_above_{month}"
                    )

        st.markdown("---")

        # --- 15 दिन तक का सेक्शन ---
        st.markdown("### ⬅️ **15 दिन तक** TA वाले कर्मचारी")
        if not upto_15_output or upto_15_output.strip() == "":
            st.warning("फ़ाइल में 15 दिन तक TA वाले कोई कर्मचारी नहीं पाए गए।")
        else:
            emp_count_match = re.search(r'TOTAL AMT\s+[\d\s]+(\d+)', upto_15_output)
            record_count = int(emp_count_match.group(1)) if emp_count_match else 0
            
            st.success(f"कुल **{record_count}** कर्मचारी (15 दिन तक TA) पाए गए।")
            st.code(upto_15_output, language='text')

            st.download_button(
                label="📁 Upto_15_Days.txt डाउनलोड करें",
                data=upto_15_output.encode("utf-8"),
                file_name="Upto_15_Days.txt",
                mime="text/plain",
                key="btn_upto"
            )

if __name__ == "__main__":
    if check_password():
        main_app()
