import streamlit as st
from datetime import datetime
from pymongo import MongoClient
from config import MONGO_URL, DB_NAME, COLLECTION_NAME

st.title("Tea Maker App")

# Database connection
try:
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Insert test record
    collection.insert_one({
        "test": "database created",
        "time": datetime.now()
    })

    st.success("Database Connected ✅")

except Exception:
    st.error("Cannot connect to MongoDB. Check if MongoDB is running.")

# User input
user_input = st.text_input(
    "Type anything and press Generate (order does not matter)"
)

if st.button("Generate Tea Steps"):

    if user_input == "":
        st.warning("⚠️ Please type something first!")

    else:
        try:
            steps = [
                "Boil the water",
                "Add tea powder and sugar",
                "Add milk",
                "Boil for a while",
                "Turn off the flame",
                "Strain off and serve"
            ]

            st.subheader("Tea Preparation Steps")

            for i in range(len(steps)):
                st.write(f"{i+1}. {steps[i]}")

            st.success("Tea is ready!! ☕")

        except Exception:
            st.error("❌ Something went wrong while generating steps.")