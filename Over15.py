import streamlit as st
import re
import pandas as pd
from io import StringIO

# --- पासवर्ड और कॉन्फ़िगरेशन ---
CORRECT_PASSWORD = "sgam@4321"

def check_password():
    """Returns True if the user enters the correct password."""
    
    # यदि सेशन स्टेट में 'password_correct' पहले से True है, तो पास करें।
    if st.session_state.get("password_correct", False):
        return True

    st.header("लॉगिन आवश्यक है")
    st.markdown("---")

    # पासवर्ड इनपुट फ़ील्ड
    password = st.text_input(
        "पासवर्ड डालें", type="password", 
        key="password_input", 
        placeholder="sgam@4321"
    )

    # जब उपयोगकर्ता 'Enter' दबाता है, तो पासवर्ड जांचें
    if st.button("लॉगिन"):
        if password == CORRECT_PASSWORD:
            st.session_state["password_correct"] = True
            st.rerun()  # सही होने पर ऐप को फिर से लोड करें
        else:
            st.error("पासवर्ड गलत है। कृपया पुनः प्रयास करें।")
            st.session_state["password_correct"] = False
    
    return False

# --- मुख्य फ़िल्टरिंग लॉजिक फ़ंक्शन (कोई बदलाव नहीं) ---

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
        
        # मुख्य डेटा तालिका की शुरुआत/समाप्ति के लिए मोटे तौर पर जाँच करें
        if "_______________________________________________________________________________________________________________________________________________" in line and not data_section_started:
            data_section_started = True
            continue
        elif "__________________________________________________________________________________________________________________________________________" in line and data_section_started and not re.match(r'^\s*\d+\s+', lines[lines.index(line)+1].strip()):
            # डेटा सेक्शन खत्म हो गया है, या केवल विभाजक है
            continue
        elif "Total :" in line:
            break  # डेटा रिकॉर्ड खत्म हो गए हैं
            
        if data_section_started:
            # SNO से शुरू होने वाली नई लाइन एक नया रिकॉर्ड शुरू करती है
            if re.match(r'^\s*\d+\s+', line):
                if current_record:
                    records.append(current_record.strip())
                current_record = line
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
        days_matches = re.findall(r'(\d+)\*\d+', record)
        
        if len(days_matches) >= 4:
            days_20 = int(days_matches[-4])
            days_30 = int(days_matches[-3])
            days_70 = int(days_matches[-2])
            days_100 = int(days_matches[-1])
            
            total_days = days_20 + days_30 + days_70 + days_100
            
            if total_days > 15:
                
                header_match = re.match(r'^\s*(\d+)\s+(\d+|[A-Z0-9]+)\s+([A-Z\s]+?)\s+([A-Z\s\-]+?)\s+(\d+|[A-Z0-9]+)\s+(Jul25|Aug25|May25|Jun25)', record)
                
                if header_match:
                    original_sno = header_match.group(1).strip()
                    # पूरे रिकॉर्ड को शामिल करें
                    total_ta_amount = int(re.search(r'(\d+)\s+0$', record).group(1)) if re.search(r'(\d+)\s+0$', record) else 0

                    filtered_records_with_data.append({
                        'original_sno': original_sno,
                        'record_line': record,
                        'total_ta_amount': total_ta_amount
                    })
    
    # --- 3. नया आउटपुट फ़ाइल टेक्स्ट तैयार करना (Total और Rs. in Word के साथ) ---
    
    if not filtered_records_with_data:
        return "फ़ाइल में 15 दिन से अधिक TA वाले कोई कर्मचारी नहीं पाए गए।"

    # नया SNO और कुल TA राशि की गणना
    new_sno_map = {item['original_sno']: i + 1 for i, item in enumerate(filtered_records_with_data)}
    total_ta_amount = sum(item['total_ta_amount'] for item in filtered_records_with_data)
    total_emp_count = len(filtered_records_with_data)
    
    # शब्दों में राशि के लिए फ़ंक्शन
    def number_to_word(number):
        try:
            import num2words
            return num2words.num2words(number, lang='en').title()
        except ImportError:
            # यदि num2words इंस्टॉल नहीं है, तो एक साधारण स्ट्रिंग प्रदान करें
            return f"Rupees {number} in Words"


    # आउटपुट टेक्स्ट की मुख्य पंक्ति तैयार करें
    output_text_lines = []
    
    # मूल हेडर लाइनों को बनाए रखें (फ़ाइल के सबसे ऊपर से शुरू)
    header_lines_start_index = 0
    header_lines_end_index = 0
    try:
        header_lines_end_index = lines.index("_______________________________________________________________________________________________________________________________________________")
    except ValueError:
        # यदि विभाजक नहीं मिला तो शुरुआत की 5 लाइनों का अनुमान लगाएं
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
    for item in filtered_records_with_data:
        original_sno_pattern = r'^\s*' + re.escape(item['original_sno']) + r'\s+'
        # पुरानी SNO को नई SNO से बदलें, और रिकॉर्ड को साफ़ करें
        new_record_line = re.sub(original_sno_pattern, f" {new_sno_map[item['original_sno']]:<4} ", item['record_line'])
        output_text_lines.append(new_record_line)
        output_text_lines.append("__________________________________________________________________________________________________________________________________________")

    # अंत में टोटल और Rs. in Word जोड़ें
    total_section = f"""
__________________________________________________________________________________________________________________________________________
							Total :                                                             {total_ta_amount}      0
__________________________________________________________________________________________________________________________________________


 ALLOCATION			  AMOUNT      EMPCOUNT
 ----------------------------------------------------------
   04025116                      {total_ta_amount}         {total_emp_count}
 ----------------------------------------------------------
            TOTAL AMT           {total_ta_amount}         {total_emp_count}

CLAIM MONTH		TA		CONTIGENT	TOTALAMT    RECORD COUNT
_____________________________________________________________________________
   202508            {total_ta_amount}                  0         {total_ta_amount}          {total_emp_count}
_____________________________________________________________________________
         TOTAL AMT   {total_ta_amount}                  0         {total_ta_amount}          {total_emp_count}

FORWARDED  IN DUPLICATE FOR VETTING OF Rs.{total_ta_amount}
( Rs.{number_to_word(total_ta_amount)} Only ) ONLY
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
        # फ़ाइल को स्ट्रिंग के रूप में पढ़ें
        file_bytes = uploaded_file.read()
        data_string = file_bytes.decode("utf-8")

        st.subheader("2. फ़िल्टर किया गया डेटा")
        
        # फ़िल्टरिंग फ़ंक्शन को कॉल करें
        result_text = parse_and_filter_ta_data(data_string)

        if result_text.startswith("फ़ाइल में"):
            st.warning(result_text)
        else:
            # रिकॉर्ड काउंट की साधारण गणना
            record_count = result_text.count('__________________________________________________________________________________________________________________________________________') - 2
            st.success(f"कुल {record_count} कर्मचारी (15 दिन से अधिक TA) पाए गए।")
            
            # आउटपुट टेक्स्ट को प्रदर्शित करें
            st.code(result_text, language='text')

            # डाउनलोड बटन प्रदान करें
            st.download_button(
                label="TXT फ़ाइल डाउनलोड करें",
                data=result_text.encode("utf-8"),
                file_name="TA_Above_15_Days_Filtered.txt",
                mime="text/plain"
            )

# --- ऐप को शुरू करने के लिए मुख्य फ़ंक्शन ---
if __name__ == "__main__":
    if check_password():
        main_app()
    # यदि पासवर्ड सही नहीं है, तो check_password() फ़ंक्शन लॉगिन स्क्रीन दिखाएगा और True return नहीं करेगा।

