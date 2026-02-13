import streamlit as st
from pymongo import MongoClient
st.title("Tea Maker App")
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["Tea_Maker"]
    collection = db["Algorithm"]
    collection.insert_one({"test": "database created"})
    st.success("Database Connected ✅")
except Exception:
    st.error("Cannot connect to MongoDB. Check if MongoDB is running.")
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