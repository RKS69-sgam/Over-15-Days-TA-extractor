import streamlit as st
import re
import pandas as pd
from io import StringIO

# --- पासवर्ड और कॉन्फ़िगरेशन ---
# सुनिश्चित करें कि आपके Streamlit Cloud Secrets में 'app_password' सेट है
# यदि आप स्थानीय रूप से चला रहे हैं, तो इसे सीधे कोड में सेट करें (या .streamlit/secrets.toml का उपयोग करें)
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

def parse_and_filter_ta_data(data_string):
    """
    अपलोड किए गए टेक्स्ट डेटा को पार्स करता है, 15 दिनों से अधिक TA वाले कर्मचारियों को फ़िल्टर करता है,
    और परिणाम को मूल फ़ाइल प्रारूप में तैयार करता है।
    """
    
    # --- 1. डेटा को लाइनों में तोड़ना और रिकॉर्ड बनाना ---
    lines = data_string.split('\n')
    records = []
    current_record = ""
    
    # डेटा अनुभाग की पहचान के लिए फ्लैग
    data_section_started = False
    
    for line in lines:
        line = line.strip()
        
        # मुख्य डेटा तालिका की शुरुआत
        if "_______________________________________________________________________________________________________________________________________________" in line:
            data_section_started = True
            continue
        
        if "Total :" in line:
            break
            
        if data_section_started:
            # SNO से शुरू होने वाली नई लाइन एक नया रिकॉर्ड शुरू करती है
            # SNO को 1-4 अंकों की संख्या के रूप में पहचानें
            if re.match(r'^\s*(\d{1,4})\s+', line):
                if current_record:
                    records.append(current_record.strip())
                current_record = line
            # विभाजक लाइनों को छोड़ दें
            elif "________________" in line:
                if current_record:
                    records.append(current_record.strip())
                current_record = ""
                continue
            elif current_record:
                # यदि SNO से शुरू नहीं होता है, तो यह पिछले रिकॉर्ड का ही हिस्सा है (wrapped line)
                current_record += " " + line
                
    # अंतिम रिकॉर्ड जोड़ें
    if current_record:
        records.append(current_record.strip())
        
    # फ़िल्टर किए गए रिकॉर्ड और डेटा की गणना के लिए सूची
    filtered_records_with_data = []

    # --- 2. प्रत्येक रिकॉर्ड को प्रोसेस करना और दिनों का योग करना ---
    for record in records:
        # 4 TA वर्गों (20%, 30%, 70%, 100%) के लिए दिनों को कैप्चर करने के लिए Regex
        # यह पैटर्न '*xxx = yyy' से पहले के दिनों की संख्या को खोजता है
        days_matches = re.findall(r'(\d+)\*[0-9\.]+\s*=\s*(\d+)', record)
        
        # सुनिश्चित करें कि 4 TA कॉलम के लिए दिन की प्रविष्टियाँ हैं
        if len(days_matches) == 4:
            # days_matches है: [('0', '0'), ('0', '0'), ('8', '3500'), ('10', '6250')]
            days_20 = int(days_matches[0][0])
            days_30 = int(days_matches[1][0])
            days_70 = int(days_matches[2][0])
            days_100 = int(days_matches[3][0])
            
            total_days = days_20 + days_30 + days_70 + days_100
            
            if total_days > 15:
                
                # अंतिम TOTAL AMOUNT को रिकॉर्ड से निकालें (अंतिम संख्या 0 से पहले)
                total_ta_amount_match = re.search(r'(\d+)\s+0$', record)
                total_ta_amount = int(total_ta_amount_match.group(1)) if total_ta_amount_match else 0

                # SNO को निकालें
                sno_match = re.match(r'^\s*(\d{1,4})\s+', record)
                original_sno = sno_match.group(1).strip() if sno_match else "0"

                filtered_records_with_data.append({
                    'original_sno': original_sno,
                    'record_line': record,
                    'total_ta_amount': total_ta_amount
                })
    
    # --- 3. नया आउटपुट फ़ाइल टेक्स्ट तैयार करना (Total और Rs. in Word के साथ) ---
    
    if not filtered_records_with_data:
        return "फ़ाइल में 15 दिन से अधिक TA वाले कोई कर्मचारी नहीं पाए गए।"

    # नया SNO और कुल TA राशि की गणना
    total_ta_amount_sum = sum(item['total_ta_amount'] for item in filtered_records_with_data)
    total_emp_count = len(filtered_records_with_data)
    
    # शब्दों में राशि के लिए फ़ंक्शन
    def number_to_word(number):
        try:
            import num2words
            return num2words.num2words(number, lang='en').title()
        except ImportError:
            return f"Rupees {number} in Words (Please install 'num2words' for correct text)"


    # आउटपुट टेक्स्ट की मुख्य पंक्ति तैयार करें
    output_text_lines = []
    
    # मूल हेडर (पहले की कुछ लाइनों) को बनाए रखें
    header_start = True
    for line in lines:
        if "______________________________________________________________________________________________________________________________________________" in line:
            header_start = False
            break
        output_text_lines.append(line.strip())

    # 'SNO' वाली लाइन और उसके बाद की लाइनों को हेडर के रूप में फिर से डालें
    output_text_lines.extend([
        "______________________________________________________________________________________________________________________________________________",
        "SNO    EMP NO          NAME           DESIG     GP/    MONTH           20% TA        30% TA   	      70% TA  	        100% TA  TOTAL  CONT        ",
        "                                     	        LEVEL  CLAIM           Amount        Amount   	      Amount   	         Amount  AMOUNT  AMT",
        "															         OF TA",
        "_______________________________________________________________________________________________________________________________________________"
    ])
    
    # प्रत्येक फ़िल्टर किए गए रिकॉर्ड को नए SNO के साथ जोड़ें
    for i, item in enumerate(filtered_records_with_data):
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

# --- Streamlit App Interface ---

def main_app():
    st.set_page_config(page_title="TA 15 Days Filter", layout="centered")

    st.title("यात्रा भत्ता (TA) फ़िल्टर: 15 दिन से अधिक")
    st.markdown("---")

    st.subheader("1. TXT फ़ाइल अपलोड करें")
    uploaded_file = st.file_uploader("कृपया अपनी TA सूची वाली TXT फ़ाइल अपलोड करें।", type="txt")

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        data_string = file_bytes.decode("utf-8")

        st.subheader("2. फ़िल्टर किया गया डेटा")
        
        result_text = parse_and_filter_ta_data(data_string)

        if result_text.startswith("फ़ाइल में"):
            st.warning(result_text)
        else:
            # कर्मचारी काउंट को अंतिम खंड से निकालें
            emp_count_match = re.search(r'TOTAL AMT\s+(\d+)\s+(\d+)', result_text)
            if emp_count_match:
                record_count = emp_count_match.group(2)
                st.success(f"कुल {record_count} कर्मचारी (15 दिन से अधिक TA) पाए गए।")
            else:
                st.success(f"फ़िल्टर किया गया डेटा सफलतापूर्वक तैयार किया गया।")
            
            st.code(result_text, language='text')

            st.download_button(
                label="TXT फ़ाइल डाउनलोड करें",
                data=result_text.encode("utf-8"),
                file_name="TA_Above_15_Days_Filtered.txt",
                mime="text/plain"
            )

if __name__ == "__main__":
    if check_password():
        main_app()
