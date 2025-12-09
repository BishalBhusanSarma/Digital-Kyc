# Digital KYC Prototype – Streamlit Application

This project is a fully interactive Digital KYC (Know Your Customer) onboarding system built using Streamlit, OCR (Tesseract), and Python.  
It replicates a real-world bank-style KYC flow including document upload, OCR extraction, OTP verification, photo verification, and final confirmation.

---

## 🚀 Features

### 1. **Dashboard**
- Displays account number  
- Shows KYC status  
- Button to start or continue KYC  

### 2. **Document Upload**
- Upload PAN and Aadhaar images  
- Automatic OCR-based extraction:
  - PAN number  
  - Name  
  - Date of Birth  
  - Aadhaar number  

### 3. **OTP Verification**
- Enter phone number  
- Sends OTP (prototype uses `1234`)  
- User must verify before moving forward  

### 4. **User Details Review**
- Shows OCR-filled details  
- All fields are editable  

### 5. **Photo Verification**
- Upload ID photo  
- Capture live selfie via camera  
- Prototype auto-verifies match  

### 6. **Final Submission**
- Displays all details + uploaded documents & photos  
- Saves KYC data into `kyc_data.json`  
- Dashboard updates to: **KYC Updated Successfully**  

---

## 🛠️ Tech Stack

| Component | Technology |
|----------|------------|
| Frontend | Streamlit |
| OCR | Tesseract (pytesseract) |
| Image Processing | Pillow (PIL) |
| State Management | Streamlit Session State |
| Data Storage | JSON |
| Styling | Custom CSS |

---

## 📁 Project Structure

