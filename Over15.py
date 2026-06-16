import streamlit as st
import re
import pandas as pd
from io import StringIO
from datetime import datetime
import locale

# --- पासवर्ड और कॉन्फ़िगरेशन ---
try:
    CORRECT_PASSWORD = st.secrets["app_password"]
except:
    CORRECT_PASSWORD = "sgam@4321"

# --- हिन्दी महीनों का डिक्शनरी (लोकल सेटिंग फेल होने की स्थिति के लिए बैकअप) ---
HINDI_MONTHS = {
    1: "जनवरी", 2: "फ़रवरी", 3: "मार्च", 4: "अप्रैल", 5: "मई", 6: "जून",
    7: "जुलाई", 8: "अगस्त", 9: "सितंबर", 10: "अक्टूबर", 11: "नवंबर", 12: "दिसंबर"
}

# --- सहायक कार्य (Helper Functions) ---

def number_to_words_indian(num):
    """संख्या को भारतीय मुद्रा प्रणाली के अनुसार अंग्रेजी शब्दों में बदलता है। (उदा: Rupees Two Thousand Five Hundred Only)"""
    try:
        num = int(num)
    except (ValueError, TypeError):
        return "Zero"

    if num == 0:
        return "Rupees Zero Only"

    def convert_chunk(n):
        units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", 
                 "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        
        words = []
        if n >= 100:
            words.append(units[n // 100] + " Hundred")
            n %= 100
        if n >= 20:
            words.append(tens[n // 10])
            n %= 10
        if n > 0:
            words.append(units[n])
        return " ".join(words).strip()

    parts = []
    
    # Crores (1,00,00,000)
    if num >= 10000000:
        crores = num // 10000000
        parts.append(convert_chunk(crores) + " Crore")
        num %= 10000000
        
    # Lakhs (100,000)
    if num >= 100000:
        lakhs = num // 100000
        parts.append(convert_chunk(lakhs) + " Lakh")
        num %= 100000
        
    # Thousands (1,000)
    if num >= 1000:
        thousands = num // 1000
        parts.append(convert_chunk(thousands) + " Thousand")
        num %= 1000
        
    # Remaining hundreds/tens/units
    if num > 0:
        parts.append(convert_chunk(num))

    ans = " ".join(parts).strip()
    return f"Rupees {ans} Only"


def get_current_time_details():
    """वर्तमान तिथि, माह और वर्ष को हिंदी और अंग्रेजी प्रारूप में प्राप्त करता है।"""
    now = datetime.now()
    current_date = now.strftime("%d.%m.%Y")
    
    # सबसे पहले लोकल सेटिंग के माध्यम से नाम प्राप्त करने का प्रयास करें
    try:
        # macOS/Linux/Windows अनुकूलित सेटअप
        locale.setlocale(locale.LC_TIME, 'hi_IN.UTF-8')
        current_month_hindi = now.strftime("%B").title()
    except Exception:
        try:
            locale.setlocale(locale.LC_TIME, 'hi_IN')
            current_month_hindi = now.strftime("%B").title()
        except Exception:
            # यदि लोकल सेटिंग पूरी तरह फेल हो जाए, तो हमारे डिक्शनरी मैप का उपयोग करें
            current_month_hindi = HINDI_MONTHS.get(now.month, now.strftime("%B"))

    current_year = now.year
    current_month_numeric = now.strftime("%Y%m") # जैसे: '202606'
    return current_date, current_month_hindi, current_year, current_month_numeric


def check_password():
    """यदि उपयोगकर्ता सही पासवर्ड दर्ज करता है तो True लौटाता है।"""
    if st.session_state.get("password_correct", False):
        return True

    # बेहतर यूज़र इंटरफेस स्टाइलिंग
    st.markdown("""
        <div style="background-color:#1e293b; padding: 20px; border-radius: 10px; margin-bottom: 25px; text-align: center;">
            <h2 style="color:#f8fafc; margin:0;">वरिष्ठ खंड अभियंता (रेल पथ) - सरईग्राम</h2>
            <p style="color:#cbd5e1; margin-top: 5px; font-size:14px;">यात्रा भत्ता (TA) पृथक्करण एवं प्रबंधन प्रणाली</p>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("🔑 लॉगिन आवश्यक है")
    st.write("सॉफ्टवेयर का उपयोग करने के लिए कृपया प्राधिकृत पासवर्ड दर्ज करें।")

    password = st.text_input(
        "पासवर्ड डालें", type="password", 
        key="password_input", 
        placeholder="यहाँ पासवर्ड लिखें"
    )

    if st.button("लॉगिन करें", use_container_width=True):
        if password == CORRECT_PASSWORD:
            st.session_state["password_correct"] = True
            st.success("सफलतापूर्वक लॉगिन हो गया!")
            st.rerun()
        else:
            st.error("पासवर्ड गलत है! कृपया पुनः सही पासवर्ड का प्रयास करें।")
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
        # पहली बार मिलने वाली मुख्य डेकोरेटिव लाइन को खोजें
        for idx, line in enumerate(lines):
            if start_pattern in line:
                start_index = idx
                break
                
        if start_index != -1:
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


def claim_month_to_numeric(month_str):
    """'Jul25' जैसे प्रारूप को '202507' जैसे संख्यात्मक प्रारूप में बदलता है।"""
    match = re.match(r'([A-Za-z]{3})(\d{2})', month_str)
    if match:
        mon_name, year_short = match.groups()
        months_map = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
            "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
        }
        mon_num = months_map.get(mon_name.title(), "01")
        year_long = "20" + year_short
        return f"{year_long}{mon_num}"
    return "Unknown"


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
    
    # क्लेम महीने के बजाय हमेशा वर्तमान महीना और वर्ष का उपयोग
    month_year_text = f"माह {current_month_hindi} {current_year}"
    if filter_type == 'upto':
        subject_detail = "15 दिवस तक के यात्रा भत्ता"
    else:
        subject_detail = f"15 दिवस से अधिक के यात्रा भत्ता ({claim_month})"
        
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

    # --- क्लेम महीना वार सारांश तालिका का निर्माण ---
    month_summary = {}
    for item in filtered_records:
        m_str = item.get('claim_month', 'Unknown_Month')
        m_numeric = claim_month_to_numeric(m_str)
        if m_numeric == "Unknown":
            m_numeric = current_month_numeric
            
        amount = item.get('total_ta_amount', 0)
        
        if m_numeric not in month_summary:
            month_summary[m_numeric] = {
                'ta': 0,
                'contingent': 0,
                'total': 0,
                'count': 0
            }
        month_summary[m_numeric]['ta'] += amount
        month_summary[m_numeric]['total'] += amount
        month_summary[m_numeric]['count'] += 1

    summary_rows = []
    for m_num in sorted(month_summary.keys()):
        stats = month_summary[m_num]
        summary_rows.append(
            f"   {m_num:<17} {stats['ta']:<23} 0         {stats['total']:<14} {stats['count']}"
        )
    summary_table_text = "\n".join(summary_rows)

    # --- 4. अंत में टोटल और Rs. in Word जोड़ें ---
    words_representation = number_to_words_indian(total_ta_amount_sum)
    
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
{summary_table_text}
_____________________________________________________________________________
         TOTAL AMT   {total_ta_amount_sum:<23} 0         {total_ta_amount_sum:<14} {total_emp_count}

FORWARDED  IN DUPLICATE FOR VETTING OF Rs.{total_ta_amount_sum}
( {words_representation} )
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
        line_stripped = line.strip()
        # यदि नई सीरियल संख्या से शुरुआत हो रही है
        if re.match(r'^\s*(\d{1,4})\s+', line):
            if current_record:
                records.append(current_record.strip())
            current_record = line
        elif "________________" in line_stripped:
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
        # दिनों के पैटर्न का मिलान (उदा: 5*150.00 = 750, या 10*500 = 5000)
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

            rec_month = extract_month_from_record(record)

            record_data = {
                'original_sno': original_sno,
                'record_line': record,
                'total_ta_amount': total_ta_amount,
                'claim_month': rec_month
            }

            if total_days > 15:
                if rec_month not in above_15_by_month:
                    above_15_by_month[rec_month] = []
                above_15_by_month[rec_month].append(record_data)
            else:
                upto_15_days_records.append(record_data)

    # 15 दिन से अधिक वाले रिकॉर्ड्स के लिए महीना-वार आउटपुट फाइलें
    above_15_outputs = {}
    for month, m_records in above_15_by_month.items():
        total_m_amount = sum(item['total_ta_amount'] for item in m_records)
        above_15_outputs[month] = create_output_text(
            m_records, total_m_amount, len(m_records), 'above', month
        )
    
    # 15 दिन तक वाले रिकॉर्ड्स के लिए
    total_upto_amount = sum(item['total_ta_amount'] for item in upto_15_days_records)
    upto_15_output = create_output_text(
        upto_15_days_records, total_upto_amount, len(upto_15_days_records), 'upto', 'Combined_Period'
    )
    
    return above_15_outputs, upto_15_output


# --- Streamlit App Interface ---

def main_app():
    st.set_page_config(page_title="TA 15 Days Filter Tool", layout="wide", page_icon="🚄")

    st.title("🚄 यात्रा भत्ता (TA) पृथक्करण एवं फ़िल्टर प्रणाली")
    st.markdown("""
    यह टूल रेलवे यात्रा भत्ता सूचियों (TA Sheets) को स्वचालित रूप से विश्लेषित करता है तथा:
    - **15 दिनों से अधिक** यात्रा करने वाले कर्मचारियों को उनके दावे के **महीने के अनुसार** अलग फाइलों में विभाजित करता है।
    - **15 दिनों तक** यात्रा करने वाले सभी कर्मचारियों की एक संयुक्त फ़ाइल तैयार करता है।
    """)
    st.markdown("---")

    # सूचना बोर्ड
    current_date, current_month_hindi, current_year, _ = get_current_time_details()
    st.info(f"📅 **वर्त्तमान बिलिंग विवरण:** तैयार करने की तिथि: **{current_date}** | आवेदन पत्र माह: **{current_month_hindi} {current_year}**")

    st.subheader("📁 1. TXT फ़ाइल अपलोड करें")
    uploaded_file = st.file_uploader("कृपया अपनी रेलवे TA सूची वाली TXT फ़ाइल यहाँ ड्रैग या ब्राउज करें:", type="txt")

    if uploaded_file is not None:
        try:
            file_bytes = uploaded_file.read()
            data_string = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                data_string = file_bytes.decode("latin-1")
            except Exception as e:
                st.error("फ़ाइल को पढ़ने में त्रुटि हुई। कृपया सुनिश्चित करें कि यह एक मानक टेक्स्ट फ़ाइल (.txt) है।")
                return
        
        st.subheader("⚙️ 2. फ़िल्टर और पृथक्करण के परिणाम")
        
        # प्रसंस्करण शुरू करें
        above_15_outputs, upto_15_output = process_ta_data(data_string)

        col1, col2 = st.columns(2)

        # --- बायां कॉलम: 15 दिन से अधिक का सेक्शन (महीना-वार) ---
        with col1:
            st.markdown("### 🔴 **15 दिन से अधिक** वाले कर्मचारी")
            st.caption("इन कर्मचारियों के दावे को उनके संबंधित महीनों (जैसे Jul25, Aug25) के अनुसार विभाजित किया गया है।")
            
            if not above_15_outputs:
                st.warning("फ़ाइल में 15 दिन से अधिक यात्रा भत्ता वाले कोई कर्मचारी नहीं मिले।")
            else:
                for month, output_text in above_15_outputs.items():
                    emp_count_match = re.search(r'TOTAL AMT\s+[\d\s]+(\d+)', output_text)
                    record_count = int(emp_count_match.group(1)) if emp_count_match else 0
                    
                    with st.expander(f"📅 माह: {month} (कुल कर्मचारी: {record_count})", expanded=True):
                        st.success(f"माह **{month}** में कुल **{record_count}** कर्मचारी मिले।")
                        st.code(output_text, language='text')

                        st.download_button(
                            label=f"📥 {month}_Above_15_Days.txt डाउनलोड करें",
                            data=output_text.encode("utf-8"),
                            file_name=f"{month}_Above_15_Days.txt",
                            mime="text/plain",
                            key=f"btn_above_{month}",
                            use_container_width=True
                        )

        # --- दायां कॉलम: 15 दिन तक का सेक्शन ---
        with col2:
            st.markdown("### 🟢 **15 दिन तक** वाले कर्मचारी")
            st.caption("15 दिन या उससे कम यात्रा भत्ता वाले सभी कर्मचारियों की संयुक्त विवरणी।")
            
            if not upto_15_output or upto_15_output.strip() == "":
                st.warning("फ़ाइल में 15 दिन तक यात्रा भत्ता वाले कोई कर्मचारी नहीं मिले।")
            else:
                emp_count_match = re.search(r'TOTAL AMT\s+[\d\s]+(\d+)', upto_15_output)
                record_count = int(emp_count_match.group(1)) if emp_count_match else 0
                
                with st.expander(f"📅 संयुक्त सूची (कुल कर्मचारी: {record_count})", expanded=True):
                    st.success(f"कुल **{record_count}** कर्मचारी मिले।")
                    st.code(upto_15_output, language='text')

                    st.download_button(
                        label="📥 Upto_15_Days.txt डाउनलोड करें",
                        data=upto_15_output.encode("utf-8"),
                        file_name="Upto_15_Days.txt",
                        mime="text/plain",
                        key="btn_upto",
                        use_container_width=True
                    )

if __name__ == "__main__":
    if check_password():
        main_app()
