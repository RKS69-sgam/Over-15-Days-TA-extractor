import streamlit as st
import re
import pandas as pd
from io import StringIO
from datetime import datetime
import locale

# सिस्टम की लोकल सेटिंग को हिंदी/भारतीय प्रारूप पर सेट करें
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

# --- सहायक कार्य ---

def get_current_time_details():
    """वर्तमान तिथि, माह और वर्ष को हिंदी प्रारूप में प्राप्त करता है।"""
    
    # वर्तमान तिथि को D.M.YYYY फॉर्मेट में प्राप्त करें (उदा: 04.10.2025)
    current_date = datetime.now().strftime("%d.%m.%Y")
    
    # वर्तमान माह का नाम हिंदी में प्राप्त करें (उदा: अक्‍तूबर) और वर्ष
    # .title() सुनिश्चित करता है कि पहला अक्षर कैपिटल हो
    current_month_hindi = datetime.now().strftime("%B").title() 
    current_year = datetime.now().year
    
    return current_date, current_month_hindi, current_year


def check_password():
    """Returns True if the user enters the correct password."""
    
    if st.session_state.get("password_correct", False):
        return True

    st.header("लॉगिन आवश्यक है")
    st.markdown("---")

    password = st.text_input(
        "पासवर्ड डालें", type="password", 
        key="password_input", 
        placeholder="sgam@4321"
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
    """
    अपलोड की गई फ़ाइल से केवल डेटा तालिका अनुभाग को निकालता है।
    """
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
            # हेडर विभाजक को भी शामिल करें
            data_section = lines[start_index:end_index] 
            
    except ValueError:
        return []

    return data_section

def get_claim_month_from_data(data_string):
    """फ़ाइल से क्लेम महीना (जैसे: Jul25) निकालता है।"""
    month_match = re.search(r'(Jul25|Aug25|Sep25|May25|Jun25)', data_string)
    return month_match.group(1) if month_match else "Data"


def create_output_text(filtered_records, total_ta_amount_sum, total_emp_count, data_string, filter_type, claim_month):
    """
    फ़िल्टर किए गए रिकॉर्ड से आउटपुट टेक्स्ट फ़ाइल बनाता है, जिसमें स्थायी नोट और फिक्स्ड हेडर शामिल होते हैं।
    """
    current_date, current_month_hindi, current_year = get_current_time_details()
    
    # शब्दों में राशि के लिए फ़ंक्शन
    def number_to_word(number):
        try:
            import num2words
            return num2words.num2words(number, lang='en').title()
        except ImportError:
            return f"Rupees {number} in Words"

    if not filtered_records:
        if filter_type == 'above':
            return "फ़ाइल में 15 दिन से अधिक TA वाले कोई कर्मचारी नहीं पाए गए।"
        else:
            return "फ़ाइल में 15 दिन तक TA वाले कोई कर्मचारी नहीं पाए गए।"

    # --- 1. आधिकारिक नोट का निर्माण ---
    
    # Base structure
    official_note_base = f"""प0म0रे0 															कार्यालय
सरईग्राम/स्‍टॉफ - IV/TA													 वरिष्‍ठ खण्‍ड अभियंता (रेल पथ)
दिनांक/{current_date}														सरईग्राम

प्रति,
	वरिष्‍ठ मण्‍डल (वित्त प्रबंधक) 
	पमरे जबलपुर

द्वारा :-	उचित माध्‍यम 
"""
    
    # Dynamic Subject Line
    month_year_text = f"माह {current_month_hindi} {current_year}"
    if filter_type == 'upto':
        subject_detail = "15 दिवस तक के यात्रा भत्ता"
    else:
        subject_detail = "15 दिवस से अधिक के यात्रा भत्ता"
        
    subject_line = f"विषय:- 	{month_year_text} की वेतन में लगने वाला {subject_detail} पर प्रतिहस्‍ताक्षर एवं भुगतान की कार्यवाही बावत ।"
    
    # Body
    official_note_body = f"""      उपरोक्‍त विषयानुसार इस डिपो के अधीन पदस्‍थ कर्मचारियों का माह {current_month_hindi} {current_year} के वेतन पत्रक में लगने वाला यात्रा भत्ता की सूची कर्मचारीवार निम्‍नानुसार तैयार कर प्रतिहस्‍ताक्षर एवं भुगतान की अग्रिम कार्यवाही हेतु 
यात्रा भत्ता संलग्‍न सादर प्रेषित है ।
"""
    
    final_official_note = official_note_base + subject_line + "\n\n" + official_note_body
    
    # --- 2. आउटपुट लाइन्स का निर्माण ---
    output_text_lines = []
    
    # आधिकारिक नोट जोड़ें
    output_text_lines.append(final_official_note)
    
    # सामान्य हेडर लाइनों को जोड़ें
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
        
        # SNO को नए क्रम संख्या से बदलें
        new_record_line = re.sub(original_sno_pattern, f" {new_sno:<4} ", item['record_line'], 1)
        output_text_lines.append(new_record_line)
        output_text_lines.append("__________________________________________________________________________________________________________________________________________")

    # --- 4. अंत में टोटल और Rs. in Word जोड़ें ---
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
   202507            {total_ta_amount_sum}                  0         {total_ta_amount_sum}          {total_emp_count}
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

    above_15_days_records = []
    upto_15_days_records = []
    
    for record in records:
        # TA days: (days)*amount=total_amount
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

    # क्लेम महीना निकालें
    claim_month = get_claim_month_from_data(data_string)

    # आउटपुट टेक्स्ट तैयार करें
    total_above_amount = sum(item['total_ta_amount'] for item in above_15_days_records)
    above_15_output = create_output_text(above_15_days_records, total_above_amount, len(above_15_days_records), data_string, 'above', claim_month)
    
    total_upto_amount = sum(item['total_ta_amount'] for item in upto_15_days_records)
    upto_15_output = create_output_text(upto_15_days_records, total_upto_amount, len(upto_15_days_records), data_string, 'upto', claim_month)
    
    return above_15_output, upto_15_output, claim_month


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
        above_15_output, upto_15_output, claim_month = process_ta_data(data_string)

        # --- 15 दिन से अधिक का सेक्शन ---
        st.markdown(f"### ➡️ {claim_month} **15 दिन से अधिक** TA वाले कर्मचारी")
        if above_15_output.startswith("फ़ाइल में"):
            st.warning(above_15_output)
        else:
            # FIX: Total AMT लाइन से कर्मचारी गणना निकालें
            emp_count_match = re.search(r'TOTAL AMT\s+[\d\s]+(\d+)', above_15_output)
            record_count = int(emp_count_match.group(1)) if emp_count_match else 0
            
            st.success(f"कुल **{record_count}** कर्मचारी (15 दिन से अधिक TA) पाए गए।")
            st.code(above_15_output, language='text')

            st.download_button(
                label=f"📁 {claim_month}_**Above_15_Days**.txt डाउनलोड करें",
                data=above_15_output.encode("utf-8"),
                file_name=f"{claim_month}_Above_15_Days.txt",
                mime="text/plain"
            )

        st.markdown("---")

        # --- 15 दिन तक का सेक्शन ---
        st.markdown(f"### ⬅️ {claim_month} **15 दिन तक** TA वाले कर्मचारी")
        if upto_15_output.startswith("फ़ाइल में"):
            st.warning(upto_15_output)
        else:
            # FIX: Total AMT लाइन से कर्मचारी गणना निकालें
            emp_count_match = re.search(r'TOTAL AMT\s+[\d\s]+(\d+)', upto_15_output)
            record_count = int(emp_count_match.group(1)) if emp_count_match else 0
            
            st.success(f"कुल **{record_count}** कर्मचारी (15 दिन तक TA) पाए गए।")
            st.code(upto_15_output, language='text')

            st.download_button(
                label=f"📁 {claim_month}_**Upto_15_Days**.txt डाउनलोड करें",
                data=upto_15_output.encode("utf-8"),
                file_name=f"{claim_month}_Upto_15_Days.txt",
                mime="text/plain"
            )

if __name__ == "__main__":
    if check_password():
        main_app()
