from rag.chunker import Chunker
from rag.vector_store import index, embed_text

RAW_TEXT = """
Block 1: General Identity & Contact
Context: Basic business details for Smile Care Dental Clinic. Content: Smile Care Dental Clinic is located at Sco No 40 First Floor, Near Hotel Magestic, Mohali Sas Nagar, Mohali-160055, Punjab. It is a highly-rated dental clinic (5.0 stars) offering comprehensive oral health care.

Block 2: Operational Hours & Appointments
Context: How to visit or contact the clinic. Content: The clinic is functional from 09:00 AM to 07:45 PM. Appointments can be booked online or via a phone call to the hospital helpline. While known for intensive care, patients should contact the helpline directly for specific 24x7 emergency service availability.

Block 3: Specialized Services (Laser & Surgery)
Context: Advanced treatments at Smile Care Dental Clinic. Content: The clinic is a specialty center for Laser Dentistry. Specialized services include minimally invasive treatments using advanced laser systems, digital X-rays for precise diagnostics, and Root Canal Treatment (RCT).

Block 4: Cosmetic & Orthodontic Services
Context: Aesthetic and alignment treatments. Content: Services include cosmetic procedures like smile makeovers, teeth whitening, and orthodontic treatments such as traditional braces and clear aligners.

Block 5: Patient Care Philosophy
Context: Experience and environment. Content: The clinic uses a patient-centric approach with a well-trained clinical team. It prioritizes patient comfort to reduce dental anxiety, providing a stress-free environment and personalized treatment plans tailored to busy lifestyles.
"""

# 1️⃣ Initialize chunker
chunker = Chunker(chunk_size=250, overlap=35)

# 2️⃣ Chunk the raw text
chunks = chunker.chunk_text(RAW_TEXT)

# 3️⃣ Build FAISS vectors
vectors = []
metadata = []
for i, chunk in enumerate(chunks):
    vec = embed_text(chunk).flatten()
    vectors.append(vec)
    metadata.append(chunk)

# 4️⃣ Add to FAISS index and save
import numpy as np
import json
vectors_array = np.array(vectors).astype('float32')
index.add(vectors_array)

# Save metadata
with open("/home/anandchoudhary/Documents/MVP_Project/ai-dental-receptionist/backend/rag/clinic_meta.json", "w") as f:
    json.dump(metadata, f)

print(f"✅ Ingested {len(vectors)} chunks into FAISS index")
