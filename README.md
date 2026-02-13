# The Sequence Thinker – The Robot Tea Maker
## Logic Summary:
The task is to make a robot follow a sequence of logical steps to prepare tea.
Each step must happen in a proper order and no step should occur before the previous one is completed.

### The process involves:
Boil the water

Add tea powder and sugar 

Add milk

Boil for a while

Turn of the flame

Strain off and serve 

This ensures sequential flow, representing how a real robot would need to think and act step by step.


## Pseudo Code:
```
START 
Boil the water 
Add tea powder and sugar 
Add milk 
Boil for a while 
Turn of the flame 
Strain off and serve 
END
```

## Python Code:
```Python
sequence=['Boil the water', 
'Add tea powder and sugar',
'Add milk',
'Boil for a while', 
'Turn of the flame', 
'Strain off and serve']
for steps in range(0,len(sequence)):
    print(sequence[steps],"\n")
print("Tea is Ready!!")
```

## Code Summary:
In this program, a list named `sequence` is created to store all the steps for making tea, such as boiling water, adding ingredients, and serving.
The `for` loop is used to go through each item (step) in the list one by one using its index number.
The `print()` function then displays each tea-making step in order, followed by a blank line (`"\n"`) for neat spacing.
After the loop finishes printing all the steps, the program finally prints **“Tea is ready!!”** to show that the process is complete.
This program demonstrates sequential flow, where every instruction is executed in the correct order — just like how a robot would follow steps to make tea.

## What I Learned:
Through this task, I learned how to translate real-life activities into a logical, step-by-step process that a computer can execute. Representing everyday tasks algorithmically helped me understand how structured thinking is essential in programming. I also recognized the importance of maintaining the correct order of execution in algorithm design. Each instruction must be logically placed to ensure the desired outcome — similar to how making tea requires a specific sequence of actions.
In addition, I gained practical experience using lists and loops in Python to display multiple steps systematically. This not only simplified the code but also demonstrated how programming concepts can be applied to automate repetitive processes. Overall, this exercise deepened my understanding of how algorithms serve as the foundation of automation, enabling machines to perform routine tasks efficiently and accurately.


## Execution Screenshot:
<img width="410" height="340" alt="image" src="https://github.com/user-attachments/assets/e50617b6-742c-4ae3-af20-2a0e49ccfcdc" />


## Working with MongoDB:
The main objective of this task is to integrate the Python code with MongoDB Compass by establishing a connection between the application and the MongoDB server. This connection enables the Python program to communicate with the database system efficiently. Through this integration, data operations such as creating and storing records can be performed. As a result, a new database is successfully created and managed using Python.

## Error Handling:
Error handling is used to stop the program from crashing when an error occurs during execution. The try block contains the code that may cause a problem, such as connecting to MongoDB or generating steps. If an error happens, the except block runs and shows a friendly error message instead of stopping the app. This makes the application stable, user-friendly, and easier to debug.

## Python Code (Streamlit and MongoDB implementation):
```Python
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
```
## Output Screenshot:
<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/b0c88377-df44-4b45-a2c0-a68111642c92" />

<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/446cf131-794e-4c45-ab84-309c090261ca" />

<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/69eb53bd-ff38-424e-bd2e-cb46bfeadf9a" />

<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/3e6854d1-08e5-41d6-ab05-472f44a9e833" />

<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/e2375dde-355a-475b-8acc-2e1b14098498" />
<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/e2375dde-355a-475b-8acc-2e1b14098498" />

