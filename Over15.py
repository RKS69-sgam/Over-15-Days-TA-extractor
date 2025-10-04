import streamlit as st
import re
import pandas as pd
from io import StringIO

# --- पासवर्ड और कॉन्फ़िगरेशन ---
try:
    CORRECT_PASSWORD = st.secrets["app_password"]
except:
    CORRECT_PASSWORD = "sgam@4321"

def check_password():
    """Returns True if the user enters the correct password."""
    
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

# --- मुख्य फ़िल्टरिंग लॉजिक फ़ंक्शन ---

def create_output_text(filtered_records, total_ta_amount_sum, total_emp_count, data_string, filter_type):
    """
    फ़िल्टर किए गए रिकॉर्ड से आउटपुट टेक्स्ट फ़ाइल बनाता है।
    filter_type: 'above' or 'upto'
    """
    lines = data_string.split('\n')
    
    # शब्दों में राशि के लिए फ़ंक्शन
    def number_to_word(number):
        try:
            import num2words
            return num2words.num2words(number, lang='en').title()
        except ImportError:
            return f"Rupees {number} in Words (Please install 'num2words' for correct text)"

    if not filtered_records:
        if filter_type == 'above':
            return "फ़ाइल में 15 दिन से अधिक TA वाले कोई कर्मचारी नहीं पाए गए।"
        else:
            return "फ़ाइल में 15 दिन तक TA वाले कोई कर्मचारी नहीं पाए गए।"

    output_text_lines = []
    
    # मूल हेडर लाइनों को बनाए रखें (फ़ाइल के सबसे ऊपर से शुरू)
    header_lines_end_index = 0
    try:
        header_lines_end_index = lines.index("_______________________________________________________________________________________________________________________________________________")
    except ValueError:
        header_lines_end_index = 5 
        
    for i in range(header_lines_end_index + 1):
        output_text_lines.append(lines[i].strip())
    
    # 'SNO' वाली लाइन और उसके बाद की लाइनों को हेडर के रूप में फिर से डालें
    output_text_lines.extend([
        "______________________________________________________________________________________________________________________________________________",
        "SNO    EMP NO          NAME           DESIG     GP/    MONTH           20% TA        30% TA   	      70% TA  	        100% TA  TOTAL  CONT        ",
        "                                     	        LEVEL  CLAIM           Amount        Amount   	      Amount   	         Amount  AMOUNT  AMT",
        "															         OF TA",
        "_______________________________________________________________________________________________________________________________________________"
    ])
    
    # प्रत्येक फ़िल्टर किए गए रिकॉर्ड को नए SNO के साथ जोड़ें
    for i, item in enumerate(filtered_records):
        new_sno = i + 1
        original_sno_pattern = r'^\s*' + re.escape(item['original_sno']) + r'\s+'
        # पुरानी SNO को नई SNO से बदलें (फिक्स्ड-चौड़ाई का ध्यान रखते हुए)
        new_record_line = re.sub(original_sno_pattern, f" {new_sno:<4} ", item['record_line'])
        output_text_lines.append(new_record_line)
        output_text_lines.append("__________________________________________________________________________________________________________________________________________")

    # अंत में टोटल और Rs. in Word जोड़ें
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
   202508            {total_ta_amount_sum}                  0         {total_ta_amount_sum}          {total_emp_count}
_____________________________________________________________________________
         TOTAL AMT   {total_ta_amount_sum}                  0         {total_ta_amount_sum}          {total_emp_count}

FORWARDED  IN DUPLICATE FOR VETTING OF Rs.{total_ta_amount_sum}
( Rs.{number_to_word(total_ta_amount_sum)} Only ) ONLY
& RETURN TO THIS OFFICE
FOR DRAWL IN THE REGULAR SALARY BILL.
THE BILL WAS NOT DRAWN PREVIOUSLY AND WILL NOT BE DRAWN IN FUTURE
"""
    output_text_lines.append(total_section)
    
    # Footer Lines
    output_text_lines.extend([
        "",
        "                                                                                    ",
        "                                                                                  WEST CENTRAL RAILWAY   ",
        "                                                                          JABALPUR DIVISION",
        "                                                              -------------",
    ])

    return "\n".join(output_text_lines)

def process_ta_data(data_string):
    """
    सभी रिकॉर्ड को पार्स करता है और उन्हें 15 दिन तक और 15 दिन से अधिक के लिए अलग करता है।
    """
    lines = data_string.split('\n')
    records = []
    current_record = ""
    data_section_started = False
    
    for line in lines:
        line = line.strip()
        
        if "_______________________________________________________________________________________________________________________________________________" in line:
            data_section_started = True
            continue
        
        if "Total :" in line:
            break
            
        if data_section_started:
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

    # दो फ़िल्टर की गई सूचियाँ
    above_15_days_records = []
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
                above_15_days_records.append(record_data)
            else:
                upto_15_days_records.append(record_data)

    # आउटपुट टेक्स्ट तैयार करें
    
    # 15 दिन से अधिक के लिए आउटपुट
    total_above_amount = sum(item['total_ta_amount'] for item in above_15_days_records)
    above_15_output = create_output_text(above_15_days_records, total_above_amount, len(above_15_days_records), data_string, 'above')
    
    # 15 दिन तक के लिए आउटपुट
    total_upto_amount = sum(item['total_ta_amount'] for item in upto_15_days_records)
    upto_15_output = create_output_text(upto_15_days_records, total_upto_amount, len(upto_15_days_records), data_string, 'upto')
    
    return above_15_output, upto_15_output


# --- Streamlit App Interface ---

def main_app():
    st.set_page_config(page_title="TA 15 Days Filter", layout="centered")

    st.title("यात्रा भत्ता (TA) फ़िल्टर: 15 दिन तक और 15 दिन से अधिक")
    st.markdown("---")

    st.subheader("1. TXT फ़ाइल अपलोड करें")
    uploaded_file = st.file_uploader("कृपया अपनी TA सूची वाली TXT फ़ाइल अपलोड करें।", type="txt")

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        data_string = file_bytes.decode("utf-8")

        st.subheader("2. फ़िल्टर किया गया डेटा")
        
        # दोनों सूचियों को प्रोसेस करें
        above_15_output, upto_15_output = process_ta_data(data_string)

        # --- 15 दिन से अधिक का सेक्शन ---
        st.markdown("### 15 दिन से अधिक TA वाले कर्मचारी")
        if above_15_output.startswith("फ़ाइल में"):
            st.warning(above_15_output)
        else:
            record_count = len(re.findall(r"__________________________________________________________________________________________________________________________________________", above_15_output)) - 1
            st.success(f"कुल **{record_count}** कर्मचारी (15 दिन से अधिक TA) पाए गए।")
            st.code(above_15_output, language='text')

            st.download_button(
                label="📁 **15 दिन से अधिक** की TXT फ़ाइल डाउनलोड करें",
                data=above_15_output.encode("utf-8"),
                file_name="TA_Above_15_Days_Filtered.txt",
                mime="text/plain"
            )

        st.markdown("---")

        # --- 15 दिन तक का सेक्शन ---
        st.markdown("### 15 दिन तक TA वाले कर्मचारी")
        if upto_15_output.startswith("फ़ाइल में"):
            st.warning(upto_15_output)
        else:
            record_count = len(re.findall(r"__________________________________________________________________________________________________________________________________________", upto_15_output)) - 1
            st.success(f"कुल **{record_count}** कर्मचारी (15 दिन तक TA) पाए गए।")
            st.code(upto_15_output, language='text')

            st.download_button(
                label="📁 **15 दिन तक** की TXT फ़ाइल डाउनलोड करें",
                data=upto_15_output.encode("utf-8"),
                file_name="TA_Upto_15_Days_Filtered.txt",
                mime="text/plain"
            )

if __name__ == "__main__":
    if check_password():
        main_app()
