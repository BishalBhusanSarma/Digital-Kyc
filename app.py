import streamlit as st
import pytesseract
from PIL import Image, ImageOps
import re, json, os, io, random

st.set_page_config(page_title="Digital KYC Prototype", layout="wide", initial_sidebar_state="collapsed")


st.markdown("""
<style>
    /* Main background and container */
    .stApp {
        background: linear-gradient(135deg, #004C8F 0%, #0066B2 100%);
    }
    
    /* Content container */
    .main .block-container {
        background: white;
        border-radius: 20px;
        padding: 2rem 3rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        max-width: 1200px;
        margin: 2rem auto;
    }
    
    /* Headers */
    h1 {
        color: #004C8F;
        font-weight: 700;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 2.5rem !important;
    }
    
    h2, h3 {
        color: #004C8F;
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #004C8F 0%, #0066B2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 76, 143, 0.4);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 76, 143, 0.6);
        background: linear-gradient(135deg, #003366 0%, #004C8F 100%);
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #004C8F;
        box-shadow: 0 0 0 3px rgba(0, 76, 143, 0.1);
    }
    
    /* File uploader */
    .stFileUploader {
        background: #f7fafc;
        border: 2px dashed #cbd5e0;
        border-radius: 10px;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: #004C8F;
        background: #edf2f7;
    }
    
    /* Images - smaller scale */
    .stImage {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        max-width: 400px;
        margin: 0 auto;
    }
    
    /* Progress bar styling */
    .progress-container {
        background: #f7fafc;
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    .step {
        display: inline-block;
        padding: 0.75rem 1.5rem;
        margin: 0.25rem;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .step-active {
        background: linear-gradient(135deg, #004C8F 0%, #0066B2 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(0, 76, 143, 0.4);
        transform: scale(1.05);
    }
    
    .step-inactive {
        background: #e2e8f0;
        color: #718096;
    }
    
    /* Info boxes */
    .stInfo, .stSuccess, .stWarning {
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Dashboard card */
    .dashboard-card {
        background: linear-gradient(135deg, #004C8F 0%, #0066B2 100%);
        color: white;
        padding: 3rem;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 20px 60px rgba(0, 76, 143, 0.3);
    }
    
    .dashboard-card h1 {
        color: white !important;
        margin-bottom: 1rem;
    }
    
    .dashboard-info {
        background: rgba(255,255,255,0.2);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    
    .dashboard-info p {
        font-size: 1.2rem;
        margin: 0.5rem 0;
        font-weight: 500;
        color: white;
    }
    
    /* Camera input */
    .stCameraInput {
        border-radius: 15px;
        overflow: hidden;
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(to right, transparent, #004C8F, transparent);
    }
</style>
""", unsafe_allow_html=True)

steps = ["Welcome", "Document Upload", "OTP", "Details", "Photo", "Submit"]

if "step" not in st.session_state:
    st.session_state.step = 0

defaults = {
    "show_dashboard": True,
    "pan_bytes": None,
    "aadhar_bytes": None,
    "scanned_photo_bytes": None,
    "live_photo_bytes": None,
    "name": "",
    "dob": "",
    "pan_number": "",
    "aadhar_number": "",
    "phone": "",
    "otp_verified": False,
    "otp_sent": False,
    "kyc_status": "Pending",
    "account_number": "".join(str(random.randint(0, 9)) for _ in range(12)),
    "ifsc": "HDFC12345"
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def correct_orientation(img):
    try: return ImageOps.exif_transpose(img)
    except: return img

def preprocess_doc(img):
    return correct_orientation(img).resize((1024, 1024))

def preprocess_photo(img):
    return correct_orientation(img).resize((512, 512))

def image_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def extract_text(bytes_data):
    return pytesseract.image_to_string(Image.open(io.BytesIO(bytes_data)))

def parse_pan(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    name = dob = number = None
    for i, line in enumerate(lines):
        m = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]", line)
        if m:
            number = m.group(0).upper()
            for j in range(i + 1, i + 4):
                if j < len(lines):
                    words = re.findall(r"[A-Za-z]+", lines[j])
                    if len(words) >= 3:
                        name = " ".join(words[-3:]).upper()
                        break
            for j in range(i + 1, len(lines)):
                m_dob = re.search(r"\b\d{2}[/-]\d{2}[/-]\d{4}\b", lines[j])
                if m_dob:
                    dob = m_dob.group(0)
                    break
            break
    return name, dob, number

def extract_aadhar(text):
    m = re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", text)
    return m.group(0).replace(" ", "") if m else None

def next_step():
    st.session_state.step += 1
    st.rerun()

def prev_step():
    st.session_state.step -= 1
    st.rerun()

DB_FILE = "kyc_data.json"
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f: json.dump([], f)

def load_db():
    with open(DB_FILE, "r") as f: return json.load(f)

def save_to_db(entry):
    db = load_db()
    db.append(entry)
    with open(DB_FILE, "w") as f: json.dump(db, f)


if st.session_state.show_dashboard:
    st.markdown(f"""
    <div class="dashboard-card">
        <h1>HDFC Digital Banking Dashboard</h1>
        <div class="dashboard-info">
            <p>Account Number: <strong>{st.session_state.account_number}</strong></p>
            <p>KYC Status: <strong>{st.session_state.kyc_status}</strong></p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Start / Continue KYC"):
        st.session_state.show_dashboard = False
        st.session_state.step = 0
        st.rerun()
    st.stop()


# Progress indicator
progress_html = "<div class='progress-container' style='text-align: center;'>"
for i, label in enumerate(steps):
    step_class = "step step-active" if i == st.session_state.step else "step step-inactive"
    progress_html += f"<span class='{step_class}'>{label}</span> "
    if i < len(steps) - 1:
        progress_html += "→ "
progress_html += "</div>"
st.markdown(progress_html, unsafe_allow_html=True)


if st.session_state.step == 0:
    st.title("Welcome to HDFC KYC Portal")
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <p style='font-size: 1.2rem; color: #718096;'>
            Complete your KYC process in just a few simple steps
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("Get Started"): next_step()

elif st.session_state.step == 1:
    st.title("Upload Your Documents")
    st.markdown("<p style='text-align: center; color: #718096;'>Please upload clear images of your PAN and Aadhar cards</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("PAN Card")
        pan_file = st.file_uploader("Upload PAN Card", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if pan_file:
            img = preprocess_doc(Image.open(pan_file))
            st.session_state.pan_bytes = image_to_bytes(img)
            name, dob, pan_number = parse_pan(extract_text(st.session_state.pan_bytes))
            st.session_state.name = name or ""
            st.session_state.dob = dob or ""
            st.session_state.pan_number = pan_number or ""
        if st.session_state.pan_bytes:
            st.image(st.session_state.pan_bytes, width=300)

    with col2:
        st.subheader("Aadhar Card")
        aadhar_file = st.file_uploader("Upload Aadhar Card", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if aadhar_file:
            img = preprocess_doc(Image.open(aadhar_file))
            st.session_state.aadhar_bytes = image_to_bytes(img)
            st.session_state.aadhar_number = extract_aadhar(extract_text(st.session_state.aadhar_bytes)) or ""
        if st.session_state.aadhar_bytes:
            st.image(st.session_state.aadhar_bytes, width=300)

    st.markdown("<br>", unsafe_allow_html=True)
    cp, cn = st.columns(2)
    if cp.button("Previous"): prev_step()
    if cn.button("Next"):
        if not st.session_state.pan_bytes or not st.session_state.aadhar_bytes:
            st.warning("Please upload both documents to proceed.")
        else: next_step()

elif st.session_state.step == 2:
    st.title("Phone Verification")
    st.markdown("<p style='text-align: center; color: #718096;'>Verify your phone number with OTP</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.session_state.phone = st.text_input("Phone Number", value=st.session_state.phone)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if not st.session_state.otp_sent:
            if st.button("Send OTP"):
                st.session_state.otp_sent = True
                st.rerun()
        
        if st.session_state.otp_sent:
            st.info("OTP Sent to your phone! (Use 1234 for demo)")
            otp_input = st.text_input("Enter OTP")
            
            if st.button("Verify OTP"):
                if otp_input == "1234":
                    st.session_state.otp_verified = True
                else:
                    st.session_state.otp_verified = False
                    st.error("Invalid OTP. Please try again.")
        
        if st.session_state.otp_verified:
            st.success("OTP Verified Successfully!")

    st.markdown("<br>", unsafe_allow_html=True)
    cp, cn = st.columns(2)
    if cp.button("Previous"): prev_step()
    if cn.button("Next"):
        if not st.session_state.phone:
            st.warning("Please enter your phone number.")
        elif not st.session_state.otp_sent:
            st.warning("Please send OTP first.")
        elif not st.session_state.otp_verified:
            st.warning("Please verify OTP to proceed.")
        else: next_step()

elif st.session_state.step == 3:
    st.title("Edit Your Details")
    st.markdown("<p style='text-align: center; color: #718096;'>Review and update your information</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.name = st.text_input("Full Name", st.session_state.name)
        st.session_state.dob = st.text_input("Date of Birth", st.session_state.dob)
        st.session_state.pan_number = st.text_input("PAN Number", st.session_state.pan_number)
    
    with col2:
        st.session_state.aadhar_number = st.text_input("Aadhar Number", st.session_state.aadhar_number)
        st.session_state.account_number = st.text_input("Account Number", st.session_state.account_number)
        st.session_state.ifsc = st.text_input("IFSC Code", st.session_state.ifsc)

    st.markdown("<br>", unsafe_allow_html=True)
    cp, cn = st.columns(2)
    if cp.button("Previous"): prev_step()
    if cn.button("Next"): next_step()

elif st.session_state.step == 4:
    st.title("Photo Verification")
    st.markdown("<p style='text-align: center; color: #718096;'>Upload and capture your photo for verification</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Upload ID Photo")
        uploaded_photo = st.file_uploader("Upload your photo", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if uploaded_photo:
            st.session_state.scanned_photo_bytes = image_to_bytes(preprocess_photo(Image.open(uploaded_photo)))
        if st.session_state.scanned_photo_bytes:
            st.image(st.session_state.scanned_photo_bytes, width=300)

    with col2:
        st.subheader("Capture Live Photo")
        live_capture = st.camera_input("Take a selfie", label_visibility="collapsed")
        if live_capture:
            st.session_state.live_photo_bytes = image_to_bytes(preprocess_photo(Image.open(live_capture)))
        if st.session_state.live_photo_bytes:
            st.image(st.session_state.live_photo_bytes, width=300)

    if st.session_state.scanned_photo_bytes and st.session_state.live_photo_bytes:
        st.success("Photo Verification Complete!")
    elif st.session_state.scanned_photo_bytes or st.session_state.live_photo_bytes:
        st.info("Please provide both photos to continue.")
    else:
        st.warning("Please upload and capture your photos.")

    st.markdown("<br>", unsafe_allow_html=True)
    cp, cn = st.columns(2)
    if cp.button("Previous"): prev_step()
    if cn.button("Next"):
        if not st.session_state.scanned_photo_bytes or not st.session_state.live_photo_bytes:
            st.warning("Please upload and capture both photos to proceed.")
        else: next_step()

elif st.session_state.step == 5:
    st.title("Final Review")
    st.markdown("<p style='text-align: center; color: #718096;'>Review all your information before submission</p>", unsafe_allow_html=True)

    st.subheader("Personal Information")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.name = st.text_input("Full Name", st.session_state.name)
        st.session_state.dob = st.text_input("Date of Birth", st.session_state.dob)
        st.session_state.pan_number = st.text_input("PAN Number", st.session_state.pan_number)
    
    with col2:
        st.session_state.aadhar_number = st.text_input("Aadhar Number", st.session_state.aadhar_number)
        st.session_state.account_number = st.text_input("Account Number", st.session_state.account_number)
        st.session_state.ifsc = st.text_input("IFSC Code", st.session_state.ifsc)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Uploaded Documents & Photos")
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.pan_bytes:
            st.markdown("**PAN Card**")
            st.image(st.session_state.pan_bytes, width=300)
        if st.session_state.aadhar_bytes:
            st.markdown("**Aadhar Card**")
            st.image(st.session_state.aadhar_bytes, width=300)
    
    with col2:
        if st.session_state.scanned_photo_bytes:
            st.markdown("**ID Photo**")
            st.image(st.session_state.scanned_photo_bytes, width=300)
        if st.session_state.live_photo_bytes:
            st.markdown("**Live Photo**")
            st.image(st.session_state.live_photo_bytes, width=300)

    st.markdown("<br>", unsafe_allow_html=True)
    cp, cs = st.columns(2)
    if cp.button("Previous"): prev_step()
    if cs.button("Submit Application"):
        save_to_db({
            "name": st.session_state.name,
            "dob": st.session_state.dob,
            "phone": st.session_state.phone,
            "pan_number": st.session_state.pan_number,
            "aadhar_number": st.session_state.aadhar_number,
            "account_number": st.session_state.account_number,
            "ifsc": st.session_state.ifsc
        })
        st.session_state.kyc_status = "Updated Successfully"
        st.session_state.show_dashboard = True
        st.session_state.step = 0
        st.rerun()