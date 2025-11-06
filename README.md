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




